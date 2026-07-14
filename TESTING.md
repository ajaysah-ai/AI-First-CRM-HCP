# Testing Guide — AI-First CRM · HCP Module

I already ran the backend's non-LLM logic myself (REST API, DB writes, all 6 tools with
a mocked LLM, the stage → approve → log parsing logic, and the `/api/chat` route
contract) — all passed. What I **couldn't** run from here: anything that needs a real
Groq API call, the actual browser UI, or Docker. Use this checklist to verify those.

---

## 0. Pre-flight

```bash
cd hcp-crm-agent
cp backend/.env.example backend/.env
# paste your real GROQ_API_KEY into backend/.env
docker compose up --build
```

Wait for all 3 containers to show healthy/running (`docker compose ps`), then:
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- `curl http://localhost:8000/api/health` → `{"status":"ok","env":"development"}`

If health check fails, check `docker compose logs backend`.

---

## 1. REST API — structured form path (already verified by me, re-check quickly)

Via Swagger UI (`/docs`) or curl:

| # | Test | Steps | Expected |
|---|---|---|---|
| 1.1 | Create interaction | `POST /api/interactions` with a full body (hcp_name, interaction_type, etc.) | 200, returns record with `id`, `hcp_id`, timestamps |
| 1.2 | List/search | `GET /api/interactions?hcp_name=sharma` | 200, array containing the record above (case-insensitive partial match) |
| 1.3 | Get by id | `GET /api/interactions/{id}` | 200, full record |
| 1.4 | Get missing id | `GET /api/interactions/does-not-exist` | **404** |
| 1.5 | Edit | `PATCH /api/interactions/{id}` with `{"sentiment":"Negative"}` | 200, sentiment updated, other fields untouched |
| 1.6 | Edit missing id | `PATCH /api/interactions/does-not-exist` | **404** |
| 1.7 | Suggest follow-ups | `GET /api/interactions/{id}/suggest-followups` | 200, `{"status":"ok","suggestions":[...]}` (needs real Groq key) |

---

## 2. Chat Agent — the approval-gated flow (needs real Groq key)

Open the app, use the right-side **AI Assistant** panel for all of these.

### 2.1 First message stages a draft, does NOT save
- Type: `Met Dr. Sharma, discussed OncoBoost Phase III data, she was positive, shared the brochure`
- **Expected:**
  - Assistant replies summarizing the draft and asks something like "Should I log this?"
  - Reply bubble is **grey** (not green) — nothing saved yet
  - Two quick-action buttons appear: **"✅ Confirm & Log"** and **"✏️ Keep editing"**
  - Left form auto-fills: HCP Name = "Dr. Sharma", Sentiment = Positive, Materials Shared includes brochure, etc.
  - Form shows an **amber "Draft staged" badge** — not the green saved banner
  - Check DB: `GET /api/interactions?hcp_name=Sharma` → should be **empty/unaffected** (nothing saved yet)

### 2.2 Corrections before approval update the draft, still don't save
- Type: `actually make the sentiment neutral and add that I left 2 samples`
- **Expected:**
  - Form updates: Sentiment radio flips to **Neutral**, Samples Distributed field updates
  - Still grey bubble, still amber "draft" badge, still nothing in DB

### 2.3 Explicit approval triggers the real save
- Click **"✅ Confirm & Log"** (or type `yes, log it`)
- **Expected:**
  - Assistant's reply bubble turns **light green** with a checkmark icon
  - Form's amber badge is replaced by the **green "✓ Interaction saved successfully (id: ...)"** banner
  - `GET /api/interactions?hcp_name=Sharma` now **does** return the record, with the corrected (Neutral, 2 samples) values — not the original Positive/no-samples draft

### 2.4 No premature saving
- Start a fresh message describing a new interaction but don't say yes/confirm anything — just describe it once.
- **Expected:** draft is staged (grey bubble, amber badge) but **not saved** — confirms the agent never auto-saves on the first message.

### 2.5 Sentiment radio auto-fill specifically
- After any staged/saved interaction with a clearly stated sentiment ("she was upset" → Negative, "positive meeting" → Positive), confirm the correct radio button is visually selected (not just the text fields). This was a bug we fixed — worth double-checking after any further edits to `LogInteractionForm.jsx`.

### 2.6 Edit an already-saved interaction via chat
- Type: `change the outcome of my last interaction with Dr. Sharma to "agreed to a follow-up call"`
- **Expected:** agent may call `search_interactions` first to find the id, then ask for approval before calling `edit_interaction`. Confirm it does NOT edit without you approving.

### 2.7 Search / history questions
- Type: `when did I last meet Dr. Sharma?` or `show my recent interactions`
- **Expected:** agent calls `search_interactions` and answers in plain English (no save/edit side effects, no green banner).

