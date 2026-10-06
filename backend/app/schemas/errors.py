from pydantic import BaseModel
from typing import Optional
class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None
