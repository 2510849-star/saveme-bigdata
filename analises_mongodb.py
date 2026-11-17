"""Análises somente leitura de saveme_analytics.jogos_analiticos."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter

import pandas as pd
from pymongo.errors import PyMongoError

from carga_mongodb import BANCO, COLECAO, ErroCarga, assinatura_estado, conectar


CAMPOS = {
    "appid": "appid", "nome": "nome", "preco": "preco.valor",
    "desconto": "preco.desconto_percentual", "positivas": "avaliacoes.positivas",
    "negativas": "avaliacoes.negativas", "total_persistido": "avaliacoes.total",
    "taxa_persistida": "avaliacoes.taxa_positivas_percentual",
    "generos": "catalogo.generos", "f2p": "catalogo.free_to_play_explicito",
    "pico": "popularidade.pico_jogadores_simultaneos",
}
FAIXAS_PRECO = ["Preço zero", "0 < preço <= 10", "10 < preço <= 20",
                "20 < preço <= 50", "Preço > 50", "Indisponível"]
FAIXAS_DESCONTO = ["Sem desconto", "0 < desconto <= 10", "10 < desconto <= 25",
                   "25 < desconto <= 50", "50 < desconto <= 75",
                   "75 < desconto <= 100", "Indisponível"]
CLASSES_F2P = ["Free To Play explícito", "Sem categoria explícita", "Classificação indisponível"]


def obter_campo(documento, caminho):
    valor = documento
    for parte in caminho.split("."):
        if not isinstance(valor, dict):
            return None
        valor = valor.get(parte)
    return valor


def ler_base(colecao, campos=None):
    campos = CAMPOS if campos is None else campos
    projecao = {c: 1 for c in campos.values()}
    projecao["_id"] = 0
    with closing(colecao.find({}, projecao).batch_size(2000)) as cursor:
        return pd.DataFrame.from_records(
            ({nome: obter_campo(d, caminho) for nome, caminho in campos.items()} for d in cursor),
            columns=list(campos))


def numero_valido(serie, inteiro=False, maximo=None):
    valores = pd.to_numeric(serie.mask(serie.map(lambda x: isinstance(x, bool))), errors="coerce")
    validos = valores.notna() & ~valores.isin([float("inf"), -float("inf")]) & valores.ge(0)
    if inteiro:
        validos &= valores.mod(1).eq(0)
    if maximo is not None:
        validos &= valores.le(maximo)
    return valores.where(validos)


def preparar_base(base):
    dados = base.copy(deep=True)
    for coluna in CAMPOS:
        if coluna not in dados:
            dados[coluna] = None
    for coluna in ["appid", "preco", "desconto", "positivas", "negativas", "total_persistido", "taxa_persistida", "pico"]:
        dados[coluna] = numero_valido(dados[coluna],
                                     inteiro=coluna not in ["preco", "taxa_persistida"],
                                     maximo=100 if coluna in ["desconto", "taxa_persistida"] else None)
    if dados["appid"].isna().any() or dados["appid"].le(0).any() or dados["appid"].duplicated().any():
        raise ValueError("A coleção deve conter appid inteiro positivo, não nulo e único")
    # Derivação exclusiva dos valores persistidos, sem acesso ao CSV.
    dados["total"] = dados["positivas"] + dados["negativas"]
    dados["percentual_positivo"] = (dados["positivas"] / dados["total"].where(dados["total"].gt(0))) * 100
    dados["faixa_preco"] = pd.cut(dados["preco"], [-1, 0, 10, 20, 50, float("inf")],
                                  labels=FAIXAS_PRECO[:-1]).astype("string").fillna("Indisponível")
    dados["faixa_desconto"] = pd.cut(dados["desconto"], [-1, 0, 10, 25, 50, 75, 100],
                                     labels=FAIXAS_DESCONTO[:-1]).astype("string").fillna("Indisponível")
    dados["classificacao_f2p"] = dados["f2p"].map(
        lambda v: CLASSES_F2P[0] if v is True else CLASSES_F2P[1] if v is False else CLASSES_F2P[2])
    return dados


def rankings(dados):
    colunas = ["appid", "nome", "positivas", "negativas", "total", "percentual_positivo"]
    validos = dados.loc[dados["total"].notna()]
    quantidade = validos.sort_values(["total", "appid"], ascending=[False, True]).head(15)[colunas]
    percentual = validos.query("total >= 100").sort_values(
        ["percentual_positivo", "total", "appid"], ascending=[False, False, True]).head(15)[colunas]
    pico = dados.loc[dados["pico"].notna()].sort_values(
        ["pico", "appid"], ascending=[False, True]).head(15)[["appid", "nome", "pico"]]
    return quantidade, percentual, pico


def generos_frequentes(colecao, total):
    # setUnion evita contar duas vezes o mesmo gênero para o mesmo jogo.
    pipeline = [
        {"$project": {"generos": {"$setUnion": [
            {"$cond": [{"$isArray": "$catalogo.generos"}, "$catalogo.generos", []]}, []]}}},
        {"$unwind": "$generos"},
        {"$match": {"generos": {"$type": "string", "$ne": ""}}},
        {"$group": {"_id": "$generos", "quantidade_jogos": {"$sum": 1}}},
        {"$sort": {"quantidade_jogos": -1, "_id": 1}}, {"$limit": 15},
        {"$project": {"_id": 0, "genero": "$_id", "quantidade_jogos": 1}},
    ]
    tabela = pd.DataFrame(list(colecao.aggregate(pipeline, allowDiskUse=True)),
                          columns=["genero", "quantidade_jogos"])
    tabela["percentual_catalogo"] = tabela["quantidade_jogos"] / total * 100 if total else None
    return tabela


def distribuicoes(dados):
    total = len(dados)
    indice = pd.MultiIndex.from_product([FAIXAS_PRECO, CLASSES_F2P], names=["faixa_preco", "classificacao_f2p"])
    precos = dados.groupby(["faixa_preco", "classificacao_f2p"]).size().reindex(indice, fill_value=0)
    precos = precos.rename("quantidade_jogos").reset_index()
    precos["percentual_catalogo"] = precos["quantidade_jogos"] / total * 100 if total else None
    descontos = dados.groupby("faixa_desconto").size().reindex(FAIXAS_DESCONTO, fill_value=0)
    descontos = descontos.rename("quantidade_jogos").rename_axis("faixa_desconto").reset_index()
    descontos["percentual_catalogo"] = descontos["quantidade_jogos"] / total * 100 if total else None
    com_desconto = int(dados["desconto"].gt(0).sum())
    descontos["percentual_entre_descontados"] = descontos.apply(
        lambda r: r["quantidade_jogos"] / com_desconto * 100
        if com_desconto and r["faixa_desconto"] not in ["Sem desconto", "Indisponível"] else None, axis=1)
    exatos = dados.loc[dados["desconto"].notna()].groupby("desconto").size().rename("quantidade_jogos").reset_index()
    return precos, descontos, exatos


def relacao_preco_avaliacao(dados):
    return dados.loc[dados["preco"].notna() & dados["percentual_positivo"].notna(),
                     ["appid", "nome", "preco", "total", "percentual_positivo"]].copy()


def correlacao(relacao, postos=False):
    if len(relacao) < 2 or relacao["preco"].nunique() < 2 or relacao["percentual_positivo"].nunique() < 2:
        return None
    x, y = relacao["preco"], relacao["percentual_positivo"]
    # Correlação de postos sem dependência adicional de SciPy.
    valor = x.rank().corr(y.rank()) if postos else x.corr(y)
    return float(valor) if pd.notna(valor) else None


def indicadores(dados, relacao):
    total = len(dados)
    qtd = int(dados["desconto"].gt(0).sum())
    total_divergente = dados["total"].notna() & dados["total_persistido"].notna() & dados["total"].ne(dados["total_persistido"])
    taxa_divergente = (dados["percentual_positivo"].isna() != dados["taxa_persistida"].isna()) | (
        (dados["percentual_positivo"] - dados["taxa_persistida"]).abs().gt(1e-8))
    return {
        "jogos": total, "avaliacoes_validas": int(dados["total"].notna().sum()),
        "jogos_sem_avaliacoes": int(dados["total"].eq(0).sum()),
        "jogos_elegiveis_ranking_percentual": int(dados["total"].ge(100).sum()),
        "precos_zero": int(dados["preco"].eq(0).sum()),
        "free_to_play_explicitos": int(dados["classificacao_f2p"].eq(CLASSES_F2P[0]).sum()),
        "preco_zero_sem_f2p_explicito": int((dados["preco"].eq(0) & dados["classificacao_f2p"].eq(CLASSES_F2P[1])).sum()),
        "com_desconto": qtd, "percentual_com_desconto": qtd / total * 100 if total else None,
        "sem_desconto": int(dados["desconto"].eq(0).sum()),
        "desconto_medio_entre_descontados": float(dados.loc[dados["desconto"].gt(0), "desconto"].mean()) if qtd else None,
        "registros_relacao_preco_avaliacao": len(relacao),
        "excluidos_relacao_preco_avaliacao": total - len(relacao),
        "correlacao_pearson": correlacao(relacao), "correlacao_spearman": correlacao(relacao, postos=True),
        "picos_validos": int(dados["pico"].notna().sum()),
        "totais_persistidos_divergentes": int(total_divergente.sum()),
        "taxas_persistidas_divergentes": int(taxa_divergente.sum()),
        "nulos_ou_invalidos_por_campo": {c: int(dados[c].isna().sum())
                                        for c in ["preco", "desconto", "positivas", "negativas", "pico"]},
    }


def gerar_graficos(tabelas, saida):
    # Backend sem janela e cache gravável; não exige sessão gráfica.
    os.environ.setdefault("MPLCONFIGDIR", str((saida / ".matplotlib-cache").resolve()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    disponiveis = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = [f for f in ["DejaVu Sans", "Microsoft YaHei", "Yu Gothic", "Segoe UI"] if f in disponiveis]

    def barras(nome, tabela, rotulo, valor, titulo, eixo, empilhado=False):
        fig, ax = plt.subplots(figsize=(12, 8))
        if tabela.empty:
            ax.text(.5, .5, "Sem dados suficientes", ha="center", transform=ax.transAxes)
        else:
            tabela = tabela.iloc[::-1]
            etiquetas = tabela[rotulo].astype(str)
            if rotulo == "nome":
                etiquetas = tabela["appid"].astype(int).astype(str) + " · " + etiquetas.str.slice(0, 48)
            if empilhado:
                ax.barh(etiquetas, tabela["positivas"], label="Positivas", color="#287d72")
                ax.barh(etiquetas, tabela["negativas"], left=tabela["positivas"], label="Negativas", color="#c66b58")
                ax.legend()
            else:
                ax.barh(etiquetas, tabela[valor], color="#287d72")
        ax.set(title=titulo, xlabel=eixo)
        fig.tight_layout()
        fig.savefig(saida / f"{nome}.png", dpi=160)
        plt.close(fig)

    barras("ranking_avaliacoes", tabelas["ranking_avaliacoes"], "nome", "total",
           "15 jogos com mais avaliações", "Quantidade de avaliações (não vendas)", True)
    barras("ranking_percentual_positivo", tabelas["ranking_percentual_positivo"], "nome", "percentual_positivo",
           "15 maiores percentuais positivos — mínimo de 100 avaliações", "Avaliações positivas (%)")
    barras("generos_frequentes", tabelas["generos_frequentes"], "genero", "quantidade_jogos",
           "15 gêneros mais frequentes — um jogo pode ter vários gêneros", "Quantidade de jogos")
    barras("ranking_popularidade", tabelas["ranking_popularidade"], "nome", "pico",
           "15 maiores picos de jogadores simultâneos", "Pico registrado na fonte")
    fig, ax = plt.subplots(figsize=(12, 7))
    tabela = tabelas["distribuicao_precos"].pivot(index="faixa_preco", columns="classificacao_f2p", values="quantidade_jogos").reindex(FAIXAS_PRECO)
    tabela[CLASSES_F2P].plot.barh(stacked=True, ax=ax, color=["#287d72", "#517da4", "#b5b5b5"])
    ax.set(title="Faixas de preço e evidência explícita de Free To Play", xlabel="Quantidade de jogos", ylabel="")
    ax.legend(title="Categoria, independente do preço")
    fig.tight_layout()
    fig.savefig(saida / "distribuicao_precos.png", dpi=160)
    plt.close(fig)
    tabela = tabelas["distribuicao_descontos"].iloc[1:-1]
    barras("distribuicao_descontos", tabela, "faixa_desconto", "quantidade_jogos",
           "Distribuição dos descontos — somente percentuais maiores que zero", "Quantidade de jogos")
    fig, ax = plt.subplots(figsize=(11, 7))
    relacao = tabelas["relacao_preco_avaliacao"]
    ax.scatter(relacao["preco"], relacao["percentual_positivo"], s=5, alpha=.15, color="#287d72", rasterized=True)
    ax.set_xscale("symlog", linthresh=10)
    ax.set(title="Preço e percentual positivo — jogos com pelo menos uma avaliação",
           xlabel="Preço na unidade da fonte (escala symlog; inclui zero)", ylabel="Avaliações positivas (%)", ylim=(-2, 102))
    fig.tight_layout()
    fig.savefig(saida / "relacao_preco_avaliacao.png", dpi=160)
    plt.close(fig)


def executar_analises(colecao, saida):
    inicio = perf_counter()
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    estado_antes = assinatura_estado(colecao)
    indices_antes = colecao.index_information()
    total_antes = colecao.count_documents({})
    dados = preparar_base(ler_base(colecao))
    if len(dados) != total_antes:
        raise ValueError("Contagem mudou durante a leitura; execute sem cargas concorrentes")
    quantidade, percentual, pico = rankings(dados)
    precos, descontos, exatos = distribuicoes(dados)
    relacao = relacao_preco_avaliacao(dados)
    tabelas = {"ranking_avaliacoes": quantidade, "ranking_percentual_positivo": percentual,
               "generos_frequentes": generos_frequentes(colecao, len(dados)),
               "distribuicao_precos": precos, "distribuicao_descontos": descontos,
               "descontos_percentuais": exatos, "relacao_preco_avaliacao": relacao,
               "ranking_popularidade": pico}
    for nome, tabela in tabelas.items():
        tabela.to_csv(saida / f"{nome}.csv", index=False, encoding="utf-8-sig")
    gerar_graficos(tabelas, saida)
    estado_depois = assinatura_estado(colecao)
    if estado_antes != estado_depois or indices_antes != colecao.index_information():
        raise ValueError("Estado ou índices mudaram durante as análises; resultados não validados")
    resumo = {
        "status": "concluido", "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": {"banco": BANCO, "colecao": COLECAO, "leitura_direta_csv": False},
        "indicadores": indicadores(dados, relacao),
        "lideres": {nome: tabelas[nome].head(1).to_dict(orient="records")
                    for nome in ["ranking_avaliacoes", "ranking_percentual_positivo", "generos_frequentes", "ranking_popularidade"]},
        "metodologia": {
            "avaliacoes": "Positivas e negativas persistidas; total e taxa recalculados para conferência. Avaliações não são vendas.",
            "ranking_percentual": "Total >= 100; desempate por total decrescente e appid crescente.",
            "generos": "Agregação MongoDB com setUnion, unwind e group; cada jogo conta uma vez por gênero, podendo integrar vários.",
            "preco": "Faixas 0, (0,10], (10,20], (20,50], >50; moeda não inferida. Categoria F2P separada do preço.",
            "descontos": "Desconto > 0 e <= 100. CSV inclui distribuição exata, por faixas e dois denominadores percentuais.",
            "relacao": "Preço não negativo e avaliações positivas/negativas válidas com total > 0; todos os elegíveis, sem amostragem ou remoção de outliers. Pearson e correlação de postos; não implica causalidade.",
            "popularidade": "Pico de jogadores simultâneos persistido; não é venda, proprietário ou número atual de jogadores.",
            "ausencias": "Dados não numéricos, infinitos, negativos e percentuais fora de 0..100 viram ausentes somente na análise; coleção não alterada.",
            "n2": "N2 auditada integralmente: docs/N2 Flaris - SaveMe Games (1)(1).pdf; veja AUDITORIA_FINAL_N2.md. Consultas baseadas no esquema persistido.",
        },
        "preservacao": {"sha256_bson_antes": estado_antes, "sha256_bson_depois": estado_depois,
                        "colecao_inalterada": True, "indices_inalterados": True},
        "arquivos_csv": [f"{nome}.csv" for nome in tabelas],
        "arquivos_png": sorted(p.name for p in saida.glob("*.png")),
        "duracao_segundos": round(perf_counter() - inicio, 3),
    }
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("outputs/analises"))
    args = parser.parse_args()
    cliente = None
    try:
        cliente = conectar()
        resumo = executar_analises(cliente[BANCO][COLECAO], args.saida)
    except (ErroCarga, PyMongoError, OSError, ValueError):
        parser.exit(1, "Análises não concluídas: verifique conexão, dados e diretório de saída. Mensagens do driver e credenciais foram omitidas.\n")
    finally:
        if cliente is not None:
            cliente.close()
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
