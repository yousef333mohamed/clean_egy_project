"""Storage backend factory."""

from app.core.config import Settings
from app.storage.base import ObjectStorage
from app.storage.local import LocalObjectStorage
from app.storage.s3 import S3ObjectStorage


def create_object_storage(settings: Settings) -> ObjectStorage:
    if settings.object_storage_backend == "s3":
        if not settings.object_storage_bucket:
            raise ValueError("OBJECT_STORAGE_BUCKET is required for S3 storage")
        return S3ObjectStorage(bucket=settings.object_storage_bucket, endpoint_url=settings.object_storage_endpoint_url, region=settings.object_storage_region)
    return LocalObjectStorage(settings.object_storage_directory)
