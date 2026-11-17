import unittest

import pandas as pd

from analises_complementares import CAMPOS_COMPLEMENTARES, TEMPOS, UNIDADE, comparar_precos, resumo_engajamento
from analises_mongodb import CAMPOS, preparar_base


def dados(*mudancas):
    linhas = []
    for i, mudanca in enumerate(mudancas, 1):
        linha = dict.fromkeys(CAMPOS)
        linha.update({"appid": i, "nome": f"Jogo {i}", "preco": 0,
                      "positivas": 1, "negativas": 0, "f2p": False})
        linha.update(dict.fromkeys(TEMPOS, 0))
        linha.update(mudanca)
        linhas.append(linha)
    return preparar_base(pd.DataFrame(linhas, columns=list(CAMPOS_COMPLEMENTARES)))


class TestAnalisesComplementares(unittest.TestCase):
    def test_periodos_e_media_mediana_nao_se_misturam(self):
        base = dados({"tempo_medio_total": 100, "tempo_mediano_total": 20,
                      "tempo_medio_duas_semanas": 10, "tempo_mediano_duas_semanas": 2})
        resumo, ranking = resumo_engajamento(base)
        self.assertEqual(resumo["media_entre_jogos_positivos"].tolist(), [100, 20, 10, 2])
        self.assertEqual(resumo["unidade"].unique().tolist(), [UNIDADE])
        self.assertEqual(len(ranking), 4)

    def test_zeros_ausentes_negativos_e_infinitos_separados(self):
        base = dados(*({"tempo_medio_total": v} for v in [0, 100, None, -1, float("inf")]))
        resumo, ranking = resumo_engajamento(base)
        linha = resumo.iloc[0]
        self.assertEqual(linha["jogos_valor_zero"], 1)
        self.assertEqual(linha["jogos_valor_positivo"], 1)
        self.assertEqual(linha["jogos_ausentes_ou_invalidos"], 3)
        self.assertEqual(linha["media_entre_jogos_com_zero"], 50)
        self.assertEqual(linha["media_entre_jogos_positivos"], 100)
        self.assertTrue(ranking["valor"].gt(0).all())

    def test_ranking_temporal_15_desempate_appid(self):
        base = dados(*({"tempo_medio_total": 10} for _ in range(20)))
        _, ranking = resumo_engajamento(base)
        total = ranking.loc[ranking["campo_mongodb"].eq("popularidade.tempo_medio_total")]
        self.assertEqual(total["appid"].tolist(), list(range(1, 16)))

    def test_media_taxas_diferente_ponderada(self):
        base = dados({"positivas": 1, "negativas": 0}, {"positivas": 0, "negativas": 99})
        comparacao = comparar_precos(base).iloc[0]
        self.assertEqual(comparacao["media_percentual_positivo_por_jogo"], 50)
        self.assertEqual(comparacao["percentual_positivo_ponderado_por_avaliacoes"], 1)
        self.assertEqual(comparacao["media_avaliacoes_por_jogo_valido"], 50)

    def test_preco_nao_classifica_free_to_play(self):
        base = dados({"preco": 0, "f2p": False}, {"preco": 10, "f2p": True},
                     {"preco": 0, "f2p": True}, {"preco": None}, {"preco": -1})
        comparacao = comparar_precos(base)
        self.assertEqual(comparacao["quantidade_jogos"].tolist(), [2, 1])
        self.assertEqual(comparacao["free_to_play_explicitos"].tolist(), [1, 1])

    def test_avaliacoes_zero_contam_jogo_nao_taxa(self):
        base = dados({"positivas": 0, "negativas": 0}, {"positivas": 1, "negativas": 1},
                     {"positivas": None}, {"positivas": -1})
        resumo = comparar_precos(base).iloc[0]
        self.assertEqual(resumo["quantidade_jogos"], 4)
        self.assertEqual(resumo["jogos_sem_avaliacoes"], 1)
        self.assertEqual(resumo["jogos_com_avaliacoes"], 1)
        self.assertEqual(resumo["jogos_avaliacoes_ausentes_ou_invalidas"], 2)
        self.assertEqual(resumo["media_avaliacoes_por_jogo_valido"], 1)
        self.assertEqual(resumo["media_percentual_positivo_por_jogo"], 50)

    def test_grupos_vazios_nao_inventam_valores(self):
        base = dados()
        comparacao = comparar_precos(base)
        self.assertEqual(comparacao["quantidade_jogos"].sum(), 0)
        self.assertTrue(comparacao["percentual_positivo_ponderado_por_avaliacoes"].isna().all())
        resumo, ranking = resumo_engajamento(base)
        self.assertTrue(resumo["media_entre_jogos_com_zero"].isna().all())
        self.assertTrue(ranking.empty)

    def test_analise_nao_muta_entrada(self):
        base = dados({"tempo_medio_total": -1}, {"preco": 1})
        anterior = base.copy(deep=True)
        resumo_engajamento(base)
        comparar_precos(base)
        pd.testing.assert_frame_equal(base, anterior)


if __name__ == "__main__":
    unittest.main()
