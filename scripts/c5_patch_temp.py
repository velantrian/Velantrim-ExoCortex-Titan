from __future__ import annotations

from pathlib import Path


workflow_path = Path(".github/workflows/docker.yml")
text = workflow_path.read_text(encoding="utf-8")

watch = '      - "scripts/export_locked_runtime_requirements.py"\n'
replacement = (
    watch
    + '      - "scripts/validate_container_sbom.py"\n'
    + '      - "tests/test_container_sbom.py"\n'
    + '      - "docs/operations/container-sbom.md"\n'
)
if text.count(watch) != 2:
    raise SystemExit(f"expected two Docker path-filter anchors, found {text.count(watch)}")
text = text.replace(watch, replacement)

start_marker = "      - name: Build image (no cache)\n"
end_marker = "\n      - name: Import smoke test\n"
if text.count(start_marker) != 1:
    raise SystemExit(f"expected one Docker build start marker, found {text.count(start_marker)}")
if text.count(end_marker) != 1:
    raise SystemExit(f"expected one Docker build end marker, found {text.count(end_marker)}")
start = text.index(start_marker)
end = text.index(end_marker, start)
new = '''      - name: Build image + final runtime SBOM (single BuildKit solve)
        run: |
          set -euo pipefail
          rm -rf container-sbom-out artifacts
          mkdir -p artifacts
          docker buildx version | tee artifacts/docker-buildx-version.txt
          docker version --format '{{.Client.Version}}' > artifacts/docker-client-version.txt
          docker buildx build --no-cache \\
            --sbom=true \\
            --build-arg RUNTIME_EXTRAS=server \\
            --output type=local,dest=container-sbom-out \\
            --load \\
            -t velantrim-titan:ci .
          test -s container-sbom-out/sbom.spdx.json
          cp container-sbom-out/sbom.spdx.json artifacts/titan-container.spdx.json
          sha256sum artifacts/titan-container.spdx.json > artifacts/titan-container.spdx.json.sha256
          source_head_sha="$(python -c 'import json, os; event=json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8")); print(event.get("pull_request", {}).get("head", {}).get("sha") or os.environ["GITHUB_SHA"])')"
          {
            echo "source_head_sha=${source_head_sha}"
            echo "image_id=$(docker image inspect velantrim-titan:ci --format '{{.Id}}')"
            echo "dockerfile_sha256=$(sha256sum Dockerfile | awk '{print $1}')"
            echo "uv_lock_sha256=$(sha256sum uv.lock | awk '{print $1}')"
          } > artifacts/titan-container-sbom.metadata.txt
          rm -rf container-sbom-out

      - name: Validate final runtime container SBOM
        run: |
          python scripts/validate_container_sbom.py \\
            --input artifacts/titan-container.spdx.json \\
            --summary artifacts/titan-container-sbom.summary.json
          python -m json.tool artifacts/titan-container-sbom.summary.json >/dev/null

      - name: Upload final runtime container SBOM evidence
        if: always()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: titan-container-sbom
          path: |
            artifacts/titan-container.spdx.json
            artifacts/titan-container.spdx.json.sha256
            artifacts/titan-container-sbom.summary.json
            artifacts/titan-container-sbom.metadata.txt
            artifacts/docker-buildx-version.txt
            artifacts/docker-client-version.txt
          if-no-files-found: error
          retention-days: 14
'''
text = text[:start] + new + text[end:]
workflow_path.write_text(text, encoding="utf-8")

gate_path = Path("scripts/check_pr_merge_evidence.py")
gate = gate_path.read_text(encoding="utf-8")
anchor = '    ".github/workflows/docker.yml",\n)\n'
gate_replacement = (
    '    "scripts/validate_container_sbom.py",\n'
    '    "tests/test_container_sbom.py",\n'
    '    "docs/operations/container-sbom.md",\n'
    + anchor
)
if gate.count(anchor) != 1:
    raise SystemExit(f"expected one DOCKER_PATHS closing anchor, found {gate.count(anchor)}")
gate_path.write_text(gate.replace(anchor, gate_replacement), encoding="utf-8")
