-- SQLite schema for MFT analysis database

-- Main MFT records table
CREATE TABLE IF NOT EXISTS mft_records (
    record_number INTEGER PRIMARY KEY,
    sequence_number INTEGER,
    flags INTEGER,
    used_size INTEGER,
    allocated_size INTEGER,
    base_record_number INTEGER,
    next_attribute_id INTEGER,
    filepath TEXT,
    filename TEXT,
    parent_record_number INTEGER,
    parent_sequence_number INTEGER,
    
    -- Standard Information timestamps
    si_creation_time TEXT,
    si_modification_time TEXT,
    si_access_time TEXT,
    si_entry_time TEXT,
    
    -- File Name timestamps
    fn_creation_time TEXT,
    fn_modification_time TEXT,
    fn_access_time TEXT,
    fn_entry_time TEXT,
    
    -- File attributes and sizes
    file_attributes INTEGER,
    allocated_file_size INTEGER,
    real_file_size INTEGER,
    
    -- Object ID information
    object_id TEXT,
    birth_volume_id TEXT,
    birth_object_id TEXT,
    birth_domain_id TEXT,
    
    -- Hash information (if computed)
    md5_hash TEXT,
    sha256_hash TEXT,
    sha512_hash TEXT,
    crc32_hash TEXT,
    
    -- Metadata
    is_active BOOLEAN,
    is_directory BOOLEAN,
    is_deleted BOOLEAN,
    has_ads BOOLEAN DEFAULT FALSE,
    
    -- Analysis timestamp
    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Attributes table for detailed attribute information
CREATE TABLE IF NOT EXISTS mft_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_number INTEGER,
    attribute_type INTEGER,
    attribute_name TEXT,
    attribute_size INTEGER,
    resident BOOLEAN,
    data_size INTEGER,
    content_preview TEXT,
    FOREIGN KEY (record_number) REFERENCES mft_records(record_number),
    FOREIGN KEY (attribute_type) REFERENCES attribute_types(id)
);

-- Alternate Data Streams table
CREATE TABLE IF NOT EXISTS alternate_data_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_number INTEGER,
    stream_name TEXT,
    stream_size INTEGER,
    md5_hash TEXT,
    sha256_hash TEXT,
    FOREIGN KEY (record_number) REFERENCES mft_records(record_number)
);

-- Security descriptors table
CREATE TABLE IF NOT EXISTS security_descriptors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_number INTEGER,
    security_id INTEGER,
    owner_sid TEXT,
    group_sid TEXT,
    dacl TEXT,
    sacl TEXT,
    FOREIGN KEY (record_number) REFERENCES mft_records(record_number)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_mft_records_filepath ON mft_records(filepath);
CREATE INDEX IF NOT EXISTS idx_mft_records_filename ON mft_records(filename);
CREATE INDEX IF NOT EXISTS idx_mft_records_parent ON mft_records(parent_record_number);
CREATE INDEX IF NOT EXISTS idx_mft_records_flags ON mft_records(flags);
CREATE INDEX IF NOT EXISTS idx_mft_records_creation_time ON mft_records(si_creation_time);
CREATE INDEX IF NOT EXISTS idx_mft_records_modification_time ON mft_records(si_modification_time);
CREATE INDEX IF NOT EXISTS idx_mft_attributes_record_type ON mft_attributes(record_number, attribute_type);

-- Views for common queries
CREATE VIEW IF NOT EXISTS active_files AS
SELECT * FROM mft_records 
WHERE is_active = 1 AND is_directory = 0;

CREATE VIEW IF NOT EXISTS active_directories AS
SELECT * FROM mft_records 
WHERE is_active = 1 AND is_directory = 1;

CREATE VIEW IF NOT EXISTS deleted_files AS
SELECT * FROM mft_records 
WHERE is_deleted = 1;

CREATE VIEW IF NOT EXISTS timeline_view AS
SELECT 
    record_number,
    filepath,
    'SI_Creation' as event_type,
    si_creation_time as timestamp
FROM mft_records WHERE si_creation_time IS NOT NULL
UNION ALL
SELECT 
    record_number,
    filepath,
    'SI_Modification' as event_type,
    si_modification_time as timestamp
FROM mft_records WHERE si_modification_time IS NOT NULL
UNION ALL
SELECT 
    record_number,
    filepath,
    'SI_Access' as event_type,
    si_access_time as timestamp
FROM mft_records WHERE si_access_time IS NOT NULL
UNION ALL
SELECT 
    record_number,
    filepath,
    'FN_Creation' as event_type,
    fn_creation_time as timestamp
FROM mft_records WHERE fn_creation_time IS NOT NULL
ORDER BY timestamp;