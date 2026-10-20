import pandas as pd
import pytest

import utilities
from utilities import CANONICAL_COLS, load_latest_snapshot, normalize_vendor1, normalize_vendor2


def vendor1_rows(**overrides):
    row = {"circuit_id": "A123", "site_code": "nyc01 ", "carrier": "AT&T", "access_type": "MPLS",
           "bandwidth_mbps": "200", "start_date": "2021-01-01", "end_date": "2027-12-31"}
    row.update(overrides)
    return pd.DataFrame([row])


def vendor2_rows(**overrides):
    row = {"vendor_service_id": "a-123 ", "location": "NYC01", "isp": "AT&T", "service_type": "MPLS",
           "speed_mbps": "200", "activation": "2021-01-01", "expiry": "2027-12-31"}
    row.update(overrides)
    return pd.DataFrame([row])


def test_both_vendors_produce_the_same_columns_in_the_same_order():
    assert list(normalize_vendor1(vendor1_rows()).columns) == CANONICAL_COLS
    assert list(normalize_vendor2(vendor2_rows()).columns) == CANONICAL_COLS


@pytest.mark.parametrize("raw", ["A123", "a123 ", "A-123", " a-123", "A 123"])
def test_circuit_ids_that_differ_only_in_format_clean_to_the_same_id(raw):
    cleaned = utilities._clean_id(pd.Series([raw]))
    assert cleaned.iloc[0] == "A123"


def test_vendors_match_on_circuit_id_but_keep_their_own_id():
    one = normalize_vendor1(vendor1_rows(circuit_id="A123")).iloc[0]
    two = normalize_vendor2(vendor2_rows(vendor_service_id="A-123")).iloc[0]
    assert one["circuit_id"] == two["circuit_id"] == "A123"
    assert one["vendor_service_id"] == "A123"
    assert two["vendor_service_id"] == "A-123"


def test_site_codes_are_trimmed_and_upper_case():
    assert normalize_vendor1(vendor1_rows()).iloc[0]["site_code"] == "NYC01"


def test_vendor2_columns_are_renamed():
    row = normalize_vendor2(vendor2_rows(isp="Lumen", service_type="DIA", speed_mbps="300")).iloc[0]
    assert row["carrier"] == "Lumen"
    assert row["access_type"] == "DIA"
    assert row["bandwidth_mbps"] == 300


def test_unreadable_numbers_and_dates_become_blank_instead_of_crashing():
    row = normalize_vendor2(vendor2_rows(speed_mbps="fast", expiry="not-a-date")).iloc[0]
    assert pd.isna(row["bandwidth_mbps"])
    assert pd.isna(row["end_date"])
    assert pd.isna(row["expiration_date"])


def test_missing_status_shows_unknown_and_quality_score_is_left_blank():
    row = normalize_vendor1(vendor1_rows()).iloc[0]
    assert row["status"] == "unknown"
    assert pd.isna(row["quality_score"])


def test_source_is_recorded():
    assert normalize_vendor1(vendor1_rows()).iloc[0]["source"] == "vendor1"
    assert normalize_vendor2(vendor2_rows()).iloc[0]["source"] == "vendor2"


def test_latest_snapshot_is_the_newest_date(tmp_path, monkeypatch):
    monkeypatch.setattr(utilities, "PROCESSED", tmp_path)
    pd.DataFrame({"circuit_id": ["OLD"]}).to_parquet(tmp_path / "2026-01-01-snapshot.parquet")
    pd.DataFrame({"circuit_id": ["NEW"]}).to_parquet(tmp_path / "2026-10-01-snapshot.parquet")
    assert load_latest_snapshot()["circuit_id"].iloc[0] == "NEW"


def test_no_snapshot_gives_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(utilities, "PROCESSED", tmp_path)
    with pytest.raises(FileNotFoundError, match="harvest.py"):
        load_latest_snapshot()
