from pathlib import Path

path = Path('.github/workflows/docker.yml')
text = path.read_text(encoding='utf-8')
anchor = "          docker buildx version | tee artifacts/docker-buildx-version.txt\n          docker version --format '{{.Client.Version}}' > artifacts/docker-client-version.txt\n"
replacement = anchor + "          docker buildx create --driver docker-container --name titan-ci-builder --use\n          docker buildx inspect --bootstrap\n"
if text.count(anchor) != 1:
    raise SystemExit(f'expected one buildx setup anchor, found {text.count(anchor)}')
path.write_text(text.replace(anchor, replacement), encoding='utf-8')
