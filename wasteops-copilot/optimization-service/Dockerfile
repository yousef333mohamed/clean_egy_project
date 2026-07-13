FROM python:3.12.11-slim-bookworm
WORKDIR /service
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 optimizer
USER optimizer
EXPOSE 8002
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8002","--no-access-log"]
