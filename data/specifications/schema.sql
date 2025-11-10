-- Schema for PyPoE specification database
-- Stores .dat file specifications in a structured format

-- Files table: stores information about each .dat file
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    version TEXT NOT NULL,  -- 'stable', 'beta', 'alpha'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(filename, version)
);

-- Fields table: stores field specifications for each file
CREATE TABLE IF NOT EXISTS fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'ref|string', 'int', 'bool', etc.
    key_field TEXT,  -- Name of referenced .dat file (e.g., 'Mods.dat')
    key_id TEXT,  -- Column name in referenced file
    key_offset INTEGER DEFAULT 0,
    enum_name TEXT,  -- Enum from PyPoE.poe.constants
    is_unique BOOLEAN DEFAULT 0,
    file_path BOOLEAN DEFAULT 0,
    file_ext TEXT,
    display TEXT,
    display_type TEXT,
    description TEXT,
    field_order INTEGER NOT NULL,  -- Preserve order of fields
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Virtual fields table: stores virtual field specifications
CREATE TABLE IF NOT EXISTS virtual_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    fields TEXT NOT NULL,  -- JSON array of field names ['Field1', 'Field2']
    zip BOOLEAN DEFAULT 0,
    description TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
CREATE INDEX IF NOT EXISTS idx_files_version ON files(version);
CREATE INDEX IF NOT EXISTS idx_fields_file_id ON fields(file_id);
CREATE INDEX IF NOT EXISTS idx_fields_name ON fields(file_id, name);
CREATE INDEX IF NOT EXISTS idx_virtual_fields_file_id ON virtual_fields(file_id);

