import os
from pathlib import Path
from typing import Optional

from starlette.exceptions import HTTPException
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from app.core.config import settings

DEFAULT_IMAGE = Path(settings.UPLOAD_DIR) / "products" / "default.png"


class FallbackStaticFiles(StaticFiles):
    """Serve static files; when the requested file is missing, serve a default placeholder instead of 404."""

    def __init__(
        self,
        *args,
        fallback_path: Optional[str] = None,
        fallback_media_type: str = "image/png",
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fallback_path = fallback_path or str(DEFAULT_IMAGE)
        self.fallback_media_type = fallback_media_type

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404 and os.path.exists(self.fallback_path):
                return FileResponse(
                    self.fallback_path,
                    media_type=self.fallback_media_type,
                    headers={"Cache-Control": "public, max-age=86400"},
                )
            raise
        return response
