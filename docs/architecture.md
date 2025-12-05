# WAN Automation Project Architecture

This project automates:
1. **Harvesting** vendor WAN circuit data
2. **Normalizing** inconsistent formats
3. **Reconciling** circuit mismatches
4. **Validating** data quality
5. **Generating** expiration alerts
6. **Preparing** data for dashboards (e.g., Splunk)

## Folder Structure
- data/raw → unmodified vendor files
- data/processed → cleaned & normalized outputs
- scripts/ → automation logic
- tests/ → unit tests
- docs/ → documentation