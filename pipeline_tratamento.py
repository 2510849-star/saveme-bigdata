"""Tratamento e documentos analíticos Steam, sem conexão ou carga em banco."""

import argparse
import ast
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from bson import BSON
import pandas as pd


COLUNAS = """appid name release_date required_age price dlc_count
detailed_description about_the_game short_description reviews header_image website
support_url support_email windows mac linux metacritic_score metacritic_url
achievements recommendations notes supported_languages full_audio_languages packages
developers publishers categories genres screenshots movies user_score score_rank
positive negative estimated_owners average_playtime_forever average_playtime_2weeks
median_playtime_forever median_playtime_2weeks discount peak_ccu tags pct_pos_total
num_reviews_total pct_pos_recent num_reviews_recent""".split()
LISTAS = {
    "genres": "generos", "developers": "desenvolvedores", "publishers": "publicadoras",
    "categories": "categorias", "supported_languages": "idiomas_suportados",
    "full_audio_languages": "idiomas_audio", "screenshots": "capturas", "movies": "videos",
}
METRICAS = ["pct_pos_total", "num_reviews_total", "pct_pos_recent", "num_reviews_recent"]


class ErroValidacao(ValueError):
    """Dados incompatíveis com o contrato de entrada."""


def ausente(valor):
    return valor is None or (not isinstance(valor, (list, dict)) and bool(pd.isna(valor)))


def texto(valor, campo, contagens, obrigatorio=False):
    if ausente(valor) or (isinstance(valor, str) and not valor.strip()):
        if obrigatorio:
            raise ErroValidacao(f"{campo}: texto obrigatório ausente")
        contagens[f"{campo}: ausente para None"] += 1
        return None
    if not isinstance(valor, str):
        raise ErroValidacao(f"{campo}: esperado texto")
    # Títulos 'none' e 'Unknown' podem ser legítimos: não são marcadores automáticos.
    return valor


def numero(valor, campo, inteiro=True, opcional=False):
    if ausente(valor):
        if opcional:
            return None
        raise ErroValidacao(f"{campo}: número obrigatório ausente")
    if isinstance(valor, bool):
        raise ErroValidacao(f"{campo}: booleano não é número válido")
    try:
        convertido = float(valor)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ErroValidacao(f"{campo}: esperado número finito") from exc
    if not math.isfinite(convertido) or (inteiro and not convertido.is_integer()):
        raise ErroValidacao(f"{campo}: esperado {'inteiro' if inteiro else 'número'} finito")
    if inteiro and abs(convertido) > 2**53 - 1:
        raise ErroValidacao(f"{campo}: inteiro fora da faixa segura de conversão")
    return int(convertido) if inteiro else convertido


def nao_negativo(valor, campo, inteiro=True, opcional=False):
    convertido = numero(valor, campo, inteiro, opcional)
    if convertido is not None and convertido < 0:
        raise ErroValidacao(f"{campo}: valor negativo não permitido")
    return convertido


def lista_textual(valor, campo, contagens):
    if ausente(valor) or (isinstance(valor, str) and not valor.strip()):
        contagens[f"{campo}: ausente para []"] += 1
        return []
    if isinstance(valor, str):
        try:
            itens = ast.literal_eval(valor)
        except (ValueError, SyntaxError, TypeError, RecursionError) as exc:
            raise ErroValidacao(f"{campo}: lista textual inválida") from exc
        contagens[f"{campo}: lista textual convertida"] += 1
    else:
        itens = valor
    if not isinstance(itens, list):
        raise ErroValidacao(f"{campo}: esperado uma lista")
    saida = []
    for item in itens:
        if item is None or (isinstance(item, str) and not item.strip()):
            contagens[f"{campo}: elementos vazios removidos"] += 1
            continue
        if not isinstance(item, str):
            raise ErroValidacao(f"{campo}: elementos devem ser textos")
        normalizado = item.strip()
        if normalizado != item:
            contagens[f"{campo}: elementos com espaços normalizados"] += 1
        saida.append(normalizado)
    if not saida:
        contagens[f"{campo}: listas vazias na saída"] += 1
    return saida


