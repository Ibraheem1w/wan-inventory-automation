import pandas as pd
from pathlib import Path
from utilities import normalize_vendor1, normalize_vendor2

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

def main():
    v1 = pd.read_csv(RAW / "vendor1.csv")
    v2 = pd.read_csv(RAW / "vendor2.csv")

    v1n = normalize_vendor1(v1)
    v2n = normalize_vendor2(v2)

    combined = pd.concat([v1n, v2n], ignore_index=True)

    
    out_path = PROCESSED / "normalized_snapshot.parquet"
    combined.to_parquet(out_path, index=False)
    print(f"Wrote {out_path} with {len(combined)} rows.")

if __name__ == "__main__":
    main()