"""Optional MLflow tracking adapter; training remains usable without a server."""

from contextlib import contextmanager


@contextmanager
def tracked_run(settings, model_name: str, metadata: dict):
    if not settings.mlflow_tracking_uri:
        yield None
        return
    try:
        import mlflow
    except ImportError as exc:
        raise RuntimeError("MLflow tracking is configured but mlflow is not installed") from exc
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(f"{settings.mlflow_experiment_prefix}-{model_name}")
    with mlflow.start_run() as run:
        mlflow.log_params({key: value for key, value in metadata.items() if isinstance(value, (str, int, float, bool))})
        yield run
