import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from bson import BSON, ObjectId
from bson.raw_bson import RawBSONDocument
from pymongo.errors import BulkWriteError, ConnectionFailure, OperationFailure

from carga_mongodb import ErroCarga, carregar, conectar, executar, verificar_colecao
from tests.test_pipeline_tratamento import jogo


class CursorSimulado(list):
    def sort(self, campo, direcao):
        return CursorSimulado(sorted(self, key=lambda doc: doc[campo]))

    def limit(self, quantidade):
        return CursorSimulado(self[:quantidade])

    def batch_size(self, quantidade):
        return self

    def close(self):
        pass


class ColecaoSimulada:
    """Modelo em memória apenas para testar o contrato de escrita/consulta usado."""
    def __init__(self):
        self.documentos = {}
        self.lotes = []
        self.indices = {}

    def create_index(self, chaves, **opcoes):
        self.indices[opcoes["name"]] = {"key": chaves, "unique": opcoes["unique"]}
        return opcoes["name"]

    def bulk_write(self, operacoes, ordered):
        self.lotes.append(len(operacoes))
        inseridos = correspondentes = alterados = 0
        for operacao in operacoes:
            # PyMongo não fornece getters públicos das operações de bulk.
            assert operacao._upsert is True
            chave = operacao._filter["appid"]
            documento = copy.deepcopy(operacao._doc)
            if chave not in self.documentos:
                inseridos += 1
                documento.setdefault("_id", ObjectId())
            else:
                correspondentes += 1
                # Reproduz o comportamento observado no servidor 8.0.38.
                sem_id = "_id" not in documento
                documento.setdefault("_id", self.documentos[chave]["_id"])
                alterados += sem_id or BSON.encode(self.documentos[chave]) != BSON.encode(documento)
            self.documentos[chave] = documento
        return SimpleNamespace(upserted_count=inseridos, matched_count=correspondentes, modified_count=alterados)

    def count_documents(self, filtro):
        return len(self.documentos)

    def aggregate(self, pipeline, **opcoes):
        return ([{"appid_distintos": len(self.documentos), "grupos_duplicados": 0}]
                if self.documentos else [])

    def index_information(self):
        return self.indices

    def find(self, filtro, projecao=None):
        documentos = list(self.documentos.values())
        if "appid" in filtro:
            documentos = [d for d in documentos if d["appid"] in filtro["appid"]["$in"]]
        if projecao is None:
            return CursorSimulado(RawBSONDocument(BSON.encode(d)) for d in documentos)
        if projecao.get("_id") == 1:
            return CursorSimulado({"appid": d["appid"], "_id": d["_id"]} for d in documentos)
        return CursorSimulado({"appid": d["appid"], "nome": d["nome"]} for d in documentos)

    def with_options(self, **opcoes):
        return self


