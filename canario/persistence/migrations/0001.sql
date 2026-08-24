-- ActaKit migration 0001 frozen SQL specification candidate.
-- NOTEBOOK DESIGN AUTHORITY ONLY: this is not a production migration or cutover.
-- Connection PRAGMAs are established by the bootstrap/open contract outside this script.
-- This script is intended to run inside the migration bootstrap transaction.

CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('web','api','feed','filesystem','manual','other')),
  name TEXT NOT NULL,
  active INTEGER NOT NULL CHECK (active IN (0,1)),
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE source_authority_scopes (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  scope_kind TEXT NOT NULL CHECK (scope_kind IN ('formal_record','recorded_speech','issuer_statement','reported_statement','dataset_value','visual_record','other')),
  valid_from TEXT,
  valid_to TEXT,
  note TEXT,
  created_at TEXT NOT NULL,
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to)
) STRICT;

CREATE TABLE source_locators (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  locator TEXT NOT NULL,
  locator_kind TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(source_id, locator),
  UNIQUE(id, source_id)
) STRICT;

CREATE TABLE acquisitions (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  source_locator_id TEXT,
  observed_at TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('success','partial','not_found','failed')),
  http_status INTEGER,
  adapter_key TEXT NOT NULL,
  adapter_version TEXT NOT NULL,
  error_code TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (source_locator_id, source_id)
    REFERENCES source_locators(id, source_id),
  CHECK (http_status IS NULL OR (http_status >= 100 AND http_status <= 599))
) STRICT;

CREATE TABLE archive_objects (
  id TEXT PRIMARY KEY,
  content_sha256 TEXT,
  byte_size INTEGER CHECK (byte_size IS NULL OR byte_size >= 0),
  storage_key TEXT,
  availability TEXT NOT NULL CHECK (availability IN ('available','purged')),
  created_at TEXT NOT NULL,
  purged_at TEXT,
  CHECK (
    content_sha256 IS NULL
    OR (
      length(content_sha256)=64
      AND content_sha256=lower(content_sha256)
      AND content_sha256 NOT GLOB '*[^0-9a-f]*'
    )
  ),
  CHECK (
    (availability='available' AND content_sha256 IS NOT NULL AND byte_size IS NOT NULL AND storage_key IS NOT NULL AND purged_at IS NULL)
    OR
    (availability='purged' AND storage_key IS NULL AND purged_at IS NOT NULL)
  )
) STRICT;
CREATE UNIQUE INDEX archive_objects_sha256_uq
  ON archive_objects(content_sha256)
  WHERE availability='available' AND content_sha256 IS NOT NULL;
CREATE UNIQUE INDEX archive_objects_storage_key_uq
  ON archive_objects(storage_key)
  WHERE availability='available' AND storage_key IS NOT NULL;

CREATE TABLE artifacts (
  id TEXT PRIMARY KEY,
  archive_object_id TEXT REFERENCES archive_objects(id),
  media_type TEXT,
  validation_state TEXT NOT NULL CHECK (validation_state IN ('pending','verified','quarantined','rejected')),
  availability TEXT NOT NULL CHECK (availability IN ('available','restricted','purged')),
  created_at TEXT NOT NULL,
  purged_at TEXT,
  CHECK (
    (availability IN ('available','restricted') AND archive_object_id IS NOT NULL AND purged_at IS NULL)
    OR
    (availability='purged' AND purged_at IS NOT NULL)
  )
) STRICT;

CREATE TABLE acquisition_artifacts (
  artifact_id TEXT PRIMARY KEY REFERENCES artifacts(id),
  acquisition_id TEXT NOT NULL REFERENCES acquisitions(id),
  role TEXT NOT NULL CHECK (role IN ('primary','attachment','response_body','other')),
  observed_filename TEXT,
  observed_url TEXT
) STRICT;
CREATE INDEX acquisition_artifacts_acquisition_idx ON acquisition_artifacts(acquisition_id);

CREATE TABLE process_runs (
  id TEXT PRIMARY KEY,
  process_kind TEXT NOT NULL CHECK (length(trim(process_kind)) > 0),
  implementation TEXT NOT NULL CHECK (length(trim(implementation)) > 0),
  implementation_version TEXT NOT NULL CHECK (length(trim(implementation_version)) > 0),
  execution_venue TEXT NOT NULL CHECK (length(trim(execution_venue)) > 0),
  configuration_hash TEXT,
  model_provider TEXT,
  model_name TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('success','partial','failed')),
  error_code TEXT,
  created_at TEXT NOT NULL,
  CHECK (started_at <= finished_at),
  CHECK (
    configuration_hash IS NULL
    OR (
      length(configuration_hash)=64
      AND configuration_hash=lower(configuration_hash)
      AND configuration_hash NOT GLOB '*[^0-9a-f]*'
    )
  ),
  CHECK (
    (model_provider IS NULL AND model_name IS NULL)
    OR (
      model_provider IS NOT NULL AND length(trim(model_provider)) > 0
      AND model_name IS NOT NULL AND length(trim(model_name)) > 0
    )
  ),
  CHECK (
    (outcome='success' AND error_code IS NULL)
    OR outcome='partial'
    OR (outcome='failed' AND error_code IS NOT NULL)
  )
) STRICT;

