from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import HCP, Interaction


def get_or_create_hcp(db: Session, name: str, specialty: Optional[str] = None) -> HCP:
    hcp = db.query(HCP).filter(HCP.name.ilike(name.strip())).first()
    if hcp:
        return hcp
    hcp = HCP(name=name.strip(), specialty=specialty)
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp


def create_interaction(db: Session, data: dict) -> Interaction:
    hcp = get_or_create_hcp(db, data["hcp_name"])
    interaction = Interaction(
        hcp_id=hcp.id,
        interaction_type=data.get("interaction_type", "Meeting"),
        attendees=data.get("attendees"),
        topics_discussed=data.get("topics_discussed"),
        materials_shared=data.get("materials_shared"),
        samples_distributed=data.get("samples_distributed"),
        sentiment=data.get("sentiment", "Neutral"),
        outcomes=data.get("outcomes"),
        follow_up_actions=data.get("follow_up_actions"),
        source=data.get("source", "form"),
        interaction_date=datetime.utcnow(),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def update_interaction(db: Session, interaction_id: str, updates: dict) -> Optional[Interaction]:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return None
    for key, value in updates.items():
        if value is not None and hasattr(interaction, key):
            setattr(interaction, key, value)
    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: str) -> Optional[Interaction]:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(db: Session, hcp_name: Optional[str] = None, limit: int = 20) -> List[Interaction]:
    query = db.query(Interaction).join(HCP)
    if hcp_name:
        query = query.filter(HCP.name.ilike(f"%{hcp_name.strip()}%"))
    return query.order_by(Interaction.interaction_date.desc()).limit(limit).all()


def search_hcps(db: Session, query_str: str, limit: int = 10) -> List[HCP]:
    return (
        db.query(HCP)
        .filter(HCP.name.ilike(f"%{query_str.strip()}%"))
        .limit(limit)
        .all()
    )


def interaction_to_dict(interaction: Interaction) -> dict:
    return {
        "id": interaction.id,
        "hcp_id": interaction.hcp_id,
        "hcp_name": interaction.hcp.name if interaction.hcp else None,
        "interaction_type": interaction.interaction_type,
        "interaction_date": interaction.interaction_date,
        "attendees": interaction.attendees,
        "topics_discussed": interaction.topics_discussed,
        "materials_shared": interaction.materials_shared,
        "samples_distributed": interaction.samples_distributed,
        "sentiment": interaction.sentiment,
        "outcomes": interaction.outcomes,
        "follow_up_actions": interaction.follow_up_actions,
        "source": interaction.source,
        "created_at": interaction.created_at,
        "updated_at": interaction.updated_at,
    }
