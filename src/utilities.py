from pathlib import Path
import pandas as pd

PROCESSED = Path("data/processed")

CANONICAL_COLS = [
    "circuit_id", "vendor_service_id", "site_code", "carrier", "access_type",
    "bandwidth_mbps", "status", "start_date", "end_date", "expiration_date",
    "device_hostname", "wan_interface", "mrc_usd", "source", "last_seen", "quality_score"
]


def _clean_id(s):
    # "a123 " and "A-123" should match "A123"
    return s.astype("string").str.strip().str.upper().str.replace(r"[-\s]", "", regex=True)


def _finish(out, source):
    out["source"] = source
    out["last_seen"] = pd.Timestamp.now(tz="UTC")
    out["quality_score"] = pd.NA   # filled in by validate_inventory.py
    for c in CANONICAL_COLS:
        if c not in out.columns:
            out[c] = pd.NA
    return out[CANONICAL_COLS]


def normalize_vendor1(df):
    out = pd.DataFrame()
    out["circuit_id"]        = _clean_id(df["circuit_id"])
    out["vendor_service_id"] = df["circuit_id"]
    out["site_code"]         = df["site_code"].astype("string").str.strip().str.upper()
    out["carrier"]           = df["carrier"]
    out["access_type"]       = df.get("access_type", "UNKNOWN")
    out["bandwidth_mbps"]    = pd.to_numeric(df["bandwidth_mbps"], errors="coerce")
    out["status"]            = df.get("status", "unknown")
    out["start_date"]        = pd.to_datetime(df["start_date"], errors="coerce")
    out["end_date"]          = pd.to_datetime(df["end_date"], errors="coerce")
    out["expiration_date"]   = out["end_date"]
    return _finish(out, "vendor1")


def normalize_vendor2(df):
    out = pd.DataFrame()
    out["circuit_id"]        = _clean_id(df["vendor_service_id"])
    out["vendor_service_id"] = df["vendor_service_id"]
    out["site_code"]         = df["location"].astype("string").str.strip().str.upper()
    out["carrier"]           = df["isp"]
    out["access_type"]       = df.get("service_type", "UNKNOWN")
    out["bandwidth_mbps"]    = pd.to_numeric(df["speed_mbps"], errors="coerce")
    out["status"]            = df.get("status", "unknown")
    out["start_date"]        = pd.to_datetime(df["activation"], errors="coerce")
    out["end_date"]          = pd.to_datetime(df["expiry"], errors="coerce")
    out["expiration_date"]   = out["end_date"]
    return _finish(out, "vendor2")


def load_latest_snapshot():
    # harvest.py names files YYYY-MM-DD-snapshot.parquet, so name order is date order
    files = sorted(PROCESSED.glob("*-snapshot.parquet"))
    if not files:
        raise FileNotFoundError("No snapshots in data/processed. Run src/harvest.py first.")
    print(f"Using {files[-1].name}")
    return pd.read_parquet(files[-1])
