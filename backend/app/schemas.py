from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------- HCP ----------
class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Interaction ----------
class InteractionBase(BaseModel):
    hcp_name: str = Field(..., description="Name of the HCP; created if it doesn't exist")
    interaction_type: str = "Meeting"
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    source: Optional[str] = "form"


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    hcp_name: Optional[str] = None
    interaction_type: str
    interaction_date: datetime
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRequest(BaseModel):
    session_id: str = "default-session"
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[str] = []
    interaction: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    saved: bool = False
    pending_approval: bool = False