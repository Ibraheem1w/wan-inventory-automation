import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")
REPORTS = Path("data/reports")
REPORTS.mkdir(exist_ok=True)

def load_latest_snapshot():
    """Load the most recent normalized snapshot from data/processed."""
    parquet_files = sorted(PROCESSED.glob("*.parquet"), reverse=True)
    if not parquet_files:
        raise FileNotFoundError("No snapshot files found in data/processed.")
    return pd.read_parquet(parquet_files[0])

def reconcile_bandwidth(df):
    """Check for bandwidth mismatches between vendor sources."""
    mismatches = df.groupby("circuit_id").agg(
        unique_bw=("bandwidth_mbps", "nunique"),
        values=("bandwidth_mbps", lambda x: list(set(x)))
    ).reset_index()

    mismatches = mismatches[mismatches["unique_bw"] > 1]
    mismatches["issue"] = "Bandwidth mismatch"
    mismatches["severity"] = "High"

    return mismatches

def reconcile_expiration(df):
    """Check for different expiration dates between vendors."""
    mismatches = df.groupby("circuit_id").agg(
        unique_exp=("end_date", "nunique"),
        values=("end_date", lambda x: list(set(x)))
    ).reset_index()

    mismatches = mismatches[mismatches["unique_exp"] > 1]
    mismatches["issue"] = "Expiration date mismatch"
    mismatches["severity"] = "Medium"

    return mismatches

def find_missing_circuits(df):
    """Detect circuits missing from one or more vendor sources."""
    counts = df.groupby("circuit_id")["source"].nunique().reset_index()
    missing = counts[counts["source"] < df["source"].nunique()].copy()
    missing["issue"] = "Missing circuit in one vendor"
    missing["severity"] = "Medium"
    return missing

def run_reconciliation():
    df = load_latest_snapshot()

    issues = []

    issues.append(reconcile_bandwidth(df))
    issues.append(reconcile_expiration(df))
    issues.append(find_missing_circuits(df))

    final_report = pd.concat(issues, ignore_index=True)
    out_path = REPORTS / "reconciliation_report.csv"
    final_report.to_csv(out_path, index=False)

    print(f"Reconciliation complete. Report saved to {out_path}")

if __name__ == "__main__":
    run_reconciliation()