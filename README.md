# Sentinel
# an FDA Adverse Event Data Pipeline

Extract, validate, transform, and analyse FDA adverse event reports (FAERS).

Files were downloaded from openFDA's 2026 Q1-Q4 Drug Adverse Events [/drug/event] files from https://open.fda.gov/apis/drug/event/download/

File names used for processing follow a format of 

- drug-event-xxxx-of-yyyy.json (xxxx = file number, yyyy = total files in quarter)
    - example: drug-event-0001-of-0031.json


## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run

# Step 1: Extract
python src/extract.py

# Step 2: Validate
python src/validate.py

# Step 3: Transform
python src/transform.py

# Step 4: Load
python src/load.py
```

## Output

- `data/processed/sentinel.db` — SQLite database with 48,000+ validated records
- `data/processed/qa_report.txt` — Data quality metrics
- `data/processed/db_stats.txt` — Database statistics

## What It Does

1. Extract: Parse JSON from FDA opendata API → flatten to CSV
2. Validate: Check 8 compliance rules, flag issues
3. Transform: Standardise dates and codes → human-readable format
4. Load: Insert into normalised SQLite database with audit trail

## Data Quality

- Total Records: 48,000+
- Completeness: 99.6%
- Serious Events: 58.5%
- Average Age: 55.1 years

## Tools and tech used

- Python 3.9
- SQLite3
- No external dependencies (stdlib only)

## Author

Taiyo Leon Moriguchi | [GitHub](https://github.com/perfectimmortalmachine)
