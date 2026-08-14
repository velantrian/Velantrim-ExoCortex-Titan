# Final runtime container SBOM

Tracking: #52

Titan generates an SPDX Software Bill of Materials for the **final Docker runtime stage** as bounded supply-chain evidence.

## Decision

The existing Docker workflow remains the runtime-behavior owner. It builds a local image and performs import, non-root, health, console, deployment-profile, filesystem allowlist, secret-canary, wheel-packaging and compose-default checks.

C5 extends that same build evidence with BuildKit SBOM generation instead of introducing registry credentials or a separate image publication lifecycle.

A single `docker buildx build` solve uses multiple exporters:

- `--load` keeps the image available as `velantrim-titan:ci` for the existing runtime-hardening checks;
- `--sbom=true` asks BuildKit to generate an SPDX SBOM;
- `--output type=local,dest=container-sbom-out` writes the final root filesystem and the local-export attestation file `sbom.spdx.json` to the runner.

The workflow copies only the SBOM evidence into `artifacts/` and removes the exported root filesystem before continuing the existing runtime checks.

## Fail-closed validation

`scripts/validate_container_sbom.py` accepts either direct SPDX JSON or the in-toto SPDX predicate wrapper produced by BuildKit exporters. It requires:

1. a valid `SPDX-*` document version;
2. a non-empty package inventory;
3. at least one Debian/OS package identity using a `pkg:deb/...` purl;
4. at least one Python package identity using a `pkg:pypi/...` purl.

This prevents a superficially valid but empty, OS-only, or Python-only artifact from satisfying the C5 contract.

The artifact `titan-container-sbom` contains:

- `titan-container.spdx.json`;
- its SHA-256 checksum;
- a compact validation summary;
- Buildx/Docker tool version evidence;
- Dockerfile and `uv.lock` SHA-256 bindings;
- the source head SHA and loaded image ID.

## Scope boundary

This is the inventory for Titan's **final runtime image**, not the discarded builder stage. Build dependencies that do not survive into the runtime image are intentionally outside this artifact.

The SBOM is inventory evidence, not vulnerability evidence. C4 separately audits the Python lock graph against OSV. C5 does **not** add OS-package vulnerability scanning, registry publication, signing, deployment authority, or Operator GO.

## Registry boundary

Titan does not push an image merely to preserve an attestation. The current workflow is a local verification workflow. The local-export evidence file is the authoritative C5 artifact; image-attached attestations can be admitted later only alongside an explicit release/registry lifecycle.
