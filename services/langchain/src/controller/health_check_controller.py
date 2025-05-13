# standard libraries 

# installed libraries

# custom libraries
from fastapi.routing import APIRouter


router = APIRouter(prefix="/rest/v1/health", tags=["health"])

@router.get("/")
async def health_check():
    return {"status": "ok", "version": "0.0.2"}
