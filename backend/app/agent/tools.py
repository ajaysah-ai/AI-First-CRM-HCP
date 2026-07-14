"""
LangGraph tools for the HCP Interaction Agent.

5 tools (assignment requirement — minimum 5):
  1. log_interaction      -> creates a new interaction record (uses LLM for entity extraction)
  2. edit_interaction     -> modifies an existing interaction record
  3. search_interactions  -> looks up past interactions for an HCP
  4. suggest_followups    -> LLM-generated next-step suggestions based on an interaction
  5. summarize_voice_note -> turns a raw dictated/voice-note transcript into structured fields
"""
"""
LangGraph tools for the HCP Interaction Agent.

6 tools (assignment requires a minimum of 5, including "Log Interaction" and "Edit Interaction"):
  1. stage_interaction    -> extracts/updates draft fields from chat text WITHOUT saving
                             (lets the rep build up or correct the interaction via conversation
                             before committing anything to the database)
  2. log_interaction      -> the required "Log Interaction" tool: performs the final DB write.
                             Only called once the user has explicitly approved saving.
  3. edit_interaction     -> the required "Edit Interaction" tool: modifies an already-saved
                             interaction record. Also requires explicit user approval.
  4. search_interactions  -> looks up past interactions for an HCP
  5. suggest_followups    -> LLM-generated next-step suggestions based on a saved interaction
  6. summarize_voice_note -> turns a raw dictated/voice-note transcript into structured fields
"""
import json
from typing import Optional
from langchain_core.tools import tool

from app.database import SessionLocal
from app import crud
from app.agent.llm import get_primary_llm, get_context_llm

EXTRACTION_SYSTEM_PROMPT = """You are an entity-extraction assistant for a pharma CRM.
Given a free-text description of a field rep's interaction with a Healthcare Professional (HCP),
extract structured fields. Respond ONLY with valid JSON, no markdown, no commentary, matching this schema:

{
  "hcp_name": string,
  "interaction_type": one of ["Meeting", "Call", "Email", "Conference"],
  "topics_discussed": string,
  "materials_shared": string (comma separated, empty string if none),
  "samples_distributed": string (comma separated, empty string if none),
  "sentiment": one of ["Positive", "Neutral", "Negative"],
  "outcomes": string,
  "follow_up_actions": string
}

If a field cannot be inferred, use a sensible empty default ("" for strings, "Neutral" for sentiment,
"Meeting" for interaction_type). Never invent an HCP name if none is mentioned — in that case use "Unknown HCP".
The input text may describe the FULL interaction, or may just be a correction/addition on top of
something already discussed (e.g. "actually make sentiment positive") — in that case still return
the complete schema, keeping unmentioned fields at their sensible defaults; the caller is responsible
for merging this with anything already staged.
"""


def _extract_fields_with_llm(raw_text: str) -> dict:
    llm = get_primary_llm(temperature=0.0)
    messages = [
        ("system", EXTRACTION_SYSTEM_PROMPT),
        ("human", raw_text),
    ]
    response = llm.invoke(messages)
    content = response.content.strip()
    # Defensive cleanup in case the model wraps JSON in markdown fences
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json\n", "", 1).replace("json", "", 1)
    try:
        parsed = json.loads(content)
        return _normalize_enums(parsed)
    except json.JSONDecodeError:
        return {
            "hcp_name": "Unknown HCP",
            "interaction_type": "Meeting",
            "topics_discussed": raw_text,
            "materials_shared": "",
            "samples_distributed": "",
            "sentiment": "Neutral",
            "outcomes": "",
            "follow_up_actions": "",
        }


def _normalize_enums(data: dict) -> dict:
    """Guard against the LLM returning slightly different casing/whitespace for
    enum-like fields (e.g. "positive " instead of "Positive") — the frontend does
    exact string comparisons (e.g. for the sentiment radio buttons), so mismatched
    casing would silently fail to auto-select the right option."""
    sentiment_map = {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}
    type_map = {"meeting": "Meeting", "call": "Call", "email": "Email", "conference": "Conference"}

    if "sentiment" in data and isinstance(data["sentiment"], str):
        data["sentiment"] = sentiment_map.get(data["sentiment"].strip().lower(), "Neutral")
    if "interaction_type" in data and isinstance(data["interaction_type"], str):
        data["interaction_type"] = type_map.get(data["interaction_type"].strip().lower(), "Meeting")
    return data


@tool
def stage_interaction(raw_text: str) -> str:
    """Extract structured interaction fields (HCP name, type, topics, materials/samples,
    sentiment, outcomes, follow-ups) from free text WITHOUT saving anything to the database.
    Use this every time the user describes or corrects interaction details in chat, so the
    on-screen form can preview the draft. This tool NEVER writes to the database — it only
    stages a draft for the user to review before they approve saving via `log_interaction`.
    Returns the staged draft as JSON."""
    extracted = _extract_fields_with_llm(raw_text)
    return json.dumps({"status": "staged", "interaction": extracted})