class TestCargaMongoDB(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.csv = Path(self.pasta.name) / "dados.csv"
        pd.DataFrame([jogo(appid=i) for i in range(1, 6)]).to_csv(self.csv, index=False)
        self.colecao = ColecaoSimulada()

    def cliente_simulado(self):
        cliente = Mock()
        cliente.__getitem__ = Mock(return_value={"jogos_analiticos": self.colecao})
        return cliente

    def test_lotes_upsert_e_idempotencia(self):
        primeira = carregar(self.colecao, self.csv, tamanho_lote=2)
        self.assertEqual(self.colecao.lotes, [2, 2, 1])
        self.assertEqual(primeira["inseridos"], 5)
        self.assertEqual(primeira["atualizados"], 0)
        self.assertEqual(primeira["rejeitados"], 0)
        self.assertTrue(self.colecao.indices["appid_unico"]["unique"])
        segunda = carregar(self.colecao, self.csv, tamanho_lote=3)
        self.assertEqual(len(self.colecao.documentos), 5)
        self.assertEqual((segunda["inseridos"], segunda["atualizados"], segunda["inalterados"]), (0, 0, 5))
        self.assertTrue(segunda["tratamento"]["csv_preservado"])

    def test_retomada_apos_interrupcao_preserva_ids_e_duas_cargas(self):
        bulk_original = self.colecao.bulk_write
        chamadas = 0

        def interromper(operacoes, ordered):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise ConnectionFailure("interrupção simulada")
            return bulk_original(operacoes, ordered)

        self.colecao.bulk_write = interromper
        with self.assertRaises(ErroCarga):
            carregar(self.colecao, self.csv, 2)
        self.assertEqual(len(self.colecao.documentos), 2)
        ids = {k: v["_id"] for k, v in self.colecao.documentos.items()}
        self.colecao.bulk_write = bulk_original
        retomada = carregar(self.colecao, self.csv, 2)
        self.assertEqual((retomada["inseridos"], retomada["atualizados"], retomada["inalterados"]), (3, 0, 2))
        for chave, identidade in ids.items():
            self.assertEqual(self.colecao.documentos[chave]["_id"], identidade)
        cliente = self.cliente_simulado()
        with patch("carga_mongodb.conectar", return_value=cliente):
            resultado = executar(self.csv, 2, segunda_carga=True)
        self.assertTrue(resultado["estado_final_identico"])
        self.assertTrue(resultado["segunda_carga_sem_modificacoes"])
        self.assertTrue(resultado["idempotencia_comprovada"])

    def test_preserva_tipo_int64_e_id_objectid(self):
        from bson.int64 import Int64
        carregar(self.colecao, self.csv)
        identidade = self.colecao.documentos[1]["_id"]
        self.colecao.documentos[1]["appid"] = Int64(1)
        primeira = carregar(self.colecao, self.csv)
        segunda = carregar(self.colecao, self.csv)
        self.assertEqual(primeira["atualizados"], 1)
        self.assertEqual(segunda["atualizados"], 0)
        self.assertEqual(self.colecao.documentos[1]["_id"], identidade)

    def test_atualizacao_substitui_documento_sem_duplicar(self):
        carregar(self.colecao, self.csv)
        # Campo obsoleto deve desaparecer na substituição, preservando identidade appid.
        self.colecao.documentos[1]["campo_obsoleto"] = True
        dados = pd.read_csv(self.csv)
        dados.loc[dados["appid"] == 1, "name"] = "Nome atualizado"
        dados.to_csv(self.csv, index=False)
        stats = carregar(self.colecao, self.csv)
        self.assertEqual((stats["inseridos"], stats["atualizados"], stats["inalterados"]), (0, 1, 4))
        self.assertEqual(self.colecao.documentos[1]["nome"], "Nome atualizado")
        self.assertNotIn("campo_obsoleto", self.colecao.documentos[1])

    def test_rejeicao_reutiliza_validacao_existente(self):
        pd.DataFrame([jogo(appid=1), jogo(appid=2, genres="invalido")]).to_csv(self.csv, index=False)
        stats = carregar(self.colecao, self.csv, 1)
        self.assertEqual((stats["inseridos"], stats["rejeitados"]), (1, 1))
        self.assertEqual(stats["tratamento"]["entrada"], 2)

    def test_falha_conexao_fecha_cliente_e_nao_expoe_uri(self):
        cliente = Mock()
        cliente.admin.command.side_effect = ConnectionFailure("mongodb://usuario:senha@servidor")
        with patch("carga_mongodb.MongoClient", return_value=cliente), self.assertRaises(ErroCarga) as erro:
            conectar()
        self.assertNotIn("senha", str(erro.exception))
        cliente.close.assert_called_once()

    def test_uri_do_ambiente_e_ping(self):
        cliente = Mock()
        with patch.dict("os.environ", {"MONGODB_URI": "mongodb://exemplo:27017/"}), \
                patch("carga_mongodb.MongoClient", return_value=cliente) as construtor:
            self.assertIs(conectar(), cliente)
        self.assertEqual(construtor.call_args.args[0], "mongodb://exemplo:27017/")
        cliente.admin.command.assert_called_once_with("ping")

    def test_erro_bulk_parcial_registra_contagens_sem_documentos(self):
        self.colecao.bulk_write = Mock(side_effect=BulkWriteError({
            "nUpserted": 1, "nMatched": 0, "nModified": 0,
            "writeErrors": [{"errmsg": "senha secreta", "op": {"conteudo": "sensivel"}}],
            "writeConcernErrors": []}))
        stats = {}
        with self.assertRaises(ErroCarga) as erro:
            carregar(self.colecao, self.csv, 2, stats)
        self.assertEqual(stats["status"], "falhou")
        self.assertEqual(stats["inseridos"], 1)
        self.assertEqual(stats["erros_escrita_lote"], 1)
        self.assertNotIn("secreta", str(erro.exception) + json.dumps(stats))

    def test_erro_rede_marca_lote_incerto(self):
        self.colecao.bulk_write = Mock(side_effect=ConnectionFailure("segredo"))
        stats = {}
        with self.assertRaises(ErroCarga):
            carregar(self.colecao, self.csv, 2, stats)
        self.assertTrue(stats["resultado_lote_incerto"])
        self.assertFalse(stats["processamento_concluido"])
        self.assertIsNone(stats["rejeitados"])

    def test_falha_leitura_ids_nao_envia_lote(self):
        self.colecao.find = Mock(side_effect=ConnectionFailure("segredo"))
        stats = {}
        with self.assertRaisesRegex(ErroCarga, "lote não foi enviado"):
            carregar(self.colecao, self.csv, 2, stats)
        self.assertEqual(self.colecao.lotes, [])
        self.assertFalse(stats["resultado_lote_incerto"])

    def test_contagem_estavel_sem_modificacoes_nao_basta_se_estado_mudou(self):
        cliente = self.cliente_simulado()
        relatorio = {}
        with patch("carga_mongodb.conectar", return_value=cliente), \
                patch("carga_mongodb.assinatura_estado", side_effect=["hash_a", "hash_b"]), \
                self.assertRaises(ErroCarga):
            executar(self.csv, 2, segunda_carga=True, relatorio=relatorio)
        self.assertTrue(relatorio["segunda_carga_sem_modificacoes"])
        self.assertFalse(relatorio["estado_final_identico"])
        self.assertFalse(relatorio["idempotencia_comprovada"])

    def test_estado_identico_nao_oculta_modificacoes_reportadas(self):
        original = self.colecao.bulk_write

        def reportar_modificacao(operacoes, ordered):
            resultado = original(operacoes, ordered)
            resultado.modified_count = resultado.matched_count
            return resultado

        self.colecao.bulk_write = reportar_modificacao
        cliente = self.cliente_simulado()
        relatorio = {}
        with patch("carga_mongodb.conectar", return_value=cliente), self.assertRaises(ErroCarga):
            executar(self.csv, 2, segunda_carga=True, relatorio=relatorio)
        self.assertTrue(relatorio["estado_final_identico"])
        self.assertFalse(relatorio["segunda_carga_sem_modificacoes"])
        self.assertFalse(relatorio["idempotencia_comprovada"])

    def test_indice_incompativel_interrompe_antes_da_carga(self):
        self.colecao.create_index = Mock(side_effect=OperationFailure("índice incompatível"))
        with self.assertRaises(OperationFailure):
            carregar(self.colecao, self.csv)
        self.assertEqual(self.colecao.lotes, [])

    def test_reutiliza_indice_unico_existente_com_outro_nome(self):
        self.colecao.indices["appid_1"] = {"key": [("appid", 1)], "unique": True}
        self.colecao.create_index = Mock(side_effect=AssertionError("Não deve recriar índice equivalente"))
        carregar(self.colecao, self.csv)
        self.colecao.create_index.assert_not_called()

    def test_indice_parcial_nao_e_prova_de_unicidade_global(self):
        self.colecao.indices["parcial"] = {"key": [("appid", 1)], "unique": True,
                                            "partialFilterExpression": {"appid": {"$gt": 0}}}
        self.assertFalse(verificar_colecao(self.colecao)["indice_appid_unico"])

    def test_verificacao_contagem_indice_e_tres_exemplos(self):
        carregar(self.colecao, self.csv)
        verificacao = verificar_colecao(self.colecao)
        self.assertEqual(verificacao["total_documentos"], 5)
        self.assertEqual(verificacao["appid_distintos"], 5)
        self.assertEqual(verificacao["grupos_appid_duplicados"], 0)
        self.assertTrue(verificacao["indice_appid_unico"])
        self.assertEqual([d["appid"] for d in verificacao["exemplos"]], [1, 2, 3])

    def test_executar_duas_cargas_e_fechar_cliente(self):
        cliente = self.cliente_simulado()
        with patch("carga_mongodb.conectar", return_value=cliente):
            relatorio = executar(self.csv, 2, segunda_carga=True)
        self.assertTrue(relatorio["idempotencia_comprovada"])
        self.assertEqual(len(relatorio["cargas"]), 2)
        self.assertEqual(relatorio["depois"]["total_documentos"], 5)
        cliente.close.assert_called_once()

    def test_verificar_nao_escreve_nem_cria_indice(self):
        cliente = self.cliente_simulado()
        with patch("carga_mongodb.conectar", return_value=cliente):
            relatorio = executar(self.csv, somente_verificar=True)
        self.assertEqual(self.colecao.lotes, [])
        self.assertEqual(self.colecao.indices, {})
        self.assertEqual(relatorio["cargas"], [])

    def test_bloqueio_nao_fabrica_contagens(self):
        relatorio = {}
        with patch("carga_mongodb.conectar", side_effect=ErroCarga("Indisponível")), \
                self.assertRaises(ErroCarga):
            executar(self.csv, relatorio=relatorio)
        self.assertFalse(relatorio["conexao_confirmada"])
        self.assertEqual(relatorio["cargas"], [])
        self.assertNotIn("depois", relatorio)

    def test_tamanho_lote_invalido(self):
        with self.assertRaises(ValueError):
            carregar(self.colecao, self.csv, 0)


if __name__ == "__main__":
    unittest.main()
