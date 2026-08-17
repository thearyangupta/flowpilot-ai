from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)

from app.core.config import get_settings


class StorageError(Exception):
    """Base error for private object-storage failures."""


class StorageConfigurationError(StorageError):
    """Raised when object storage is not configured."""


class StorageService:
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        self.bucket_name = bucket_name

        self.client = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def put_private(
        self,
        user_id: UUID,
        checksum: str,
        content: bytes,
    ) -> str:
        storage_key = (
            f"knowledge/{user_id}/{checksum}"
        )

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=content,
                ContentType=(
                    "application/octet-stream"
                ),
            )

        except (
            BotoCoreError,
            ClientError,
        ) as error:
            raise StorageError(
                "Failed to store private object."
            ) from error

        return storage_key

    def read(
        self,
        storage_key: str,
    ) -> bytes:
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )

            body = response["Body"]

            return body.read()

        except (
            BotoCoreError,
            ClientError,
            KeyError,
        ) as error:
            raise StorageError(
                "Failed to read private object."
            ) from error

    def delete(
        self,
        storage_key: str,
    ) -> None:
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )

        except (
            BotoCoreError,
            ClientError,
        ) as error:
            raise StorageError(
                "Failed to delete private object."
            ) from error


@lru_cache
def get_storage_service() -> StorageService:
    settings = get_settings()

    endpoint_url = (
        settings.r2_endpoint_url.strip()
    )

    access_key_id = (
        settings.r2_access_key_id.strip()
    )

    secret_access_key = (
        settings.r2_secret_access_key.strip()
    )

    bucket_name = (
        settings.r2_bucket_name.strip()
    )

    if not endpoint_url:
        raise StorageConfigurationError(
            "R2 endpoint URL is not configured."
        )

    if not access_key_id:
        raise StorageConfigurationError(
            "R2 access key is not configured."
        )

    if not secret_access_key:
        raise StorageConfigurationError(
            "R2 secret key is not configured."
        )

    if not bucket_name:
        raise StorageConfigurationError(
            "R2 bucket name is not configured."
        )

    return StorageService(
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket_name=bucket_name,
    )