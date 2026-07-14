import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50), default="Meeting")  # Meeting, Call, Email, Conference
    interaction_date = Column(DateTime, default=datetime.utcnow)

    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)      # comma separated
    samples_distributed = Column(Text, nullable=True)   # comma separated

    sentiment = Column(String(20), default="Neutral")   # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)

    source = Column(String(20), default="form")  # "form" or "chat"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class ChatMessage(Base):
    """Stores chat history per session so the LangGraph agent has conversational memory."""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20))  # user | assistant | tool
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
