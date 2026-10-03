## ADDED Requirements

### Requirement: Deterministic retrieve-then-answer pipeline

The engine SHALL retrieve chunks once and generate one answer from them, honoring
the configured retrieval mode, `top_k`, `rrf_k`, and `prefetch_k`, and applying
`module`/`component`/`version` filters to retrieval. An explicit per-request mode
MUST override the configured default, and an invalid mode MUST be rejected with
an error naming the valid modes (`hybrid`, `semantic`, `bm25`).

#### Scenario: Configured defaults are used
- **WHEN** a request omits mode and `k`
- **THEN** retrieval uses `retrieval.mode` and returns at most `retrieval.top_k`
  chunks

#### Scenario: Explicit mode overrides the default
- **WHEN** `retrieval.mode` is `hybrid` and a request specifies `bm25`
- **THEN** retrieval uses BM25 and the result reports `bm25`

#### Scenario: Invalid mode is rejected
- **WHEN** a request specifies an unsupported retrieval mode
- **THEN** the engine raises an error naming `hybrid`, `semantic`, and `bm25`

#### Scenario: Filters constrain retrieval
- **WHEN** a request supplies `module=module-api`
- **THEN** every retrieved chunk matches `module-api`

### Requirement: Native structured output

The engine SHALL obtain its structured answer through the model provider's native
structured-output mechanism, validating the response against `AnswerResponse`.
The engine MUST NOT recover structured fields by parsing JSON out of free-form
text or by any regex/heuristic extraction.

#### Scenario: Answer is validated natively
- **WHEN** the model returns a structured response
- **THEN** the engine surface the validated `AnswerResponse` fields without
  text-based JSON extraction

#### Scenario: Non-conforming output fails loudly
- **WHEN** the model does not return a schema-conforming response
- **THEN** generation raises rather than fabricating an answer from raw text

### Requirement: Structured fields are surfaced

The engine's detailed result SHALL include the model's `confidence` (when
provided), `citations`, and `reasoning` alongside the answer text.

#### Scenario: Optional fields pass through
- **WHEN** the model returns confidence, citations, and reasoning
- **THEN** the detailed result contains those values

#### Scenario: Optional fields may be absent
- **WHEN** the model omits confidence or reasoning
- **THEN** the detailed result reports them as absent without failing

### Requirement: Detailed result shape

The engine SHALL produce a detailed result containing `question`, `answer`,
`confidence`, `citations`, `reasoning`, `sources`, `chunk_details` (with
per-chunk provenance), `retrieved_count`, and `retrieval_mode`. Duplicate chunks
MUST be reported once.

#### Scenario: Result field set
- **WHEN** the engine answers a question
- **THEN** the result contains every field listed above

#### Scenario: Provenance is reported
- **WHEN** retrieved chunks are reported in `chunk_details`
- **THEN** each entry carries the retrievers and ranks that produced it

### Requirement: Engine chunk search

The engine SHALL expose chunk search equivalent to `get_related_chunks`, using
the default retrieval mode and returning scored chunks with provenance.

#### Scenario: Search returns scored chunks
- **WHEN** a search is performed through the engine
- **THEN** the result is an ordered list of scored chunks with provenance
