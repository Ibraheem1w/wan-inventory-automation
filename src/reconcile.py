import pandas as pd
from pathlib import Path
from utilities import load_latest_snapshot

REPORTS = Path("data/reports")


def compare(df, col, issue, severity):
    # a blank from one vendor and a value from another also counts as a mismatch
    g = df.groupby("circuit_id")[col].agg(
        n_values=lambda x: x.nunique(dropna=False),
        values=lambda x: sorted(set(x.astype(str))),
    ).reset_index()
    g = g[g["n_values"] > 1].copy()
    g["issue"] = issue
    g["severity"] = severity
    return g


def find_missing_circuits(df):
    n_sources = df["source"].nunique()
    g = df.groupby("circuit_id")["source"].agg(lambda x: sorted(set(x))).reset_index(name="found_in")
    g = g[g["found_in"].apply(len) < n_sources].copy()
    g["issue"] = "Missing from at least one vendor"
    g["severity"] = "Medium"
    return g


def run_reconciliation():
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = load_latest_snapshot()

    report = pd.concat([
        compare(df, "bandwidth_mbps", "Bandwidth mismatch", "High"),
        compare(df, "end_date", "Expiration date mismatch", "Medium"),
        find_missing_circuits(df),
    ], ignore_index=True)

    out = REPORTS / "reconciliation_report.csv"
    report.to_csv(out, index=False)
    print(f"Reconciliation found {len(report)} issues. Saved to {out}")


if __name__ == "__main__":
    run_reconciliation()