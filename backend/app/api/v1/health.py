from fastapi import APIRouter, Depends, Response

from app.schemas.health import HealthResponse
from app.services.health import check_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    responses={503: {"model": HealthResponse, "description": "Dependencies unavailable"}},
)
def health(response: Response, result: HealthResponse = Depends(check_health)) -> HealthResponse:
    if result.status != "ok":
        response.status_code = 503
    return result
