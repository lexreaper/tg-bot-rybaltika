import asyncio
import logging
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote

import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class S3Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    yandex_s3_access_key_id: SecretStr
    yandex_s3_secret_key: SecretStr
    yandex_s3_bucket_name: str
    yandex_s3_region: str = "ru-central1"


class S3ServiceError(Exception):
    pass


class S3ObjectNotFound(S3ServiceError):
    pass


@dataclass(frozen=True)
class S3File:
    content: bytes
    content_type: str


@lru_cache
def _get_client():
    settings = S3Settings()
    return boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=settings.yandex_s3_access_key_id.get_secret_value(),
        aws_secret_access_key=settings.yandex_s3_secret_key.get_secret_value(),
        region_name=settings.yandex_s3_region,
    )


@lru_cache
def _get_bucket_name() -> str:
    return S3Settings().yandex_s3_bucket_name


def _validate_key(file_key: str) -> str:
    key = file_key.strip("/")
    if not key or any(part in {".", ".."} for part in key.split("/")):
        raise ValueError("A valid S3 object key is required")
    return key


def get_file_url(file_key: str) -> str:
    key = _validate_key(file_key)
    return (
        f"https://storage.yandexcloud.net/{_get_bucket_name()}/"
        f"{quote(key, safe='/')}"
    )


def _upload_file(file: UploadFile, file_key: str) -> None:
    _get_client().upload_fileobj(
        file.file,
        _get_bucket_name(),
        file_key,
        ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
    )


async def upload_file_to_s3(file: UploadFile, folder: str) -> str:
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not filename:
        raise ValueError("Uploaded file must have a filename")

    folder_parts = [part for part in folder.split("/") if part]
    if any(part in {".", ".."} for part in folder_parts):
        raise ValueError("A valid S3 folder is required")
    file_key = _validate_key("/".join([*folder_parts, filename]))

    try:
        await asyncio.to_thread(_upload_file, file, file_key)
    except (Boto3Error, BotoCoreError, ClientError) as exc:
        logger.exception("Failed to upload object to S3")
        raise S3ServiceError("Failed to upload file to object storage") from exc

    return get_file_url(file_key)


def _download_file(file_key: str) -> S3File:
    response = _get_client().get_object(Bucket=_get_bucket_name(), Key=file_key)
    body = response["Body"]
    try:
        content = body.read()
    finally:
        body.close()
    return S3File(
        content=content,
        content_type=response.get("ContentType", "application/octet-stream"),
    )


async def get_file_from_s3(file_key: str) -> S3File:
    key = _validate_key(file_key)
    try:
        return await asyncio.to_thread(_download_file, key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            raise S3ObjectNotFound("File not found in object storage") from exc
        logger.exception("Failed to download object from S3")
        raise S3ServiceError("Failed to download file from object storage") from exc
    except (Boto3Error, BotoCoreError) as exc:
        logger.exception("Failed to download object from S3")
        raise S3ServiceError("Failed to download file from object storage") from exc


def _delete_file(file_key: str) -> None:
    _get_client().delete_object(Bucket=_get_bucket_name(), Key=file_key)


async def delete_file_from_s3(file_key: str) -> None:
    key = _validate_key(file_key)
    try:
        await asyncio.to_thread(_delete_file, key)
    except (Boto3Error, BotoCoreError, ClientError) as exc:
        logger.exception("Failed to delete object from S3")
        raise S3ServiceError("Failed to delete file from object storage") from exc
