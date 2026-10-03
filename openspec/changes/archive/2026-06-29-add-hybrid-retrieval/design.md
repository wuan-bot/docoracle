## Context

The current retrieval pipeline is a single class (`VectorStore`) wrapping FAISS, holding both the embeddings index and the chunk list, with a metadata filter helper. Retrieval runs once per query and feeds the LLM context directly. There is no lexical path.

The codebase is small and Pythonic — flat module layout under `src/core/`, dataclasses, no DI container, no abstract base classes. Existing dependencies are `faiss-cpu`, `numpy`, `tiktoken` (for BPE chunk sizing), `requests`, `click`, `fastapi`. Documentation sources are German-language AsciiDoc files processed through Antora.

The project is maintained by a single team; docs are re-ingested regularly. Backward compatibility with existing on-disk stores is not required.

## Goals / Non-Goals

**Goals:**

- Hybrid retrieval (semantic + BM25) as the default for both `qa ask` and the `/ask` HTTP endpoint
- Reciprocal Rank Fusion as the fusion algorithm — minimal score-compatibility friction, no need to normalize heterogeneous distance/score distributions
- A small, narrow `SearchIndex` Protocol so both `SemanticIndex` and `BM25Index` are interchangeable projections over the same chunk corpus
- BM25 tokenization tuned for German (lowercase → word-split → stopword filter → Snowball stem via `PyStemmer`)
- Retrieval provenance surfaced in results: each chunk in the final list carries which retriever(s) found it and its per-retriever rank
- Config-driven retrieval: `mode`, `rrf_k`, `prefetch_k`, and BM25 hyperparameters (`k1`, `b`, `stemming`, `stopwords`, `min_token_length`) live in `config.yaml`
- On-disk layout matches the new structure: `index.faiss` (semantic vectors), `chunks.pkl` (canonical chunks), `bm25.pkl` (tokenized corpus + BM25 parameters)

**Non-Goals:**

- Cross-encoder reranking (would add model + latency; not needed for v1)
- Weighted fusion with per-retriever weight tuning exposed to users (RRF defaults work; weighting can be added later without breaking changes)
- Multi-language stemming beyond German (the corpus is German-only; English/other languages can be added as a config option later)
- A backward-compatible loader for the old `metadata.pkl` format (re-ingest is acceptable)
- Distributed deployment, sharded indices, or query-side caching

## Decisions

### 1. SearchIndex Protocol with `add` / `search` / `save` / `load` contract

**Decision:** Introduce a small `SearchIndex` Protocol in `src/core/search_index.py` defining the four methods both indices implement. Use `typing.Protocol` (not ABC) to keep things duck-typed with a clear type contract.

**Rationale:** Two implementers (semantic + BM25) is the minimum where a Protocol pays off. It documents the contract, lets mypy catch drift, and makes adding a third path trivial. ABC would be heavier ceremony for no real benefit at this scale.

**Alternatives considered:**

- *Duck typing only, no Protocol*: works, but loses the contract clarity. Skipped because the cost is one small file.
- *Abstract Base Class*: forces inheritance; the user code composes rather than inherits. Skipped — Protocol is the modern Python idiom here.
- *Single concrete `HybridIndex` class with internal switches*: collapses two genuinely different retrieval mechanisms into one class. Skipped — defeats the refactor.

### 2. HybridSearcher owns the canonical chunks list

**Decision:** The chunk list (`List[Chunk]` + `chunk_dict`) lives on `HybridSearcher`. Each index receives a read-only view of the chunks (or its own copy of just IDs) at construction. On `add_chunks`, the chunks are passed to each index for indexing, and the canonical list is updated on the searcher.

**Rationale:** Single source of truth. Avoids the doubled-storage problem of two indices each holding their own chunks list. Filters operate on the canonical chunk; indices return their own IDs and the searcher looks up the full chunk for results.

**Alternatives considered:**

- *Each index owns its chunks*: matches the current `VectorStore` pattern but doubles storage and risks drift if chunks are added differently to each. Skipped.
- *External `ChunkCorpus` object*: adds a fourth class for one piece of state. Skipped — `HybridSearcher` is the natural owner.

### 3. `rank_bm25` over `bm25s` / `Whoosh` / `Tantivy`

