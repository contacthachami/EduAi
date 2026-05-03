FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    HF_HOME=/app/models_cache \
    TRANSFORMERS_CACHE=/app/models_cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt

# Install CPU-only PyTorch first — prevents pip from pulling multi-GB CUDA
# libraries (nvidia-cudnn-cu13, cuda-toolkit, etc.) from PyPI when resolving
# torch>=2.5.0 on Linux.
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch>=2.5.0,<3.0.0"

# Install remaining dependencies (torch is already satisfied — won't reinstall)
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && python -m spacy download fr_core_news_lg \
    && apt-get purge -y --auto-remove build-essential

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/data/faiss_indexes /app/models_cache \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser backend ./backend

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read()"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