def faixa_proprietarios(valor, contagens):
    bruto = texto(valor, "estimated_owners", contagens)
    if bruto is None:
        return {"bruto": None, "limite_inferior": None, "limite_superior": None}
    correspondencia = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", bruto)
    if not correspondencia:
        raise ErroValidacao("estimated_owners: esperado intervalo inteiro - inteiro")
    inferior, superior = map(int, correspondencia.groups())
    if inferior > superior or superior > 2**63 - 1:
        raise ErroValidacao("estimated_owners: limites invertidos ou fora de int64")
    contagens["estimated_owners: faixas extraídas"] += 1
    return {"bruto": bruto, "limite_inferior": inferior, "limite_superior": superior}


def validar_esquema(df):
    if df.columns.duplicated().any():
        raise ErroValidacao("Esquema: nomes de colunas duplicados")
    faltantes = sorted(set(COLUNAS) - set(df.columns))
    if faltantes:
        raise ErroValidacao("Esquema: colunas obrigatórias ausentes: " + ", ".join(faltantes))


def validar_appids(df, vistos):
    ids = []
    for indice, valor in df["appid"].items():
        try:
            appid = nao_negativo(valor, "appid")
            if appid == 0:
                raise ErroValidacao("appid: deve ser maior que zero")
        except ErroValidacao as exc:
            raise ErroValidacao(f"Linha de dados {indice + 1}: {exc}") from exc
        if appid in vistos:
            raise ErroValidacao(f"Linha de dados {indice + 1}: appid duplicado: {appid}")
        vistos.add(appid)
        ids.append(appid)
    return ids


