"""
Usage:
    python src/load.py                                       # Load faers_transformed.csv to SQLite
    python src/load.py --csv data/raw/faers_transformed.csv  # Load specific transformed CSV

Process:
    1. Validates all records using validate.py
    2. Creates database schema from schema.sql
    3. Loads transformed data into normalized SQLite tables
    4. Logs validation issues to validation_log table
    5. Generates database statistics report

Output:
    - data/processed/sentinel.db (SQLite database)
    - data/processed/db_stats.txt (statistics report)

Options:
    --csv PATH              Input transformed CSV file path (default: data/raw/faers_transformed.csv)
"""

import sqlite3
import csv
import argparse
from pathlib import Path
from typing import List, Dict

class FAERSLoader:
    def __init__(self, db_file: str = "data/processed/sentinel.db"):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        print(f"Connected to {self.db_file}")
    
    def create_schema(self, schema_file: str = "schema.sql"):
        with open(schema_file, 'r') as f:
            sql = f.read()
        
        self.cursor.executescript(sql)
        self.conn.commit()
        print("✓ Schema created")
    
    def load_from_csv(self, csv_file: str = "data/raw/faers_transformed.csv"):
        records_loaded = 0
        records_skipped = 0
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    self.cursor.execute("""
                        INSERT INTO adverse_events 
                        (safetyreportid, receivedate, transmissiondate, reporttype, serious)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get('safetyreportid'),
                        row.get('receivedate'),
                        row.get('transmissiondate'),
                        row.get('reporttype'),
                        row.get('serious')
                    ))
                    
                    safetyreportid = row.get('safetyreportid')
                    
                    self.cursor.execute("""
                        INSERT INTO seriousness_flags
                        (safetyreportid, seriousness_death, seriousness_lifethreatening,
                         seriousness_hospitalization, seriousness_disability,
                         seriousness_congenital, seriousness_other)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        safetyreportid,
                        row.get('seriousness_death'),
                        row.get('seriousness_lifethreatening'),
                        row.get('seriousness_hospitalization'),
                        row.get('seriousness_disability'),
                        row.get('seriousness_congenital'),
                        row.get('seriousness_other')
                    ))
                    
                    self.cursor.execute("""
                        INSERT INTO patient_info
                        (safetyreportid, patient_age, patient_age_unit, patient_sex)
                        VALUES (?, ?, ?, ?)
                    """, (
                        safetyreportid,
                        row.get('patient_age'),
                        row.get('patient_age_unit'),
                        row.get('patient_sex')
                    ))
                    
                    self.cursor.execute("""
                        INSERT INTO reporter_info
                        (safetyreportid, reporter_country, reporter_qualification, sender_organization)
                        VALUES (?, ?, ?, ?)
                    """, (
                        safetyreportid,
                        row.get('reporter_country'),
                        row.get('reporter_qualification'),
                        row.get('sender_organization')
                    ))
                    
                    records_loaded += 1
                    
                except sqlite3.IntegrityError as e:
                    records_skipped += 1
                    print(f"Skipped record {row.get('safetyreportid')}: {e}")
        
        self.conn.commit()
        print(f"✓ Loaded {records_loaded} records, skipped {records_skipped}")
    
    def log_validation_issues(self, validation_results: Dict):
        for issue_record in validation_results.get('issues_by_record', []):
            safetyreportid = issue_record.get('safetyreportid')
            issues = issue_record.get('issues', [])
            
            for issue in issues:
                self.cursor.execute("""
                    INSERT INTO validation_log
                    (safetyreportid, validation_issue, severity)
                    VALUES (?, ?, ?)
                """, (safetyreportid, issue, 'warning'))
        
        self.conn.commit()
        print(f"✓ Logged {len(validation_results.get('issues_by_record', []))} validation issues")
    
    def generate_db_stats(self) -> str:
        stats = f"""

╔════════════════════════════════════════════════════════════╗
║        SENTINEL: DATABASE LOAD STATISTICS                 ║
╚════════════════════════════════════════════════════════════╝

RECORD COUNTS
─────────────
"""
        
        self.cursor.execute("SELECT COUNT(*) FROM adverse_events")
        total = self.cursor.fetchone()[0]
        stats += f"Total Adverse Event Records: {total:,}\n"
        
        self.cursor.execute("SELECT serious, COUNT(*) FROM adverse_events GROUP BY serious ORDER BY serious")
        for serious, count in self.cursor.fetchall():
            stats += f"  {serious:20s}: {count:>6,} ({100*count/total:.1f}%)\n"
        
        self.cursor.execute("SELECT COUNT(*) FROM validation_log")
        issues_logged = self.cursor.fetchone()[0]
        stats += f"\nValidation Issues Logged: {issues_logged}\n"
        
        self.cursor.execute("""
            SELECT validation_issue, COUNT(*) as count 
            FROM validation_log 
            GROUP BY validation_issue 
            ORDER BY count DESC
        """)
        stats += "\nTop Issues by Type:\n"
        for issue, count in self.cursor.fetchall():
            stats += f"  {issue:40s}: {count:>6} records\n"
        
        self.cursor.execute("SELECT COUNT(*) FROM patient_info WHERE patient_age IS NOT NULL")
        age_count = self.cursor.fetchone()[0]
        stats += f"\nPatient Demographics\n"
        stats += f"  Records with Age Data: {age_count:,}\n"
        
        self.cursor.execute("SELECT AVG(CAST(patient_age AS FLOAT)) FROM patient_info WHERE patient_age IS NOT NULL")
        avg_age = self.cursor.fetchone()[0]
        stats += f"  Average Age: {avg_age:.1f} years\n"
        
        stats += "\n" + "="*60 + "\n"
        return stats
    
    def close(self):
        if self.conn:
            self.conn.close()
            print(f"✓ Database connection closed")


if __name__ == "__main__":
    from validate import FAERSValidator
    
    parser = argparse.ArgumentParser(description="Load FAERS data to SQLite")
    parser.add_argument('--csv', type=str, default='data/raw/faers_transformed.csv', help='Input CSV file path')
    
    args = parser.parse_args()
    
    print("STEP 1: VALIDATION")
    validator = FAERSValidator()
    validation_results = validator.validate_all()
    
    print("\nSTEP 2: DATABASE LOAD")
    loader = FAERSLoader()
    loader.connect()
    loader.create_schema()
    loader.load_from_csv(csv_file=args.csv)
    loader.log_validation_issues(validation_results)
    
    print("\nSTEP 3: DATABASE STATISTICS")
    stats = loader.generate_db_stats()
    print(stats)
    
    with open('data/processed/db_stats.txt', 'w') as f:
        f.write(stats)
    print("✓ Database statistics saved to data/processed/db_stats.txt")
    
    loader.close()