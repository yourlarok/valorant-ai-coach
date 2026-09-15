from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.analysis.baselines import load_baseline
from app.analysis.metrics import compute_raws
from app.coaching.planner import build_plan
from app.coaching.rules import detect_problems
from app.db import load_plan, save_plan, set_task_done

router = APIRouter(prefix="/api")


class ToggleBody(BaseModel):
    task_name: str
    done: bool


@router.get("/plan")
def get_plan(request: Request, name: str, rank_tier: str = "钻石"):
    existing = load_plan(name)
    if existing:
        return {"tasks": existing}
    collector = request.app.state.collector
    matches = collector.recent_matches(name, 10)
    if not matches:
        return {"tasks": []}
    raws = compute_raws(matches, name)
    problems = detect_problems(raws, load_baseline(rank_tier))
    tasks = [t.model_dump() for t in build_plan(problems)]
    save_plan(name, tasks)
    return {"tasks": tasks}


@router.post("/plan/toggle")
def toggle_task(body: ToggleBody, name: str):
    updated = set_task_done(name, body.task_name, body.done)
    return {"ok": updated}
