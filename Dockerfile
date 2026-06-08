FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TCM_HOST=0.0.0.0 \
    TCM_PORT=8000 \
    TCM_ENV=production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app \
    && mkdir -p data vector_store tcm_knowledge models \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ready')" || exit 1

CMD ["python", "-c", "import os,uvicorn; uvicorn.run('web_server:app', host=os.getenv('TCM_HOST','0.0.0.0'), port=int(os.getenv('TCM_PORT','8000')))"]
