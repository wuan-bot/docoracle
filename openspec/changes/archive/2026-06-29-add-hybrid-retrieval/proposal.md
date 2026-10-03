## Why

The system currently retrieves documentation chunks using only semantic similarity over embeddings (FAISS). This works well for natural-language questions but consistently underperforms on technical retrieval: exact error codes, configuration keys, identifiers, paths, and German inflected word forms are often diluted or missed entirely by embedding similarity. A lexical BM25 index over the same chunks complements this failure mode — exact-term matches surface that semantic search was burying. A small refactor makes this composable: extract the retrieval layer into a `HybridSearcher` that combines semantic + BM25 via Reciprocal Rank Fusion (RRF), with BM25 using German stemming to handle the project's German-language documentation.

## What Changes

- Add a `BM25Index` that performs lexical search over the canonical chunks list using `rank_bm25`, with a Snowball German stemmer and stopword filtering
- Extract the FAISS-based retrieval into a `SemanticIndex` that follows the same interface
- Introduce a `SearchIndex` Protocol and a `HybridSearcher` that composes both indices and fuses their rankings via RRF
- Move chunk storage out of `VectorStore`; chunks become a single source of truth owned by the `HybridSearcher`
- Replace `qa_engine.py`'s direct use of `VectorStore` with `HybridSearcher`; hybrid becomes the default retrieval mode (semantic and bm25 remain selectable)
- Add a `--retrieval` flag (`hybrid` | `semantic` | `bm25`) to the `ask` and `search` CLI commands; expose the same field on the `/ask` and `/search` API requests; expose `--rrf-k` and the BM25 hyperparameters in config
- Add a `retrieval` block to `config.yaml` documenting `mode`, `rrf_k`, `prefetch_k`, and BM25-specific settings (`k1`, `b`, `stemming`, `stopwords`, `min_token_length`)
- Include retrieval provenance in results: each chunk records which retriever(s) found it and its per-retriever rank, surfaced in the response and CLI `--show-context` output
- Persist the BM25 index alongside FAISS; on-disk layout changes from `index.faiss` + `metadata.pkl` to `index.faiss` + `chunks.pkl` + `bm25.pkl`
- **BREAKING**: `VectorStore` is removed; existing users must re-ingest (acceptable because documentation sources update regularly); on-disk `metadata.pkl` is no longer loadable

## Capabilities

### New Capabilities

- `hybrid-retrieval`: The retrieval subsystem — composable semantic and BM25 indices, RRF fusion, metadata filtering, and provenance tracking across both paths.

### Modified Capabilities

<!-- No existing specs; first run. -->

## Impact

- **Code**: `src/core/vectorstore.py` deleted. New files: `src/core/search_index.py`, `src/core/semantic_index.py`, `src/core/bm25_index.py`, `src/core/hybrid_searcher.py`. Modifications: `src/core/qa_engine.py`, `src/cli.py`, `src/server/main.py`.
- **API**: `POST /ask` and `POST /search` gain a `retrieval` field (defaults to `hybrid`). `GET /info` reports both index sizes. Existing request fields remain backward-compatible.
- **Dependencies**: Add `PyStemmer` to `pyproject.toml` runtime dependencies for Snowball German stemming.
- **Disk**: `./data/vectorstore/` gains `bm25.pkl`; `metadata.pkl` is renamed to `chunks.pkl`. **BREAKING** for existing installations — re-ingest required.
- **Behavior**: Because hybrid is now the default, answers retrieved via existing CLI/API calls will shift. Expected direction: more source-grounded for technical queries (identifiers, error codes, German inflected forms), similar or marginally better for natural-language queries. This is a user-visible change and should be called out in release notes.
- **Tests**: Add tests for BM25 tokenization (with/without stemming), RRF scoring math, metadata filtering parity across both indices, hybrid result correctness on a small fixture corpus, and on-disk round-trip persistence.
