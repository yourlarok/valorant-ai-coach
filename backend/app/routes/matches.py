from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/matches")
def list_matches(request: Request, name: str, count: int = 10):
    collector = request.app.state.collector
    return collector.recent_matches(name, count)
