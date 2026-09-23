"""
Usage:
    python src/transform.py                                                      # Transform faers_flattened.csv
    python src/transform.py --csv data/raw/faers_flattened_2026-09-23_14-30.csv  # Transform specific file
    python src/transform.py --output data/raw/custom_transformed.csv             # Custom output path

Transformations applied:
    - Dates: YYYYMMDD → YYYY-MM-DD format
    - Sex codes: 1/2/9 → Male/Female/Unknown
    - Serious flag: 1/2 → Serious/Non-Serious
    - Age units: 801/802/803/804 → Years/Months/Weeks/Days
    - Age values: String → Integer

Options:
    --csv PATH              Input CSV file path (default: data/raw/faers_flattened.csv)
    --output PATH           Output CSV file path (default: data/raw/faers_transformed.csv)
"""

import csv
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class FAERSTransformer:
    def __init__(self, csv_file: str = "data/raw/faers_flattened.csv"):
        self.csv_file = csv_file
        self.records = []
        self.load_csv()
    
    def load_csv(self):
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            self.records = list(reader)
        print(f"Loaded {len(self.records)} records for transformation")
    
    def parse_date(self, date_str: str) -> str:
        if not date_str or len(date_str) != 8:
            return None
        try:
            parsed = datetime.strptime(date_str, '%Y%m%d')
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    def map_sex(self, sex_code: str) -> str:
        sex_map = {
            '1': 'Male',
            '2': 'Female',
            '9': 'Unknown'
        }
        return sex_map.get(sex_code, 'Unknown')
    
    def map_serious(self, serious_code: str) -> str:
        serious_map = {
            '1': 'Serious',
            '2': 'Non-Serious'
        }
        return serious_map.get(serious_code, 'Unknown')
    
    def map_age_unit(self, unit_code: str) -> str:
        unit_map = {
            '801': 'Years',
            '802': 'Months',
            '803': 'Weeks',
            '804': 'Days'
        }
        return unit_map.get(unit_code, 'Unknown')
    
    def transform_record(self, record: Dict) -> Dict:
        transformed = {}
        
        transformed['safetyreportid'] = record.get('safetyreportid')
        transformed['receivedate'] = self.parse_date(record.get('receivedate'))
        transformed['transmissiondate'] = self.parse_date(record.get('transmissiondate'))
        transformed['reporttype'] = record.get('reporttype')
        transformed['serious'] = self.map_serious(record.get('serious'))
        
        transformed['seriousness_death'] = record.get('seriousness_death')
        transformed['seriousness_lifethreatening'] = record.get('seriousness_lifethreatening')
        transformed['seriousness_hospitalization'] = record.get('seriousness_hospitalization')
        transformed['seriousness_disability'] = record.get('seriousness_disability')
        transformed['seriousness_congenital'] = record.get('seriousness_congenital')
        transformed['seriousness_other'] = record.get('seriousness_other')
        
        patient_age = record.get('patient_age')
        transformed['patient_age'] = int(patient_age) if patient_age and patient_age.isdigit() else None
        transformed['patient_age_unit'] = self.map_age_unit(record.get('patient_age_unit'))
        transformed['patient_sex'] = self.map_sex(record.get('patient_sex'))
        
        transformed['reporter_country'] = record.get('reporter_country')
        transformed['reporter_qualification'] = record.get('reporter_qualification')
        transformed['sender_organization'] = record.get('sender_organization')
        
        return transformed
    
    def transform_all(self) -> List[Dict]:
        transformed_records = []
        
        for record in self.records:
            transformed = self.transform_record(record)
            transformed_records.append(transformed)
        
        print(f"Transformed {len(transformed_records)} records")
        return transformed_records
    
    def export_as_csv(self, records: List[Dict], output_file: str = "data/raw/faers_transformed.csv"):
        if not records:
            print("No records to save")
            return
        
        fields = records[0].keys()
        
        output_path = Path(output_file)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"Saved {len(records)} records to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform FAERS validated CSV data")
    parser.add_argument('--csv', type=str, default='data/raw/faers_flattened.csv', help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/raw/faers_transformed.csv', help='Output CSV file path')
    
    args = parser.parse_args()
    
    transformer = FAERSTransformer(csv_file=args.csv)
    transformed_records = transformer.transform_all()
    transformer.export_as_csv(transformed_records, output_file=args.output)