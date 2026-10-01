from utilities import load_latest_snapshot

df = load_latest_snapshot()
df.to_csv("data/processed/wan_snapshot.csv", index=False)
print("Export complete: data/processed/wan_snapshot.csv")