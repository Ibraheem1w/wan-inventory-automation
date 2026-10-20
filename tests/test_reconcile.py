import pandas as pd

import reconcile as r


def frame(*rows):
    return pd.DataFrame(list(rows))


def test_matching_values_are_not_flagged():
    df = frame({"circuit_id": "A123", "bandwidth_mbps": 200.0},
               {"circuit_id": "A123", "bandwidth_mbps": 200.0})
    assert r.compare(df, "bandwidth_mbps", "Bandwidth mismatch", "High").empty


def test_different_values_are_flagged_with_both_values():
    df = frame({"circuit_id": "C777", "bandwidth_mbps": 500.0},
               {"circuit_id": "C777", "bandwidth_mbps": 1000.0})
    out = r.compare(df, "bandwidth_mbps", "Bandwidth mismatch", "High")
    assert list(out["circuit_id"]) == ["C777"]
    assert out.iloc[0]["severity"] == "High"
    assert out.iloc[0]["values"] == ["1000.0", "500.0"]


def test_a_blank_from_one_vendor_and_a_value_from_the_other_is_a_mismatch():
    df = frame({"circuit_id": "F111", "bandwidth_mbps": 1000.0},
               {"circuit_id": "F111", "bandwidth_mbps": None})
    assert len(r.compare(df, "bandwidth_mbps", "Bandwidth mismatch", "High")) == 1


def test_circuit_listed_by_only_one_vendor_is_flagged():
    df = frame({"circuit_id": "A123", "source": "vendor1"},
               {"circuit_id": "A123", "source": "vendor2"},
               {"circuit_id": "E999", "source": "vendor1"})
    out = r.find_missing_circuits(df)
    assert list(out["circuit_id"]) == ["E999"]
    assert out.iloc[0]["found_in"] == ["vendor1"]
    assert out.iloc[0]["severity"] == "Medium"


def test_nothing_is_missing_when_both_vendors_list_everything():
    df = frame({"circuit_id": "A123", "source": "vendor1"},
               {"circuit_id": "A123", "source": "vendor2"})
    assert r.find_missing_circuits(df).empty
