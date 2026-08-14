# Deterministic Python dependency SBOM

Tracking: #52

Titan generates a deterministic CycloneDX 1.6 inventory from the repository's authoritative `uv.lock` and `pyproject.toml`.

## Scope

The artifact is intentionally a **lock-universe SBOM** for Python packages represented by `uv.lock`.

It proves:

- package names and exact locked versions are inventoried;
- PyPI-backed components receive Package URLs;
- available distribution hashes from `uv.lock` are retained as component properties;
- the document is cryptographically bound to both `uv.lock` and `pyproject.toml` SHA-256 values;
- identical inputs generate byte-for-byte identical JSON;
- CI publishes the generated JSON together with its SHA-256 checksum.

It does **not** prove:

- absence of known vulnerabilities;
- OS/base-image package inventory;
- the exact dependency subset installed for one optional-extra profile;
- runtime/production authority;
- Canon or truth admission.

Those are separate concerns and, where applicable, separate #52 residuals.

## Generate locally

```bash
python scripts/generate_sbom.py --output artifacts/titan-uv-lock.cdx.json
sha256sum artifacts/titan-uv-lock.cdx.json
```

The generator uses only Python 3.11+ standard-library modules and performs no network access.

## CI evidence

The `Deterministic lock SBOM` CI job generates the SBOM twice from the exact checked-out head and requires `cmp` equality before uploading:

- `titan-uv-lock.cdx.json`
- `titan-uv-lock.cdx.json.sha256`

This artifact is evidence about the locked Python dependency universe only; it must not be described as a full container or production SBOM.
