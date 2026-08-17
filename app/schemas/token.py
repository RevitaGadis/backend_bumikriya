from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None
    type: str = None

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None
