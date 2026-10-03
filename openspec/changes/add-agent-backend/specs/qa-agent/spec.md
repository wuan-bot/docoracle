## ADDED Requirements

### Requirement: Agent retrieval parity

When acting as the answer backend, the agent MUST honor the same retrieval
inputs as the engine:

- the default retrieval mode MUST come from `retrieval.mode` in configuration,
  and an explicit per-request mode MUST override it;
- the number of requested chunks MUST default to `retrieval.top_k`;
- `module`, `component`, and `version` filters MUST be applied to retrieval
  deterministically, not merely suggested to the model;
- `rrf_k` and `prefetch_k` MUST be applied to the searcher as the engine does;
- an invalid retrieval mode MUST be rejected with an error naming the valid
  modes (`hybrid`, `semantic`, `bm25`).

#### Scenario: Configured default mode is honored
- **WHEN** `retrieval.mode` is `bm25` and a request does not specify a mode
- **THEN** the agent retrieves using BM25 and reports `bm25` as the mode used

#### Scenario: Explicit mode overrides the configured default
- **WHEN** `retrieval.mode` is `hybrid` and a request specifies `semantic`
- **THEN** the agent retrieves using semantic search and reports `semantic`

#### Scenario: Filters constrain retrieval
- **WHEN** a request supplies `module=module-api` and the model calls the
  retrieval tool
- **THEN** every chunk returned by the tool matches `module-api`

#### Scenario: Chunk count defaults to configured top_k
- **WHEN** a request omits `k` and `retrieval.top_k` is 8
- **THEN** retrieval requests at most 8 chunks

#### Scenario: Invalid mode is rejected
- **WHEN** a request specifies an unsupported retrieval mode
- **THEN** the agent rejects the request with an error naming the valid modes

### Requirement: Agent native structured output

The agent SHALL produce its answer as a provider-validated `AnswerResponse` using
pydantic-ai's structured output, without recovering fields by parsing JSON out of
free-form text.

#### Scenario: Answer is validated
- **WHEN** the agent completes a run
- **THEN** the result is a validated `AnswerResponse` instance

### Requirement: Agent detailed result shape

The agent SHALL produce a detailed result with the same fields as the engine,
including `question`, `answer`, `confidence`, `citations`, `reasoning`,
`sources`, `chunk_details` (with per-chunk provenance), `retrieved_count`, and
`retrieval_mode`. Duplicate chunks MUST be reported once.

#### Scenario: Detailed result matches the engine shape
- **WHEN** the agent answers a question
- **THEN** the result contains the same field set the engine returns

#### Scenario: Provenance is reported
- **WHEN** retrieved chunks are reported in `chunk_details`
- **THEN** each entry carries the retrievers and ranks that produced it

#### Scenario: Duplicate chunks are collapsed
- **WHEN** the same chunk is returned by more than one retrieval call
- **THEN** it appears once in `sources`, `chunk_details`, and `retrieved_count`

### Requirement: Agent chunk search parity

The agent backend SHALL provide chunk search equivalent to the engine's
`get_related_chunks` so the CLI `search` command and the HTTP `/search` endpoint
behave identically regardless of the selected backend.

#### Scenario: Search returns scored chunks
- **WHEN** the agent backend is selected and a search is performed
- **THEN** the result is an ordered list of scored chunks with provenance

#### Scenario: Search respects the configured mode
- **WHEN** the agent backend is selected, a search is performed, and no mode is
  supplied
- **THEN** the search uses `retrieval.mode` from configuration
