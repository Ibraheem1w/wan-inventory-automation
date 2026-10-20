import pandas as pd

import validate_inventory as v


def row(**overrides):
    today = pd.Timestamp.now().normalize()
    base = {"circuit_id": "A123", "source": "vendor1", "site_code": "NYC01",
            "bandwidth_mbps": 200.0, "end_date": today + pd.DateOffset(years=3)}
    base.update(overrides)
    return base


def frame(*rows):
    return pd.DataFrame(list(rows))


def test_a_clean_row_has_no_issues():
    df = frame(row())
    for check in (v.check_missing_fields, v.check_duplicates, v.check_bandwidth,
                  v.check_expiration, v.check_site_codes):
        assert check(df).empty


def test_missing_required_field_is_high():
    for column in ("circuit_id", "bandwidth_mbps", "end_date", "site_code"):
        issues = v.check_missing_fields(frame(row(**{column: None})))
        assert len(issues) == 1, column
        assert issues.iloc[0]["severity"] == "High"


def test_duplicate_within_one_vendor_is_flagged_but_across_vendors_is_not():
    same_vendor = frame(row(), row())
    assert len(v.check_duplicates(same_vendor)) == 2
    two_vendors = frame(row(source="vendor1"), row(source="vendor2"))
    assert v.check_duplicates(two_vendors).empty


def test_bandwidth_limits():
    assert v.check_bandwidth(frame(row(bandwidth_mbps=1.0))).empty
    assert v.check_bandwidth(frame(row(bandwidth_mbps=10000.0))).empty
    assert len(v.check_bandwidth(frame(row(bandwidth_mbps=0.0)))) == 1
    assert len(v.check_bandwidth(frame(row(bandwidth_mbps=10001.0)))) == 1


def test_expired_circuit_is_high_and_far_future_is_low():
    today = pd.Timestamp.now().normalize()
    expired = v.check_expiration(frame(row(end_date=today - pd.Timedelta(days=1))))
    assert list(expired["severity"]) == ["High"]
    far = v.check_expiration(frame(row(end_date=today + pd.DateOffset(years=11))))
    assert list(far["severity"]) == ["Low"]


def test_circuit_expiring_today_is_not_expired():
    today = pd.Timestamp.now().normalize()
    assert v.check_expiration(frame(row(end_date=today))).empty


def test_site_code_format():
    good = frame(row(site_code="NYC01"), row(site_code="ATL02", circuit_id="B"))
    assert v.check_site_codes(good).empty
    for bad in ("AUS1", "NYC001", "nyc01", "NY001"):
        assert len(v.check_site_codes(frame(row(site_code=bad)))) == 1, bad


def test_blank_site_code_is_reported_as_missing_not_as_bad_format():
    df = frame(row(site_code=None))
    assert v.check_site_codes(df).empty
    assert len(v.check_missing_fields(df)) == 1


def scored(severities):
    df = pd.DataFrame({"row_id": [0, 1]})
    issues = pd.DataFrame([{"row_id": 0, "issue": f"issue {i}", "severity": s}
                           for i, s in enumerate(severities)],
                          columns=["row_id", "issue", "severity"])
    return v.build_quality_scores(df, issues)["quality_score"].tolist()


def test_quality_score_penalties():
    assert scored([]) == [1.0, 1.0]
    assert scored(["High"]) == [0.6, 1.0]
    assert scored(["Medium"]) == [0.8, 1.0]
    assert scored(["Low"]) == [0.9, 1.0]
    assert scored(["High", "Medium", "Low"]) == [0.3, 1.0]


def test_quality_score_never_goes_below_zero():
    assert scored(["High", "High", "High"]) == [0.0, 1.0]


def test_same_issue_on_the_same_row_counts_once():
    df = pd.DataFrame({"row_id": [0]})
    issues = pd.DataFrame([{"row_id": 0, "issue": "Duplicate", "severity": "High"}] * 2)
    assert v.build_quality_scores(df, issues)["quality_score"].tolist() == [0.6]
