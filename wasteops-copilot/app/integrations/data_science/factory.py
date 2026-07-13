"""Provider selection with production mock prohibition."""

from app.integrations.data_science.client import DataScienceClient
from app.integrations.data_science.interfaces import DisabledDataScienceProvider
from app.integrations.data_science.mock_provider import MockDataScienceProvider
from app.integrations.data_science.providers import RemoteDataScienceProvider

_remote_provider = None
_admin_client = None


def build_data_science_provider(settings):
    global _remote_provider
    if settings.data_science_provider == "disabled":
        return DisabledDataScienceProvider()
    if settings.data_science_provider == "mock":
        return MockDataScienceProvider(settings)
    if _remote_provider is None:
        _remote_provider = RemoteDataScienceProvider(DataScienceClient(settings))
    return _remote_provider


def build_ml_admin_client(settings):
    global _admin_client
    if settings.data_science_provider != "remote" or not settings.ml_admin_service_token:
        return None
    if _admin_client is None:
        _admin_client = DataScienceClient(settings, token=settings.ml_admin_service_token)
    return _admin_client
