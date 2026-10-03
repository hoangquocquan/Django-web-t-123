# ChatGPT Handoff Report - MecPrecision Vietnam AI Demo

Date: 2026-09-19
Branch: `codex/demo-database-validation`
Workspace: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`

## Purpose

This report summarizes the real local demo attempt for three AI features of the MecPrecision Vietnam project on the current branch, using the existing FULL local data and cross-checking against:

- `BAO_CAO_TONG_THE_DU_AN.md`
- `PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md`

No database reset, destructive seed, branch merge, GitHub push, or public deployment was performed.

## Pre-Run Safety Check

- Git branch: `codex/demo-database-validation`
- Working tree was already dirty before the demo. Existing modified/untracked files were preserved.
- Target database: local SQLite database at `django_backend/db.sqlite3`
- Database counts observed before demo:
  - `KnowledgeDocument`: 200
  - `KnowledgeDocument(permission_level="public")`: 0
  - Sales leads: 700
- Django health/check:
  - `python manage.py check`: PASS
  - Local API health after startup: `http://127.0.0.1:8000/api/v1/health/`: HTTP 200
- Frontend after startup:
  - `http://127.0.0.1:5173`: HTTP 200
- Redis:
  - No local Redis process/service was observed during this demo.
- Ollama:
  - Ollama daemon was running.
  - Installed local models included `qwen2.5-coder:7b` and `deepseek-r1:8b`.
  - Django default configuration still attempted to use `llama3`, which was not installed, causing Ollama HTTP 404 for the AI Sales default path.

Important distinction: the FULL dataset contains 150 evaluation cases according to the project reports. This demo did not rerun all 150 cases. Only the checks described in this report were actually executed during this handoff.

## Feature 1 - AI Sales

Status: BLOCKED for end-to-end UI demo; backend advisory path partially worked with fallback.

URL inspected:

- `http://127.0.0.1:5173/#/sales-ai`

Actual UI result:

- The page rendered successfully.
- The visible AI Sales screen is currently static/mock content.
- The input/button on the page did not call the backend AI Sales API during this demo.
- The static UI showed fixed examples such as Samsung SDI, Thaco, and Viettel, not the actual backend lead selected from the local demo database.

Backend input used for real service check:

- Lead id: `3`
- Company: `[PDV1] Sales Lead 3`
- Contact: `Demo Lead Contact 3`
- Industry: Medical Fixture
- Status: quotation
- Priority: low
- Notes: production demo dataset

Backend result observed:

- Lead score: 79
- Grade: B
- Recommendation summary: verify technical need, drawings, material, quantity, tolerance, and delivery timeline.
- Email draft was generated as draft-only text.
- Safety flags indicated human approval is required and autonomous execution is false.
- No email was sent.
- No business record update was performed by the demo action.

Ollama/fallback distinction:

- Default Django AI Sales config called `llama3`, but that model was not installed in Ollama.
- Result therefore fell back to a deterministic/source-based fallback.
- A separate direct test showed `qwen2.5-coder:7b` can answer a simple prompt through Ollama, but the AI Sales structured JSON response path rejected its output as invalid JSON.
- Therefore this feature cannot be reported as "Ollama successfully generated the Sales result" in the current configuration.

Weekly work suggestion result:

- Backend returned advisory suggestions based on local lead/opportunity data.
- Example guidance included prioritizing contacted/meeting-stage leads and reviewing high-value opportunities with low probability.
- This was backend-only evidence, not an end-to-end UI interaction.

Remaining blocker:

- Frontend `sales-ai` screen is not wired to the live backend AI Sales response.
- Ollama model configuration and structured JSON validation need correction before claiming Ollama-backed Sales AI PASS.

## Feature 2 - Internal Document Assistant

Status: BLOCKED for required demo path.

Required user scenario:

- Login with a suitable demo account.
- Ask at least three questions about CNC, RFQ, and quotation process.
- Show answers, source documents, confidence, and warning.
- Ask one out-of-scope question and verify the assistant refuses to invent an answer.