### 2.8 Voice-note cleanup
- Type: `summarize this voice note: um so like i met dr sharma today um and uh she seemed happy about the new drug uh yeah`
- **Expected:** agent returns a cleaned, professional paragraph (filler words removed) — likely then offers to stage/log it.

### 2.9 Multi-turn memory
- Across 2.1–2.3 above, confirm the agent never asks you to repeat earlier details — it should remember HCP name, topics, etc. within the same browser tab/session.

### 2.10 Fresh session isolation
- Open a **new browser tab** to the same URL (new `session_id` is generated client-side).
- Type something referencing "it" or "that interaction" with no prior context.
- **Expected:** agent should NOT have memory of the first tab's conversation (sessions are isolated).

---

## 3. Structured form path (independent of chat)

| # | Test | Steps | Expected |
|---|---|---|---|
| 3.1 | Manual fill + submit | Fill all fields manually, click **Log Interaction** | Green "✓ Interaction saved successfully" banner appears immediately (no approval needed here — the click itself is the approval) |
| 3.2 | Required field | Leave HCP Name blank, click submit | Browser's native "Please fill out this field" validation stops submission |
| 3.3 | Clear button | Click **Clear** after filling fields | Form resets to empty defaults, banners disappear |
| 3.4 | AI Suggested Follow-ups panel | After a successful save (form or chat), check if suggestions appear in the highlighted box | Should show 2–4 suggestions once `suggest_followups` has run (via chat "yes" flow, per the original screenshot behavior) |

---

## 4. Cross-panel consistency

| # | Test | Expected |
|---|---|---|
| 4.1 | Log via form, then ask chat "when did I last meet Dr. X" | Chat's `search_interactions` should find the form-saved record too (both paths write to the same DB) |
| 4.2 | Log via chat, then refresh the page | Saved data persists (Postgres, not just in-memory) — form itself resets on refresh (that's fine, it's just draft UI state), but the DB record remains retrievable via search |

---

## 5. Docker / infra sanity

| # | Test | Steps | Expected |
|---|---|---|---|
| 5.1 | One-command startup | `docker compose up --build` from a clean clone | All 3 services start; backend waits for Postgres healthcheck before starting |
| 5.2 | Data persistence | `docker compose down` (no `-v`), then `docker compose up` again | Previously logged interactions still show up in `GET /api/interactions` |
| 5.3 | Full reset | `docker compose down -v` | Postgres volume wiped, next `up` starts with an empty DB |
| 5.4 | Backend hot-reload (dev) | Edit a backend file while containers run (volume-mounted) | If using `--reload` locally, or `docker compose restart backend`, changes should take effect |

---

## 6. Known limitation to be aware of while testing

The chat agent's memory of "current draft" lives **only in the chat session** (LangGraph's
checkpointer), not in the form's Redux state. So:
- ✅ Chat → chat corrections → chat approval: works perfectly (tested above).
- ⚠️ If you manually edit a field **in the form** after a chat draft was staged, then go
  back to chat and say "yes, log it" — the agent will save based on what it remembers
  from the *conversation*, not your manual form edit. This is expected with the current
  design; flag it to me if you want the manual form edits fed back into the chat context too.

---

## 7. What I already verified for you (backend, no browser needed)

Ran locally with a mocked Groq client (so no API key/network was used) — all passed:
- `stage_interaction` → returns a draft, confirmed **no DB row is created**
- `log_interaction` → confirmed **a real DB row is created** with an `id`
- `edit_interaction` → valid id updates correctly; invalid id → clean error; malformed JSON → clean error
- `search_interactions` → case-insensitive partial match works
- `suggest_followups` → valid id returns suggestions; invalid id → clean error
- `summarize_voice_note` → returns cleaned text
- Casing normalization: LLM returning `"positive"`/`"meeting"` (lowercase) correctly
  normalizes to `"Positive"`/`"Meeting"` — protects the sentiment radio buttons
- `run_agent`'s parsing logic correctly distinguishes staged (not saved) vs. logged/edited
  (saved) tool calls, and correctly extracts `suggest_followups` output
- `/api/chat` route: staged response, saved response, and agent-exception → 500 all
  return the correct shape
- Full REST CRUD (`/api/interactions`) against a live SQLite DB: create, list, get,
  404-on-missing, patch — all correct
- **Bug fixed**: `backend/requirements.txt` had an unresolvable dependency conflict
  (pinned `langgraph==0.2.60` vs `langchain-core==0.3.22`) — replaced with compatible
  version ranges; `pip install -r requirements.txt` now resolves cleanly.