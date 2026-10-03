## 1. Dependencies and shared abstractions

- [x] 1.1 Add `PyStemmer` to the runtime dependencies in `pyproject.toml` and refresh the lockfile
- [x] 1.2 Create `src/core/search_index.py` with the `SearchIndex` Protocol, the `ScoredChunk` dataclass, and a module-level `matches_filters(chunk, filters)` function lifted from the current `_matches_filters``

## 2. Index implementations

- [x] 2.1 Create `src/core/semantic_index.py` by extracting the FAISS logic from `src/core/vectorstore.py`; the new class satisfies `SearchIndex`, owns only `index.faiss`, and does NOT store the chunks list
- [x] 2.2 Create `src/core/bm25_index.py` with: a German tokenizer (lowercase → `\w+` split → stopword filter → `min_token_length` filter → Snowball stem via `PyStemmer`), a `rank_bm25.BM25Okapi` instance, and `SearchIndex` methods that read/write `bm25.pkl`
- [x] 2.3 Create `src/core/hybrid_searcher.py` that owns the canonical `chunks` list, delegates `add_chunks` to both indices, runs both searches in `search()`, fuses results via RRF, applies `matches_filters` to the fused list, and reads/writes `chunks.pkl`

## 3. Q&A engine integration

- [x] 3.1 Refactor `src/core/qa_engine.py`: replace the `VectorStore` parameter with a `HybridSearcher`, read `retrieval.mode` from config, and route the `search` call through the hybrid searcher (or bypass to one path when mode is `semantic` or `bm25`)
- [x] 3.2 Add provenance to `QAEngine.ask`'s return value: each entry in `chunk_details` gains a `sources` field (`{"semantic": rank, "bm25": rank}`), and the LLM context-building path excludes provenance from the prompt string

## 4. CLI and HTTP surface

- [x] 4.1 Update `src/cli.py`: add a `--retrieval` (`hybrid|semantic|bm25`) flag to both the `ask` and `search` commands, plumb the value into `QAEngine`, validate the value, and surface the new provenance info under `--show-context`
- [x] 4.2 Update `src/server/main.py`: add `retrieval: Optional[str]` to `AskRequest` and `SearchRequest`, default from config, validate the value, and pass it through to `QAEngine.ask`; add the lazy-loaded `HybridSearcher` to the module-level state replacing the `VectorStore` references
- [x] 4.3 Extend `GET /info` to report sizes of both indices (`semantic_chunks`, `bm25_chunks`, `chunks`) and the active retrieval mode

## 5. Configuration

- [x] 5.1 Add the `retrieval:` block to `config.yaml` documenting `mode`, `rrf_k`, `prefetch_k`, and BM25 settings (`k1`, `b`, `stemming`, `stopwords`, `min_token_length`) with their default values
- [x] 5.2 Verify the `QAEngine` and `HybridSearcher` pick up these values (no hard-coded constants leak through)

## 6. Cleanup and documentation

- [x] 6.1 Delete `src/core/vectorstore.py` and remove any remaining imports of it across the codebase
- [x] 6.2 Update `README.md` to document the hybrid retrieval model, the `--retrieval` flag, the new `retrieval` API field, the new on-disk layout (`chunks.pkl`, `index.faiss`, `bm25.pkl`), and the breaking-change note that re-ingest is required

## 7. Tests

- [x] 7.1 Add tests for the German tokenizer: identical stemming for inflected forms, stopword removal, `min_token_length` enforcement, and `stemming=none` skipping
- [x] 7.2 Add tests for RRF scoring: chunk in both lists, chunk in one list, custom `rrf_k` value
- [x] 7.3 Add tests for `matches_filters` parity: filters exclude chunks from both paths; multiple filters combine with AND
- [x] 7.4 Add a fixture-corpus test for `HybridSearcher.search` that verifies the top result against an expected ordering for a small hand-built set of German/English chunks
- [x] 7.5 Add an on-disk round-trip test: build a `HybridSearcher` with chunks, save, reconstruct, and confirm identical search results
- [x] 7.6 Add CLI tests for `--retrieval` flag values (hybrid, semantic, bm25, invalid)
- [x] 7.7 Add a test confirming the LLM prompt excludes provenance fields (only `[Source N]` markers and chunk text appear)

## 8. Verification

- [x] 8.1 Run the full test suite (`pytest`) and confirm all new and existing tests pass
- [x] 8.2 Run linter (`ruff check src/ tests/`) and formatter (`black --check src/ tests/`) with no errors
- [x] 8.3 Manually exercise end-to-end: clear `data/vectorstore/`, run `qa ingest`, run `qa ask "..."` with each retrieval mode, run `qa search "..."`, and exercise the `/ask` and `/search` HTTP endpoints
