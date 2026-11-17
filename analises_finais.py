"""Positivas, faixas de proprietários e características por gênero; MongoDB somente leitura."""

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


CAMPOS_FINAIS = {**CAMPOS,
    "proprietarios_bruto": "popularidade.proprietarios_estimados.bruto",
    "limite_inferior": "popularidade.proprietarios_estimados.limite_inferior",
    "limite_superior": "popularidade.proprietarios_estimados.limite_superior",
}


def ranking_positivas(dados):
    return dados.loc[dados["positivas"].notna()].sort_values(
        ["positivas", "appid"], ascending=[False, True]).head(15)[
            ["appid", "nome", "positivas", "negativas", "total", "percentual_positivo"]].copy()


def proprietarios_por_faixa(dados):
    base = dados[["appid", "nome", "proprietarios_bruto", "limite_inferior", "limite_superior"]].copy()
    for coluna in ["limite_inferior", "limite_superior"]:
        base[coluna] = numero_valido(base[coluna], inteiro=True)
    valido = (base["limite_inferior"].notna() & base["limite_superior"].notna()
              & base["limite_inferior"].le(base["limite_superior"]))
    base = base.loc[valido].copy()
    base["faixa_proprietarios"] = (base["limite_inferior"].astype("Int64").astype(str)
                                  + " - " + base["limite_superior"].astype("Int64").astype(str))
    chaves = ["faixa_proprietarios", "limite_inferior", "limite_superior"]
    tabela = base.groupby(chaves).size().rename("quantidade_jogos").reset_index().sort_values(
        ["limite_inferior", "limite_superior"], ascending=True).reset_index(drop=True)
    tabela["percentual_catalogo"] = tabela["quantidade_jogos"] / len(dados) * 100 if len(dados) else None
    tabela["percentual_faixas_validas"] = tabela["quantidade_jogos"] / len(base) * 100 if len(base) else None
    ranking = base.sort_values(["limite_inferior", "limite_superior", "appid"], ascending=[False, False, True]).head(15)
    return tabela, ranking.reset_index(drop=True), len(dados) - len(base)


def comparar_generos(dados):
    base = dados.copy()
    base["generos"] = base["generos"].map(
        lambda itens: list(dict.fromkeys(g.strip() for g in itens if isinstance(g, str) and g.strip()))
        if isinstance(itens, list) else [])
    sem_genero = int(base["generos"].map(len).eq(0).sum())
    base = base.explode("generos").dropna(subset=["generos"]).drop_duplicates(["appid", "generos"])
    linhas = []
    for genero, grupo in base.groupby("generos", sort=True):
        precos = grupo["preco"].dropna()
        avaliados = grupo.loc[grupo["total"].gt(0)]
        robustos = grupo.loc[grupo["total"].ge(100)]
        total = float(avaliados["total"].sum()) if len(avaliados) else None
        linhas.append({
            "genero": genero, "quantidade_jogos": len(grupo),
            "precos_validos": len(precos), "precos_ausentes_ou_invalidos": len(grupo) - len(precos),
            "preco_medio": float(precos.mean()) if len(precos) else None,
            "preco_mediano": float(precos.median()) if len(precos) else None,
            "jogos_sem_avaliacoes": int(grupo["total"].eq(0).sum()),
            "jogos_avaliacoes_ausentes_ou_invalidas": int(grupo["total"].isna().sum()),
            "jogos_com_avaliacoes": len(avaliados),
            "media_percentual_positivo": float(avaliados["percentual_positivo"].mean()) if len(avaliados) else None,
            "mediana_percentual_positivo": float(avaliados["percentual_positivo"].median()) if len(avaliados) else None,
            "percentual_positivo_ponderado": float(avaliados["positivas"].sum()) / total * 100 if total else None,
            "jogos_minimo_100_avaliacoes": len(robustos),
            "media_percentual_positivo_minimo_100": float(robustos["percentual_positivo"].mean()) if len(robustos) else None,
        })
    colunas = ["genero", "quantidade_jogos", "precos_validos", "precos_ausentes_ou_invalidos", "preco_medio",
               "preco_mediano", "jogos_sem_avaliacoes", "jogos_avaliacoes_ausentes_ou_invalidas",
               "jogos_com_avaliacoes", "media_percentual_positivo", "mediana_percentual_positivo",
               "percentual_positivo_ponderado", "jogos_minimo_100_avaliacoes", "media_percentual_positivo_minimo_100"]
    return pd.DataFrame(linhas, columns=colunas).sort_values(
        ["quantidade_jogos", "genero"], ascending=[False, True]).reset_index(drop=True), sem_genero


