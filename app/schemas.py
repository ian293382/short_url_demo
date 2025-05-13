from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


class ShortURLRequest(BaseModel):
    original_url: str = Field(..., title="original_url")
    
    # validate the URL format 
    @validator("original_url")
    def validate_url_length(cls, v):
        max_length = 2048
        if len(v) > max_length:
            raise ValueError(f"URL is too long (max {max_length} characters)")
        return v


class ShortURLResponse(BaseModel):
    short_url: str = Field(..., title='short_url')
    expiration_date: datetime = Field(..., title='expiration_date')
    success: bool = True
    reason: Optional[str] = Field(..., title='reason')

