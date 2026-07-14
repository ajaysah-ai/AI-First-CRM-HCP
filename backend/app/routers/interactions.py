from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import crud
from app.schemas import InteractionCreate, InteractionUpdate, InteractionOut

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


def _to_out(interaction) -> InteractionOut:
    d = crud.interaction_to_dict(interaction)
    return InteractionOut(**d)


@router.post("", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    interaction = crud.create_interaction(db, payload.model_dump())
    return _to_out(interaction)


@router.get("", response_model=List[InteractionOut])
def get_interactions(hcp_name: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    interactions = crud.list_interactions(db, hcp_name=hcp_name, limit=limit)
    return [_to_out(i) for i in interactions]


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _to_out(interaction)


@router.patch("/{interaction_id}", response_model=InteractionOut)
def edit_interaction(interaction_id: str, payload: InteractionUpdate, db: Session = Depends(get_db)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    interaction = crud.update_interaction(db, interaction_id, updates)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _to_out(interaction)


@router.get("/{interaction_id}/suggest-followups")
def suggest_followups_route(interaction_id: str, db: Session = Depends(get_db)):
    from app.agent.tools import suggest_followups
    import json
    interaction = crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    raw = suggest_followups.invoke({"interaction_id": interaction_id})
    return json.loads(raw)
