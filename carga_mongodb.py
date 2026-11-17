"""Carga idempotente Steam em saveme_analytics.jogos_analiticos."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

from bson.codec_options import CodecOptions
from bson.raw_bson import RawBSONDocument
from pymongo import ASCENDING, MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError, PyMongoError

from pipeline_tratamento import ErroValidacao, iterar_documentos
import pandas as pd


BANCO = "saveme_analytics"
COLECAO = "jogos_analiticos"
URI_PADRAO = "mongodb://127.0.0.1:27017/"


class ErroCarga(RuntimeError):
    """Erro sanitizado; não inclui URI, credenciais ou documentos."""


def conectar():
    cliente = None
    try:
        cliente = MongoClient(os.environ.get("MONGODB_URI", URI_PADRAO),
                              serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                              socketTimeoutMS=30000, appname="saveme-n3")
        cliente.admin.command("ping")
        return cliente
    except (PyMongoError, ValueError):
        if cliente is not None:
            cliente.close()
        raise ErroCarga("MongoDB indisponível ou configuração inválida; verifique o serviço e MONGODB_URI.") from None


def tem_indice_appid_unico(indices):
    return any(info.get("unique") is True and list(info["key"]) == [("appid", ASCENDING)]
               and not info.get("sparse") and not info.get("partialFilterExpression")
               for info in indices.values())


def assinatura_estado(colecao):
    """Hash dos BSONs efetivamente persistidos, incluindo _id, ordenados por appid."""
    digest = hashlib.sha256()
    raw = colecao.with_options(codec_options=CodecOptions(document_class=RawBSONDocument))
    with closing(raw.find({}).sort("appid", ASCENDING).batch_size(1000)) as cursor:
        for documento in cursor:
            digest.update(documento.raw)
    return digest.hexdigest()


def verificar_colecao(colecao, incluir_assinatura=False):
    total = colecao.count_documents({})
    grupos = list(colecao.aggregate([
        {"$group": {"_id": "$appid", "quantidade": {"$sum": 1}}},
        {"$group": {"_id": None, "appid_distintos": {"$sum": 1},
                     "grupos_duplicados": {"$sum": {"$cond": [{"$gt": ["$quantidade", 1]}, 1, 0]}}}},
    ], allowDiskUse=True))
    resumo = grupos[0] if grupos else {"appid_distintos": 0, "grupos_duplicados": 0}
    indices = colecao.index_information()
    unico = tem_indice_appid_unico(indices)
    exemplos = list(colecao.find({}, {"_id": 0, "appid": 1, "nome": 1, "preco": 1,
                                      "avaliacoes.taxa_positivas_percentual": 1,
                                      "origem": 1}).sort("appid", ASCENDING).limit(3))
    resultado = {"total_documentos": total, "appid_distintos": resumo["appid_distintos"],
                 "grupos_appid_duplicados": resumo["grupos_duplicados"],
                 "indice_appid_unico": unico, "exemplos": exemplos}
    if incluir_assinatura:
        resultado["sha256_estado_bson"] = assinatura_estado(colecao)
    return resultado


def carregar(colecao, caminho, tamanho_lote=1000, estatisticas=None):
    """Usa o iterador existente; retém somente um lote de operações por vez."""
    if tamanho_lote <= 0:
        raise ValueError("tamanho_lote deve ser positivo")
    stats = estatisticas if estatisticas is not None else {}
    stats.update({"status": "em_andamento", "inseridos": 0, "atualizados": 0,
                  "correspondentes": 0, "inalterados": 0, "lotes_confirmados": 0,
                  "documentos_confirmados": 0, "rejeitados": None,
                  "processamento_concluido": False, "resultado_lote_incerto": False})
    inicio = perf_counter()
    documentos_lote, tratamento = [], {}

    def registrar(resultado):
        stats["inseridos"] += resultado.upserted_count
        stats["correspondentes"] += resultado.matched_count
        stats["atualizados"] += resultado.modified_count
        stats["inalterados"] += resultado.matched_count - resultado.modified_count
        stats["documentos_confirmados"] += resultado.upserted_count + resultado.matched_count

    def enviar_lote():
        try:
            ids = {d["appid"]: d["_id"] for d in colecao.find(
                {"appid": {"$in": [d["appid"] for d in documentos_lote]}}, {"appid": 1, "_id": 1})}
        except PyMongoError:
            raise ErroCarga("Falha ao consultar identificadores; este lote não foi enviado.") from None
        # MongoDB 8.0.38 pode contabilizar substituição sem _id como modificação
        # mesmo quando o BSON final é idêntico. Preserva a identidade existente.
        operacoes = [ReplaceOne(
            {"appid": d["appid"]},
            {"_id": ids[d["appid"]], **d} if d["appid"] in ids else d,
            upsert=True) for d in documentos_lote]
        try:
            resultado = colecao.bulk_write(operacoes, ordered=False)
        except BulkWriteError as exc:
            # Usa somente contagens; detalhes podem conter documentos/segredos.
            detalhes = exc.details or {}
            stats["inseridos"] += detalhes.get("nUpserted", 0)
            stats["correspondentes"] += detalhes.get("nMatched", 0)
            stats["atualizados"] += detalhes.get("nModified", 0)
            stats["inalterados"] += detalhes.get("nMatched", 0) - detalhes.get("nModified", 0)
            stats["documentos_confirmados"] += detalhes.get("nUpserted", 0) + detalhes.get("nMatched", 0)
            stats["erros_escrita_lote"] = len(detalhes.get("writeErrors", []))
            stats["resultado_lote_incerto"] = bool(detalhes.get("writeConcernErrors"))
            raise ErroCarga("Falha parcial de escrita em lote; confira as contagens e reexecute por appid.") from None
        except PyMongoError:
            stats["resultado_lote_incerto"] = True
            raise ErroCarga("Conexão/escrita interrompida; o último lote pode ter sido aplicado parcialmente.") from None
        registrar(resultado)
        stats["lotes_confirmados"] += 1
        documentos_lote.clear()

    try:
        if not tem_indice_appid_unico(colecao.index_information()):
            colecao.create_index([("appid", ASCENDING)], unique=True, name="appid_unico")
        with closing(iterar_documentos(caminho, tamanho_lote, tratamento)) as documentos:
            for documento in documentos:
                documentos_lote.append(documento)
                if len(documentos_lote) == tamanho_lote:
                    enviar_lote()
        if documentos_lote:
            enviar_lote()
        stats["tratamento"] = tratamento
        stats["rejeitados"] = tratamento["rejeitados"]
        stats["processamento_concluido"] = True
        stats["status"] = "concluido"
    except Exception:
        stats["status"] = "falhou"
        raise
    finally:
        stats["duracao_segundos"] = round(perf_counter() - inicio, 3)
    return stats


def executar(caminho, tamanho_lote=1000, segunda_carga=False, somente_verificar=False, relatorio=None):
    relatorio = relatorio if relatorio is not None else {}
    relatorio.update({"executado_em_utc": datetime.now(timezone.utc).isoformat(),
                      "banco": BANCO, "colecao": COLECAO, "status": "em_andamento",
                      "conexao_confirmada": False, "cargas": []})
    inicio = perf_counter()
    cliente = None
    try:
        cliente = conectar()
        relatorio["conexao_confirmada"] = True
        colecao = cliente[BANCO][COLECAO]
        relatorio["antes"] = verificar_colecao(colecao)
        if not somente_verificar:
            for numero_carga in range(2 if segunda_carga else 1):
                stats = {"execucao": numero_carga + 1}
                relatorio["cargas"].append(stats)
                carregar(colecao, caminho, tamanho_lote, stats)
                stats["verificacao"] = verificar_colecao(colecao, incluir_assinatura=segunda_carga)
                if stats["verificacao"]["grupos_appid_duplicados"] or not stats["verificacao"]["indice_appid_unico"]:
                    raise ErroCarga("Verificação falhou: appid duplicado ou índice único ausente.")
            if segunda_carga:
                primeira, segunda = relatorio["cargas"]
                relatorio["estado_final_identico"] = (
                    primeira["verificacao"]["total_documentos"] == segunda["verificacao"]["total_documentos"]
                    and primeira["verificacao"]["sha256_estado_bson"] == segunda["verificacao"]["sha256_estado_bson"]
                    and primeira["tratamento"]["sha256_antes"] == segunda["tratamento"]["sha256_antes"])
                relatorio["segunda_carga_sem_modificacoes"] = segunda["inseridos"] == 0 and segunda["atualizados"] == 0
                relatorio["idempotencia_comprovada"] = (
                    relatorio["estado_final_identico"] and relatorio["segunda_carga_sem_modificacoes"])
                if not relatorio["idempotencia_comprovada"]:
                    raise ErroCarga("Segunda carga não confirmou idempotência; confira alterações concorrentes e a origem.")
        relatorio["depois"] = verificar_colecao(colecao)
        relatorio["status"] = "concluido"
    except (ErroCarga, PyMongoError, ValueError, OSError, pd.errors.ParserError) as exc:
        relatorio["status"] = "falhou"
        # Nunca repassa mensagens de drivers, URIs ou conteúdo de documentos.
        relatorio["erro"] = str(exc) if isinstance(exc, ErroCarga) else "Falha de validação, arquivo ou MongoDB; nenhuma credencial foi registrada."
        raise ErroCarga(relatorio["erro"]) from None
    finally:
        if cliente is not None:
            cliente.close()
        relatorio["duracao_segundos"] = round(perf_counter() - inicio, 3)
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("data/games_march2025_cleaned.csv"))
    parser.add_argument("--tamanho-lote", type=int, default=1000)
    parser.add_argument("--comprovar-idempotencia", action="store_true")
    parser.add_argument("--verificar", action="store_true", help="Apenas consultar, sem escrever ou criar índice")
    parser.add_argument("--relatorio", type=Path, default=Path("outputs/mongodb/carga.json"))
    args = parser.parse_args()
    if args.tamanho_lote <= 0:
        parser.error("--tamanho-lote deve ser positivo")
    if args.relatorio.resolve() == args.csv.resolve():
        parser.error("O relatório não pode sobrescrever o CSV")
    relatorio = {}
    codigo = 0
    try:
        executar(args.csv, args.tamanho_lote, args.comprovar_idempotencia, args.verificar, relatorio)
    except ErroCarga:
        codigo = 1
    args.relatorio.parent.mkdir(parents=True, exist_ok=True)
    args.relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    raise SystemExit(codigo)


if __name__ == "__main__":
    main()