def transformar_jogo(linha, contagens=None):
    """Converte uma linha sem mutá-la; retorna somente tipos Python/BSON nativos."""
    if contagens is None:
        contagens = Counter()
    appid = nao_negativo(linha["appid"], "appid")
    if appid == 0:
        raise ErroValidacao("appid: deve ser maior que zero")
    nome = texto(linha["name"], "name", contagens, obrigatorio=True)
    data_bruta = texto(linha["release_date"], "release_date", contagens)
    data_iso = None
    if data_bruta is not None:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data_bruta):
                raise ValueError("formato")
            data_iso = datetime.strptime(data_bruta, "%Y-%m-%d").date().isoformat()
        except ValueError as exc:
            raise ErroValidacao("release_date: esperado data válida AAAA-MM-DD") from exc
        contagens["release_date: datas validadas"] += 1
    catalogo = {destino: lista_textual(linha[origem], origem, contagens)
                for origem, destino in LISTAS.items()}
    plataformas = {}
    for campo in ["windows", "mac", "linux"]:
        valor = linha[campo]
        if ausente(valor):
            plataformas[campo] = None
            contagens[f"{campo}: ausente para None"] += 1
        elif isinstance(valor, bool):
            plataformas[campo] = valor
        else:
            raise ErroValidacao(f"{campo}: esperado booleano")
    catalogo["plataformas"] = plataformas
    idade_bruta = numero(linha["required_age"], "required_age", opcional=True)
    idade = idade_bruta if idade_bruta is not None and idade_bruta >= 0 else None
    if idade_bruta is None or idade_bruta < 0:
        contagens["required_age: indisponível para None"] += 1
    catalogo["idade_minima"] = {"bruto": idade_bruta, "tratado": idade}
    for campo, destino in [("dlc_count", "quantidade_dlcs"), ("achievements", "conquistas")]:
        catalogo[destino] = nao_negativo(linha[campo], campo, opcional=True)
        if catalogo[destino] is None:
            contagens[f"{campo}: ausente para None"] += 1
    positivas = nao_negativo(linha["positive"], "positive")
    negativas = nao_negativo(linha["negative"], "negative")
    total = positivas + negativas
    taxa = positivas / total * 100 if total > 0 else None
    contagens["avaliacoes: taxa calculada" if total else "avaliacoes: denominador zero para None"] += 1
    metricas = {}
    for campo in METRICAS:
        bruto = numero(linha[campo], campo, opcional=True)
        if bruto is not None and (bruto < -1 or (campo.startswith("pct_") and bruto > 100)):
            raise ErroValidacao(f"{campo}: fora do domínio (-1 ou valor válido não negativo)")
        tratado = None if bruto == -1 else bruto
        if bruto == -1:
            contagens[f"{campo}: sentinela -1 para None"] += 1
        elif bruto is None:
            contagens[f"{campo}: ausente para None"] += 1
        metricas[campo] = {"bruto": bruto, "tratado": tratado}
    precos = {"valor": nao_negativo(linha["price"], "price", inteiro=False),
              "desconto_percentual": nao_negativo(linha["discount"], "discount")}
    if precos["desconto_percentual"] > 100:
        raise ErroValidacao("discount: deve estar entre 0 e 100")
    # Ausência da categoria não comprova uma classificação comercial oposta.
    explicito = any(g.casefold() == "free to play" for g in catalogo["generos"])
    catalogo["free_to_play_explicito"] = explicito
    contagens["catalogo: Free To Play explícito"] += int(explicito)
    contagens["preco: zero preservado"] += int(precos["valor"] == 0)
    popularidade = {"proprietarios_estimados": faixa_proprietarios(linha["estimated_owners"], contagens)}
    campos_popularidade = {
        "peak_ccu": "pico_jogadores_simultaneos", "recommendations": "recomendacoes",
        "average_playtime_forever": "tempo_medio_total",
        "average_playtime_2weeks": "tempo_medio_duas_semanas",
        "median_playtime_forever": "tempo_mediano_total",
        "median_playtime_2weeks": "tempo_mediano_duas_semanas",
    }
    for campo, destino in campos_popularidade.items():
        popularidade[destino] = nao_negativo(linha[campo], campo, opcional=True)
        if popularidade[destino] is None:
            contagens[f"{campo}: ausente para None"] += 1
    textos = {
        "short_description": "descricao_curta", "about_the_game": "sobre",
        "detailed_description": "descricao_detalhada", "reviews": "resenhas",
        "notes": "notas", "website": "site", "header_image": "imagem_cabecalho",
        "support_url": "suporte_url", "support_email": "suporte_email",
        "metacritic_url": "metacritic_url",
    }
    adicionais = {destino: texto(linha[campo], campo, contagens) for campo, destino in textos.items()}
    scores = {}
    for campo in ["metacritic_score", "user_score", "score_rank"]:
        scores[campo] = nao_negativo(linha[campo], campo, inteiro=campo != "score_rank", opcional=True)
        if scores[campo] is None:
            contagens[f"{campo}: ausente para None"] += 1
        if campo != "score_rank" and scores[campo] is not None and scores[campo] > 100:
            raise ErroValidacao(f"{campo}: deve estar entre 0 e 100")
    return {
        "appid": appid, "nome": nome,
        "lancamento": {"bruto": data_bruta, "data_iso": data_iso},
        "catalogo": catalogo, "preco": precos,
        "avaliacoes": {"positivas": positivas, "negativas": negativas, "total": total,
                       "taxa_positivas_percentual": taxa, "metricas_fonte": metricas, "scores": scores},
        "popularidade": popularidade, "informacoes": adicionais,
        "origem": {"plataforma": "Steam", "mes_referencia": "2025-03",
                   "arquivo": "games_march2025_cleaned.csv"},
        "versao_documento": 1,
    }


