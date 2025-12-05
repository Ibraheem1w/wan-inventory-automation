WAN Circuit Inventory Automation

This project automates the process of cleaning, organizing, and checking WAN (Wide Area Network) circuit data that comes from different telecom vendors. Each vendor provides data in its own format, so the main goal is to standardize everything and make it easier to analyze.

The system includes scripts for normalizing vendor files, detecting mismatches, checking data quality, and creating daily snapshots.

What the Project Does
1. Normalize vendor data

Different vendors use different column names and formats.
The normalization script (snapshot.py) converts them into one consistent structure so the data can be compared and processed.

2. Automate ingestion

harvest.py looks inside the data/raw/ folder, figures out which vendor each file belongs to, normalizes them, adds timestamps, and saves a snapshot for that day.

This removes a lot of manual work and makes updates repeatable.

3. Reconcile differences

reconcile.py compares circuit records across vendors and reports issues like:

bandwidth differences

expiration dates that don’t match

circuits missing from one source

duplicate circuit IDs

A CSV report is generated so inconsistencies are easy to review.

4. Validate data quality

validate_inventory.py runs several checks to make sure the data is usable:

missing fields

invalid or expired dates

unrealistic bandwidth values

incorrect site codes

duplicates

Each circuit gets a simple quality score based on any issues found.

Folder Structure
wan-inventory-automation/
│
├── scripts/
│   ├── harvest.py 
│   ├── snapshot.py
│   ├── reconcile.py
│   ├── validate_inventory.py
│   └── utilities.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
│
├── docs/
│   ├── architecture.md
│   └── data_dictionary.md
│
├── requirements.txt
└── README.md

How to Run It
Create and activate a virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Add vendor CSVs:

Place them into:

data/raw/

Generate a snapshot:
python scripts/harvest.py

Reconciliation:
python scripts/reconcile.py

Validation:
python scripts/validate_inventory.py

## Why This Project Matters

WAN circuit data usually comes from multiple vendors, and the formats rarely match.
Teams often spend time cleaning spreadsheets before any real work can begin.

This project helps with:
- getting all the data into one consistent format
- spotting missing or incorrect fields early
- making it easier to review inventory during audits
- supporting SD-WAN and network operations teams who need accurate circuit data

It basically turns a messy set of files into something a network engineer can actually use.