CREATE TABLE process_run_egress (
  process_run_id TEXT PRIMARY KEY REFERENCES process_runs(id),
  bytes_egressed INTEGER NOT NULL CHECK (bytes_egressed >= 0),
  policy_profile TEXT NOT NULL CHECK (length(trim(policy_profile)) > 0),
  data_control_profile TEXT NOT NULL CHECK (length(trim(data_control_profile)) > 0),
  request_template_hash TEXT,
  endpoint_profile TEXT CHECK (endpoint_profile IS NULL OR length(trim(endpoint_profile)) > 0),
  created_at TEXT NOT NULL,
  CHECK (
    request_template_hash IS NULL
    OR (
      length(request_template_hash)=64
      AND request_template_hash=lower(request_template_hash)
      AND request_template_hash NOT GLOB '*[^0-9a-f]*'
    )
  )
) STRICT;

CREATE TABLE representations (
  id TEXT PRIMARY KEY,
  artifact_id TEXT REFERENCES artifacts(id),
  archive_object_id TEXT REFERENCES archive_objects(id),
  parent_representation_id TEXT REFERENCES representations(id),
  kind TEXT NOT NULL CHECK (kind IN ('original','extracted_text','ocr_text','normalized_text','table','page_image','transcript','redacted_derivative','other')),
  media_type TEXT,
  language TEXT,
  charset TEXT,
  process_run_id TEXT REFERENCES process_runs(id),
  availability TEXT NOT NULL CHECK (availability IN ('available','restricted','purged')),
  created_at TEXT NOT NULL,
  purged_at TEXT,
  UNIQUE(id, artifact_id),
  FOREIGN KEY (parent_representation_id, artifact_id)
    REFERENCES representations(id, artifact_id),
  CHECK (
    (availability IN ('available','restricted') AND artifact_id IS NOT NULL AND purged_at IS NULL)
    OR
    (availability='purged' AND purged_at IS NOT NULL)
  ),
  CHECK (parent_representation_id IS NULL OR parent_representation_id <> id),
  CHECK (
    availability='purged'
    OR (
      kind='original'
      AND archive_object_id IS NULL
      AND parent_representation_id IS NULL
      AND process_run_id IS NULL
    )
    OR (
      kind<>'original'
      AND archive_object_id IS NOT NULL
      AND parent_representation_id IS NOT NULL
      AND process_run_id IS NOT NULL
    )
  )
) STRICT;
CREATE UNIQUE INDEX representations_one_original_per_artifact_uq
  ON representations(artifact_id) WHERE kind='original';

CREATE TABLE representation_targets (
  id TEXT PRIMARY KEY,
  representation_id TEXT NOT NULL REFERENCES representations(id),
  selector_kind TEXT,
  selector_version TEXT,
  selector_payload_json TEXT,
  state_payload_json TEXT,
  availability TEXT NOT NULL CHECK (availability IN ('available','purged')),
  created_at TEXT NOT NULL,
  purged_at TEXT,
  UNIQUE(id, representation_id),
  CHECK (
    (availability='available' AND selector_kind IS NOT NULL AND selector_version IS NOT NULL AND selector_payload_json IS NOT NULL AND purged_at IS NULL)
    OR
    (availability='purged' AND purged_at IS NOT NULL)
  )
) STRICT;

CREATE TABLE process_run_inputs (
  process_run_id TEXT NOT NULL REFERENCES process_runs(id),
  ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
  representation_id TEXT NOT NULL,
  representation_target_id TEXT NOT NULL,
  PRIMARY KEY(process_run_id, ordinal),
  UNIQUE(process_run_id, representation_target_id),
  FOREIGN KEY (representation_target_id, representation_id)
    REFERENCES representation_targets(id, representation_id)
) STRICT;

CREATE TABLE quality_evidence (
  id TEXT PRIMARY KEY,
  process_run_id TEXT NOT NULL REFERENCES process_runs(id),
  ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
  representation_id TEXT NOT NULL,
  representation_target_id TEXT NOT NULL,
  signal_key TEXT NOT NULL CHECK (length(trim(signal_key)) > 0),
  signal_version TEXT NOT NULL CHECK (length(trim(signal_version)) > 0),
  payload_json TEXT NOT NULL,
  interpretation_key TEXT CHECK (interpretation_key IS NULL OR length(trim(interpretation_key)) > 0),
  created_at TEXT NOT NULL,
  UNIQUE(process_run_id, ordinal),
  UNIQUE(process_run_id, representation_target_id, signal_key, signal_version),
  FOREIGN KEY (representation_target_id, representation_id)
    REFERENCES representation_targets(id, representation_id),
  FOREIGN KEY (process_run_id, representation_target_id)
    REFERENCES process_run_inputs(process_run_id, representation_target_id)
) STRICT;

CREATE TABLE quality_decisions (
  id TEXT PRIMARY KEY,
  process_run_id TEXT NOT NULL REFERENCES process_runs(id),
  representation_id TEXT NOT NULL,
  representation_target_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('accept','escalate','quarantine_review')),
  policy_key TEXT NOT NULL CHECK (length(trim(policy_key)) > 0),
  policy_version TEXT NOT NULL CHECK (length(trim(policy_version)) > 0),
  reason_code TEXT NOT NULL CHECK (length(trim(reason_code)) > 0),
  next_capability_key TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(process_run_id, representation_target_id),
  FOREIGN KEY (representation_target_id, representation_id)
    REFERENCES representation_targets(id, representation_id),
  FOREIGN KEY (process_run_id, representation_target_id)
    REFERENCES process_run_inputs(process_run_id, representation_target_id),
  CHECK (
    (decision='escalate' AND next_capability_key IS NOT NULL AND length(trim(next_capability_key)) > 0)
    OR (decision IN ('accept','quarantine_review') AND next_capability_key IS NULL)
  )
) STRICT;

