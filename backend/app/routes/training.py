from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app import db

router = APIRouter(prefix="/api/training")

Drill = Literal["headline_flick", "reaction", "tracking"]


class ScoreIn(BaseModel):
    player: str
    drill: Drill
    score: float
    extra: dict = {}


@router.post("/scores")
def post_score(body: ScoreIn):
    best, is_record = db.save_training_score(
        body.player, body.drill, body.score, body.extra)
    return {"ok": True, "best": best, "is_record": is_record}


@router.get("/scores")
def get_scores(player: str = Query(...), drill: Drill | None = None):
    scores, bests = db.load_training_scores(player, drill)
    return {"scores": scores, "bests": bests}
