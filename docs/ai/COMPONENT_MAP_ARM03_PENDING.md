# ARM-03 component route (pending validation)

- Feature flag owner: `core/feature_config.py`
- Compatibility flag readout: `core/runtime_flags.py`
- Proposal-only extractor: `core/selective_memory_candidates.py`
- Focused contracts: `tests/test_selective_memory_candidates.py`
- Speed boundary: `tests/test_selective_memory_speed_contract.py`
- Benchmark: `benchmarks/bench_selective_memory_candidates.py`
- Replay fixture: `tests/fixtures/evaluation_replay/selective_memory_candidates.json`
- Blocking focused workflow: `.github/workflows/arm03-contracts.yml`
- Detailed contract: `docs/SELECTIVE_MEMORY_SPEED_AND_SAFETY.md`

Authority boundary: no storage, Canon, TruthGate, WriteGate, model, network, response, or
action authority.
