import copy
from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest

from bson import BSON
import pandas as pd

from pipeline_tratamento import (
    COLUNAS, LISTAS, METRICAS, ErroValidacao, faixa_proprietarios,
    lista_textual, processar_csv, transformar_jogo, validar_appids, validar_esquema,
)


def jogo(**alteracoes):
    linha = dict.fromkeys(COLUNAS, None)
    linha.update({"appid": 123, "name": "Jogo", "release_date": "2025-03-01",
                  "required_age": 0, "price": 0.0, "discount": 0,
                  "positive": 3, "negative": 1, "estimated_owners": "0 - 20000",
                  "windows": True, "mac": False, "linux": False})
    linha.update(dict.fromkeys(LISTAS, "[]"))
    linha.update(dict.fromkeys(METRICAS, 0))
    linha.update(alteracoes)
    return linha


class TestTransformacao(unittest.TestCase):
    def test_documento_normal_e_formatos(self):
        doc = transformar_jogo(jogo(genres="['Action', 'Free To Play']"))
        self.assertEqual(doc["avaliacoes"]["taxa_positivas_percentual"], 75.0)
        self.assertTrue(doc["catalogo"]["free_to_play_explicito"])
        self.assertEqual(doc["lancamento"]["data_iso"], "2025-03-01")
        self.assertEqual(doc["origem"]["mes_referencia"], "2025-03")
        self.assertIs(type(doc["appid"]), int)
        self.assertEqual(BSON(BSON.encode(doc)).decode(), doc)
        json.dumps(doc, allow_nan=False)

    def test_nao_muta_entrada(self):
        linha = jogo(genres=[" Action ", ""])
        original = copy.deepcopy(linha)
        transformar_jogo(linha)
        self.assertEqual(linha, original)

    def test_listas_vazias_nulas_e_espacos(self):
        for valor in [None, float("nan"), pd.NA, "", "  ", "[]"]:
            with self.subTest(valor=valor):
                self.assertEqual(lista_textual(valor, "genres", Counter()), [])
        contagens = Counter()
        self.assertEqual(lista_textual("[' Action ', '', ' ', None]", "genres", contagens), ["Action"])
        self.assertEqual(contagens["genres: elementos vazios removidos"], 3)

    def test_listas_invalidas_nao_executam_codigo(self):
        for valor in ["[", "{'a': 1}", "'Action'", "[1]", "[True]", "[['Action']]",
                      "__import__('os').getcwd()"]:
            with self.subTest(valor=valor), self.assertRaisesRegex(ErroValidacao, "genres"):
                lista_textual(valor, "genres", Counter())

    def test_publicadora_item_vazio(self):
        self.assertEqual(transformar_jogo(jogo(publishers="['']"))["catalogo"]["publicadoras"], [])

    def test_nulos_opcionais_e_titulo_legitimo(self):
        doc = transformar_jogo(jogo(name="Unknown", required_age=None, release_date=None,
                                    estimated_owners=None, windows=None))
        self.assertEqual(doc["nome"], "Unknown")
        self.assertIsNone(doc["informacoes"]["descricao_curta"])
        self.assertIsNone(doc["lancamento"]["data_iso"])
        self.assertIsNone(doc["popularidade"]["proprietarios_estimados"]["limite_inferior"])
        self.assertIsNone(doc["catalogo"]["plataformas"]["windows"])

    def test_idade_negativa_preserva_bruto(self):
        for idade in [-1, -2]:
            self.assertEqual(transformar_jogo(jogo(required_age=idade))["catalogo"]["idade_minima"],
                             {"bruto": idade, "tratado": None})

    def test_sentinelas_e_nulos_metricas(self):
        for campo in METRICAS:
            for valor in [-1, None, 0, 25]:
                with self.subTest(campo=campo, valor=valor):
                    metrica = transformar_jogo(jogo(**{campo: valor}))["avaliacoes"]["metricas_fonte"][campo]
                    self.assertEqual(metrica, {"bruto": valor, "tratado": None if valor == -1 else valor})
            with self.assertRaises(ErroValidacao):
                transformar_jogo(jogo(**{campo: -2}))

    def test_avaliacoes_sem_denominador(self):
        doc = transformar_jogo(jogo(positive=0, negative=0))
        self.assertIsNone(doc["avaliacoes"]["taxa_positivas_percentual"])
        self.assertEqual(transformar_jogo(jogo(positive=0))["avaliacoes"]["taxa_positivas_percentual"], 0)

    def test_preco_zero_nao_define_free_to_play(self):
        doc = transformar_jogo(jogo(price=0, genres="['Action']"))
        self.assertEqual(doc["preco"]["valor"], 0)
        self.assertFalse(doc["catalogo"]["free_to_play_explicito"])
        self.assertTrue(transformar_jogo(jogo(price=10, genres="['Free To Play']"))["catalogo"]["free_to_play_explicito"])

    def test_faixas_validas_e_invalidas(self):
        for valor, limites in [("0 - 0", (0, 0)), (" 20 - 50 ", (20, 50))]:
            faixa = faixa_proprietarios(valor, Counter())
            self.assertEqual(faixa["bruto"], valor)
            self.assertEqual((faixa["limite_inferior"], faixa["limite_superior"]), limites)
        for valor in ["20 - 10", "-1 - 10", "20", "a - b", "0 - 9223372036854775808"]:
            with self.subTest(valor=valor), self.assertRaises(ErroValidacao):
                faixa_proprietarios(valor, Counter())

    def test_numeros_obrigatorios_invalidos(self):
        for campo, valores in {"appid": [0, -1, 1.5, True, None, float("inf")],
                               "price": [-1, None, float("inf"), "abc"],
                               "discount": [101, -1, 1.5], "positive": [-1, None],
                               "negative": [-1, None]}.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor), self.assertRaises(ErroValidacao):
                    transformar_jogo(jogo(**{campo: valor}))

    def test_nome_data_plataforma_e_percentual_invalidos(self):
        for mudanca in [{"name": " "}, {"release_date": "2025-02-30"},
                        {"release_date": "01/03/2025"}, {"windows": "yes"},
                        {"pct_pos_total": 101}, {"metacritic_score": 101}]:
            with self.subTest(mudanca=mudanca), self.assertRaises(ErroValidacao):
                transformar_jogo(jogo(**mudanca))