@tool
def log_interaction(raw_text: str, source: str = "chat") -> str:
    """Permanently save a new HCP interaction to the database. `raw_text` must comprehensively
    describe the FULL interaction as gathered so far across the conversation (merge in any
    corrections the user made). ONLY call this tool after the user has explicitly approved
    saving (e.g. said "yes", "log it", "save", "confirm", "submit") in response to a staged
    draft — never call it proactively on the first message. Uses the LLM to extract HCP name,
    interaction type, topics, materials/samples, sentiment, outcomes and follow-up actions,
    then commits the record. Returns a JSON string with the saved interaction."""
    extracted = _extract_fields_with_llm(raw_text)
    db = SessionLocal()
    try:
        interaction = crud.create_interaction(db, {**extracted, "source": source})
        result = crud.interaction_to_dict(interaction)
        result["interaction_date"] = str(result["interaction_date"])
        result["created_at"] = str(result["created_at"])
        result["updated_at"] = str(result["updated_at"])
        return json.dumps({"status": "logged", "interaction": result})
    finally:
        db.close()


@tool
def edit_interaction(interaction_id: str, field_updates: str) -> str:
    """Edit/modify an existing SAVED interaction. `interaction_id` is the record id
    (use `search_interactions` first if you don't already have it). `field_updates` is a
    JSON string of the fields to change, e.g. '{"sentiment": "Positive", "outcomes": "Agreed to trial samples"}'.
    Valid fields: interaction_type, attendees, topics_discussed, materials_shared,
    samples_distributed, sentiment, outcomes, follow_up_actions.
    This permanently updates the database — only call it after the user has explicitly
    approved the change. Returns the updated record as JSON, or an error if the id doesn't exist."""
    db = SessionLocal()
    try:
        try:
            updates = json.loads(field_updates)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "field_updates must be valid JSON"})

        interaction = crud.update_interaction(db, interaction_id, updates)
        if not interaction:
            return json.dumps({"status": "error", "message": f"No interaction found with id {interaction_id}"})

        result = crud.interaction_to_dict(interaction)
        result["interaction_date"] = str(result["interaction_date"])
        result["created_at"] = str(result["created_at"])
        result["updated_at"] = str(result["updated_at"])
        return json.dumps({"status": "updated", "interaction": result})
    finally:
        db.close()


@tool
def search_interactions(hcp_name: Optional[str] = None, limit: int = 5) -> str:
    """Search/retrieve past logged interactions, optionally filtered by HCP name
    (partial match, case-insensitive). Returns the most recent interactions first as JSON.
    Use this to answer questions like 'when did I last meet Dr. Sharma?' or
    'show my recent interactions'."""
    db = SessionLocal()
    try:
        interactions = crud.list_interactions(db, hcp_name=hcp_name, limit=limit)
        results = []
        for i in interactions:
            d = crud.interaction_to_dict(i)
            d["interaction_date"] = str(d["interaction_date"])
            d["created_at"] = str(d["created_at"])
            d["updated_at"] = str(d["updated_at"])
            results.append(d)
        return json.dumps({"status": "ok", "count": len(results), "interactions": results})
    finally:
        db.close()


@tool
def suggest_followups(interaction_id: str) -> str:
    """Given a logged interaction id, use the LLM to suggest 2-4 concrete, realistic
    next-step follow-up actions for the field rep (e.g. schedule a follow-up meeting,
    send specific literature, add to an advisory board list). Returns JSON list of suggestions."""
    db = SessionLocal()
    try:
        interaction = crud.get_interaction(db, interaction_id)
        if not interaction:
            return json.dumps({"status": "error", "message": f"No interaction found with id {interaction_id}"})

        context = crud.interaction_to_dict(interaction)
        llm = get_context_llm(temperature=0.4)
        prompt = f"""Based on this HCP interaction, suggest 2-4 short, concrete follow-up actions
a pharma field rep should take. Respond ONLY as a JSON array of short strings, no commentary.

HCP: {context['hcp_name']}
Type: {context['interaction_type']}
Topics discussed: {context['topics_discussed']}
Sentiment: {context['sentiment']}
Outcomes: {context['outcomes']}
"""
        response = llm.invoke([("human", prompt)])
        content = response.content.strip().strip("`")
        content = content.replace("json\n", "", 1).replace("json", "", 1)
        try:
            suggestions = json.loads(content)
        except json.JSONDecodeError:
            suggestions = [line.strip("- ") for line in content.splitlines() if line.strip()]
        return json.dumps({"status": "ok", "suggestions": suggestions})
    finally:
        db.close()


@tool
def summarize_voice_note(transcript: str) -> str:
    """Take a raw voice-note transcript (dictated by the field rep, requires consent)
    and produce a clean, structured one-paragraph summary suitable for the
    'Topics Discussed' field, stripping filler words and disfluencies.
    Returns JSON with the cleaned summary."""
    llm = get_context_llm(temperature=0.2)
    prompt = f"""Clean up this dictated voice-note transcript from a pharma field rep into a
concise, professional one-paragraph summary suitable for a CRM 'Topics Discussed' field.
Remove filler words, false starts, and repetitions. Keep all factual/medical details intact.
Respond with ONLY the cleaned summary text, no preamble.

Transcript: {transcript}
"""
    response = llm.invoke([("human", prompt)])
    return json.dumps({"status": "ok", "summary": response.content.strip()})


ALL_TOOLS = [
    stage_interaction,
    log_interaction,
    edit_interaction,
    search_interactions,
    suggest_followups,
    summarize_voice_note,
]