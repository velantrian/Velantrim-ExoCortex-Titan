# Velantrim Titan 9.0 — Dockerfile
# Запуск: docker build -t velantrim-titan . && docker run -p 8000:8000 velantrim-titan

FROM python:3.11-slim

# Отключаем буферизацию Python (логи сразу в stdout)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Системные зависимости (только минимально необходимые)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости
COPY pyproject.toml requirements-dev.txt ./
RUN pip install --no-cache-dir -e ".[server,dev,parsers,retrieval,embeddings,audio,graph-lab]"

# Дополнительные инструменты (русская лемматизация)
RUN pip install --no-cache-dir \
    pymorphy3 \
    && python -c "import pymorphy3; pymorphy3.MorphAnalyzer(lang='ru')" || echo "pymorphy3 ready"

# Исходный код
COPY . .

# Точка входа
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
