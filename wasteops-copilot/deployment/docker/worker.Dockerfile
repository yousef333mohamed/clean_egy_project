FROM python:3.12.10-slim-bookworm AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PIP_NO_CACHE_DIR=1
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install .

FROM python:3.12.10-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
RUN addgroup --system --gid 10001 wasteops && adduser --system --uid 10001 --ingroup wasteops --no-create-home wasteops
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=wasteops:wasteops app ./app
USER 10001:10001
STOPSIGNAL SIGTERM
CMD ["celery", "-A", "app.jobs.celery_app:celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]
