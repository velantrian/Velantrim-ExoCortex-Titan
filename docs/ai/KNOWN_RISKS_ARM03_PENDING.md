# ARM-03 pending risks

This branch is not merged. Current risks under validation:

- regex/rule extraction remains heuristic;
- safe serialization must prove synthetic PII/credentials absent;
- memory-injection patterns are bounded and cannot claim complete detection;
- supersession hints are within-input proposals only;
- no admission or persistence may be inferred from candidate extraction;
- full CI, benchmark and replay evidence are pending.

The final accepted risk entry will be folded into `docs/ai/KNOWN_RISKS.md` before merge.
