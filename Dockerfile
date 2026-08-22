FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/thorax

WORKDIR /app

RUN useradd --create-home --home-dir /home/thorax thorax

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip check

COPY --chown=thorax:thorax . .

USER thorax

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=8)"

CMD ["python", "-m", "uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8000"]
