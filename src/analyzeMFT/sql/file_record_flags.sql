CREATE TABLE file_record_flags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

INSERT INTO file_record_flags (id, name) VALUES
(1, 'FILE_RECORD_IN_USE'),
(2, 'FILE_RECORD_IS_DIRECTORY'),
(4, 'FILE_RECORD_IS_EXTENSION'),
(8, 'FILE_RECORD_HAS_SPECIAL_INDEX');