Actual finding:

- The FULL seed demo accounts observed in code are not directly login-ready because they are created with unusable passwords.
- The expected demo password environment variable was not available in the current local environment.
- The inspected frontend `sales-docs` page is a static Document Intelligence/upload-style mock, not a chat assistant UI with source citations.

URL inspected:

- `http://127.0.0.1:5173/#/sales-docs`

Actual UI result:

- Page rendered successfully.
- It showed a static document extraction form/result.
- It did not provide a real internal assistant chat flow for CNC/RFQ/quotation questions.

Read-only backend evidence:

- Local knowledge database exists and contains 200 knowledge documents and 10,601 chunks/embeddings according to the reports.
- A live search check for CNC-related content returned relevant local source context, including `[PDV1] CNC milling capability 1`.
- Historical corrective report evidence shows prior successful retrieval for CNC, SUS304 quotation, RFQ drawing, quote approval, and delivery-process queries, plus no-answer behavior for out-of-scope queries.

Important distinction:

- The above historical report evidence is not the same as this demo running three live authenticated chat questions through the UI.
- Because login and UI chat surface were blocked, this feature remains BLOCKED for the requested end-to-end demo.

Remaining blocker:

- Provide or enable a real demo login credential.
- Wire or expose the internal knowledge chat UI with answer/source/confidence/warning fields.
- Then run the three in-scope questions and one out-of-scope question through the UI.

## Feature 3 - Public AI Chatbot

Status: BLOCKED / insufficient data for public chatbot demo.

Pre-check result:

- `KnowledgeDocument(permission_level="public")`: 0
- No internal document permission was changed to public.

URL inspected:

- `http://127.0.0.1:5173/`

Actual UI result:

- Public homepage rendered successfully.
- No public chatbot input/surface was found on the inspected public page.
- Because there are zero public knowledge documents and no visible public chatbot UI, there was not enough data/surface to perform the requested public chatbot demo.

Security/privacy result:

- No internal knowledge document was exposed through a chatbot during this demo.
- No customer, stock, quote, or internal process data was intentionally made public.
- This is not a full PASS for non-leakage; it is blocked because the public chatbot could not be exercised.

Recommended public documents to prepare:

- Public CNC machining capability overview.
- Public materials and tolerance capability guide.
- Public RFQ intake checklist for customers.
- Public quotation process FAQ without prices, customer names, inventory, supplier details, or internal approval rules.
- Public quality and inspection overview.

## Final Status

| Feature | Status | Reason |
| --- | --- | --- |
| AI Sales | BLOCKED for end-to-end UI; backend fallback partially works | UI is static/mock and not wired to live backend; default Ollama model `llama3` is missing; fallback result must not be called Ollama output. |
| Internal Document Assistant | BLOCKED | No usable demo login credential found; inspected UI is static document extraction mock, not authenticated chat with citations. |
| Public AI Chatbot | BLOCKED | No `permission_level="public"` knowledge documents and no public chatbot UI found. |

## Commands / URLs To Reopen Locally

From `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO\django_backend`:

```powershell
python manage.py runserver 127.0.0.1:8000 --noreload
```

From `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO\figma_make_frontend`:

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Useful local URLs:

- Backend health: `http://127.0.0.1:8000/api/v1/health/`
- Frontend public page: `http://127.0.0.1:5173/`
- AI Sales screen: `http://127.0.0.1:5173/#/sales-ai`
- Document screen: `http://127.0.0.1:5173/#/sales-docs`

## Recommended Next Fixes

1. Configure Django development AI settings to use an installed Ollama model, then verify strict JSON output for AI Sales.
2. Wire the AI Sales frontend to the backend service and display live input/result/safety state.
3. Create or document a real login-ready internal demo account without resetting existing data.
4. Expose the internal knowledge assistant UI with source, confidence, and warning fields.
5. Prepare reviewed public knowledge documents and only then enable a public chatbot route constrained to `permission_level="public"`.

