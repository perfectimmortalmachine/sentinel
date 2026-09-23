CREATE TABLE IF NOT EXISTS adverse_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safetyreportid TEXT NOT NULL UNIQUE,
    receivedate DATE NOT NULL,
    transmissiondate DATE,
    reporttype TEXT,
    serious TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_receivedate CHECK (receivedate IS NOT NULL),
    CONSTRAINT valid_serious CHECK (serious IN ('Serious', 'Non-Serious', 'Unknown'))
);

CREATE TABLE IF NOT EXISTS seriousness_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safetyreportid TEXT NOT NULL,
    seriousness_death TEXT,
    seriousness_lifethreatening TEXT,
    seriousness_hospitalization TEXT,
    seriousness_disability TEXT,
    seriousness_congenital TEXT,
    seriousness_other TEXT,
    
    FOREIGN KEY (safetyreportid) REFERENCES adverse_events(safetyreportid)
);

CREATE TABLE IF NOT EXISTS patient_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safetyreportid TEXT NOT NULL,
    patient_age INTEGER,
    patient_age_unit TEXT,
    patient_sex TEXT,
    
    CONSTRAINT valid_age CHECK (patient_age >= 0 AND patient_age <= 150),
    CONSTRAINT valid_sex CHECK (patient_sex IN ('Male', 'Female', 'Unknown')),
    FOREIGN KEY (safetyreportid) REFERENCES adverse_events(safetyreportid)
);

CREATE TABLE IF NOT EXISTS reporter_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safetyreportid TEXT NOT NULL,
    reporter_country TEXT,
    reporter_qualification TEXT,
    sender_organization TEXT,
    
    FOREIGN KEY (safetyreportid) REFERENCES adverse_events(safetyreportid)
);

CREATE TABLE IF NOT EXISTS validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safetyreportid TEXT NOT NULL,
    validation_issue TEXT,
    severity TEXT DEFAULT 'warning',
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (safetyreportid) REFERENCES adverse_events(safetyreportid)
);

CREATE INDEX IF NOT EXISTS idx_receivedate ON adverse_events(receivedate);
CREATE INDEX IF NOT EXISTS idx_serious ON adverse_events(serious);
CREATE INDEX IF NOT EXISTS idx_patient_age ON patient_info(patient_age);