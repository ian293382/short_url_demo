import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel
from .redis import get_redis_client  

app = FastAPI()

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
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")

# 短網址服務設定
EXPIRATION_SECOND = 600  # 預設過期時間
RATE_LIMIT = 100  # 預設速率限制

async def enforce_rate_limit(redis_client, client_ip: str, limit: int = 10, window: int = 60) -> None:
    rate_limit_key = f"rate_limit:{client_ip}"
    current_count = await redis_client.get(rate_limit_key)
    
    # limit access to 10 requests per minute
    if current_count is None:
        await redis_client.setex(rate_limit_key, window, 1)
    elif int(current_count) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    else:
        await redis_client.incr(rate_limit_key)


@app.get("/items/{item_id}")
async def read_item(item_id: int, request: Request):
    redis_client = await get_redis_client()
    client_ip = request.client.host
    

    await enforce_rate_limit(redis_client, client_ip, limit=10, window=60)
    
    item_key = f"item_{item_id}"
    cached_item = await redis_client.get(item_key)
    
    if cached_item:
        return {"item_id": item_id, "cached": True, "data": cached_item}
    
    # 600 seconds expiration
    item_data = f"Item data for {item_id}"
    await redis_client.setex(item_key, EXPIRATION_SECOND, item_data)
    
    return {"item_id": item_id, "cached": False, "data": item_data}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    redis_client = await get_redis_client()
    await redis_client.delete(f"item_{item_id}")
    return {"status": "cache cleared"}


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)