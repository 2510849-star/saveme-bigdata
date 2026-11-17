import unittest
from unittest.mock import Mock

import pandas as pd

from analises_mongodb import (
    CAMPOS, CLASSES_F2P, FAIXAS_PRECO, correlacao, distribuicoes, generos_frequentes,
    indicadores, ler_base, preparar_base, rankings, relacao_preco_avaliacao,
)


def base(*alteracoes):
    linhas = []
    for i, mudancas in enumerate(alteracoes, 1):
        linha = {"appid": i, "nome": f"Jogo {i}", "preco": 10.0, "desconto": 0,
                 "positivas": 75, "negativas": 25, "total_persistido": 100,
                 "taxa_persistida": 75.0, "generos": ["Action"], "f2p": False, "pico": 10}
        linha.update(mudancas)
        linhas.append(linha)
    return preparar_base(pd.DataFrame(linhas, columns=list(CAMPOS)))


class TestAnalisesMongoDB(unittest.TestCase):
    def test_ranking_total_e_desempate(self):
        dados = base({"appid": 3}, {"appid": 1}, {"appid": 2, "positivas": 100})
        quantidade, _, _ = rankings(dados)
        self.assertEqual(quantidade["appid"].tolist(), [2, 1, 3])
        self.assertEqual(quantidade.iloc[0]["total"], 125)

    def test_ranking_percentual_minimo_100_e_desempates(self):
        dados = base({"positivas": 99, "negativas": 0},
                     {"positivas": 100, "negativas": 0},
                     {"positivas": 200, "negativas": 0},
                     {"positivas": 90, "negativas": 10})
        _, percentual, _ = rankings(dados)
        self.assertEqual(percentual["appid"].tolist(), [3, 2, 4])

    def test_rankings_limitados_a_15(self):
        for tabela in rankings(base(*({} for _ in range(20)))):
            self.assertEqual(len(tabela), 15)

    def test_nulos_denominador_zero_e_taxa_zero_real(self):
        dados = base({"positivas": 0, "negativas": 0, "taxa_persistida": None, "total_persistido": 0},
                     {"positivas": 0, "negativas": 10}, {"positivas": None}, {"negativas": -1})
        self.assertTrue(pd.isna(dados.iloc[0]["percentual_positivo"]))
        self.assertEqual(dados.iloc[1]["percentual_positivo"], 0)
        self.assertEqual(len(relacao_preco_avaliacao(dados)), 1)

    def test_preco_zero_independente_da_categoria(self):
        dados = base({"preco": 0, "f2p": False}, {"preco": 0, "f2p": True},
                     {"preco": 20, "f2p": True}, {"preco": 0, "f2p": None})
        tabela, _, _ = distribuicoes(dados)
        zeros = tabela.loc[tabela["faixa_preco"].eq("Preço zero")].set_index("classificacao_f2p")
        for classe in CLASSES_F2P:
            self.assertEqual(zeros.loc[classe, "quantidade_jogos"], 1)
        resumo = indicadores(dados, relacao_preco_avaliacao(dados))
        self.assertEqual(resumo["precos_zero"], 3)
        self.assertEqual(resumo["free_to_play_explicitos"], 2)

    def test_fronteiras_faixas_precos_e_invalido(self):
        dados = base(*({"preco": p} for p in [0, .01, 10, 10.01, 20, 20.01, 50, 50.01, None, -1]))
        self.assertEqual(dados["faixa_preco"].tolist(), [FAIXAS_PRECO[i] for i in [0, 1, 1, 2, 2, 3, 3, 4, 5, 5]])
        tabela, _, _ = distribuicoes(dados)
        self.assertEqual(tabela["quantidade_jogos"].sum(), 10)
        self.assertAlmostEqual(tabela["percentual_catalogo"].sum(), 100)

    def test_descontos_faixas_denominadores_e_invalidos(self):
        dados = base(*({"desconto": x} for x in [0, 10, 25, 50, 75, 100, None, -1, 101]))
        _, tabela, exatos = distribuicoes(dados)
        self.assertEqual(tabela["quantidade_jogos"].sum(), 9)
        self.assertEqual(tabela.iloc[-1]["quantidade_jogos"], 3)
        self.assertAlmostEqual(tabela["percentual_entre_descontados"].sum(), 100)
        self.assertEqual(len(exatos), 6)

    def test_sem_descontos_nao_inventa_percentual(self):
        _, tabela, _ = distribuicoes(base({}))
        self.assertTrue(tabela["percentual_entre_descontados"].isna().all())

    def test_numericos_invalidos_nao_viram_zero(self):
        dados = base({"preco": float("inf")}, {"positivas": True},
                     {"negativas": .5}, {"desconto": "abc"}, {"pico": -1})
        for indice, campo in [(0, "preco"), (1, "positivas"), (2, "negativas"), (3, "desconto"), (4, "pico")]:
            self.assertTrue(pd.isna(dados.iloc[indice][campo]))

    def test_correlacoes_e_dados_insuficientes(self):
        dados = base({"preco": 0, "positivas": 10, "negativas": 90},
                     {"preco": 10, "positivas": 50, "negativas": 50},
                     {"preco": 20, "positivas": 90, "negativas": 10})
        relacao = relacao_preco_avaliacao(dados)
        self.assertAlmostEqual(correlacao(relacao), 1)
        self.assertAlmostEqual(correlacao(relacao, postos=True), 1)
        self.assertIsNone(correlacao(relacao.head(1)))
        relacao["preco"] = 0
        self.assertIsNone(correlacao(relacao))

    def test_popularidade_ignora_ausentes(self):
        _, _, pico = rankings(base({"pico": None}, {"pico": 30}, {"pico": 0}))
        self.assertEqual(pico["appid"].tolist(), [2, 3])

    def test_conferencia_totais_e_taxas_persistidos(self):
        dados = base({"total_persistido": 999, "taxa_persistida": 1})
        resultado = indicadores(dados, relacao_preco_avaliacao(dados))
        self.assertEqual(resultado["totais_persistidos_divergentes"], 1)
        self.assertEqual(resultado["taxas_persistidas_divergentes"], 1)

    def test_appid_invalido_ou_duplicado_falha(self):
        for alteracoes in [({"appid": None},), ({"appid": 0},), ({"appid": 1}, {"appid": 1})]:
            with self.subTest(alteracoes=alteracoes), self.assertRaises(ValueError):
                base(*alteracoes)

    def test_fonte_mongo_projecao_sem_leitura_csv(self):
        cursor = Mock()
        cursor.__iter__ = Mock(return_value=iter([{"appid": 1, "preco": {"valor": 4.99}}]))
        cursor.batch_size.return_value = cursor
        colecao = Mock()
        colecao.find.return_value = cursor
        dados = ler_base(colecao)
        self.assertEqual(dados.iloc[0]["preco"], 4.99)
        self.assertEqual(colecao.find.call_args.args[1]["_id"], 0)
        cursor.close.assert_called_once()

    def test_agregacao_generos_multivalorada_sem_duplicar_jogo(self):
        colecao = Mock()
        colecao.aggregate.return_value = [{"genero": "Action", "quantidade_jogos": 2},
                                           {"genero": "Indie", "quantidade_jogos": 1}]
        tabela = generos_frequentes(colecao, 2)
        self.assertEqual(tabela["percentual_catalogo"].tolist(), [100, 50])
        pipeline = colecao.aggregate.call_args.args[0]
        self.assertIn("$setUnion", pipeline[0]["$project"]["generos"])
        self.assertEqual(pipeline[-2], {"$limit": 15})

    def test_base_vazia_nao_divide_por_zero(self):
        dados = base()
        self.assertEqual(indicadores(dados, relacao_preco_avaliacao(dados))["jogos"], 0)
        self.assertIsNone(indicadores(dados, relacao_preco_avaliacao(dados))["percentual_com_desconto"])
        for tabela in rankings(dados):
            self.assertTrue(tabela.empty)


if __name__ == "__main__":
    unittest.main()
