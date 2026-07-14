"""
The LangGraph agent that powers the chat side of the "Log HCP Interaction" screen.

Role of the agent (per assignment requirement):
The agent acts as an AI copilot embedded in the CRM's HCP module. Instead of forcing
the field rep to fill a structured form, the rep can describe an interaction in plain
language (typed or dictated), keep correcting it conversationally, and only commit it
to the database once they explicitly approve. The agent, backed by Groq's gemma2-9b-it
for fast routing/reasoning and llama-3.3-70b-versatile for heavier summarization/suggestion
tasks, decides which of its 6 tools to invoke: staging/updating a draft interaction,
permanently logging it (on approval), editing a previously saved one (on approval),
searching interaction history, suggesting follow-ups, or cleaning up a dictated voice
note. It maintains short conversational memory per session so the rep can issue
follow-up commands like "actually make that Positive sentiment" without repeating context.
"""
import json
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.agent.llm import get_primary_llm
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI Assistant embedded in the HCP (Healthcare Professional)
module of a pharma CRM, used by field representatives to log interactions with doctors.

How logging works — a two-step, approval-gated flow:
1. STAGE: whenever the user describes or corrects interaction details (first message or
   any later correction like "actually make sentiment positive" or "add that I shared
   2 samples"), call `stage_interaction` with a comprehensive description that merges the
   new info with everything gathered so far in this conversation. This only previews the
   draft on screen — it never saves anything. After staging, briefly summarize the draft
   and ask something like "Should I log this?".
2. COMMIT: only when the user's current message is a clear, explicit approval — words like
   "yes", "log it", "save", "confirm", "submit", "go ahead" — call `log_interaction` with a
   raw_text that comprehensively captures the FULL interaction as discussed across the
   whole conversation (including any corrections). Never call `log_interaction` on the
   first message or without a clear approval immediately preceding it.

Other tools:
- To change something on an ALREADY-SAVED interaction, call `edit_interaction` — but only
  after explicit approval too. Use `search_interactions` first if you need the interaction_id.
- To answer questions about past interactions, call `search_interactions`.
- To propose next steps after an interaction is saved, call `suggest_followups` with its interaction_id.
- If the user pastes a rough dictated/voice transcript, call `summarize_voice_note` first,
  then fold the cleaned summary into your next `stage_interaction`/`log_interaction` call.

General style:
- Always confirm briefly, in plain English, what you did (e.g. "Staged: meeting with Dr.
  Sharma, sentiment Positive. Should I log this?" or, after saving, "✅ Logged your meeting
  with Dr. Sharma. Want me to suggest follow-ups?").
- Be concise. You are a working tool for busy field reps, not a chatbot for small talk.
"""

_checkpointer = MemorySaver()

agent_executor = create_react_agent(
    model=get_primary_llm(),
    tools=ALL_TOOLS,
    state_modifier=SYSTEM_PROMPT,
    checkpointer=_checkpointer,
)


def run_agent(session_id: str, user_message: str) -> dict:
    """Invoke the agent for one conversational turn. Returns the final reply text,
    the list of tool names that were called (for UI transparency), the structured
    interaction data (staged OR saved) so the on-screen form can auto-fill, whether
    a real DB write happened this turn (`saved`), whether a draft is now waiting on
    the user's approval (`pending_approval`), and any follow-up suggestions."""
    config = {"configurable": {"thread_id": session_id}}
    result = agent_executor.invoke(
        {"messages": [("human", user_message)]},
        config=config,
    )
    messages = result["messages"]
    final_reply = messages[-1].content

    tool_calls = []
    interaction_data = None
    suggestions = []
    saved = False
    pending_approval = False

    for m in messages:
        if getattr(m, "tool_calls", None):
            tool_calls.extend([tc["name"] for tc in m.tool_calls])

        if isinstance(m, ToolMessage):
            try:
                parsed = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                continue

            if m.name == "stage_interaction" and "interaction" in parsed:
                interaction_data = parsed["interaction"]
                pending_approval = True
            elif m.name in ("log_interaction", "edit_interaction") and "interaction" in parsed:
                interaction_data = parsed["interaction"]
                saved = True
                pending_approval = False
            elif m.name == "suggest_followups" and "suggestions" in parsed:
                suggestions = parsed["suggestions"]

    return {
        "reply": final_reply,
        "tool_calls": tool_calls,
        "interaction": interaction_data,
        "suggestions": suggestions,
        "saved": saved,
        "pending_approval": pending_approval,
    }