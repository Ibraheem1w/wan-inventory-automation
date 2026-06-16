import pandas as pd

df = pd.read_parquet("data/processed/normalized_snapshot.parquet")
df.to_csv("data/processed/wan_snapshot.csv", index=False)

print("Export complete: data/processed/wan_snapshot.csv")