def gerar_graficos(tabelas, saida):
    os.environ.setdefault("MPLCONFIGDIR", str((saida / ".matplotlib-cache").resolve()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    disponiveis = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = [f for f in ["DejaVu Sans", "Microsoft YaHei", "Yu Gothic", "Segoe UI"] if f in disponiveis]
    fig, ax = plt.subplots(figsize=(13, 8))
    tabela = tabelas["ranking_positivas"].iloc[::-1]
    if len(tabela):
        etiquetas = tabela["appid"].astype(int).astype(str) + " · " + tabela["nome"].str.slice(0, 48)
        ax.barh(etiquetas, tabela["positivas"], color="#287d72")
    else:
        ax.text(.5, .5, "Sem dados suficientes", ha="center", transform=ax.transAxes)
    ax.set(title="15 jogos com mais avaliações positivas", xlabel="Avaliações positivas (não total de avaliações ou vendas)")
    fig.tight_layout()
    fig.savefig(saida / "ranking_positivas.png", dpi=160)
    plt.close(fig)

    tabela = tabelas["proprietarios_faixas"]
    fig, ax = plt.subplots(figsize=(13, 8))
    if len(tabela):
        ax.barh(tabela["faixa_proprietarios"], tabela["quantidade_jogos"], color="#517da4")
    else:
        ax.text(.5, .5, "Sem faixas válidas", ha="center", transform=ax.transAxes)
    ax.set(title="Proprietários estimados — distribuição por intervalos da fonte",
           xlabel="Quantidade de jogos em cada faixa (limites não são contagens exatas)", ylabel="Faixa estimada")
    fig.tight_layout()
    fig.savefig(saida / "proprietarios_faixas.png", dpi=160)
    plt.close(fig)

    tabela = tabelas["comparacao_generos"].head(15).iloc[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(19, 9), sharey=True)
    for ax, campo, titulo in zip(axes,
        ["quantidade_jogos", "preco_mediano", "media_percentual_positivo_minimo_100"],
        ["Quantidade de jogos", "Preço mediano (unidade da fonte)", "Média das taxas positivas (%)\nSomente jogos com >= 100 avaliações"]):
        if len(tabela):
            ax.barh(tabela["genero"], tabela[campo], color="#287d72")
        else:
            ax.text(.5, .5, "Sem dados suficientes", ha="center", transform=ax.transAxes)
        ax.set_title(titulo)
        ax.grid(axis="x", alpha=.15)
    axes[-1].set_xlim(0, 100)
    fig.suptitle("Características dos 15 gêneros mais frequentes — jogos podem pertencer a vários gêneros")
    fig.tight_layout()
    fig.savefig(saida / "comparacao_generos.png", dpi=160)
    plt.close(fig)


def executar(colecao, saida):
    inicio = perf_counter()
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    antes, indices = assinatura_estado(colecao), colecao.index_information()
    total = colecao.count_documents({})
    dados = preparar_base(ler_base(colecao, CAMPOS_FINAIS))
    if len(dados) != total:
        raise ValueError("Contagem mudou durante a leitura")
    faixas, ranking_faixas, invalidos = proprietarios_por_faixa(dados)
    generos, sem_genero = comparar_generos(dados)
    tabelas = {"ranking_positivas": ranking_positivas(dados), "proprietarios_faixas": faixas,
               "ranking_faixas_proprietarios": ranking_faixas, "comparacao_generos": generos}
    for nome, tabela in tabelas.items():
        tabela.to_csv(saida / f"{nome}.csv", index=False, encoding="utf-8-sig")
    gerar_graficos(tabelas, saida)
    depois = assinatura_estado(colecao)
    if antes != depois or indices != colecao.index_information():
        raise ValueError("Coleção ou índices mudaram durante a análise")
    resumo = {
        "status": "concluido", "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": {"banco": BANCO, "colecao": COLECAO, "leitura_csv_original": False},
        "jogos": len(dados), "faixas_distintas": len(faixas), "faixas_ausentes_ou_invalidas": invalidos,
        "generos_distintos": len(generos), "jogos_sem_genero": sem_genero,
        "lider_positivas": tabelas["ranking_positivas"].head(1).to_dict(orient="records"),
        "faixas": faixas.to_dict(orient="records"), "generos_top_5": generos.head(5).to_dict(orient="records"),
        "metodologia": {
            "positivas": "Ordenação por positivas decrescente, appid crescente; negativas e total exibidos separadamente.",
            "proprietarios": "Agrupamento por limites inferior/superior válidos, não negativos e ordenados. Não há ponto médio, soma de proprietários ou conversão das faixas em contagens exatas. Faixa 0-0 não prova ausência de proprietários.",
            "ranking_faixas": "Ordem descritiva por limite inferior, superior e appid; não é ranking de quantidades exatas. Intervalos sobrepostos não permitem ordenação exata.",
            "generos": "Um jogo por gênero, sem duplicações internas. Quantidade e preço usam todos os jogos válidos do gênero; taxas usam somente denominador > 0. Média, mediana, ponderada e sensibilidade com >=100 avaliações são separadas.",
            "grafico_generos": "15 gêneros mais frequentes; preço mediano inclui zero; taxa média usa somente jogos com >=100 avaliações. CSV contém todos os gêneros, contagens de elegíveis e ambas as populações.",
            "limites": "Moeda não confirmada; avaliações não são vendas, gêneros não são exclusivos e comparação não implica causalidade.",
        },
        "preservacao": {"sha256_bson_antes": antes, "sha256_bson_depois": depois,
                        "colecao_inalterada": True, "indices_inalterados": True},
        "arquivos_csv": [f"{nome}.csv" for nome in tabelas],
        "arquivos_png": sorted(p.name for p in saida.glob("*.png")),
        "duracao_segundos": round(perf_counter() - inicio, 3),
    }
    def limpar(v):
        if isinstance(v, dict):
            return {k: limpar(x) for k, x in v.items()}
        if isinstance(v, list):
            return [limpar(x) for x in v]
        return None if isinstance(v, float) and pd.isna(v) else v
    resumo = limpar(resumo)
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("outputs/analises/finais"))
    args = parser.parse_args()
    cliente = None
    try:
        cliente = conectar()
        resumo = executar(cliente[BANCO][COLECAO], args.saida)
    except (ErroCarga, PyMongoError, OSError, ValueError):
        parser.exit(1, "Análises finais não concluídas: verifique conexão, dados e saída. Credenciais omitidas.\n")
    finally:
        if cliente is not None:
            cliente.close()
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
