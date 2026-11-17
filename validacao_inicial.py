"""Diagnóstico somente leitura do CSV Steam; execute a partir da raiz do projeto."""

import ast
import hashlib
from pathlib import Path

import pandas as pd


ARQUIVO = Path("data/games_march2025_cleaned.csv")
NUMERICAS = ["appid", "price", "discount", "positive", "negative"]
LISTAS = ["genres", "developers", "publishers"]


def hash_arquivo():
    with ARQUIVO.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def formato_lista(valor):
    """Inspeciona listas textuais com literal_eval, sem executar conteúdo."""
    if pd.isna(valor):
        return "ausente"
    try:
        itens = ast.literal_eval(str(valor))
    except (ValueError, SyntaxError):
        return "texto fora do formato de lista"
    if not isinstance(itens, list):
        return "literal que não é lista"
    if not itens:
        return "lista vazia"
    if any(not isinstance(item, str) or not item.strip() for item in itens):
        return "lista com item inválido ou vazio"
    return "lista de textos não vazios"


def main():
    hash_antes = hash_arquivo()
    df = pd.read_csv(ARQUIVO, low_memory=False)
    print("=== ORIGEM ===")
    print("Arquivo:", ARQUIVO)
    print("SHA256:", hash_antes)
    print("Pandas:", pd.__version__)
    print("Dimensões:", df.shape)
    print("Referência N2 (89618, 47):", df.shape == (89618, 47))
    print("\n=== INFO / COLUNAS E TIPOS ===")
    df.info(show_counts=True)
    print("\n=== NULOS POR COLUNA ===")
    print(df.isna().sum().to_string())
    print("Linhas com algum nulo:", int(df.isna().any(axis=1).sum()))
    print("Células nulas:", int(df.isna().sum().sum()))
    print("\n=== DUPLICAÇÕES ===")
    print("Linhas integralmente duplicadas:", int(df.duplicated().sum()))
    print("appid repetidos além da primeira ocorrência:", int(df.duplicated("appid").sum()))
    print("Linhas envolvidas em appid repetido:", int(df.duplicated("appid", keep=False).sum()))
    print("appid distintos não nulos:", df["appid"].nunique())
    print("\n=== TIPOS REAIS E EXEMPLOS DOS CAMPOS PRIORITÁRIOS ===")
    for coluna in NUMERICAS + LISTAS + ["estimated_owners"]:
        serie = df[coluna]
        print(coluna, "dtype=", serie.dtype, "tipos Python=", serie.dropna().map(type).value_counts().to_dict())
        print("Exemplos:", serie.dropna().head(3).tolist())
    print("\n=== DESCRIBE NUMÉRICO ===")
    print(df[NUMERICAS].describe().to_string())
    print("\n=== VALIDAÇÃO NUMÉRICA (sem modificar o DataFrame) ===")
    for coluna in NUMERICAS:
        serie = df[coluna]
        numerica = pd.to_numeric(serie, errors="coerce")
        print(coluna, {
            "ausentes": int(serie.isna().sum()),
            "não numéricos presentes": int((serie.notna() & numerica.isna()).sum()),
            "negativos": int((numerica < 0).sum()),
            "zeros": int((numerica == 0).sum()),
            "infinitos": int(numerica.isin([float("inf"), -float("inf")]).sum()),
            "fracionários": int((numerica.notna() & numerica.mod(1).ne(0)).sum()),
        })
    print("appid <= 0:", len(df.query("appid <= 0")))
    print("discount fora de 0..100:", len(df.query("discount < 0 or discount > 100")))
    print("Avaliações positivas e negativas ambas zero:", len(df.query("positive == 0 and negative == 0")))
    print("\n=== NEGATIVOS EM TODAS AS COLUNAS NUMÉRICAS ===")
    numericas = df.select_dtypes(include="number")
    print(numericas.lt(0).sum().to_string())
    print("\n=== DETALHES DAS INCONSISTÊNCIAS ===")
    print("Idades negativas:")
    print(df.query("required_age < 0")[["appid", "name", "required_age"]].to_string(index=False))
    for coluna in ["pct_pos_total", "num_reviews_total", "pct_pos_recent", "num_reviews_recent"]:
        print(coluna, "valores negativos:", df.loc[df[coluna] < 0, coluna].value_counts().to_dict())
    for coluna in ["pct_pos_total", "pct_pos_recent", "metacritic_score", "user_score"]:
        print(coluna, "acima de 100:", int((df[coluna] > 100).sum()))
    print("Maiores preços (valores a revisar, não necessariamente erros):")
    print(df.sort_values("price", ascending=False)[["appid", "name", "price"]].head(5).to_string(index=False))
    print("Nomes que coincidem com marcadores textuais (podem ser títulos legítimos):")
    marcadores_nome = df["name"].str.strip().str.lower().isin(["null", "none", "nan", "n/a", "unknown"])
    print(df.loc[marcadores_nome, ["appid", "name"]].to_string(index=False))
    print("\n=== LISTAS TEXTUAIS ===")
    for coluna in LISTAS:
        print(coluna)
        formatos = df[coluna].map(formato_lista)
        print(formatos.value_counts().to_string())
        invalidos = ~formatos.isin(["lista de textos não vazios", "lista vazia", "ausente"])
        if invalidos.any():
            print(df.loc[invalidos, ["appid", coluna]].head(10).to_string(index=False))
    print("\n=== ESTIMATED_OWNERS ===")
    donos = df["estimated_owners"].astype("string")
    faixas = donos.str.extract(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
    formato_valido = faixas.notna().all(axis=1)
    print("Ausentes:", int(donos.isna().sum()))
    print("Presentes fora do formato inteiro - inteiro:", int((donos.notna() & ~formato_valido).sum()))
    limites = faixas.apply(pd.to_numeric, errors="coerce")
    print("Faixas invertidas:", int((limites[0] > limites[1]).sum()))
    print("Faixas mais frequentes:")
    print(donos.value_counts().head(10).to_string())
    print("\n=== TEXTOS VAZIOS / ESPAÇOS / MARCADORES TEXTUAIS ===")
    for coluna in df.select_dtypes(include=["object", "string"]).columns:
        serie = df[coluna].astype("string")
        vazios = int(serie.str.strip().eq("").sum())
        espacos = int(serie.ne(serie.str.strip()).sum())
        marcadores = int(serie.str.strip().str.lower().isin(["null", "none", "nan", "n/a", "unknown"]).sum())
        if vazios or espacos or marcadores:
            print(coluna, {"vazios": vazios, "espaços externos": espacos, "marcadores a revisar": marcadores})
    print("\n=== VERIFICAÇÃO DE PRESERVAÇÃO ===")
    hash_depois = hash_arquivo()
    print("SHA256 final:", hash_depois)
    print("CSV preservado:", hash_antes == hash_depois)


if __name__ == "__main__":
    main()
