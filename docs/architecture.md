# Architecture

Raw vendor CSV files go into data/raw. harvest.py reads them, converts each vendor format into one standard set of columns, and writes a dated snapshot to data/processed. reconcile.py and validate_inventory.py each read the latest snapshot and write their reports to data/reports.

Folders

data/raw: vendor files. The scripts never change these.
data/processed: dated snapshots, one file per day.
data/reports: reconciliation and validation output.
src: all of the scripts.
docs: this file and the data dictionary.

Ideas not built yet: expiration alerts and dashboards.