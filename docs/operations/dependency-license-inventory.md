# Dependency license inventory

Titan's own code is MIT. That does not relicense optional packages, model weights,
fonts, datasets or externally installed tools.

`uv.lock` and the deterministic CycloneDX SBOM identify the locked package universe.
The CI `installed-dependency-licenses` artifact additionally records actual installed
name/version, License-Expression, declared License and license classifiers. Missing
metadata is explicit. Generate it for an exact environment with:

```bash
python scripts/dependency_licenses.py --output artifacts/installed-licenses.json
```

This inventory is evidence, not a certification of legal compatibility. It covers the
selected installed extras, not every manually installed parser or remote model. Retain
required notices and verify redistribution/service terms for the actual deployment.

PyMuPDF (`fitz`) is an optional auto-detected PDF fallback; it is not an MIT component
and is not included by the current locked parser extras. Its AGPL/commercial terms need
an explicit deployment decision if installed or redistributed. Marker/MinerU and model
weights also require their own license review; availability is not a license grant.
The current MinerU/Vision adapters are unfinished and must not be described as active
Reader capabilities. No confirmed license violation was established by the audit.

Deployment records should include the wheel/image digest, selected extras, additional
packages/resources, inventory and any required commercial license. Do not infer license
compatibility from a green vulnerability audit or from an absent SBOM license field.
