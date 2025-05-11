import os
import uvicorn
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl, Field
from .utils import get_redis_client
from redis.asyncio import RedisError, ValidationError

app = FastAPI()


# URL 縮短請求模型
class ShortURLRequest(BaseModel):
    original_url: HttpUrl = Field(..., max_length=2048)


# URL 縮短回應模型
class ShortURLResponse(BaseModel):
    short_url: str
    expiration_date: datetime
    success: bool = True
    reason: str = ""


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on.This
    endpoint can primarily be used Docker to ensure a robust container
    orchestration and management is in place. Other services which rely on
    proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


# 短網址服務設定
EXPIRATION_SECOND = 600  # 預設過期時間
RATE_LIMIT = 100  # 預設速率限制


async def enforce_rate_limit(
    redis_client, client_ip: str, limit: int = 10, window: int = 60
) -> None:
    rate_limit_key = f"rate_limit:{client_ip}"
    current_count = await redis_client.get(rate_limit_key)

    # limit access to 10 requests per minute
    if current_count is None:
        await redis_client.setex(rate_limit_key, window, 1)
    elif int(current_count) >= limit:
        raise HTTPException(
            status_code=429, detail="Too many requests. Please try again later."
        )
    else:
        await redis_client.incr(rate_limit_key)


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, request: Request):
#     redis_client = await get_redis_client()
#     client_ip = request.client.host


#     await enforce_rate_limit(redis_client, client_ip, limit=10, window=60)

#     item_key = f"item_{item_id}"
#     cached_item = await redis_client.get(item_key)

#     if cached_item:
#         return {"item_id": item_id, "cached": True, "data": cached_item}

#     # 600 seconds expiration
#     item_data = f"Item data for {item_id}"
#     await redis_client.setex(item_key, EXPIRATION_SECOND, item_data)

#     return {"item_id": item_id, "cached": False, "data": item_data}


# def handle_redis_errors(func):
#     async def wrapper(*args, **kwargs):
#         try:
#             return await func(*args, **kwargs)
#         except aioredis.ConnectionError:
#             raise HTTPException(status_code=503, detail="Unable to connect to Redis")
#         except aioredis.RedisError as e:
#             raise HTTPException(
#                 status_code=500, detail=f"Failed to save URL in Redis: {str(e)}"
#             )
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500, detail=f"Unexpected server error: {str(e)}"
#             )

#     return wrapper


@app.post(
    "/api/shorten",
    tags=["shorten"],
    summary="Create a Short URL",
    response_description="Generate a short URL with expiration date",
    status_code=status.HTTP_201_CREATED,
    response_model=ShortURLResponse,
)
async def create_short_url(request: ShortURLRequest) -> ShortURLResponse:
    try:
        short_id = uuid.uuid4().hex[:8]
        short_url = f"http://localhost:8000/{short_id}"
        redis_client = await get_redis_client()
        await redis_client.setex(short_id, 60 * 60 * 24 * 30, request.original_url)
        return {"short_url": short_url}

    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    except RedisError as re:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {str(re)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@app.get(
    "/{short_id}",
    tags=["redirect"],
    summary="Redirect to Original URL",
    response_description="Redirect to the original URL",
    response_class=HTMLResponse,
)
async def redirect_to_original(short_id: str, request: Request):
    try:
        redis_client = await get_redis_client()
        original_url = await redis_client.get(short_id)

        if original_url is None:
            return HTTPException(status_code=404, detail="Short URL not found")

        # 返回跳轉頁面
        return RedirectResponse(url=original_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error redirecting to original URL: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
