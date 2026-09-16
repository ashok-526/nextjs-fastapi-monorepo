from __future__ import annotations

import uuid
from typing import Literal

import boto3
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/media", tags=["media"])


ALLOWED_EXT_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


class PresignRequest(BaseModel):
    contentType: str = Field(alias="contentType")
    ext: str
    size: int


class PresignResponse(BaseModel):
    url: str
    fields: dict


@router.post("/presign", response_model=PresignResponse)
async def presign_upload(
    payload: PresignRequest,
    current_user: User = Depends(get_current_user),
) -> PresignResponse:
    content_type = payload.contentType.lower()
    ext = payload.ext.lower().lstrip(".")
    size = payload.size

    if size <= 0 or size > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file size")

    if ext not in ALLOWED_EXT_MIME or ALLOWED_EXT_MIME[ext] != content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported type")

    settings = get_settings()

    key = f"user/{current_user.id}/{uuid.uuid4()}.{ext}"

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
    )

    conditions = [
        {"Content-Type": content_type},
        {"key": key},
        ["content-length-range", 1, MAX_SIZE],
    ]
    fields = {
        "Content-Type": content_type,
        "key": key,
    }

    presigned = s3.generate_presigned_post(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=60,
    )

    return PresignResponse(url=presigned["url"], fields=presigned["fields"])

