from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import run_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        result = run_agent(payload.session_id, payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(
        session_id=payload.session_id,
        reply=result["reply"],
        tool_calls=result["tool_calls"],
        interaction=result.get("interaction"),
        suggestions=result.get("suggestions", []),
        saved=result.get("saved", False),
        pending_approval=result.get("pending_approval", False),
    )