def sha256(caminho):
    with caminho.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def iterar_documentos(caminho, tamanho_lote=2000, relatorio=None):
    """Produz documentos um a um; finaliza o relatório ao esgotar o iterador.

    Reutilizado pela análise e pela carga, mantendo uma única implementação das regras.
    """
    if tamanho_lote <= 0:
        raise ValueError("tamanho_lote deve ser positivo")
    if relatorio is None:
        relatorio = {}
    caminho = Path(caminho)
    hash_antes = sha256(caminho)
    vistos, nulos, transformacoes, motivos = set(), Counter(), Counter(), Counter()
    entrada = saida = rejeitados = 0
    exemplos_rejeitados = []
    colunas = []
    with pd.read_csv(caminho, low_memory=False, chunksize=tamanho_lote) as leitor:
        for lote in leitor:
            validar_esquema(lote)
            validar_appids(lote, vistos)  # Falha global: não escolhe arbitrariamente duplicados.
            colunas = list(lote.columns)
            entrada += len(lote)
            nulos.update({c: int(n) for c, n in lote.isna().sum().items()})
            for linha in lote.to_dict(orient="records"):
                contagens_linha = Counter()
                try:
                    documento = transformar_jogo(linha, contagens_linha)
                    # Verificação local do formato BSON; não cria cliente de banco.
                    if len(BSON.encode(documento)) > 16 * 1024 * 1024:
                        raise ErroValidacao("documento: excede 16 MiB")
                    json.dumps(documento, allow_nan=False)
                except (ErroValidacao, OverflowError) as exc:
                    rejeitados += 1
                    motivos[str(exc)] += 1
                    if len(exemplos_rejeitados) < 10:
                        exemplos_rejeitados.append({"appid": int(linha["appid"]), "motivo": str(exc)})
                    continue
                transformacoes.update(contagens_linha)
                saida += 1
                yield documento
    if not colunas:  # CSV apenas com cabeçalho também deve ter esquema válido.
        validar_esquema(pd.read_csv(caminho, nrows=0))
    hash_depois = sha256(caminho)
    if hash_antes != hash_depois:
        raise ErroValidacao("Integridade: o CSV mudou durante o processamento")
    relatorio.update({
        "colecao_destino_prevista": "jogos_analiticos", "mongo_conectado": False,
        "origem": caminho.name, "pandas": pd.__version__,
        "sha256_antes": hash_antes, "sha256_depois": hash_depois, "csv_preservado": True,
        "colunas_entrada": len(colunas) if colunas else len(COLUNAS),
        "colunas_extras": sorted(set(colunas) - set(COLUNAS)),
        "entrada": entrada, "appid_distintos": len(vistos), "rejeitados": rejeitados,
        "saida": saida, "documentos_bson_verificados": saida,
        "nulos_entrada_por_campo": dict(nulos), "nulos_entrada_total": sum(nulos.values()),
        "transformacoes_documentos_aceitos": dict(sorted(transformacoes.items())),
        "motivos_rejeicao": dict(motivos), "exemplos_rejeitados": exemplos_rejeitados,
    })


def processar_csv(caminho, tamanho_lote=2000):
    """API anterior preservada: relatório completo e até três amostras."""
    relatorio, amostras = {}, []
    for documento in iterar_documentos(caminho, tamanho_lote, relatorio):
        if len(amostras) < 3:
            amostras.append(documento)
    return relatorio, amostras


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("data/games_march2025_cleaned.csv"))
    parser.add_argument("--saida", type=Path, default=Path("outputs/tratamento"))
    args = parser.parse_args()
    # Impede que a saída substitua o arquivo original, inclusive por link simbólico.
    destinos = [args.saida / "qualidade.json", args.saida / "amostra_documentos.json"]
    if any(p.resolve() == args.csv.resolve() for p in destinos):
        parser.error("A saída não pode sobrescrever o CSV original")
    try:
        relatorio, amostras = processar_csv(args.csv)
    except (OSError, ErroValidacao, pd.errors.ParserError) as exc:
        parser.exit(1, f"Erro no pipeline: {exc}\n")
    args.saida.mkdir(parents=True, exist_ok=True)
    for destino, dados in zip(destinos, [relatorio, amostras]):
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    print(f"Somente relatório e {len(amostras)} amostras em {args.saida}. Nenhuma carga em banco.")


if __name__ == "__main__":
    main()
