PRAGMA application_id=1347571761;
PRAGMA user_version=1;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
PRAGMA locking_mode=EXCLUSIVE;
PRAGMA foreign_keys=ON;
PRAGMA trusted_schema=OFF;
PRAGMA secure_delete=ON;
CREATE TABLE authorizations(
  production_launch_authorization_digest TEXT PRIMARY KEY NOT NULL,
  launch_nonce TEXT NOT NULL UNIQUE,
  process_start_nonce TEXT NOT NULL UNIQUE,
  reservation_request_digest TEXT NOT NULL UNIQUE,
  authorization_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TABLE records(
  store_revision INTEGER PRIMARY KEY NOT NULL CHECK(store_revision>0),
  production_launch_authorization_digest TEXT NOT NULL REFERENCES authorizations(production_launch_authorization_digest),
  state TEXT NOT NULL CHECK(state IN ('reserved','finalizer_registered','controller_registered','supervisor_registered','host_registered','witnessed','completed','failed')),
  record_digest TEXT NOT NULL UNIQUE,
  prior_record_digest TEXT,
  append_request_digest TEXT UNIQUE,
  record_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TABLE histories(
  store_revision INTEGER PRIMARY KEY NOT NULL REFERENCES records(store_revision),
  head_digest TEXT NOT NULL UNIQUE,
  prior_head_digest TEXT,
  record_digest TEXT NOT NULL UNIQUE REFERENCES records(record_digest),
  history_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TABLE exchanges(
  request_kind TEXT NOT NULL CHECK(request_kind IN ('reservation','append')),
  request_digest TEXT PRIMARY KEY NOT NULL,
  request_jcs BLOB NOT NULL UNIQUE,
  response_digest TEXT NOT NULL UNIQUE,
  response_jcs BLOB NOT NULL UNIQUE,
  receipt_jcs BLOB,
  result_record_digest TEXT NOT NULL REFERENCES records(record_digest),
  result_history_digest TEXT NOT NULL REFERENCES histories(head_digest),
  UNIQUE(request_kind,request_digest)
) STRICT;
CREATE TRIGGER authorizations_no_update BEFORE UPDATE ON authorizations BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER authorizations_no_delete BEFORE DELETE ON authorizations BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER histories_no_update BEFORE UPDATE ON histories BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER histories_no_delete BEFORE DELETE ON histories BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER exchanges_no_update BEFORE UPDATE ON exchanges BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER exchanges_no_delete BEFORE DELETE ON exchanges BEGIN SELECT RAISE(ABORT,'immutable'); END;
