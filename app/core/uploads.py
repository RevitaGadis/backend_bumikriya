import os
import uuid
from pathlib import Path

from fastapi import HTTPException, status, UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

DEFAULT_IMAGE_PATH = "/images/products/default.png"

def save_upload(file: UploadFile, subdir: str = "products") -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    upload_root = Path(settings.UPLOAD_DIR) / subdir
    upload_root.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    destination = upload_root / filename

    size = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.MAX_UPLOAD_SIZE:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
                )
            buffer.write(chunk)

    return f"/uploads/{subdir}/{filename}"
