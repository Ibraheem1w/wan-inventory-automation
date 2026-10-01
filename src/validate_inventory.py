import pandas as pd
from pathlib import Path
from utilities import load_latest_snapshot

REPORTS = Path("data/reports")
PENALTIES = {"High": 0.4, "Medium": 0.2, "Low": 0.1}
SITE_CODE = r"^[A-Z]{3}\d{2}$"   # e.g. NYC01, MEX01


def flag(rows, issue, severity):
    rows = rows.copy()
    rows["issue"] = issue
    rows["severity"] = severity
    return rows


def check_missing_fields(df):
    # bad dates and numbers become blanks during normalization, so they land here
    required = ["circuit_id", "bandwidth_mbps", "end_date", "site_code"]
    return flag(df[df[required].isna().any(axis=1)], "Missing or unreadable required field", "High")


def check_duplicates(df):
    # the same circuit from two vendors is expected, twice from one vendor is not
    return flag(df[df.duplicated(["circuit_id", "source"], keep=False)],
                "Duplicate circuit_id within a vendor", "High")


def check_bandwidth(df):
    bad = (df["bandwidth_mbps"] < 1) | (df["bandwidth_mbps"] > 10000)
    return flag(df[bad], "Bandwidth outside 1 to 10,000 Mbps", "Medium")


def check_expiration(df):
    today = pd.Timestamp.now().normalize()
    end = pd.to_datetime(df["end_date"], errors="coerce")
    expired = flag(df[end < today], "Circuit already expired", "High")
    too_far = flag(df[end > today + pd.DateOffset(years=10)], "Expiration more than 10 years out", "Low")
    return pd.concat([expired, too_far])


def check_site_codes(df):
    ok = df["site_code"].astype("string").str.match(SITE_CODE, na=False)
    return flag(df[df["site_code"].notna() & ~ok], "Invalid site_code format", "Low")


def build_quality_scores(df, issues):
    # 1.0 means no issues, same 0 to 1 scale as the data dictionary
    per_row = issues.drop_duplicates(["row_id", "issue"])
    penalty = per_row["severity"].map(PENALTIES).groupby(per_row["row_id"]).sum()
    scored = df.copy()
    scored["quality_score"] = (1 - scored["row_id"].map(penalty).fillna(0)).clip(lower=0).round(2)
    return scored


def run_validation():
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = load_latest_snapshot().reset_index(drop=True)
    df["row_id"] = df.index

    issues = pd.concat([
        check_missing_fields(df),
        check_duplicates(df),
        check_bandwidth(df),
        check_expiration(df),
        check_site_codes(df),
    ], ignore_index=True).drop(columns=["quality_score"])

    scored = build_quality_scores(df, issues)

    issues.to_csv(REPORTS / "validation_report.csv", index=False)
    scored.to_csv(REPORTS / "circuit_quality_scores.csv", index=False)
    print(f"Validation found {len(issues)} issues across {issues['row_id'].nunique()} rows.")


if __name__ == "__main__":
    run_validation()