import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.s3_service import S3ServiceError, upload_file_to_s3

router = APIRouter(prefix="/images", tags=["Images"])
logger = logging.getLogger(__name__)


@router.post("/upload", status_code=201)
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")

    try:
        image_url = await upload_file_to_s3(file, folder="dishes")
        return {"url": image_url}
    except S3ServiceError as exc:
        logger.exception("Image upload failed")
        raise HTTPException(
            status_code=502,
            detail="Не удалось загрузить изображение",
        ) from exc