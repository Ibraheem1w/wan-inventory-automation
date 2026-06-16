import pandas as pd
from pathlib import Path
import re
from datetime import datetime

PROCESSED = Path("data/processed")
REPORTS = Path("data/reports")
REPORTS.mkdir(exist_ok=True)

def load_latest_snapshot():
    """Load the newest normalized snapshot."""
    files = sorted(PROCESSED.glob("*.parquet"), reverse=True)
    if not files:
        raise FileNotFoundError("No snapshot parquet files found.")
    return pd.read_parquet(files[0])

def check_missing_fields(df):
    """Find rows missing critical fields."""
    required = ["circuit_id", "bandwidth_mbps", "end_date", "site_code"]
    missing = df[df[required].isnull().any(axis=1)].copy()
    missing["issue"] = "Missing required field"
    missing["severity"] = "High"
    return missing

def check_duplicates(df):
    """Find duplicate circuit IDs."""
    dup = df[df["circuit_id"].duplicated(keep=False)].copy()
    dup["issue"] = "Duplicate circuit_id"
    dup["severity"] = "High"
    return dup

def check_bandwidth(df):
    """Validate bandwidth range (1 Mbps to 10,000 Mbps)."""
    invalid = df[(df["bandwidth_mbps"] < 1) | (df["bandwidth_mbps"] > 10000)].copy()
    invalid["issue"] = "Invalid bandwidth"
    invalid["severity"] = "Medium"
    return invalid

def check_expiration(df):
    """Detect expired circuits or invalid dates."""
    today = datetime.now().date()

    def parse_date(date_val):
        try:
            return pd.to_datetime(date_val).date()
        except:
            return None

    df["parsed_end_date"] = df["end_date"].apply(parse_date)

    invalid_date = df[df["parsed_end_date"].isnull()].copy()
    invalid_date["issue"] = "Invalid expiration date format"
    invalid_date["severity"] = "Medium"

    expired = df[(df["parsed_end_date"].notnull()) & (df["parsed_end_date"] < today)].copy()
    expired["issue"] = "Circuit already expired"
    expired["severity"] = "High"

    future_too_far = df[(df["parsed_end_date"].notnull()) & 
                        (df["parsed_end_date"] > (today.replace(year=today.year + 10)))].copy()
    future_too_far["issue"] = "Expiration date too far in the future"
    future_too_far["severity"] = "Low"

    return pd.concat([invalid_date, expired, future_too_far], ignore_index=True)

def check_site_codes(df):
    """Validate site codes (e.g., NY01, TX03)."""
    pattern = re.compile(r"^[A-Z]{2}\d{2}$")
    invalid = df[~df["site_code"].astype(str).str.match(pattern)].copy()
    invalid["issue"] = "Invalid site_code format"
    invalid["severity"] = "Low"
    return invalid

def build_quality_scores(df, issues_df):
    """Assign a quality score (0–100) based on issues found."""
    df = df.copy()
    df["quality_score"] = 100

    # penalty weights
    penalties = {
        "High": 40,
        "Medium": 20,
        "Low": 10
    }

    for _, row in issues_df.iterrows():
        cid = row["circuit_id"]
        sev = row["severity"]
        df.loc[df["circuit_id"] == cid, "quality_score"] -= penalties[sev]

    df["quality_score"] = df["quality_score"].clip(lower=0)
    return df

def run_validation():
    df = load_latest_snapshot()

    issues = []
    issues.append(check_missing_fields(df))
    issues.append(check_duplicates(df))
    issues.append(check_bandwidth(df))
    issues.append(check_expiration(df))
    issues.append(check_site_codes(df))

    all_issues = pd.concat(issues, ignore_index=True)

    quality_scored = build_quality_scores(df, all_issues)

    # Save results
    validation_path = REPORTS / "validation_report.csv"
    quality_path = REPORTS / "circuit_quality_scores.csv"

    all_issues.to_csv(validation_path, index=False)
    quality_scored.to_csv(quality_path, index=False)

    print(f"Validation complete.")
    print(f"- Issues saved to: {validation_path}")
    print(f"- Quality scores saved to: {quality_path}")

if __name__ == "__main__":
    run_validation()