**Decision:** Use `rank_bm25` for BM25 scoring; serialize the tokenized corpus and BM25 object via `pickle` into `bm25.pkl`.

**Rationale:** Corpus size is small to medium (hundreds to low thousands of chunks for an Antora project). `rank_bm25` is pure Python, the de-facto Python BM25 implementation, and serializes trivially. We control tokenization explicitly, which matters for German stemming.

**Alternatives considered:**

- *`bm25s`*: Numba-backed, faster on large corpora, has its own `.npz` persistence. Premature optimization at this scale. Skipped.
- *Whoosh*: real full-text search engine, but heavier concepts (analyzers, schemas) and richer than we need. Skipped.
- *Tantivy*: Rust-backed, very fast, but Python bindings add complexity and a system-level feel that doesn't match the codebase. Skipped.

### 4. Reciprocal Rank Fusion with `k=60` as the damping constant

**Decision:** Fuse via RRF: `rrf_score(d) = Σ_i 1/(k + rank_i(d))` with `k=60` (Cormack et al. 2009 default). Each retriever returns up to `prefetch_k` results (default `4 × top_k`); the fused list is sorted descending by `rrf_score` and the top `top_k` are returned.

**Rationale:** RRF requires no score normalization — BM25 scores are unbounded positive, FAISS L2 distances are positive, and their scales are incompatible. RRF uses ranks only, so the two can be combined without calibration. `k=60` is the literature default and rarely needs tuning; it dampens the influence of rank-1 vs. rank-2 disagreements.

**Alternatives considered:**

- *Weighted linear fusion* (`α·norm(semantic) + (1-α)·norm(bm25)`): requires per-corpus calibration of `α` and per-retriever score normalization. More tunable but harder to use well. Skipped for v1; can be added as a second strategy later.
- *Cross-encoder reranking*: highest accuracy but adds a model dependency and per-query latency. Skipped — out of scope for v1.

### 5. German stemming via `PyStemmer` (Snowball)

**Decision:** Tokenize BM25 input as: lowercase → `re.findall(r'\w+', text)` → drop stopwords → Snowball stem with `PyStemmer` (`Stemmer('german')`). Stopword list is a small inline set of ~200 common German words (plus a few English ones since some docs use English terms).

**Rationale:** German is heavily inflected; without stemming, queries for "konfigurieren" miss chunks written "Konfiguration" or "konfiguriert". Snowball is the standard lightweight German stemmer, ships in `PyStemmer` (a thin wrapper around the C Snowball library), and adds negligible runtime cost.

**Alternatives considered:**

- *No stemming*: works for English, weak for German given the corpus. Skipped.
- *spaCy pipeline with German model*: full lemmatization is more accurate but adds a large dependency and startup cost. Skipped — Snowball is the right weight.
- *nltk + Snowball data*: similar capability but `nltk` requires a one-time data download. `PyStemmer` ships the algorithms in the wheel. Skipped.

### 6. `ScoredChunk` carries provenance

**Decision:** Replace the current `(chunk, distance)` tuple return type with a `ScoredChunk` dataclass:

```python
@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float  # RRF score for the final result
    sources: Dict[str, int]  # {"semantic": rank, "bm25": rank} (subset possible)
```

For paths that return intermediate (non-fused) results — e.g., the `--retrieval=bm25` CLI flag — `sources` contains a single entry.

**Rationale:** Provenance is the only way to debug retrieval quality. A user (or developer) looking at a result list and seeing `sources: {"bm25": 1, "semantic": 14}` immediately understands *why* this chunk surfaced. Without it, hybrid retrieval is a black box.

**Alternatives considered:**

- *No provenance, just the chunk and score*: simpler, but loses debuggability. Skipped.
- *Provenance only in a separate debug log*: hidden from primary results. Skipped — provenance is cheap to include and useful.

### 7. Filter logic extracted to `search_index.py`

**Decision:** Move `_matches_filters` from `VectorStore` to a module-level function in `search_index.py`. Both indices and `HybridSearcher` call it on results before returning them.

**Rationale:** The current filter implementation in `VectorStore` works against the `Chunk` dataclass and is not specific to FAISS. Lifting it out removes duplication risk when BM25Index needs to apply the same filters.

### 8. Disk layout: `chunks.pkl` + `index.faiss` + `bm25.pkl`

