PRAGMA foreign_keys=ON;
CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  publisher TEXT NOT NULL,
  canonical_uri TEXT,
  retrieved_at TEXT NOT NULL,
  issued_at TEXT,
  effective_from TEXT,
  effective_until_excl TEXT,
  jurisdiction TEXT,
  language TEXT NOT NULL,
  document_version TEXT,
  sha256_original TEXT NOT NULL,
  license TEXT NOT NULL,
  redistribution_allowed INTEGER NOT NULL CHECK(redistribution_allowed IN (0,1)),
  source_type TEXT NOT NULL,
  authority_rank INTEGER,
  legal_status TEXT,          -- active, superseded, repealed, historical, n/a
  snapshot_path TEXT,
  notes TEXT
);

CREATE TABLE chunks (
  rowid INTEGER PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  parent_section_id TEXT,
  title TEXT,
  section TEXT,
  article TEXT,
  locator TEXT NOT NULL,
  canonical_text TEXT NOT NULL,
  search_text TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  character_start INTEGER,
  character_end INTEGER,
  effective_from TEXT,
  effective_until_excl TEXT,
  dense_row INTEGER UNIQUE NOT NULL,
  FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
  title,
  section,
  article,
  search_text,
  content='chunks',
  content_rowid='rowid',
  tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE relations (
  from_chunk_id TEXT NOT NULL,
  to_chunk_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  provenance TEXT NOT NULL,   -- explicit-reference, structure, curated
  confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
  PRIMARY KEY(from_chunk_id, to_chunk_id, relation_type)
);

CREATE TABLE aliases (
  alias TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  target_type TEXT NOT NULL CHECK(target_type IN ('source','chunk')),
  target_id TEXT NOT NULL,
  alias_type TEXT NOT NULL,   -- article-id, law-number, error-code, acronym, synonym
  PRIMARY KEY(normalized_alias, target_type, target_id)
);

CREATE INDEX aliases_norm_idx ON aliases(normalized_alias);

CREATE TABLE derived_texts (
  chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id),
  purpose TEXT NOT NULL CHECK(purpose IN ('generator')),
  language TEXT NOT NULL,
  text TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  derivation_method TEXT NOT NULL,  -- official_translation, human_reviewed_translation, machine_draft
  derivation_source TEXT,
  reviewer_id TEXT,
  reviewed_at TEXT,
  PRIMARY KEY(chunk_id, purpose, language)
);
