PRAGMA application_id=1346978865;
PRAGMA user_version=1;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
PRAGMA locking_mode=EXCLUSIVE;
PRAGMA foreign_keys=ON;
PRAGMA trusted_schema=OFF;
PRAGMA secure_delete=ON;
CREATE TABLE artifacts(
  content_digest TEXT PRIMARY KEY NOT NULL,
  byte_length INTEGER NOT NULL CHECK(byte_length>=0),
  bytes BLOB NOT NULL CHECK(length(bytes)=byte_length)
) STRICT;
CREATE TABLE records(
  store_revision INTEGER PRIMARY KEY NOT NULL CHECK(store_revision>0),
  record_digest TEXT NOT NULL UNIQUE,
  prior_store_head_digest TEXT,
  commit_request_digest TEXT NOT NULL UNIQUE,
  recovery_identity_jcs BLOB NOT NULL UNIQUE,
  artifact_digest TEXT NOT NULL UNIQUE REFERENCES artifacts(content_digest),
  record_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TABLE heads(
  store_revision INTEGER PRIMARY KEY NOT NULL REFERENCES records(store_revision),
  head_digest TEXT NOT NULL UNIQUE,
  record_digest TEXT NOT NULL UNIQUE REFERENCES records(record_digest),
  prior_store_head_digest TEXT,
  terminal_sealed INTEGER NOT NULL CHECK(terminal_sealed IN (0,1)),
  head_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TRIGGER artifacts_no_update BEFORE UPDATE ON artifacts BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER artifacts_no_delete BEFORE DELETE ON artifacts BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER heads_no_update BEFORE UPDATE ON heads BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER heads_no_delete BEFORE DELETE ON heads BEGIN SELECT RAISE(ABORT,'immutable'); END;