**Decision:** Store three files in `./data/vectorstore/`:
- `index.faiss` — FAISS index, owned by `SemanticIndex`
- `chunks.pkl` — `List[Chunk]`, owned by `HybridSearcher`
- `bm25.pkl` — `{"tokenized_corpus": [...], "doc_freqs": ..., "params": {...}}`, owned by `BM25Index`

**Rationale:** Clear ownership. Each file is read by exactly one class. Renaming `metadata.pkl` → `chunks.pkl` reflects that the file now holds the canonical chunk list, not arbitrary metadata.

**Alternatives considered:**

- *Keep `metadata.pkl` and add `bm25.pkl`*: smaller diff but misleading filename once chunks are the canonical store. Skipped.
- *Single pickle file containing all three*: harder to load independently (e.g., FAISS alone for a sanity check). Skipped.

### 9. CLI/API parameter: `retrieval: "hybrid" | "semantic" | "bm25"`

**Decision:** Add a `--retrieval` CLI flag with these three values, and a `retrieval` field on the `AskRequest` and `SearchRequest` API models. Default value is `hybrid` (from config). RRF-specific knob (`--rrf-k`) and BM25-specific knobs live in `config.yaml` only for v1 — not surfaced as CLI flags to avoid surface-area sprawl.

**Rationale:** Three modes cover the design space. Defaults via config keep the CLI clean. Tuning the BM25 / RRF hyperparameters is a power-user activity that doesn't need a CLI flag for v1.

### 10. Delete `vectorstore.py` outright

**Decision:** Remove `vectorstore.py` rather than keep it as a compatibility shim. All imports are updated to point at `HybridSearcher` / `SemanticIndex` / `BM25Index`.

**Rationale:** User confirmed re-ingest is acceptable. A shim adds maintenance burden for no real benefit since there's no external consumer. Clean cut.

## Risks / Trade-offs

- **Behavior shift for existing users** → Mitigation: release notes document that hybrid is the new default and answers may shift toward more source-grounded responses on technical queries; provenance is exposed so users can inspect which path produced each chunk.
- **BM25 tokenization is a hidden knob** → Mitigation: tokenizer parameters are config-driven (`stemming`, `stopwords`, `min_token_length`); defaults are sensible for German but exposed for tuning.
- **`PyStemmer` adds a C-extension dependency** → Mitigation: it's a small, widely-used library; the wheel includes the Snowball algorithms directly with no data download required.
- **Re-ingest required for existing installs** → Mitigation: documented as a breaking change; users re-ingest on doc-source updates anyway, so this aligns with their normal cadence.
- **Hybrid search latency ≈ max(semantic_latency, bm25_latency)** → Mitigation: at this corpus scale (low thousands of chunks), both paths are sub-millisecond; the dominant cost remains embedding generation on the query, which is unchanged.
- **RRF with `k=60` may overweight low-information rank-1 hits** → Mitigation: `k=60` is the literature default and empirically robust; configurable via `retrieval.rrf_k` if a corpus needs different damping.
- **Provenance noise in API responses** → Mitigation: included in `chunk_details` (the human-facing field), not in the LLM context; the LLM still sees clean `[Source N]` markers.

## Migration Plan

This is a clean refactor with no required migration path for existing data — `metadata.pkl` is simply not loaded. The migration steps for a developer applying the change:

1. Add `PyStemmer` to `pyproject.toml` runtime dependencies; run `uv lock` / `pip install`.
2. Delete `src/core/vectorstore.py`.
3. Create the four new files (`search_index.py`, `semantic_index.py`, `bm25_index.py`, `hybrid_searcher.py`).
4. Update `src/core/qa_engine.py` to take a `HybridSearcher` instead of a `VectorStore`.
5. Update `src/cli.py` and `src/server/main.py` to instantiate `HybridSearcher`, add the `--retrieval` flag and API field, and update `/info`.
6. Add the `retrieval:` block to `config.yaml`.
7. Add tests for the new pieces and update any existing tests that referenced `VectorStore`.
8. For an existing local install: `rm -rf data/vectorstore/*` and re-run `qa ingest`. The new layout will be created on first ingest.

Rollback: revert the changes and re-ingest with the old code. No data migration is needed in either direction since the on-disk format is the contract.

## Open Questions

None remaining. All decisions above were surfaced and resolved during exploration.
