from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# 健康檢查
class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


# URL 縮短請求模型
class ShortURLRequest(BaseModel):
    original_url: str = Field(..., max_length=2048, title="original_url")


# URL 縮短回應模型
class ShortURLResponse(BaseModel):
    short_url: str = Field(..., title='short_url')
    expiration_date: datetime = Field(..., title='expiration_date')
    success: bool = True
    reason: Optional[str] = Field(..., title='reason')

