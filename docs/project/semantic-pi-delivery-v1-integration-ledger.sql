PRAGMA application_id=1346980913;
PRAGMA user_version=1;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
PRAGMA locking_mode=EXCLUSIVE;
PRAGMA foreign_keys=ON;
PRAGMA trusted_schema=OFF;
PRAGMA secure_delete=ON;
CREATE TABLE records(
  store_revision INTEGER PRIMARY KEY NOT NULL CHECK(store_revision>0),
  decision_id INTEGER NOT NULL CHECK(decision_id>0),
  sequence INTEGER NOT NULL CHECK(sequence>=0),
  state TEXT NOT NULL CHECK(state IN ('available','claimed','controller_registered','supervisor_registered','supervised','reserved','authorized','consumed','failed','cancelled')),
  authorization_envelope_digest TEXT NOT NULL,
  record_digest TEXT NOT NULL UNIQUE,
  prior_record_digest TEXT,
  prior_store_head_digest TEXT,
  record_jcs BLOB NOT NULL UNIQUE,
  UNIQUE(decision_id,sequence)
) STRICT;
CREATE UNIQUE INDEX one_decision_anchor ON records(decision_id) WHERE sequence=0;
CREATE TABLE heads(
  store_revision INTEGER PRIMARY KEY NOT NULL REFERENCES records(store_revision),
  head_digest TEXT NOT NULL UNIQUE,
  record_digest TEXT NOT NULL UNIQUE REFERENCES records(record_digest),
  prior_store_head_digest TEXT,
  head_jcs BLOB NOT NULL UNIQUE
) STRICT;
CREATE TRIGGER records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER heads_no_update BEFORE UPDATE ON heads BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER heads_no_delete BEFORE DELETE ON heads BEGIN SELECT RAISE(ABORT,'immutable'); END;
