"""Validate the static analytics catalog without executing SQL."""

from app.analytics.metric_registry import METRIC_REGISTRY
from app.analytics.tool_registry import build_tool_registry
from app.core.config import get_settings


def main() -> None:
    registry = build_tool_registry(get_settings())
    for tool in registry.list():
        unknown = set(tool.supported_metrics) - set(METRIC_REGISTRY)
        if unknown:
            raise RuntimeError(f"{tool.name} references unknown metrics: {sorted(unknown)}")
        print(f"OK {tool.name}: {tool.domain}")


if __name__ == "__main__":
    main()
