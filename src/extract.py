import json
import csv
from pathlib import Path
from typing import List, Dict

class FAERSExtractor:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
    
    def flatten_record(self, record: Dict) -> Dict:
        """Flatten nested JSON record into flat dictionary"""
        flat = {}
        
        # Top-level fields
        flat['safetyreportid'] = record.get('safetyreportid')
        flat['receivedate'] = record.get('receivedate')
        flat['transmissiondate'] = record.get('transmissiondate')
        flat['serious'] = record.get('serious')
        flat['reporttype'] = record.get('reporttype')
        
        # Seriousness flags
        flat['seriousness_death'] = record.get('seriousnessdeath')
        flat['seriousness_lifethreatening'] = record.get('seriousnesslifethreatening')
        flat['seriousness_hospitalization'] = record.get('seriousnesshospitalization')
        flat['seriousness_disability'] = record.get('seriousnessdisabling')
        flat['seriousness_congenital'] = record.get('seriousnesscongenitalanomali')
        flat['seriousness_other'] = record.get('seriousnessother')
        
        # Patient fields (nested)
        patient = record.get('patient', {})
        flat['patient_age'] = patient.get('patientonsetage')
        flat['patient_age_unit'] = patient.get('patientonsetageunit')
        flat['patient_sex'] = patient.get('patientsex')
        
        # Source fields (nested)
        primary_source = record.get('primarysource', {})
        flat['reporter_country'] = primary_source.get('reportercountry')
        flat['reporter_qualification'] = primary_source.get('qualification')
        
        sender = record.get('sender', {})
        flat['sender_organization'] = sender.get('senderorganization')
        
        return flat
    
    def extract_json_files(self) -> List[Dict]:
        records = []
        json_files = sorted(self.data_dir.glob('*.json'))
        
        print(f"Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            print(f"Processing {json_file.name}...")
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    
                res = data.get('res', [])
                print(f"  Found {len(res)} records")
            
                for record in res:
                    flat_record = self.flatten_record(record)
                    records.append(flat_record)
            
            except Exception as e:
                print(f"  Error processing {json_file.name}: {e}")
        
        print(f"\nTotal records extracted: {len(records)}")
        return records
    
    def export_as_csv(self, records: List[Dict], output_file: str = "data/raw/faers_flattened.csv"):
        if not records:
            print("No records to save")
            return
        
        fields = records[0].keys()
        
        output_path = Path(output_file)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fields=fields)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"Saved {len(records)} records to {output_file}")


if __name__ == "__main__":
    extractor = FAERSExtractor()
    records = extractor.extract_json_files()
    extractor.export_as_csv(records)