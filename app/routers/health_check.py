from fastapi import APIRouter, status
from ..schemas import HealthCheck


router = APIRouter(
    tags=['healthcheck']
)


@router.get(
    "/health",
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
