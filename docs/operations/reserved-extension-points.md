# Reserved extension points and placeholder capabilities

Absence of an in-tree caller is not proof that an exported API has no external users.
The audit therefore distinguishes confirmed private dead work from compatibility APIs.

- `core.output_faithfulness.GCRResult`: retained public result type; no in-tree consumer
  was found. It is not a running semantic-support verifier.
- `HybridRetriever.retrieve_diverse`: retained optional public ranking API. It changes
  result diversity, not canonical confidence or fact admission.
- `core.contradiction_registry._set_nli_scorer`: retained injection hook for external/test
  compatibility. It does not by itself activate NLI or confer evidence authority.
- `PDFParser._parse_mineru`: explicitly unimplemented and excluded from capability
  availability; rejects before reading PDF bytes. Package installation alone is not an
  implemented adapter.
- `ImageParser._parse_vision_llm`: reserved unimplemented adapter. A requested Vision
  path reports `vision_llm_not_implemented` and retains the OCR fallback.
- `_parse_openai_sse_chunk` and `_check_prometheus`: confirmed unused private helpers
  removed by audit fixes; the actual streaming parser and metrics implementation remain.

GraphStoreBackend provides the shared read-only spreading-activation algorithm. Memory,
SQLite and Cypher backends supply their existing neighbors; edge/node storage semantics
are unchanged by extracting the three identical algorithm copies.

Large canonical write/orchestration methods still require staged decomposition with
transaction/receipt boundaries intact. This cleanup does not claim to complete that work
or silently remove public compatibility surfaces.
