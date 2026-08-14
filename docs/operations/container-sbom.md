# Final runtime container SBOM

Tracking: #52

Titan generates an SPDX Software Bill of Materials for the **final Docker runtime stage** as bounded supply-chain evidence.

## Decision

The existing Docker workflow remains the runtime-behavior owner. It builds a local image and performs import, non-root, health, console, deployment-profile, filesystem allowlist, secret-canary, wheel-packaging and compose-default checks.

C5 extends that workflow with BuildKit SBOM generation without introducing registry credentials or an image publication lifecycle.

Hosted-runner evidence showed that the default Docker driver rejects attestations, and that an attested manifest produced by the `docker-container` driver cannot be loaded through the classic Docker exporter. Titan therefore uses two bounded solves over the same checked-out Dockerfile, immutable base reference, build arguments and `uv.lock`:

1. `docker build --no-cache` produces `velantrim-titan:ci` for all existing runtime-hardening checks;
2. a `docker-container` Buildx builder runs `docker buildx build --no-cache --sbom=true --output type=local,...` without `--load`, producing the final-stage root filesystem plus `sbom.spdx.json` evidence.

No image is pushed merely to retain an attestation. The local-export SPDX file is the authoritative C5 artifact.

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
- the source head SHA and the separately runtime-tested local image ID;
- explicit `sbom_exporter=buildkit-local` and `sbom_scope=final-runtime-stage` metadata.

## Scope boundary

This is the inventory for Titan's **final runtime stage**, not the discarded builder stage. Build dependencies that do not survive into the runtime stage are intentionally outside this artifact.

The runtime-tested Docker image and the SBOM solve are separate exports because of the hosted runner's classic Docker image-store limitation. C5 therefore proves that both are derived from the same repository inputs and final-stage contract; it does not falsely claim that the classic local image store retained an attached attestation.

The SBOM is inventory evidence, not vulnerability evidence. C4 separately audits the Python lock graph against OSV. C5 does **not** add OS-package vulnerability scanning, registry publication, signing, deployment authority, or Operator GO.

## Registry boundary

Titan does not push an image merely to preserve an attestation. Image-attached attestations can be admitted later only alongside an explicit release/registry lifecycle; until then, the local-export SPDX evidence is the bounded supply-chain truth.