CREATE TABLE entities (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('person','organization','place','project','legal_instrument','contract','program','other')),
  canonical_name TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE civic_documents (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE civic_document_revisions (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES civic_documents(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  supersedes_document_revision_id TEXT,
  title TEXT,
  issuer_entity_id TEXT REFERENCES entities(id),
  document_date TEXT,
  language TEXT,
  visibility TEXT NOT NULL CHECK (visibility IN ('normal','restricted')),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  created_at TEXT NOT NULL,
  UNIQUE(document_id, revision_no),
  UNIQUE(id, document_id),
  FOREIGN KEY (supersedes_document_revision_id, document_id)
    REFERENCES civic_document_revisions(id, document_id),
  CHECK (supersedes_document_revision_id IS NULL OR supersedes_document_revision_id <> id),
  CHECK ((revision_no=1 AND supersedes_document_revision_id IS NULL) OR (revision_no>1 AND supersedes_document_revision_id IS NOT NULL)),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX civic_document_revisions_one_successor_uq ON civic_document_revisions(supersedes_document_revision_id) WHERE supersedes_document_revision_id IS NOT NULL;

CREATE TABLE document_identifiers (
  id TEXT PRIMARY KEY,
  supersedes_document_identifier_id TEXT,
  document_id TEXT NOT NULL REFERENCES civic_documents(id),
  scheme TEXT NOT NULL,
  value TEXT NOT NULL,
  issuer_entity_id TEXT REFERENCES entities(id),
  representation_target_id TEXT REFERENCES representation_targets(id),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, document_id),
  FOREIGN KEY (supersedes_document_identifier_id, document_id)
    REFERENCES document_identifiers(id, document_id),
  CHECK (supersedes_document_identifier_id IS NULL OR supersedes_document_identifier_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX document_identifiers_one_successor_uq ON document_identifiers(supersedes_document_identifier_id) WHERE supersedes_document_identifier_id IS NOT NULL;
CREATE INDEX document_identifiers_lookup_idx ON document_identifiers(scheme, value);

CREATE TABLE document_classifications (
  id TEXT PRIMARY KEY,
  supersedes_document_classification_id TEXT,
  document_id TEXT NOT NULL REFERENCES civic_documents(id),
  source_supplied_type TEXT,
  source_type_label TEXT,
  normalized_type TEXT NOT NULL CHECK (normalized_type IN ('unknown','acta','agenda','convocatoria','acuerdo','resolucion','oficio','informe','dictamen','presupuesto','plan','reglamento_ordenanza','aviso_publico','correspondencia','comunicado_prensa','contrato','dataset','grabacion','otro')),
  subtype TEXT,
  profile_key TEXT,
  profile_version TEXT,
  confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
  representation_target_id TEXT REFERENCES representation_targets(id),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, document_id),
  FOREIGN KEY (supersedes_document_classification_id, document_id)
    REFERENCES document_classifications(id, document_id),
  CHECK (supersedes_document_classification_id IS NULL OR supersedes_document_classification_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX document_classifications_one_successor_uq ON document_classifications(supersedes_document_classification_id) WHERE supersedes_document_classification_id IS NOT NULL;

CREATE TABLE document_representations (
  id TEXT PRIMARY KEY,
  supersedes_document_representation_id TEXT,
  document_id TEXT NOT NULL REFERENCES civic_documents(id),
  representation_id TEXT NOT NULL REFERENCES representations(id),
  occurrence_kind TEXT NOT NULL CHECK (occurrence_kind IN ('whole','contained','attachment','other')),
  representation_target_id TEXT,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, document_id),
  FOREIGN KEY (representation_target_id, representation_id)
    REFERENCES representation_targets(id, representation_id),
  FOREIGN KEY (supersedes_document_representation_id, document_id)
    REFERENCES document_representations(id, document_id),
  CHECK (supersedes_document_representation_id IS NULL OR supersedes_document_representation_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX document_representations_one_successor_uq ON document_representations(supersedes_document_representation_id) WHERE supersedes_document_representation_id IS NOT NULL;

CREATE TABLE claims (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE claim_revisions (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES claims(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  supersedes_revision_id TEXT,
  claim_kind TEXT NOT NULL CHECK (claim_kind IN ('source_assertion','derived_inference','community_report','verification_question')),
  text TEXT NOT NULL,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  attribution_entity_id TEXT REFERENCES entities(id),
  attribution_text TEXT,
  temporal_start TEXT,
  temporal_end TEXT,
  sensitive INTEGER NOT NULL CHECK (sensitive IN (0,1)),
  quantitative INTEGER NOT NULL CHECK (quantitative IN (0,1)),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('active','rejected','retracted','restricted')),
  created_at TEXT NOT NULL,
  UNIQUE(claim_id, revision_no),
  UNIQUE(id, claim_id),
  FOREIGN KEY (supersedes_revision_id, claim_id)
    REFERENCES claim_revisions(id, claim_id),
  CHECK (supersedes_revision_id IS NULL OR supersedes_revision_id <> id),
  CHECK ((revision_no=1 AND supersedes_revision_id IS NULL) OR (revision_no>1 AND supersedes_revision_id IS NOT NULL)),
  CHECK (temporal_start IS NULL OR temporal_end IS NULL OR temporal_start <= temporal_end),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;

CREATE TABLE evidence_links (
  id TEXT PRIMARY KEY,
  supersedes_evidence_link_id TEXT,
  claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  representation_target_id TEXT NOT NULL REFERENCES representation_targets(id),
  relation TEXT NOT NULL CHECK (relation IN ('supports','challenges','contextualizes','quotes','mentions')),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, claim_revision_id),
  FOREIGN KEY (supersedes_evidence_link_id, claim_revision_id)
    REFERENCES evidence_links(id, claim_revision_id),
  CHECK (supersedes_evidence_link_id IS NULL OR supersedes_evidence_link_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX evidence_links_one_successor_uq ON evidence_links(supersedes_evidence_link_id) WHERE supersedes_evidence_link_id IS NOT NULL;

CREATE TABLE entity_mentions (
  id TEXT PRIMARY KEY,
  representation_target_id TEXT NOT NULL REFERENCES representation_targets(id),
  claim_revision_id TEXT REFERENCES claim_revisions(id),
  observed_text TEXT NOT NULL,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  created_at TEXT NOT NULL,
  UNIQUE(id, claim_revision_id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;

CREATE TABLE entity_names (
  id TEXT PRIMARY KEY,
  supersedes_entity_name_id TEXT,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  name TEXT NOT NULL,
  name_kind TEXT NOT NULL CHECK (name_kind IN ('official','alias','former','display','other')),
  representation_target_id TEXT REFERENCES representation_targets(id),
  valid_from TEXT,
  valid_to TEXT,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, entity_id),
  FOREIGN KEY (supersedes_entity_name_id, entity_id)
    REFERENCES entity_names(id, entity_id),
  CHECK (supersedes_entity_name_id IS NULL OR supersedes_entity_name_id <> id),
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX entity_names_one_successor_uq ON entity_names(supersedes_entity_name_id) WHERE supersedes_entity_name_id IS NOT NULL;

CREATE TABLE entity_identifiers (
  id TEXT PRIMARY KEY,
  supersedes_entity_identifier_id TEXT,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  scheme TEXT NOT NULL,
  value TEXT NOT NULL,
  issuer_entity_id TEXT REFERENCES entities(id),
  representation_target_id TEXT REFERENCES representation_targets(id),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, entity_id),
  FOREIGN KEY (supersedes_entity_identifier_id, entity_id)
    REFERENCES entity_identifiers(id, entity_id),
  CHECK (supersedes_entity_identifier_id IS NULL OR supersedes_entity_identifier_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX entity_identifiers_one_successor_uq ON entity_identifiers(supersedes_entity_identifier_id) WHERE supersedes_entity_identifier_id IS NOT NULL;
CREATE INDEX entity_identifiers_lookup_idx ON entity_identifiers(scheme, value);

CREATE TABLE mention_resolution_candidates (
  id TEXT PRIMARY KEY,
  mention_id TEXT NOT NULL REFERENCES entity_mentions(id),
  entity_id TEXT NOT NULL REFERENCES entities(id),
  score REAL CHECK (score IS NULL OR (score >= 0.0 AND score <= 1.0)),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  created_at TEXT NOT NULL,
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE INDEX mention_resolution_candidates_mention_idx ON mention_resolution_candidates(mention_id, created_at);

CREATE TABLE mention_resolution_revisions (
  id TEXT PRIMARY KEY,
  mention_id TEXT NOT NULL REFERENCES entity_mentions(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  resolved_entity_id TEXT REFERENCES entities(id),
  resolution_state TEXT NOT NULL CHECK (resolution_state IN ('resolved','cleared')),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  actor TEXT,
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(mention_id, revision_no),
  UNIQUE(id, mention_id, resolved_entity_id),
  CHECK (
    (resolution_state='resolved' AND resolved_entity_id IS NOT NULL)
    OR
    (resolution_state='cleared' AND resolved_entity_id IS NULL)
  ),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;

CREATE TABLE entity_reconciliations (
  id TEXT PRIMARY KEY,
  supersedes_entity_reconciliation_id TEXT REFERENCES entity_reconciliations(id),
  kind TEXT NOT NULL CHECK (kind IN ('merge','split')),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  actor TEXT,
  rationale TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  created_at TEXT NOT NULL,
  CHECK (supersedes_entity_reconciliation_id IS NULL OR supersedes_entity_reconciliation_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX entity_reconciliations_one_successor_uq ON entity_reconciliations(supersedes_entity_reconciliation_id) WHERE supersedes_entity_reconciliation_id IS NOT NULL;

CREATE TABLE entity_reconciliation_inputs (
  reconciliation_id TEXT NOT NULL REFERENCES entity_reconciliations(id),
  entity_id TEXT NOT NULL REFERENCES entities(id),
  PRIMARY KEY(reconciliation_id, entity_id)
) STRICT;

CREATE TABLE entity_reconciliation_outputs (
  reconciliation_id TEXT NOT NULL REFERENCES entity_reconciliations(id),
  entity_id TEXT NOT NULL REFERENCES entities(id),
  PRIMARY KEY(reconciliation_id, entity_id)
) STRICT;

CREATE TABLE entity_reconciliation_basis_mentions (
  reconciliation_id TEXT NOT NULL REFERENCES entity_reconciliations(id),
  mention_id TEXT NOT NULL REFERENCES entity_mentions(id),
  PRIMARY KEY(reconciliation_id, mention_id)
) STRICT;

CREATE TABLE entity_reconciliation_basis_identifiers (
  reconciliation_id TEXT NOT NULL REFERENCES entity_reconciliations(id),
  entity_identifier_id TEXT NOT NULL REFERENCES entity_identifiers(id),
  PRIMARY KEY(reconciliation_id, entity_identifier_id)
) STRICT;

CREATE TABLE claim_entity_links (
  id TEXT PRIMARY KEY,
  supersedes_claim_entity_link_id TEXT,
  claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  entity_id TEXT NOT NULL REFERENCES entities(id),
  mention_id TEXT,
  mention_resolution_revision_id TEXT,
  role TEXT,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, claim_revision_id),
  FOREIGN KEY (supersedes_claim_entity_link_id, claim_revision_id)
    REFERENCES claim_entity_links(id, claim_revision_id),
  FOREIGN KEY (mention_id, claim_revision_id)
    REFERENCES entity_mentions(id, claim_revision_id),
  FOREIGN KEY (mention_resolution_revision_id, mention_id, entity_id)
    REFERENCES mention_resolution_revisions(id, mention_id, resolved_entity_id),
  CHECK (supersedes_claim_entity_link_id IS NULL OR supersedes_claim_entity_link_id <> id),
  CHECK (
    (mention_id IS NULL AND mention_resolution_revision_id IS NULL)
    OR
    (mention_id IS NOT NULL AND mention_resolution_revision_id IS NOT NULL)
  ),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX claim_entity_links_one_successor_uq ON claim_entity_links(supersedes_claim_entity_link_id) WHERE supersedes_claim_entity_link_id IS NOT NULL;
CREATE INDEX claim_entity_links_entity_claim_idx ON claim_entity_links(entity_id, claim_revision_id);
CREATE INDEX claim_entity_links_resolution_idx ON claim_entity_links(mention_resolution_revision_id);

CREATE TABLE tags (
  id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  key TEXT NOT NULL,
  label TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(namespace, key)
) STRICT;

CREATE TABLE claim_tag_links (
  id TEXT PRIMARY KEY,
  supersedes_claim_tag_link_id TEXT,
  claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  tag_id TEXT NOT NULL REFERENCES tags(id),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(id, claim_revision_id),
  FOREIGN KEY (supersedes_claim_tag_link_id, claim_revision_id)
    REFERENCES claim_tag_links(id, claim_revision_id),
  CHECK (supersedes_claim_tag_link_id IS NULL OR supersedes_claim_tag_link_id <> id),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX claim_tag_links_one_successor_uq ON claim_tag_links(supersedes_claim_tag_link_id) WHERE supersedes_claim_tag_link_id IS NOT NULL;
CREATE INDEX claim_tag_links_tag_claim_idx ON claim_tag_links(tag_id, claim_revision_id);

CREATE TABLE claim_relations (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE claim_relation_revisions (
  id TEXT PRIMARY KEY,
  claim_relation_id TEXT NOT NULL REFERENCES claim_relations(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  supersedes_relation_revision_id TEXT,
  from_claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  to_claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  relation_type TEXT NOT NULL CHECK (relation_type IN ('updates','contradicts','corrects','responds_to','implements','supersedes','same_matter_as','other')),
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  basis_kind TEXT NOT NULL CHECK (basis_kind IN ('source_evidence','analyst_inference','mechanical_identity','other')),
  rationale TEXT,
  process_run_id TEXT REFERENCES process_runs(id),
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  created_at TEXT NOT NULL,
  UNIQUE(claim_relation_id, revision_no),
  UNIQUE(id, claim_relation_id),
  FOREIGN KEY (supersedes_relation_revision_id, claim_relation_id)
    REFERENCES claim_relation_revisions(id, claim_relation_id),
  CHECK (supersedes_relation_revision_id IS NULL OR supersedes_relation_revision_id <> id),
  CHECK ((revision_no=1 AND supersedes_relation_revision_id IS NULL) OR (revision_no>1 AND supersedes_relation_revision_id IS NOT NULL)),
  CHECK (from_claim_revision_id <> to_claim_revision_id),
  CHECK (
    relation_type NOT IN ('contradicts','same_matter_as')
    OR from_claim_revision_id < to_claim_revision_id
  ),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;

CREATE TABLE claim_relation_evidence_links (
  id TEXT PRIMARY KEY,
  claim_relation_revision_id TEXT NOT NULL REFERENCES claim_relation_revisions(id),
  representation_target_id TEXT NOT NULL REFERENCES representation_targets(id),
  basis_role TEXT NOT NULL CHECK (basis_role IN ('source_basis','context')),
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE role_assignments (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE role_assignment_revisions (
  id TEXT PRIMARY KEY,
  role_assignment_id TEXT NOT NULL REFERENCES role_assignments(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  supersedes_role_assignment_revision_id TEXT,
  subject_entity_id TEXT NOT NULL REFERENCES entities(id),
  organization_entity_id TEXT NOT NULL REFERENCES entities(id),
  role_key TEXT,
  role_label TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  origin_kind TEXT NOT NULL CHECK (origin_kind IN ('machine','rule','human')),
  basis_kind TEXT NOT NULL CHECK (basis_kind IN ('source_evidence','analyst_inference','mechanical_identity','other')),
  process_run_id TEXT REFERENCES process_runs(id),
  rationale TEXT,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('candidate','active','rejected')),
  created_at TEXT NOT NULL,
  UNIQUE(role_assignment_id, revision_no),
  UNIQUE(id, role_assignment_id),
  FOREIGN KEY (supersedes_role_assignment_revision_id, role_assignment_id)
    REFERENCES role_assignment_revisions(id, role_assignment_id),
  CHECK (supersedes_role_assignment_revision_id IS NULL OR supersedes_role_assignment_revision_id <> id),
  CHECK ((revision_no=1 AND supersedes_role_assignment_revision_id IS NULL) OR (revision_no>1 AND supersedes_role_assignment_revision_id IS NOT NULL)),
  CHECK (subject_entity_id <> organization_entity_id),
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
  CHECK (origin_kind='human' OR process_run_id IS NOT NULL)
) STRICT;

CREATE TABLE role_assignment_evidence_links (
  id TEXT PRIMARY KEY,
  role_assignment_revision_id TEXT NOT NULL REFERENCES role_assignment_revisions(id),
  representation_target_id TEXT NOT NULL REFERENCES representation_targets(id),
  basis_role TEXT NOT NULL CHECK (basis_role IN ('source_basis','context')),
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE review_actions (
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('strict','batch','supervised')),
  created_at TEXT NOT NULL,
  note TEXT
) STRICT;

CREATE TABLE claim_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  claim_revision_id TEXT NOT NULL REFERENCES claim_revisions(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE document_identifier_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  document_identifier_id TEXT NOT NULL REFERENCES document_identifiers(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE document_classification_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  document_classification_id TEXT NOT NULL REFERENCES document_classifications(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE document_representation_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  document_representation_id TEXT NOT NULL REFERENCES document_representations(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE evidence_link_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  evidence_link_id TEXT NOT NULL REFERENCES evidence_links(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE entity_name_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  entity_name_id TEXT NOT NULL REFERENCES entity_names(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE entity_identifier_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  entity_identifier_id TEXT NOT NULL REFERENCES entity_identifiers(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE claim_relation_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  claim_relation_revision_id TEXT NOT NULL REFERENCES claim_relation_revisions(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE mention_resolution_candidate_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  mention_resolution_candidate_id TEXT NOT NULL REFERENCES mention_resolution_candidates(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE claim_entity_link_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  claim_entity_link_id TEXT NOT NULL REFERENCES claim_entity_links(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE claim_tag_link_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  claim_tag_link_id TEXT NOT NULL REFERENCES claim_tag_links(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE entity_reconciliation_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  entity_reconciliation_id TEXT NOT NULL REFERENCES entity_reconciliations(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE role_assignment_reviews (
  id TEXT PRIMARY KEY,
  review_action_id TEXT REFERENCES review_actions(id),
  role_assignment_revision_id TEXT NOT NULL REFERENCES role_assignment_revisions(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_work')),
  reviewer TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
) STRICT;

CREATE TABLE purges (
  id TEXT PRIMARY KEY,
  reason_code TEXT NOT NULL,
  actor TEXT NOT NULL,
  retention_mode TEXT NOT NULL CHECK (retention_mode IN ('minimal_tombstone','no_tombstone')),
  created_at TEXT NOT NULL,
  executed_at TEXT,
  outcome TEXT NOT NULL CHECK (outcome IN ('planned','completed','partial','failed')),
  note TEXT,
  CHECK (
    (outcome='planned' AND executed_at IS NULL)
    OR
    (outcome IN ('completed','partial','failed') AND executed_at IS NOT NULL)
  )
) STRICT;

CREATE TABLE purge_targets (
  purge_id TEXT NOT NULL REFERENCES purges(id),
  record_kind TEXT NOT NULL CHECK (record_kind IN (
    'source','source_authority_scope','source_locator','acquisition','acquisition_artifact',
    'archive_object','artifact','process_run','process_run_egress','quality_evidence','quality_decision','representation','representation_target',
    'civic_document','civic_document_revision','document_identifier','document_identifier_review','document_classification','document_classification_review','document_representation','document_representation_review',
    'claim','claim_revision','evidence_link','evidence_link_review','entity_mention','entity','entity_name','entity_name_review','entity_identifier','entity_identifier_review',
    'mention_resolution_candidate','mention_resolution_revision','entity_reconciliation',
    'claim_entity_link','claim_entity_link_review','entity_reconciliation_review','tag','claim_tag_link','claim_tag_link_review','claim_relation','claim_relation_revision','claim_relation_evidence_link',
    'role_assignment','role_assignment_revision','role_assignment_evidence_link','review_action','claim_review',
    'claim_relation_review','mention_resolution_candidate_review','role_assignment_review'
  )),
  record_id TEXT NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('delete_record','scrub_payload','detach','delete_bytes')),
  planned_at TEXT NOT NULL,
  executed_at TEXT,
  outcome TEXT CHECK (outcome IS NULL OR outcome IN ('completed','failed','skipped')),
  PRIMARY KEY(purge_id, record_kind, record_id, action),
  CHECK (
    (executed_at IS NULL AND outcome IS NULL)
    OR
    (executed_at IS NOT NULL AND outcome IS NOT NULL)
  )
) STRICT;

CREATE VIRTUAL TABLE claim_fts USING fts5(
  claim_revision_id UNINDEXED,
  text
);
CREATE VIRTUAL TABLE representation_fts USING fts5(
  representation_id UNINDEXED,
  text
);
CREATE VIRTUAL TABLE document_fts USING fts5(
  document_revision_id UNINDEXED,
  title
);
INSERT INTO claim_fts(claim_fts, rank) VALUES('secure-delete', 1);
INSERT INTO representation_fts(representation_fts, rank) VALUES('secure-delete', 1);
INSERT INTO document_fts(document_fts, rank) VALUES('secure-delete', 1);

CREATE INDEX acquisitions_source_time_idx ON acquisitions(source_id, observed_at);
CREATE INDEX artifacts_archive_object_idx ON artifacts(archive_object_id);
CREATE INDEX representations_artifact_kind_idx ON representations(artifact_id, kind);
CREATE INDEX representations_parent_idx ON representations(parent_representation_id);
CREATE INDEX representation_targets_rep_kind_idx ON representation_targets(representation_id, selector_kind);
CREATE INDEX process_run_inputs_representation_idx ON process_run_inputs(representation_id, process_run_id);
CREATE INDEX process_run_inputs_target_representation_fk_idx ON process_run_inputs(representation_target_id, representation_id);
CREATE INDEX quality_evidence_target_representation_fk_idx ON quality_evidence(representation_target_id, representation_id);
CREATE INDEX quality_decisions_target_representation_fk_idx ON quality_decisions(representation_target_id, representation_id);
CREATE INDEX document_classifications_doc_time_idx ON document_classifications(document_id, created_at);
CREATE INDEX document_representations_doc_rep_idx ON document_representations(document_id, representation_id);
CREATE UNIQUE INDEX claim_revisions_one_successor_uq ON claim_revisions(supersedes_revision_id) WHERE supersedes_revision_id IS NOT NULL;
CREATE INDEX claim_revisions_lifecycle_time_idx ON claim_revisions(lifecycle, created_at);
CREATE INDEX evidence_links_claim_idx ON evidence_links(claim_revision_id);
CREATE INDEX evidence_links_target_idx ON evidence_links(representation_target_id);
CREATE INDEX entity_mentions_claim_idx ON entity_mentions(claim_revision_id);
CREATE UNIQUE INDEX claim_relation_revisions_one_successor_uq ON claim_relation_revisions(supersedes_relation_revision_id) WHERE supersedes_relation_revision_id IS NOT NULL;
CREATE INDEX claim_relation_revisions_from_idx ON claim_relation_revisions(from_claim_revision_id, relation_type);
CREATE INDEX claim_relation_revisions_to_idx ON claim_relation_revisions(to_claim_revision_id, relation_type);
CREATE INDEX claim_reviews_claim_reviewer_time_idx ON claim_reviews(claim_revision_id, reviewer, created_at DESC, id DESC);
CREATE UNIQUE INDEX role_assignment_revisions_one_successor_uq ON role_assignment_revisions(supersedes_role_assignment_revision_id) WHERE supersedes_role_assignment_revision_id IS NOT NULL;
CREATE INDEX role_assignment_revisions_subject_org_idx ON role_assignment_revisions(subject_entity_id, organization_entity_id);
CREATE INDEX role_assignment_revisions_org_role_time_idx ON role_assignment_revisions(organization_entity_id, role_key, valid_from, valid_to);

-- Reverse-dependency / foreign-key child indexes.
-- These keep FK enforcement, purge closure, restore validation and provenance walks bounded.
CREATE INDEX source_authority_scopes_source_fk_idx ON source_authority_scopes(source_id);
CREATE INDEX representations_process_run_fk_idx ON representations(process_run_id);
CREATE INDEX representations_archive_object_fk_idx ON representations(archive_object_id);
CREATE INDEX civic_document_revisions_process_run_fk_idx ON civic_document_revisions(process_run_id);
CREATE INDEX civic_document_revisions_issuer_entity_fk_idx ON civic_document_revisions(issuer_entity_id);
CREATE INDEX document_identifiers_process_run_fk_idx ON document_identifiers(process_run_id);
CREATE INDEX document_identifiers_representation_target_fk_idx ON document_identifiers(representation_target_id);
CREATE INDEX document_identifiers_issuer_entity_fk_idx ON document_identifiers(issuer_entity_id);
CREATE INDEX document_identifiers_document_fk_idx ON document_identifiers(document_id);
CREATE INDEX document_classifications_process_run_fk_idx ON document_classifications(process_run_id);
CREATE INDEX document_classifications_representation_target_fk_idx ON document_classifications(representation_target_id);
CREATE INDEX document_representations_representation_target_representation_fk_idx ON document_representations(representation_target_id, representation_id);
CREATE INDEX document_representations_process_run_fk_idx ON document_representations(process_run_id);
CREATE INDEX document_representations_representation_fk_idx ON document_representations(representation_id);
CREATE INDEX claim_revisions_attribution_entity_fk_idx ON claim_revisions(attribution_entity_id);
CREATE INDEX claim_revisions_process_run_fk_idx ON claim_revisions(process_run_id);
CREATE INDEX evidence_links_process_run_fk_idx ON evidence_links(process_run_id);
CREATE INDEX entity_mentions_process_run_fk_idx ON entity_mentions(process_run_id);
CREATE INDEX entity_mentions_representation_target_fk_idx ON entity_mentions(representation_target_id);
CREATE INDEX entity_names_process_run_fk_idx ON entity_names(process_run_id);
CREATE INDEX entity_names_representation_target_fk_idx ON entity_names(representation_target_id);
CREATE INDEX entity_names_entity_fk_idx ON entity_names(entity_id);
CREATE INDEX entity_identifiers_process_run_fk_idx ON entity_identifiers(process_run_id);
CREATE INDEX entity_identifiers_representation_target_fk_idx ON entity_identifiers(representation_target_id);
CREATE INDEX entity_identifiers_issuer_entity_fk_idx ON entity_identifiers(issuer_entity_id);
CREATE INDEX entity_identifiers_entity_fk_idx ON entity_identifiers(entity_id);
CREATE INDEX mention_resolution_candidates_process_run_fk_idx ON mention_resolution_candidates(process_run_id);
CREATE INDEX mention_resolution_candidates_entity_fk_idx ON mention_resolution_candidates(entity_id);
CREATE INDEX mention_resolution_revisions_process_run_fk_idx ON mention_resolution_revisions(process_run_id);
CREATE INDEX mention_resolution_revisions_resolved_entity_fk_idx ON mention_resolution_revisions(resolved_entity_id);
CREATE INDEX entity_reconciliations_process_run_fk_idx ON entity_reconciliations(process_run_id);
CREATE INDEX entity_reconciliation_inputs_entity_fk_idx ON entity_reconciliation_inputs(entity_id);
CREATE INDEX entity_reconciliation_outputs_entity_fk_idx ON entity_reconciliation_outputs(entity_id);
CREATE INDEX entity_reconciliation_basis_mentions_mention_fk_idx ON entity_reconciliation_basis_mentions(mention_id);
CREATE INDEX entity_reconciliation_basis_identifiers_entity_identifier_fk_idx ON entity_reconciliation_basis_identifiers(entity_identifier_id);
CREATE INDEX claim_entity_links_mention_claim_revision_fk_idx ON claim_entity_links(mention_id, claim_revision_id);
CREATE INDEX claim_entity_links_process_run_fk_idx ON claim_entity_links(process_run_id);
CREATE INDEX claim_entity_links_claim_revision_fk_idx ON claim_entity_links(claim_revision_id);
CREATE INDEX claim_tag_links_process_run_fk_idx ON claim_tag_links(process_run_id);
CREATE INDEX claim_tag_links_claim_revision_fk_idx ON claim_tag_links(claim_revision_id);
CREATE INDEX claim_relation_revisions_process_run_fk_idx ON claim_relation_revisions(process_run_id);
CREATE INDEX claim_relation_evidence_links_representation_target_fk_idx ON claim_relation_evidence_links(representation_target_id);
CREATE INDEX claim_relation_evidence_links_claim_relation_revision_fk_idx ON claim_relation_evidence_links(claim_relation_revision_id);
CREATE INDEX role_assignment_revisions_process_run_fk_idx ON role_assignment_revisions(process_run_id);
CREATE INDEX role_assignment_evidence_links_representation_target_fk_idx ON role_assignment_evidence_links(representation_target_id);
CREATE INDEX role_assignment_evidence_links_role_assignment_revision_fk_idx ON role_assignment_evidence_links(role_assignment_revision_id);
CREATE INDEX claim_reviews_review_action_fk_idx ON claim_reviews(review_action_id);
CREATE INDEX document_identifier_reviews_subject_reviewer_time_idx ON document_identifier_reviews(document_identifier_id, reviewer, created_at DESC, id DESC);
CREATE INDEX document_identifier_reviews_review_action_fk_idx ON document_identifier_reviews(review_action_id);
CREATE INDEX document_classification_reviews_subject_reviewer_time_idx ON document_classification_reviews(document_classification_id, reviewer, created_at DESC, id DESC);
CREATE INDEX document_classification_reviews_review_action_fk_idx ON document_classification_reviews(review_action_id);
CREATE INDEX document_representation_reviews_subject_reviewer_time_idx ON document_representation_reviews(document_representation_id, reviewer, created_at DESC, id DESC);
CREATE INDEX document_representation_reviews_review_action_fk_idx ON document_representation_reviews(review_action_id);
CREATE INDEX evidence_link_reviews_subject_reviewer_time_idx ON evidence_link_reviews(evidence_link_id, reviewer, created_at DESC, id DESC);
CREATE INDEX evidence_link_reviews_review_action_fk_idx ON evidence_link_reviews(review_action_id);
CREATE INDEX entity_name_reviews_subject_reviewer_time_idx ON entity_name_reviews(entity_name_id, reviewer, created_at DESC, id DESC);
CREATE INDEX entity_name_reviews_review_action_fk_idx ON entity_name_reviews(review_action_id);
CREATE INDEX entity_identifier_reviews_subject_reviewer_time_idx ON entity_identifier_reviews(entity_identifier_id, reviewer, created_at DESC, id DESC);
CREATE INDEX entity_identifier_reviews_review_action_fk_idx ON entity_identifier_reviews(review_action_id);
CREATE INDEX claim_relation_reviews_subject_reviewer_time_idx ON claim_relation_reviews(claim_relation_revision_id, reviewer, created_at DESC, id DESC);
CREATE INDEX claim_relation_reviews_review_action_fk_idx ON claim_relation_reviews(review_action_id);
CREATE INDEX mention_resolution_candidate_reviews_subject_reviewer_time_idx ON mention_resolution_candidate_reviews(mention_resolution_candidate_id, reviewer, created_at DESC, id DESC);
CREATE INDEX mention_resolution_candidate_reviews_review_action_fk_idx ON mention_resolution_candidate_reviews(review_action_id);
CREATE INDEX claim_entity_link_reviews_subject_reviewer_time_idx ON claim_entity_link_reviews(claim_entity_link_id, reviewer, created_at DESC, id DESC);
CREATE INDEX claim_entity_link_reviews_review_action_fk_idx ON claim_entity_link_reviews(review_action_id);
CREATE INDEX claim_tag_link_reviews_subject_reviewer_time_idx ON claim_tag_link_reviews(claim_tag_link_id, reviewer, created_at DESC, id DESC);
CREATE INDEX claim_tag_link_reviews_review_action_fk_idx ON claim_tag_link_reviews(review_action_id);
CREATE INDEX entity_reconciliation_reviews_subject_reviewer_time_idx ON entity_reconciliation_reviews(entity_reconciliation_id, reviewer, created_at DESC, id DESC);
CREATE INDEX entity_reconciliation_reviews_review_action_fk_idx ON entity_reconciliation_reviews(review_action_id);
CREATE INDEX role_assignment_reviews_subject_reviewer_time_idx ON role_assignment_reviews(role_assignment_revision_id, reviewer, created_at DESC, id DESC);
CREATE INDEX role_assignment_reviews_review_action_fk_idx ON role_assignment_reviews(review_action_id);

-- Query-surface indexes not implied by foreign keys.
CREATE INDEX civic_document_revisions_date_idx ON civic_document_revisions(document_date, document_id);
CREATE INDEX document_classifications_type_lifecycle_idx ON document_classifications(normalized_type, lifecycle, document_id, created_at);
CREATE INDEX entity_names_name_lifecycle_idx ON entity_names(name, lifecycle, entity_id);
CREATE INDEX purge_targets_record_idx ON purge_targets(record_kind, record_id, purge_id);

-- File identity/schema markers are the final writes of migration 0001.
PRAGMA application_id = 1095453012; -- 0x414B4954 = ASCII "AKIT"
PRAGMA user_version = 1;
