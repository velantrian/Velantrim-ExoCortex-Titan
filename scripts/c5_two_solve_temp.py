from pathlib import Path

path = Path('.github/workflows/docker.yml')
text = path.read_text(encoding='utf-8')
start_marker = '      - name: Build image + final runtime SBOM (single BuildKit solve)\n'
end_marker = '\n      - name: Validate final runtime container SBOM\n'
if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    raise SystemExit('expected one C5 build block')
start = text.index(start_marker)
end = text.index(end_marker, start)
replacement = '''      - name: Build runtime image (no cache)
        run: |
          docker build --no-cache \\
            --build-arg RUNTIME_EXTRAS=server \\
            -t velantrim-titan:ci .

      - name: Generate final runtime SBOM (BuildKit local exporter)
        run: |
          set -euo pipefail
          rm -rf container-sbom-out artifacts
          mkdir -p artifacts
          docker buildx version | tee artifacts/docker-buildx-version.txt
          docker version --format '{{.Client.Version}}' > artifacts/docker-client-version.txt
          docker buildx create --driver docker-container --name titan-sbom-builder --use
          docker buildx inspect --bootstrap
          docker buildx build --no-cache \\
            --sbom=true \\
            --build-arg RUNTIME_EXTRAS=server \\
            --output type=local,dest=container-sbom-out \\
            .
          test -s container-sbom-out/sbom.spdx.json
          cp container-sbom-out/sbom.spdx.json artifacts/titan-container.spdx.json
          sha256sum artifacts/titan-container.spdx.json > artifacts/titan-container.spdx.json.sha256
          source_head_sha="$(python -c 'import json, os; event=json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8")); print(event.get("pull_request", {}).get("head", {}).get("sha") or os.environ["GITHUB_SHA"])')"
          {
            echo "source_head_sha=${source_head_sha}"
            echo "runtime_image_id=$(docker image inspect velantrim-titan:ci --format '{{.Id}}')"
            echo "dockerfile_sha256=$(sha256sum Dockerfile | awk '{print $1}')"
            echo "uv_lock_sha256=$(sha256sum uv.lock | awk '{print $1}')"
            echo "sbom_exporter=buildkit-local"
            echo "sbom_scope=final-runtime-stage"
          } > artifacts/titan-container-sbom.metadata.txt
          rm -rf container-sbom-out
'''
path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')
