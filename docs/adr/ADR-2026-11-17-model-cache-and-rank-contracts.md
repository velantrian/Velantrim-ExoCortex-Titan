# Model cache lifetime and retrieval rank contracts

Status: draft fixes stacked on PR #523; no deployment activation.

A dense retriever's failure must not change another instance's availability. Model
construction is serialized in the existing class cache; vector-cache locking remains
unchanged. This prevents duplicate expensive loads without holding a vector-cache lock
through encoding or introducing new execution authority.

RRF depends only on ranked positions; unused score normalization is removed. Without
graph expansion, five-stage final_score equals its existing retrieval score. When graph
neighbors exist, they enter an explicit RRF channel and receive a real ranking score.
This changes ranking eligibility, never epistemic confidence or canonical state.

Gemini cachedContents handles are process-local hints, keyed by full system/model and
credential namespace. Retain at most 128 LRU entries and expire locally after 3540 seconds,
below the requested provider TTL of 3600 seconds. A cached generation receiving 404
invalidates the handle and retries once without it, retaining the complete approved
system prompt. Version fallback remains bounded by the existing two API versions.
Failures with another status are not blindly retried as expired caches. Expired/evicted
provider resources still expire at the provider TTL; no deletion authority is added.

No public Reader size limit, credential routing change, extra Canon writer, confidence
boost or provider activation is introduced. Concurrent cache creation can still create
more than one provider resource; TTL bounds resource lifetime, while provider quotas and
single-flight creation are separate operational work. The local map remains bounded.

Tests use fake models/provider responses and deterministic ranks. No real provider call
is evidence for this PR. Remote full-model CI remains required.
