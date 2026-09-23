"""
Usage:
    python src/validate.py                                      # validate all JSON files to faers_flattened.csv
    python src/validate.py --csv                                # validate from a specific CSV file not named faers_flattened.csv

Options:
    --csv            read from a specific file that has a timestamp appended on the file name (e.g., faers_flattened_2026-09-23_15-09.csv)
"""

import csv
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

class FAERSValidator:
    def __init__(self, csv_file: str = "data/raw/faers_flattened.csv"):
        self.csv_file = csv_file
        self.records = []
        self.issues = []
        self.load_csv()
    
    def load_csv(self):
        """Load flattened CSV into memory"""
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            self.records = list(reader)
        print(f"Loaded {len(self.records)} records")
    
    def validate_all(self) -> Dict:
        """Run all validation checks"""
        print("\n=== VALIDATION RULES ===\n")
        
        res = {
            'total_records': len(self.records),
            'issues': {
                'missing_safetyreportid': 0,
                'missing_receivedate': 0,
                'invalid_receivedate_format': 0,
                'invalid_patient_age': 0,
                'missing_serious_flag': 0,
                'inconsistent_seriousness': 0,
                'invalid_sex': 0,
                'date_logic_error': 0,
            },
            'issues_by_record': []
        }
        
        for idx, record in enumerate(self.records):
            record_issues = []
            
            # Rule 1: Required - safetyreportid
            if not record.get('safetyreportid'):
                record_issues.append('missing_safetyreportid')
                res['issues']['missing_safetyreportid'] += 1
            
            # Rule 2: Required - receivedate
            if not record.get('receivedate'):
                record_issues.append('missing_receivedate')
                res['issues']['missing_receivedate'] += 1
            else:
                # Rule 3: Date format validation (YYYY-MM-DD)
                if not self._validate_date_format(record.get('receivedate')):
                    record_issues.append('invalid_receivedate_format')
                    res['issues']['invalid_receivedate_format'] += 1
            
            # Rule 4: Patient age validation (0-150)
            patient_age = record.get('patient_age')
            if patient_age:
                try:
                    age = int(patient_age)
                    if age < 0 or age > 150:
                        record_issues.append('invalid_patient_age')
                        res['issues']['invalid_patient_age'] += 1
                except (ValueError, TypeError):
                    record_issues.append('invalid_patient_age')
                    res['issues']['invalid_patient_age'] += 1
            
            # Rule 5: Required - serious flag
            if not record.get('serious'):
                record_issues.append('missing_serious_flag')
                res['issues']['missing_serious_flag'] += 1
            
            # Rule 6: Seriousness consistency (if serious=1, at least one seriousness flag should be set)
            if record.get('serious') == '1':
                seriousness_flags = [
                    record.get('seriousness_death'),
                    record.get('seriousness_lifethreatening'),
                    record.get('seriousness_hospitalization'),
                    record.get('seriousness_disability'),
                    record.get('seriousness_congenital'),
                    record.get('seriousness_other')
                ]
                if not any(seriousness_flags):
                    record_issues.append('inconsistent_seriousness')
                    res['issues']['inconsistent_seriousness'] += 1
            
            # Rule 7: Patient sex validation (1=Male, 2=Female, 9=Unknown)
            patient_sex = record.get('patient_sex')
            if patient_sex and patient_sex not in ['1', '2', '9']:
                record_issues.append('invalid_sex')
                res['issues']['invalid_sex'] += 1
            
            # Rule 8: Date logic - receivedate should not be before transmissiondate
            if record.get('receivedate') and record.get('transmissiondate'):
                if self._validate_date_format(record.get('receivedate')) and \
                   self._validate_date_format(record.get('transmissiondate')):
                    if record.get('receivedate') > record.get('transmissiondate'):
                        record_issues.append('date_logic_error')
                        res['issues']['date_logic_error'] += 1
            
            if record_issues:
                res['issues_by_record'].append({
                    'safetyreportid': record.get('safetyreportid'),
                    'issues': record_issues
                })
        
        return res
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate YYYYMMDD format"""
        if not date_str or len(date_str) != 8:
            return False
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False
    
    def generate_report(self, res: Dict) -> str:
        """Generate QA report"""
        total = res['total_records']
        issues = res['issues']
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║           SENTINEL: FAERS DATA QUALITY REPORT              ║
╚════════════════════════════════════════════════════════════╝

DATASET OVERVIEW
────────────────
Total Records Processed: {total:,}
Records with Issues: {len(res['issues_by_record']):,}
Completeness Rate: {(1 - len(res['issues_by_record']) / total) * 100:.1f}%

VALIDATION ISSUES BREAKDOWN
────────────────────────────
Missing safetyreportid:              {issues['missing_safetyreportid']:>6} ({100*issues['missing_safetyreportid']/total:.2f}%)
Missing receivedate:                 {issues['missing_receivedate']:>6} ({100*issues['missing_receivedate']/total:.2f}%)
Invalid receivedate format:          {issues['invalid_receivedate_format']:>6} ({100*issues['invalid_receivedate_format']/total:.2f}%)
Invalid patient age (0-150):         {issues['invalid_patient_age']:>6} ({100*issues['invalid_patient_age']/total:.2f}%)
Missing serious flag:                {issues['missing_serious_flag']:>6} ({100*issues['missing_serious_flag']/total:.2f}%)
Inconsistent seriousness flags:      {issues['inconsistent_seriousness']:>6} ({100*issues['inconsistent_seriousness']/total:.2f}%)
Invalid sex code:                    {issues['invalid_sex']:>6} ({100*issues['invalid_sex']/total:.2f}%)
Date logic errors:                   {issues['date_logic_error']:>6} ({100*issues['date_logic_error']/total:.2f}%)

RECOMMENDATIONS
────────────────
1. Exclude {issues['missing_safetyreportid']} records with missing safetyreportid
2. Flag {issues['invalid_patient_age']} age outliers for manual review
3. Investigate {issues['inconsistent_seriousness']} seriousness flag inconsistencies
4. Validate {issues['invalid_receivedate_format']} malformed date records

DATA QUALITY METRICS
─────────────────────
Required Fields Completeness: {(1 - (issues['missing_safetyreportid'] + issues['missing_receivedate'] + issues['missing_serious_flag']) / (total * 3)) * 100:.1f}%
Format Compliance: {(1 - issues['invalid_receivedate_format'] / total) * 100:.1f}%
Value Range Compliance: {(1 - issues['invalid_patient_age'] / total) * 100:.1f}%
Overall Data Quality: {(1 - len(res['issues_by_record']) / total) * 100:.1f}%

"""
        return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate FAERS CSV data")
    parser.add_argument('--csv', type=str, default='data/raw/faers_flattened.csv', help='Input CSV file path')
    args = parser.parse_args()
    
    validator = FAERSValidator(csv_file=args.csv)
    res = validator.validate_all()
    report = validator.generate_report(res)
    print(report)
    
    with open('data/processed/qa_report.txt', 'w') as f:
        f.write(report)
    print(f"QA report saved to data/processed/qa_report.txt")
