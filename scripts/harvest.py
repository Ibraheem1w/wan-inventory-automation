import pandas as pd
from pathlib import Path
from utilities import normalize_vendor1, normalize_vendor2



def detect_vendor(filename):
    name = filename.lower()
    if "vendor1" in name:
        return "vendor1"
    elif "vendor2" in name:
        return "vendor2"
    else:
        raise ValueError(f"Unknown vendor type in {filename}")


def process_file(file_path):
    df = pd.read_csv(file_path)
    vendor = detect_vendor(file_path.name)

 
    if vendor == "vendor1":
        df_norm = normalize_vendor1(df)
    elif vendor == "vendor2":
        df_norm = normalize_vendor2(df)

    df_norm["last_seen"] = pd.Timestamp.now()
    df_norm["source_file"] = file_path.name

    return df_norm


def main():
    RAW = Path("data/raw")
    PROCESSED = Path("data/processed")

    raw_files = list(RAW.glob("*.csv"))
    normalized_list = []

    for file_path in raw_files:
        df_norm = process_file(file_path)
        normalized_list.append(df_norm)

   
    all_data = pd.concat(normalized_list, ignore_index=True)

   
    date_tag = pd.Timestamp.now().strftime("%Y-%m-%d")
    output_file = PROCESSED / f"{date_tag}-snapshot.parquet"

    all_data.to_parquet(output_file, index=False)
    print(f"Wrote {output_file} with {len(all_data)} rows.")


if __name__ == "__main__":
    main()

