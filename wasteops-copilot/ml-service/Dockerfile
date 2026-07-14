FROM python:3.12.11-slim-bookworm AS builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY app ./app
COPY training ./training
RUN python -m pip install --no-cache-dir --upgrade pip && python -m pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/home/ml/.local/bin:$PATH
RUN useradd --create-home --uid 10001 ml
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels wasteops-ml-service && rm -rf /wheels
WORKDIR /service
COPY --chown=ml:ml app ./app
COPY --chown=ml:ml artifacts ./artifacts
USER ml
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--no-access-log"]
