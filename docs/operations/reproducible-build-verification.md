# Reproducible build verification

Tracking: #52

Titan treats build reproducibility as an evidence claim with an explicit artifact boundary. The first admitted target is the Python wheel distribution produced from an exact source commit.

## What is proved

The blocking CI job `Reproducible Titan wheel`:

1. checks out the exact PR head on pull requests, or the exact pushed SHA on `main`;
2. derives `SOURCE_DATE_EPOCH` from that commit's timestamp;
3. reads the active PEP 517 build backend requirement from `pyproject.toml`;
4. binds the build backend to the version and artifact hashes already present in authoritative `uv.lock`;
5. invokes `uv build --wheel` with `--build-constraint` and `--require-hashes`;
6. cleans local Setuptools build state;
7. waits long enough that uncontrolled wall-clock ZIP timestamps would differ;
8. performs a second clean build with the same source epoch and hash-bound backend;
9. fails unless the wheel filename, SHA-256, and bytes are identical;
10. uploads the retained wheel, generated build constraints, SHA-256, and machine-readable metadata as `titan-reproducible-wheel` evidence.

The evidence metadata records the source head, source epoch, uv version, build backend/version, build-constraint hash, wheel filename/hash/size, build count, and `byte_identical=true`.

## Build-backend ownership

Titan uses `setuptools.build_meta`. The project no longer lists the separate `wheel` package in `[build-system].requires`: modern Setuptools owns its wheel command, and retaining a redundant unconstrained build dependency would widen the reproducibility surface.

The manifest intentionally keeps `setuptools>=83` as the publishing compatibility declaration. The verification procedure narrows that requirement to the exact Setuptools version and hashes recorded in `uv.lock`. If the build backend requirement changes or the lock no longer contains one unambiguous Setuptools package with SHA-256 artifacts, the verifier fails closed and the C8 contract must be updated deliberately.

## Claim boundary

`byte_identical=true` means:

> two clean Titan wheel builds from the recorded exact source head, using the recorded `SOURCE_DATE_EPOCH`, uv release, and hash-bound build backend, produced byte-for-byte identical wheel files in the same CI platform class.

It does **not** mean:

- Docker/OCI image manifests or layer archives have identical bytes;
- Debian `apt` repository state is frozen forever;
- arbitrary operating systems, CPU architectures, Python releases, or future build backends produce the same bytes;
- external registry availability is guaranteed;
- a reproducible artifact is automatically secure, correct, signed, or release-approved.

C5 separately proves final-runtime container inventory. C4 separately audits locked Python dependencies. C7 separately provides static-analysis evidence. None of those controls are replaced by this procedure.

## Local verification

With repository `uv` 0.12.3 available and the exact source commit checked out:

```bash
python scripts/verify_reproducible_wheel.py \
  --source-head-sha "$(git rev-parse HEAD)" \
  --artifact-dir artifacts/reproducible-wheel
```

A successful run prints the machine-readable evidence and exits 0. Any backend/lock mismatch, unhashed build dependency, source-SHA mismatch, build failure, filename drift, or byte mismatch fails closed.

## Authority boundary

Build reproducibility is supply-chain evidence only. It cannot change Canon, runtime flags, Operator GO, production authority, release state, or knowledge admission.