-- Contrato inicial de dados. Nao e um executor nem uma trava financeira pronta.
-- Valores monetarios: nanodolares inteiros (1 USD = 1_000_000_000).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiments (
  experiment_id TEXT PRIMARY KEY,
  protocol_version TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  primary_metric TEXT NOT NULL,
  decision_rule_json TEXT NOT NULL,
  preregistered_at_utc TEXT,
  seed INTEGER NOT NULL,
  budget_cap_nusd INTEGER NOT NULL CHECK(budget_cap_nusd >= 0),
  status TEXT NOT NULL CHECK(status IN ('planned','preregistered','running','paused','completed','blocked')),
  amendments_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  dataset_version TEXT NOT NULL,
  task TEXT NOT NULL,
  group_id TEXT NOT NULL,
  split TEXT NOT NULL CHECK(split IN ('pilot','development','calibration','test','diagnostic')),
  origin TEXT NOT NULL,
  source_url TEXT,
  source_date TEXT,
  language TEXT NOT NULL,
  input_sha256 TEXT NOT NULL,
  input_artifact_path TEXT NOT NULL,
  provenance_json TEXT NOT NULL,
  ambiguous INTEGER NOT NULL DEFAULT 0 CHECK(ambiguous IN (0,1))
);
CREATE INDEX IF NOT EXISTS cases_group ON cases(dataset_version, group_id, split);

CREATE TABLE IF NOT EXISTS annotations (
  annotation_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  annotator_id TEXT NOT NULL,
  annotator_kind TEXT NOT NULL CHECK(annotator_kind IN ('human','model','deterministic_verifier')),
  rubric_version TEXT NOT NULL,
  label_json TEXT NOT NULL,
  evidence TEXT NOT NULL,
  blinded_to_predictions INTEGER NOT NULL CHECK(blinded_to_predictions IN (0,1)),
  elapsed_seconds REAL CHECK(elapsed_seconds >= 0),
  adjudication_of_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS arms (
  arm_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  system_id TEXT NOT NULL,
  repo_sha TEXT,
  provider TEXT NOT NULL,
  endpoint TEXT,
  model_requested TEXT,
  config_sha256 TEXT NOT NULL,
  rubric_version TEXT NOT NULL,
  conditions_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
  attempt_id TEXT PRIMARY KEY,
  arm_id TEXT NOT NULL REFERENCES arms(arm_id),
  parent_attempt_id TEXT REFERENCES attempts(attempt_id),
  block_id TEXT NOT NULL,
  provider_request_id TEXT,
  model_resolved TEXT,
  host_id TEXT NOT NULL,
  batch_group_id TEXT,
  transport_group_id TEXT,
  execution_order INTEGER NOT NULL,
  evidence_level TEXT NOT NULL CHECK(evidence_level IN ('offline','cached_replay','live_component','mock_integration','live_e2e')),
  payload_sha256 TEXT NOT NULL,
  request_path TEXT NOT NULL,
  response_path TEXT,
  started_at_utc TEXT,
  ended_at_utc TEXT,
  latency_ms REAL CHECK(latency_ms >= 0),
  status TEXT NOT NULL CHECK(status IN ('reserved','sent','success','timeout','http_error','invalid_response','cancelled_before_send')),
  error_json TEXT,
  raw_usage_json TEXT,
  input_tokens INTEGER CHECK(input_tokens >= 0),
  output_tokens INTEGER CHECK(output_tokens >= 0),
  known_cost_nusd INTEGER CHECK(known_cost_nusd >= 0),
  price_snapshot_id TEXT NOT NULL,
  cache_key TEXT,
  runtime_manifest_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempt_cases (
  attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  position INTEGER NOT NULL,
  PRIMARY KEY(attempt_id,case_id)
);

CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  question_id TEXT NOT NULL,
  question_sha256 TEXT NOT NULL,
  options_order_json TEXT NOT NULL,
  predicted_json TEXT,
  probabilities_json TEXT,
  confidence REAL,
  gold_annotation_id TEXT REFERENCES annotations(annotation_id),
  correct INTEGER CHECK(correct IN (0,1)),
  valid INTEGER NOT NULL CHECK(valid IN (0,1)),
  severity TEXT,
  error_family TEXT,
  UNIQUE(attempt_id,case_id,question_id)
);

CREATE TABLE IF NOT EXISTS task_outcomes (
  outcome_id TEXT PRIMARY KEY,
  arm_id TEXT NOT NULL REFERENCES arms(arm_id),
  case_id TEXT NOT NULL REFERENCES cases(case_id),
  verifier_version TEXT NOT NULL,
  success INTEGER CHECK(success IN (0,1)),
  elapsed_ms REAL CHECK(elapsed_ms >= 0),
  human_minutes REAL CHECK(human_minutes >= 0),
  steps INTEGER CHECK(steps >= 0),
  evidence_path TEXT NOT NULL,
  outcome_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS budget_events (
  event_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
  attempt_id TEXT REFERENCES attempts(attempt_id),
  created_at_utc TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN ('authorize','reserve','settle','release','reconcile','historical_commitment')),
  amount_nusd INTEGER NOT NULL CHECK(amount_nusd >= 0),
  evidence_json TEXT NOT NULL,
  parent_event_id TEXT REFERENCES budget_events(event_id)
);

CREATE TABLE IF NOT EXISTS provider_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  captured_at_utc TEXT NOT NULL,
  usage_nusd INTEGER,
  key_limit_nusd INTEGER,
  sanitized_json TEXT NOT NULL,
  sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(experiment_id),
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  kind TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  provenance_json TEXT NOT NULL
);
