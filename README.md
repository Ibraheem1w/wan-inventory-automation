# WAN Circuit Inventory Automation

Telecom vendors send circuit data in different formats. This project cleans it into one standard format, compares what the records say about the same circuit, and checks the data for problems.

## What it does

harvest.py reads every vendor CSV in data/raw, converts it to one set of columns, and saves a dated snapshot in data/processed. The conversion rules for each vendor live in utilities.py. Circuit IDs are cleaned up so that A123 from one vendor and A-123 from another match.

reconcile.py compares records that share a circuit ID and reports bandwidth differences, expiration date differences, and circuits that only one vendor lists.

validate_inventory.py checks each row for missing or unreadable fields, duplicate circuit IDs within one vendor, bandwidth outside 1 to 10,000 Mbps, circuits that have already expired or expire more than 10 years out, and site codes that are not three letters followed by two digits. Each row gets a quality score from 0 to 1. A High issue takes off 0.4, a Medium issue 0.2, and a Low issue 0.1.

export_snapshot.py saves the latest snapshot as a CSV.

## Example run

The sample files in data/raw have 13 rows. On 2026-10-01 the results were:

Reconciliation found 7 issues: bandwidth mismatches on C777 and F111, an expiration mismatch on D888, and four circuits that only one vendor lists.

Validation found 12 issues across 8 rows. Quality scores ranged from 0.0 to 1.0. A123, which both vendors agree on, scored 1.0. F111 appears twice in one vendor file with a blank bandwidth on one row and scored 0.0.

Results from reconcile.py and validate_inventory.py are saved in data/reports.

## Running it

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python src/harvest.py
    python src/reconcile.py
    python src/validate_inventory.py

Run these from the top folder of the project. Real vendor files go in data/raw. Give them names that contain vendor1 or vendor2 so harvest.py knows which format they use. Files named exactly vendor1.csv and vendor2.csv are the made up samples.

## Limits

The sample data is made up.

Only two vendor formats are supported. A third vendor needs its own function in utilities.py and an entry in harvest.py.

Circuits count as expired based on the day you run the scripts, so scores change over time.

Vendors do not send a status, so it shows as unknown.

The site code format and the penalty sizes are assumptions, not rules from a real network.