class TestPipeline(unittest.TestCase):
    def test_esquema_faltante_e_duplicado(self):
        with self.assertRaisesRegex(ErroValidacao, "colunas obrigatórias ausentes"):
            validar_esquema(pd.DataFrame({"appid": [1]}))
        with self.assertRaisesRegex(ErroValidacao, "colunas duplicados"):
            validar_esquema(pd.DataFrame(columns=["appid", "appid"]))

    def test_appid_global_entre_lotes(self):
        vistos = set()
        validar_appids(pd.DataFrame({"appid": [1, 2]}), vistos)
        with self.assertRaisesRegex(ErroValidacao, "appid duplicado: 1"):
            validar_appids(pd.DataFrame({"appid": [3, 1]}), vistos)
        with self.assertRaisesRegex(ErroValidacao, "Linha de dados 1"):
            validar_appids(pd.DataFrame({"appid": [None]}), set())

    def test_processamento_rejeicoes_preservacao_e_repetibilidade(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.csv"
            pd.DataFrame([jogo(), jogo(appid=124, genres="invalido"),
                          jogo(appid=125, required_age=-1, positive=0, negative=0)]).to_csv(caminho, index=False)
            original = caminho.read_bytes()
            relatorio, amostras = processar_csv(caminho, tamanho_lote=1)
            self.assertEqual((relatorio["entrada"], relatorio["rejeitados"], relatorio["saida"]), (3, 1, 2))
            self.assertEqual(len(amostras), 2)
            self.assertEqual(relatorio["documentos_bson_verificados"], 2)
            self.assertEqual(relatorio["sha256_antes"], relatorio["sha256_depois"])
            self.assertEqual(caminho.read_bytes(), original)
            self.assertEqual(processar_csv(caminho, tamanho_lote=2), (relatorio, amostras))


if __name__ == "__main__":
    unittest.main()
