import pandas as pd
from pathlib import Path
from utilities import normalize_vendor1, normalize_vendor2

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
NORMALIZERS = {"vendor1": normalize_vendor1, "vendor2": normalize_vendor2}


def detect_vendor(filename):
    name = filename.lower()
    for vendor in NORMALIZERS:
        if vendor in name:
            return vendor
    return None


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    frames = []

    for path in sorted(RAW.glob("*.csv")):
        vendor = detect_vendor(path.name)
        if vendor is None:
            print(f"Skipping {path.name}: unknown vendor")
            continue
        df = NORMALIZERS[vendor](pd.read_csv(path))
        df["source_file"] = path.name
        frames.append(df)
        print(f"Read {path.name}: {len(df)} rows ({vendor})")

    if not frames:
        raise SystemExit("No vendor files found in data/raw.")

    all_data = pd.concat(frames, ignore_index=True)
    out = PROCESSED / f"{pd.Timestamp.now():%Y-%m-%d}-snapshot.parquet"
    all_data.to_parquet(out, index=False)
    print(f"Wrote {out} with {len(all_data)} rows.")


if __name__ == "__main__":
    main()

