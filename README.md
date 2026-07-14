# AI-First CRM — HCP Module · Log Interaction Screen

An AI-first CRM module for pharma field representatives to log interactions with
Healthcare Professionals (HCPs) — through a **structured form**, a **conversational
chat interface**, or both together. The chat assistant can fill the form, keep
correcting it as you talk, and only ever saves to the database once you explicitly
approve — nothing is written silently.

Built for: *Technical & Development Task — AI-First CRM HCP Module (Log Interaction Screen)*

---

## 1. Architecture Overview

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│   React + Redux (Vite)  │  HTTP  │        FastAPI Backend        │
│  ┌────────────┐┌───────┐│ ─────► │ ┌──────────────────────────┐ │
│  │ Structured ││  Chat ││        │ │  REST routes (/api/*)    │ │
│  │   Form     ││ Panel ││        │ └──────────┬───────────────┘ │
│  └────────────┘└───────┘│        │            │                 │
└─────────────────────────┘        │  ┌─────────▼──────────────┐  │
                                    │  │   LangGraph Agent      │  │
                                    │  │  (create_react_agent)  │  │
                                    │  │  Groq: gpt-oss-120b     │  │
                                    │  │  Groq: qwen3.6-27b      │  │
                                    │  │                         │  │
                                    │  │  6 Tools:               │  │
                                    │  │   • stage_interaction   │  │
                                    │  │   • log_interaction     │  │
                                    │  │   • edit_interaction    │  │
                                    │  │   • search_interactions │  │
                                    │  │   • suggest_followups   │  │
                                    │  │   • summarize_voice_note│  │
                                    │  └──────────┬──────────────┘ │
                                    │             │                │
                                    │   ┌─────────▼───────────┐    │
                                    │   │  SQLAlchemy ORM      │    │
                                    │   └─────────┬───────────┘    │
                                    └─────────────┼────────────────┘
                                                  │
                                          ┌───────▼────────┐
                                          │   PostgreSQL    │
                                          │  (Docker volume)│
                                          └─────────────────┘
```

### Role of the LangGraph agent
The agent is the "brain" behind the chat side of the Log Interaction screen. Instead of
the rep filling every field manually, they describe the interaction in plain language
(typed, or a pasted dictated voice-note) — e.g. *"Met Dr. Sharma, discussed OncoBoost
Phase III data, she was positive, shared the brochure and left 2 samples"* — and the
agent handles the rest through a deliberately **two-step, approval-gated flow**:

1. **Stage** — every time the rep describes or corrects details, the agent calls
   `stage_interaction`. This only *previews* a draft (auto-filling the form on screen)
   and **never writes to the database**. The agent then asks "Should I log this?"
2. **Commit** — only once the rep gives an explicit approval ("yes", "log it", "save",
   "confirm", "submit"), the agent calls `log_interaction`, which performs the real,
   permanent database write.

This means the rep can keep talking, correcting sentiment, adding a follow-up, changing
the interaction type, etc. — the draft updates live in the form — and nothing is
committed until they say so. The same approval gate applies to `edit_interaction` for
changes to already-saved records.

Under the hood the agent is backed by two Groq models: **`openai/gpt-oss-120b`** for
the main reasoning/tool-routing loop and structured-field extraction, and
**`qwen/qwen3.6-27b`** for the heavier-reasoning tasks (follow-up suggestions,
voice-note cleanup). It keeps short-term memory per browser session (via LangGraph's
`MemorySaver` checkpointer) so multi-turn corrections work without repeating context.

> **Note on models:** Groq deprecated `gemma2-9b-it` and `llama-3.3-70b-versatile` in
> 2026. This project uses their recommended replacements. If you swap in a different
> model (e.g. a newer Qwen release), just update `GROQ_MODEL` / `GROQ_FALLBACK_MODEL`
> in `backend/.env` — no code changes needed. Always check
> [console.groq.com/docs/models](https://console.groq.com/docs/models) for the current
> supported list.

### The 6 LangGraph Tools

| Tool | Writes to DB? | Purpose |
|---|:---:|---|
| **`stage_interaction`** | ❌ | Extracts structured fields from free text and returns them as a **draft only** — powers live form auto-fill without saving anything. Called on the first description and on every correction. |
| **`log_interaction`** *(required)* | ✅ | Performs the final save. Only called after the rep's explicit approval; composes the full interaction from everything discussed in the conversation. |
| **`edit_interaction`** *(required)* | ✅ | Modifies an already-saved record by id (sentiment correction, adding outcomes, etc.) — also approval-gated. |
| **`search_interactions`** | ❌ | Looks up interaction history, optionally filtered by HCP name — powers "when did I last meet Dr. Sharma?". |
| **`suggest_followups`** | ❌ | Proposes 2–4 concrete next steps for a saved interaction — mirrors the "AI Suggested Follow-ups" panel. |
| **`summarize_voice_note`** | ❌ | Cleans a raw dictated transcript into a professional summary before staging/logging. |

---

## 2. What the UI shows you

| State | Where | What it looks like |
|---|---|---|
| **Draft staged, not saved** | Chat bubble + form | Grey chat bubble with quick actions **"✅ Confirm & Log"** / **"✏️ Keep editing"**; form shows an amber "Draft staged — not yet saved" badge |
| **Saved successfully** | Chat bubble + form | Chat bubble turns **light green** with a checkmark; form shows a green **"✓ Interaction saved successfully"** banner |
| **Sentiment radios** | Form | Auto-select correctly based on agent-extracted sentiment (emoji labels are cosmetic only — the underlying value always matches the backend's `Positive`/`Neutral`/`Negative` exactly) |

---

## 3. Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Redux Toolkit, Tailwind CSS, Vite, Google Inter font |
| Backend | Python, FastAPI |
| AI Agent | LangGraph (`create_react_agent`) |
| LLMs | Groq — `openai/gpt-oss-120b` (primary) & `qwen/qwen3.6-27b` (context/reasoning) |
| Database | PostgreSQL (Dockerized), SQLAlchemy ORM |
| Infra | Docker + Docker Compose |

---

## 4. Running the Project — One Command (Docker)

### Prerequisites
- Docker & Docker Compose installed
- A free Groq API key from https://console.groq.com

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/ajaysah-ai/<repo-name>.git
cd <repo-name>

# 2. Configure your Groq API key
cp backend/.env.example backend/.env
# open backend/.env and paste your GROQ_API_KEY

# 3. Run everything — Postgres + backend + frontend
docker compose up --build
```

That's it. Once containers are healthy:

- **Frontend (Log Interaction Screen):** http://localhost:5173
- **Backend API docs (Swagger):** http://localhost:8000/docs
- **Postgres:** localhost:5432 (user: `hcp_admin`, password: `hcp_password`, db: `hcp_crm`)

Postgres data persists across restarts via the `hcp_crm_pgdata` Docker volume.
To stop: `docker compose down` (add `-v` to also wipe the database volume).

### What Docker Compose sets up
- **`db`** — Postgres 16, with a healthcheck so the backend waits until it's ready.
- **`backend`** — FastAPI + LangGraph agent, builds tables automatically on startup,
  connects to Postgres over the internal Docker network.
- **`frontend`** — React app built with Vite and served via Nginx.

---

## 5. Running Without Docker (local dev)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY; DATABASE_URL defaults to local SQLite
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173, backend at http://localhost:8000.

---

## 6. Folder Structure

```
hcp-crm-agent/
├── docker-compose.yml
├── .gitignore
├── README.md
├── TESTING.md                      # full manual test checklist (see section 8)    
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI app, CORS, table creation
│       ├── config.py               # env-based settings (Groq models, DB URL, CORS)
│       ├── database.py             # SQLAlchemy engine/session
│       ├── models.py               # HCP, Interaction, ChatMessage tables
│       ├── schemas.py              # Pydantic request/response models
│       ├── crud.py                 # shared DB logic (used by REST + agent tools)
│       ├── agent/
│       │   ├── llm.py              # Groq ChatGroq wrappers (primary + context model)
│       │   ├── tools.py            # the 6 LangGraph tools
│       │   └── graph.py            # create_react_agent + approval-gated system prompt
│       └── routers/
│           ├── interactions.py     # REST endpoints for the structured form
│           └── chat.py             # /api/chat endpoint for the AI panel
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── .dockerignore
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                    # two-column layout: form + chat
        ├── index.css
        ├── api/client.js               # axios instance
        ├── store/
        │   ├── store.js
        │   ├── interactionSlice.js     # form state, draft/saved status, thunks
        │   └── chatSlice.js            # chat messages (with saved/pendingApproval flags)
        └── components/
            ├── LogInteractionForm.jsx  # structured form + draft/saved banners
            └── ChatAssistant.jsx       # chat panel + quick-approve buttons
```

---

## 7. API Reference (quick view)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/interactions` | Create interaction from the structured form |
| `GET` | `/api/interactions?hcp_name=&limit=` | List/search interaction history |
| `GET` | `/api/interactions/{id}` | Get one interaction |
| `PATCH` | `/api/interactions/{id}` | Edit an interaction |
| `GET` | `/api/interactions/{id}/suggest-followups` | AI follow-up suggestions |
| `POST` | `/api/chat` | Talk to the LangGraph agent — `{session_id, message}` → `{reply, tool_calls, interaction, suggestions, saved, pending_approval}` |
| `GET` | `/api/health` | Health check |

Full interactive docs at `/docs` (Swagger UI) once the backend is running.

---

## 8. Testing

See **`TESTING.md`** for the full manual test checklist — covers the REST API, all 6
tools, the staged-draft → approval → save flow, sentiment auto-fill, cross-panel
(form ⇄ chat) consistency, and Docker persistence.

Everything not requiring a live Groq call (REST CRUD, all 6 tools with a mocked LLM,
the agent's staged/saved parsing logic, and the `/api/chat` route contract) has
already been verified with an automated test pass.

---

## 9. Notes & Design Decisions
- **Approval-gated writes**: `stage_interaction` never touches the database; only
  `log_interaction`/`edit_interaction` do, and only after explicit user approval. This
  avoids ever silently saving something the rep hasn't confirmed.
- **Sync SQLAlchemy over async**: kept the DB layer synchronous for reliability and
  simplicity within the assignment's scope — FastAPI runs sync `def` routes in a
  threadpool automatically, so this doesn't block the event loop under normal load.
- **Two Groq models**: `openai/gpt-oss-120b` drives the agent's main reasoning/tool-routing
  loop and structured-field extraction (fast + cheap). `qwen/qwen3.6-27b` is used only
  where deeper reasoning helps — follow-up suggestions and voice-note cleanup.
- **Enum normalization**: the extraction layer normalizes sentiment/interaction-type
  casing (e.g. `"positive"` → `"Positive"`) so the frontend's exact-string comparisons
  (radio buttons, dropdowns) never silently fail to auto-select.
- **Form ⇄ Chat consistency**: both paths write through the same `crud.py` functions,
  so an interaction logged via chat shows up identically to one logged via the form.
- **LangGraph memory**: `MemorySaver` checkpointer keys conversation state by
  `session_id`, generated per browser tab, so multi-turn chat corrections work — but
  this memory is chat-only. If you edit a field manually in the form after the agent
  staged a draft, the agent won't know about that manual edit when you later approve
  via chat, since it reasons from conversation history, not form state. Keep a single
  chat-driven flow per interaction for the cleanest demo.

---

## 10. What I Learned Building This

I'd already built agentic systems with LangGraph before (my GitHub Automation Agent
uses a multi-graph LangGraph setup with a hybrid RAG tool retriever), so the basic
mechanics of tool-calling agents weren't new to me. What this task pushed me on was
different:

**Designing for trust, not just capability.** My first version of the agent saved
every interaction to the database the moment it extracted enough fields — it worked,
but it was the wrong design for a CRM a rep actually has to trust. Splitting the flow
into `stage_interaction` (preview only) and `log_interaction` (the actual write, gated
behind explicit approval) taught me that "the AI can do it" and "the AI *should* do it
unsupervised" are different questions, especially anywhere a permanent record is being
created. This is the same instinct I'll now carry into any agent that writes to a
real system of record.

**LLMs are non-deterministic, so your contracts can't be.** I hit a real bug where the
LLM would return `"positive"` instead of `"Positive"`, and my frontend's exact-string
comparison for the sentiment radio button silently failed — the field text filled in
fine, but the button just didn't select. That's a class of bug I hadn't thought about
before: when an LLM is the thing populating a UI's state, you have to defensively
normalize its output at the boundary, the same way you'd sanitize any other untrusted
input.

**Testing an agent without hitting the real API is its own skill.** I couldn't verify
the LangGraph/Groq path against real network calls during development, so I learned to
mock the LLM layer itself — faking `ChatGroq.invoke()` responses and fake `ToolMessage`
sequences to unit-test the agent's *parsing logic* (did it correctly mark something as
`saved` vs. `pending_approval`?) completely independent of model quality. That
separation — "is my plumbing correct" vs. "is the model's judgment good" — is something
I'll reuse for every agent I build from now on.

**Model deprecation is a config problem, not a code problem, if you design for it.**
Midway through this task, Groq deprecated both `gemma2-9b-it` and
`llama-3.3-70b-versatile`. Because I kept model names in `.env`/`config.py` rather than
hardcoded in `tools.py` or `graph.py`, swapping to `openai/gpt-oss-120b` and
`qwen/qwen3.6-27b` took one file edit and zero code changes. Small decision, but it's
the kind of thing that only pays off when you actually hit it.

**Docker Compose orchestration for a real multi-service app.** Wiring Postgres →
backend → frontend with healthchecks (so the backend doesn't start hammering a DB
that isn't ready yet) and named volumes (so data survives restarts but can still be
wiped with `-v` for a clean slate) was straightforward individually, but getting the
*sequencing* right — and testing the "one command, clean clone" experience — mattered
more than I expected for making the whole thing actually reviewer-friendly.
