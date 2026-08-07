# 📚 Portable KB Graph Governance

**Status:** ACTIVE CONTRACT  
**Artifact:** `kb_graph.json`  
**Preservation policy:** `KEEP_VERSIONED_KNOWLEDGE_ASSET`

## Purpose

`kb_graph.json` is a portable knowledge asset of Velantrim Titan. It is not treated as
an accidental build residue and must not be deleted merely because it is large.
The asset preserves a local-first graph representation that can be inspected,
validated, distributed in a release bundle and rebuilt from accepted source material.

This contract does **not** declare every claim true. Artifact integrity, provenance,
epistemic validation and runtime authority are separate questions.

```text
valid JSON
  ≠ referentially valid graph
  ≠ reproducible source build
  ≠ trustworthy claim
  ≠ admitted Canon fact
  ≠ runtime authority
```

## Existing owners

| Responsibility | Existing owner |
|---|---|
| Parse accepted source corpus | `core/world_skills_ingest.py` |
| Deterministic graph construction | `core/knowledge_linker.py` |
| Build SQLite graph and portable export | `scripts/build_kb_graph.py` |
| Export portable JSON | `scripts/export_kb_graph.py` |
| Audit SQLite graph quality | `scripts/audit_kb_graph.py` |
| Verify release sizes and SHA-256 | `scripts/verify_release_bundle.py` |
| Validate portable JSON graph integrity | `scripts/validate_kb_graph.py` |

The portable validator extends the existing release and SQLite audit mechanisms. It is
not a second knowledge store, graph builder, truth gate or promotion owner.

## Required invariants

The portable artifact must satisfy:

1. root object contains `meta`, `nodes` and `edges`;
2. node IDs are non-empty and unique;
3. every edge endpoint references an existing node;
4. self-edges and duplicate `(source, target, relation)` edges fail validation;
5. `meta.total_nodes` and `meta.total_edges` match the arrays;
6. the full artifact can be hashed with SHA-256;
7. integrity validation grants `ARTIFACT_INTEGRITY_ONLY`, never Canon or runtime authority;
8. updates preserve provenance and are produced through an explicit build/export path;
9. a change that removes knowledge units or relations must include a semantic diff and rationale;
10. destructive history rewriting requires an independent decision and backup proof.

## Validation

Validate the committed or unpacked portable graph:

```bash
python scripts/validate_kb_graph.py kb_graph.json
```

Machine-readable report:

```bash
python scripts/validate_kb_graph.py kb_graph.json --json
```

For the SQLite graph and bilingual source corpus, run the existing deeper audit:

```bash
python scripts/audit_kb_graph.py \
  --db data/velantrim_kb_clean_20260710_graph.db \
  --json data/kb_graph_audit.json
```

For an extracted production bundle, also run:

```bash
python scripts/verify_release_bundle.py /path/to/extracted/bundle
```

## Change classification

| Change | Required evidence |
|---|---|
| Metadata-only documentation | docs review; no KB regeneration claim |
| Validator or manifest logic | focused tests + full CI |
| Graph generator change | deterministic rebuild + before/after quality report |
| Source corpus change | source provenance + bilingual checks + semantic graph diff |
| Node/edge deletion | explicit rationale, affected IDs, rollback artifact and review |
| Runtime consumption change | separate architecture/authority review and activation evidence |

## Semantic diff minimum

A regenerated graph should report at least:

- previous and new SHA-256;
- nodes added, removed and changed;
- edges added and removed by relation type and edge basis;
- dangling, self and duplicate edge counts;
- isolated/connected node counts;
- source-corpus or generator revision;
- known provenance or licensing changes.

## Current boundary

The graph remains a preserved, inspectable knowledge asset. This document and validator
add governance and integrity checks only. They do not alter `kb_graph.json`, do not
change its claims or relations, do not wire it into a new runtime path and do not grant
write, answer, action, policy, TruthGate or Canon authority.
