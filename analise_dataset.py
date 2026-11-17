import pandas as pd

ARQUIVO = "data/games_march2025_cleaned.csv"

df = pd.read_csv(ARQUIVO, low_memory=False)

print("=== ANÁLISE DO DATASET STEAM ===")
print("Dimensões:", df.shape)
print("Duplicados:", df.duplicated("appid").sum())

colunas = [
    "appid", "name", "price", "discount", "positive",
    "negative", "genres", "developers", "publishers",
    "estimated_owners", "peak_ccu", "average_playtime_forever"
]

print("\n=== AMOSTRA DOS 10 PRIMEIROS JOGOS ===")
print(df[colunas].head(10).to_string(index=False))

print("\n=== VALORES NULOS ===")
print(df.isna().sum().to_string())
