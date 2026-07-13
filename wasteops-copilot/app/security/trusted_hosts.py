"""Trusted-host parsing."""

from app.core.config import Settings


def trusted_hosts(settings: Settings) -> list[str]:
    return [host.strip() for host in settings.trusted_hosts.split(",") if host.strip()]
