"""Runs harvest, reconcile and validate on small files in a temporary folder."""
import pandas as pd

import harvest
import reconcile
import validate_inventory


def write_samples(folder):
    today = pd.Timestamp.now().normalize()
    good_end = (today + pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    (folder / "vendor1.csv").write_text(
        "circuit_id,site_code,carrier,access_type,bandwidth_mbps,start_date,end_date\n"
        f"A123,NYC01,AT&T,MPLS,200,2021-01-01,{good_end}\n"
        f"C777,ATL02,Lumen,DIA,500,2022-03-15,{good_end}\n"
        "F111,HOU03,Verizon,MPLS,,2022-08-01,2020-08-01\n"
        "F111,HOU03,Verizon,MPLS,1000,2022-08-01,2020-08-01\n"
    )
    (folder / "vendor2.csv").write_text(
        "vendor_service_id,location,isp,service_type,speed_mbps,activation,expiry\n"
        f"A-123,NYC01,AT&T,MPLS,200,2021-01-01,{good_end}\n"
        f"C-777,ATL02,Lumen,DIA,1000,2022-03-15,{good_end}\n"
    )


def run_everything(tmp_path, monkeypatch):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    write_samples(raw)
    monkeypatch.chdir(tmp_path)
    harvest.main()
    reconcile.run_reconciliation()
    validate_inventory.run_validation()
    return tmp_path / "data"


def test_harvest_writes_one_snapshot_with_every_row(tmp_path, monkeypatch):
    data = run_everything(tmp_path, monkeypatch)
    snapshots = list((data / "processed").glob("*-snapshot.parquet"))
    assert len(snapshots) == 1
    assert len(pd.read_parquet(snapshots[0])) == 6


def test_harvest_skips_files_it_does_not_recognize(tmp_path, monkeypatch, capsys):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    write_samples(raw)
    (raw / "other.csv").write_text("a,b\n1,2\n")
    monkeypatch.chdir(tmp_path)
    harvest.main()
    assert "Skipping other.csv" in capsys.readouterr().out


def test_reconciliation_report(tmp_path, monkeypatch):
    data = run_everything(tmp_path, monkeypatch)
    report = pd.read_csv(data / "reports" / "reconciliation_report.csv")
    by_issue = report.groupby("issue")["circuit_id"].apply(sorted).to_dict()
    assert by_issue["Bandwidth mismatch"] == ["C777", "F111"]
    assert by_issue["Missing from at least one vendor"] == ["F111"]


def test_quality_scores(tmp_path, monkeypatch):
    data = run_everything(tmp_path, monkeypatch)
    scores = pd.read_csv(data / "reports" / "circuit_quality_scores.csv")
    by_circuit = scores.groupby("circuit_id")["quality_score"].min()
    assert by_circuit["A123"] == 1.0
    assert by_circuit["F111"] == 0.0


def test_validation_report_has_one_row_per_issue(tmp_path, monkeypatch):
    data = run_everything(tmp_path, monkeypatch)
    issues = pd.read_csv(data / "reports" / "validation_report.csv")
    assert set(issues["circuit_id"]) == {"F111"}
    assert "Duplicate circuit_id within a vendor" in set(issues["issue"])
    assert "Circuit already expired" in set(issues["issue"])
