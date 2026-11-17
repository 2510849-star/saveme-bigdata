"""Engajamento e comparação de avaliações por preço, somente a partir do MongoDB."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter

import pandas as pd
from pymongo.errors import PyMongoError

from analises_mongodb import CAMPOS, ler_base, numero_valido, preparar_base
from carga_mongodb import BANCO, COLECAO, ErroCarga, assinatura_estado, conectar


TEMPOS = {
    "tempo_medio_total": ("Período total da fonte", "Média por jogo"),
    "tempo_mediano_total": ("Período total da fonte", "Mediana por jogo"),
    "tempo_medio_duas_semanas": ("Duas semanas da fonte", "Média por jogo"),
    "tempo_mediano_duas_semanas": ("Duas semanas da fonte", "Mediana por jogo"),
}
CAMPOS_COMPLEMENTARES = {**CAMPOS, **{c: "popularidade." + c for c in TEMPOS}}
UNIDADE = "Unidade original não confirmada"


def resumo_engajamento(dados):
    linhas, rankings = [], []
    for campo, (periodo, medida) in TEMPOS.items():
        serie = numero_valido(dados[campo])
        positivos = serie.loc[serie.gt(0)]
        linhas.append({
            "campo_mongodb": "popularidade." + campo, "periodo": periodo,
            "medida_fonte": medida, "unidade": UNIDADE, "jogos_total": len(dados),
            "jogos_valor_valido": int(serie.notna().sum()),
            "jogos_valor_zero": int(serie.eq(0).sum()), "jogos_valor_positivo": len(positivos),
            "jogos_ausentes_ou_invalidos": int(serie.isna().sum()),
            "media_entre_jogos_com_zero": float(serie.mean()) if serie.notna().any() else None,
            "mediana_entre_jogos_com_zero": float(serie.median()) if serie.notna().any() else None,
            "media_entre_jogos_positivos": float(positivos.mean()) if len(positivos) else None,
            "mediana_entre_jogos_positivos": float(positivos.median()) if len(positivos) else None,
            "p25_entre_jogos_positivos": float(positivos.quantile(.25)) if len(positivos) else None,
            "p75_entre_jogos_positivos": float(positivos.quantile(.75)) if len(positivos) else None,
            "maximo": float(serie.max()) if serie.notna().any() else None,
        })
        ranking = dados[["appid", "nome"]].copy()
        ranking["valor"] = serie
        ranking = ranking.loc[ranking["valor"].gt(0)].sort_values(
            ["valor", "appid"], ascending=[False, True]).head(15)
        for posicao, linha in enumerate(ranking.to_dict(orient="records"), 1):
            rankings.append({"campo_mongodb": "popularidade." + campo, "periodo": periodo,
                             "medida_fonte": medida, "unidade": UNIDADE, "posicao": posicao, **linha})
    return pd.DataFrame(linhas), pd.DataFrame(rankings, columns=[
        "campo_mongodb", "periodo", "medida_fonte", "unidade", "posicao", "appid", "nome", "valor"])


def comparar_precos(dados):
    resultados = []
    grupos = [("Preço zero", dados["preco"].eq(0)), ("Preço positivo", dados["preco"].gt(0))]
    for rotulo, mascara in grupos:
        grupo = dados.loc[mascara]
        validos = grupo.loc[grupo["total"].notna()]
        taxas = grupo["percentual_positivo"].dropna()
        total = float(validos["total"].sum()) if len(validos) else None
        positivas = float(validos["positivas"].sum()) if len(validos) else None
        resultados.append({
            "grupo_preco": rotulo, "quantidade_jogos": len(grupo),
            "jogos_avaliacoes_validas": len(validos),
            "jogos_avaliacoes_ausentes_ou_invalidas": len(grupo) - len(validos),
            "jogos_sem_avaliacoes": int(grupo["total"].eq(0).sum()),
            "jogos_com_avaliacoes": len(taxas),
            "avaliacoes_positivas_somadas": positivas,
            "avaliacoes_negativas_somadas": float(validos["negativas"].sum()) if len(validos) else None,
            "avaliacoes_totais_somadas": total,
            "media_avaliacoes_por_jogo_valido": float(validos["total"].mean()) if len(validos) else None,
            "mediana_avaliacoes_por_jogo_valido": float(validos["total"].median()) if len(validos) else None,
            "media_percentual_positivo_por_jogo": float(taxas.mean()) if len(taxas) else None,
            "mediana_percentual_positivo_por_jogo": float(taxas.median()) if len(taxas) else None,
            "percentual_positivo_ponderado_por_avaliacoes": positivas / total * 100 if total and total > 0 else None,
            "free_to_play_explicitos": int(grupo["classificacao_f2p"].eq("Free To Play explícito").sum()),
        })
    return pd.DataFrame(resultados)


def graficos(engajamento, comparacao, saida):
    os.environ.setdefault("MPLCONFIGDIR", str((saida / ".matplotlib-cache").resolve()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rotulos = engajamento["periodo"] + " / " + engajamento["medida_fonte"]
    fig, ax = plt.subplots(figsize=(13, 6))
    esquerda = pd.Series(0, index=engajamento.index)
    for coluna, label, cor in [("jogos_valor_positivo", "Valor > 0", "#287d72"),
                               ("jogos_valor_zero", "Zero (sem inferir ausência de atividade)", "#517da4"),
                               ("jogos_ausentes_ou_invalidos", "Ausente/inválido", "#b5b5b5")]:
        ax.barh(rotulos, engajamento[coluna], left=esquerda, label=label, color=cor)
        esquerda = esquerda + engajamento[coluna]
    ax.set(title="Cobertura dos indicadores de engajamento", xlabel="Quantidade de jogos")
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.12), ncols=1)
    fig.tight_layout()
    fig.savefig(saida / "engajamento_cobertura.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13, 6))
    tabela = engajamento.set_axis(rotulos)[["media_entre_jogos_positivos", "mediana_entre_jogos_positivos"]]
    tabela = tabela.rename(columns={"media_entre_jogos_positivos": "Média entre jogos com valor > 0",
                                    "mediana_entre_jogos_positivos": "Mediana entre jogos com valor > 0"})
    tabela.plot.barh(ax=ax, color=["#287d72", "#517da4"])
    ax.set(title="Engajamento — estatísticas entre jogos, sem misturar períodos",
           xlabel=UNIDADE + " (sem conversão para horas)", ylabel="")
    fig.tight_layout()
    fig.savefig(saida / "engajamento_valores_positivos.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    eixos = [("quantidade_jogos", "Quantidade de jogos"),
             ("media_avaliacoes_por_jogo_valido", "Média de avaliações por jogo válido")]
    for ax, (campo, titulo) in zip(axes, eixos):
        ax.bar(comparacao["grupo_preco"], comparacao[campo], color=["#287d72", "#517da4"])
        ax.set(title=titulo, ylabel="Quantidade")
    fig.suptitle("Preço zero versus positivo — não são classificações Free To Play/pago")
    fig.tight_layout()
    fig.savefig(saida / "comparacao_preco_avaliacoes.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 7))
    tabela = comparacao.set_index("grupo_preco")[["media_percentual_positivo_por_jogo", "mediana_percentual_positivo_por_jogo",
                                                 "percentual_positivo_ponderado_por_avaliacoes"]]
    tabela.columns = ["Média das taxas por jogo", "Mediana das taxas por jogo", "Taxa ponderada por avaliações"]
    tabela.plot.bar(ax=ax, color=["#287d72", "#517da4", "#c66b58"], rot=0)
    ax.set(ylabel="Avaliações positivas (%)", ylim=(0, 100), xlabel="")
    fig.suptitle("Percentual positivo — jogos com alguma avaliação", y=.98)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, .925), bbox_transform=fig.transFigure, ncols=1)
    fig.tight_layout(rect=(0, 0, 1, .78))
    fig.savefig(saida / "comparacao_preco_percentuais.png", dpi=160)
    plt.close(fig)


def executar(colecao, saida):
    inicio = perf_counter()
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    antes = assinatura_estado(colecao)
    indices = colecao.index_information()
    total = colecao.count_documents({})
    dados = preparar_base(ler_base(colecao, CAMPOS_COMPLEMENTARES))
    if len(dados) != total:
        raise ValueError("Contagem mudou durante a leitura")
    engajamento, ranking = resumo_engajamento(dados)
    comparacao = comparar_precos(dados)
    tabelas = {"engajamento_resumo": engajamento, "engajamento_ranking": ranking, "comparacao_precos": comparacao}
    for nome, tabela in tabelas.items():
        tabela.to_csv(saida / f"{nome}.csv", index=False, encoding="utf-8-sig")
    graficos(engajamento, comparacao, saida)
    depois = assinatura_estado(colecao)
    if antes != depois or indices != colecao.index_information():
        raise ValueError("Coleção ou índices mudaram durante as análises")
    resumo = {
        "status": "concluido", "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": {"banco": BANCO, "colecao": COLECAO, "csv_lido": False},
        "jogos": len(dados), "precos_ausentes_ou_invalidos": int(dados["preco"].isna().sum()),
        "engajamento": engajamento.to_dict(orient="records"),
        "comparacao_precos": comparacao.to_dict(orient="records"),
        "metodologia": {
            "unidade_tempo": UNIDADE + "; N2 p.2 exige validar a unidade, mas não a informa. Não foi presumida conversão.",
            "periodos": "Total da fonte e duas semanas da fonte separados; datas exatas da janela e população de jogadores não informadas.",
            "estatisticas": "Estatísticas entre jogos de indicadores já agregados por jogo; não são médias/medianas da população de jogadores. Não há ponderação por usuários.",
            "zeros": "Zeros separados de ausentes; não comprovam ausência de atividade. Valores positivos também resumidos separadamente, sem descartar zeros da versão completa.",
            "precos": "Grupos exclusivamente pelo preço persistido igual a zero ou maior que zero; não equivalem a gêneros ou classificação comercial. Preços inválidos excluídos e contados.",
            "avaliacoes": "Total = positivas + negativas; média/mediana das taxas consideram somente denominador > 0. Contagens por jogo incluem zeros válidos.",
            "ponderada": "100 * soma(positivas) / soma(total) nos jogos com contagens válidas; diferente da média das taxas por jogo.",
        },
        "preservacao": {"sha256_bson_antes": antes, "sha256_bson_depois": depois,
                        "colecao_inalterada": True, "indices_inalterados": True},
        "arquivos_csv": [nome + ".csv" for nome in tabelas],
        "arquivos_png": sorted(p.name for p in saida.glob("*.png")),
        "duracao_segundos": round(perf_counter() - inicio, 3),
    }
    # Converte NaN dos DataFrames para null sem gerar JSON fora do padrão.
    def limpar(valor):
        if isinstance(valor, dict):
            return {k: limpar(v) for k, v in valor.items()}
        if isinstance(valor, list):
            return [limpar(v) for v in valor]
        return None if isinstance(valor, float) and pd.isna(valor) else valor
    resumo = limpar(resumo)
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("outputs/analises/complementares"))
    args = parser.parse_args()
    cliente = None
    try:
        cliente = conectar()
        resumo = executar(cliente[BANCO][COLECAO], args.saida)
    except (ErroCarga, PyMongoError, OSError, ValueError):
        parser.exit(1, "Análises complementares não concluídas; verifique dados, conexão e saída. Credenciais omitidas.\n")
    finally:
        if cliente is not None:
            cliente.close()
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
