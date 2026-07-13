"""Private, encrypted S3-compatible object storage."""

import asyncio


class S3ObjectStorage:
    def __init__(self, *, bucket: str, endpoint_url: str, region: str) -> None:
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint_url or None, region_name=region or None)

    @staticmethod
    def _key(key: str) -> str:
        if not key or key.startswith("/") or ".." in key.split("/"):
            raise ValueError("Invalid object key")
        return key

    async def put(self, namespace: str, data: bytes, *, sha256: str) -> str:
        import hashlib

        if hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError("Object hash mismatch")
        key = self._key(f"{namespace}/{sha256}")
        await asyncio.to_thread(self.client.put_object, Bucket=self.bucket, Key=key, Body=data, ServerSideEncryption="AES256", Metadata={"sha256": sha256})
        return key

    async def get(self, key: str) -> bytes:
        response = await asyncio.to_thread(self.client.get_object, Bucket=self.bucket, Key=self._key(key))
        return await asyncio.to_thread(response["Body"].read)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=self._key(key))

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=self._key(key))
            return True
        except self.client.exceptions.ClientError:
            return False

    async def create_signed_download(self, key: str, *, expires_seconds: int = 300) -> str:
        if not 1 <= expires_seconds <= 900:
            raise ValueError("Signed URL expiry must be at most 15 minutes")
        return await asyncio.to_thread(
            self.client.generate_presigned_url, "get_object", Params={"Bucket": self.bucket, "Key": self._key(key)}, ExpiresIn=expires_seconds
        )
