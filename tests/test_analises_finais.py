import unittest

import pandas as pd

from analises_finais import CAMPOS_FINAIS, comparar_generos, proprietarios_por_faixa, ranking_positivas
from analises_mongodb import preparar_base


def dados(*alteracoes):
    linhas = []
    for i, alteracao in enumerate(alteracoes, 1):
        linha = dict.fromkeys(CAMPOS_FINAIS)
        linha.update({"appid": i, "nome": f"Jogo {i}", "preco": 10, "positivas": 80,
                      "negativas": 20, "generos": ["Action"], "limite_inferior": 0,
                      "limite_superior": 20000, "proprietarios_bruto": "0 - 20000"})
        linha.update(alteracao)
        linhas.append(linha)
    return preparar_base(pd.DataFrame(linhas, columns=list(CAMPOS_FINAIS)))


class TestAnalisesFinais(unittest.TestCase):
    def test_positivas_nao_sao_total(self):
        ranking = ranking_positivas(dados({"positivas": 10, "negativas": 1000},
                                         {"positivas": 20, "negativas": 0}))
        self.assertEqual(ranking["appid"].tolist(), [2, 1])
        self.assertEqual(ranking["total"].tolist(), [20, 1010])

    def test_positivas_limite_15_empate_e_ausencia(self):
        base = dados(*({} for _ in range(20)), {"positivas": None})
        self.assertEqual(ranking_positivas(base)["appid"].tolist(), list(range(1, 16)))

    def test_faixas_agrupadas_sem_ponto_medio(self):
        tabela, ranking, invalidos = proprietarios_por_faixa(dados({}, {},
            {"limite_inferior": 20000, "limite_superior": 50000, "proprietarios_bruto": "20000 - 50000"}))
        self.assertEqual(tabela["quantidade_jogos"].tolist(), [2, 1])
        self.assertEqual(ranking.iloc[0]["appid"], 3)
        self.assertEqual(invalidos, 0)
        self.assertNotIn("proprietarios_exatos", tabela.columns)
        self.assertAlmostEqual(tabela["percentual_catalogo"].sum(), 100)

    def test_faixas_invalidas_separadas_zero_preservado(self):
        tabela, _, invalidos = proprietarios_por_faixa(dados(
            {"limite_inferior": 0, "limite_superior": 0, "proprietarios_bruto": "0 - 0"},
            {"limite_inferior": -1}, {"limite_superior": None},
            {"limite_inferior": 20001}, {"limite_superior": float("inf")},
            {"limite_inferior": .5}))
        self.assertEqual(invalidos, 5)
        self.assertEqual(tabela.iloc[0]["faixa_proprietarios"], "0 - 0")
        self.assertEqual(tabela.iloc[0]["quantidade_jogos"], 1)

    def test_genero_multivalorado_sem_duplicacao(self):
        tabela, sem = comparar_generos(dados({"generos": ["Action", "Action", " Indie ", "", None]},
                                           {"generos": ["Indie"]}, {"generos": []}))
        self.assertEqual(sem, 1)
        contagens = tabela.set_index("genero")["quantidade_jogos"].to_dict()
        self.assertEqual(contagens, {"Indie": 2, "Action": 1})

    def test_sem_avaliacoes_nao_reduz_taxa_para_zero(self):
        tabela, _ = comparar_generos(dados({"positivas": 0, "negativas": 0},
                                          {"positivas": 1, "negativas": 0}))
        linha = tabela.iloc[0]
        self.assertEqual(linha["quantidade_jogos"], 2)
        self.assertEqual(linha["jogos_sem_avaliacoes"], 1)
        self.assertEqual(linha["jogos_com_avaliacoes"], 1)
        self.assertEqual(linha["media_percentual_positivo"], 100)
        self.assertTrue(pd.isna(linha["media_percentual_positivo_minimo_100"]))

    def test_taxa_simples_ponderada_e_minimo_100_separados(self):
        tabela, _ = comparar_generos(dados({"positivas": 1, "negativas": 0},
                                          {"positivas": 0, "negativas": 100}))
        linha = tabela.iloc[0]
        self.assertEqual(linha["media_percentual_positivo"], 50)
        self.assertAlmostEqual(linha["percentual_positivo_ponderado"], 100 / 101)
        self.assertEqual(linha["media_percentual_positivo_minimo_100"], 0)
        self.assertEqual(linha["jogos_minimo_100_avaliacoes"], 1)

    def test_precos_zero_entram_na_mediana_e_nulos_sao_contados(self):
        tabela, _ = comparar_generos(dados({"preco": 0}, {"preco": 10}, {"preco": None}))
        self.assertEqual(tabela.iloc[0]["preco_mediano"], 5)
        self.assertEqual(tabela.iloc[0]["precos_validos"], 2)
        self.assertEqual(tabela.iloc[0]["precos_ausentes_ou_invalidos"], 1)

    def test_vazios_e_generos_invalidos(self):
        tabela, sem = comparar_generos(dados({"generos": None}, {"generos": "Action"}))
        self.assertTrue(tabela.empty)
        self.assertEqual(sem, 2)
        tabela, ranking, invalidos = proprietarios_por_faixa(dados())
        self.assertTrue(tabela.empty)
        self.assertTrue(ranking.empty)
        self.assertEqual(invalidos, 0)

    def test_entrada_preservada(self):
        base = dados({"generos": ["Action", "Action"]})
        anterior = base.copy(deep=True)
        ranking_positivas(base)
        proprietarios_por_faixa(base)
        comparar_generos(base)
        pd.testing.assert_frame_equal(base, anterior)


if __name__ == "__main__":
    unittest.main()
