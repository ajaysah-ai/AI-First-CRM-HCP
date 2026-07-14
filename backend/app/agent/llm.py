from langchain_groq import ChatGroq
from app.config import get_settings

settings = get_settings()


def get_primary_llm(temperature: float = 0.2) -> ChatGroq:
    """gemma2-9b-it — fast, cheap, used for the main agent loop & tool routing."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
    )


def get_context_llm(temperature: float = 0.3) -> ChatGroq:
    """llama-3.3-70b-versatile — heavier model, used where more reasoning/context
    quality is useful (e.g. summarizing long voice notes, nuanced follow-up suggestions)."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_fallback_model,
        temperature=temperature,
    )
