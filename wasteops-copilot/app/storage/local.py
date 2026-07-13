"""Path-safe local development object storage."""

import asyncio
import hashlib
from pathlib import Path


class LocalObjectStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not key or Path(key).is_absolute() or ".." in Path(key).parts:
            raise ValueError("Invalid object key")
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError("Invalid object key")
        return target

    async def put(self, namespace: str, data: bytes, *, sha256: str) -> str:
        actual = hashlib.sha256(data).hexdigest()
        if actual != sha256:
            raise ValueError("Object hash mismatch")
        safe_namespace = "".join(char for char in namespace if char.isalnum() or char in "-_")
        if not safe_namespace:
            raise ValueError("Invalid namespace")
        key = f"{safe_namespace}/{actual}"
        path = self._path(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return key

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, missing_ok=True)

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._path(key).is_file)

    async def create_signed_download(self, key: str, *, expires_seconds: int = 300) -> str:
        raise NotImplementedError("Local downloads must be served by an authorized application endpoint")
