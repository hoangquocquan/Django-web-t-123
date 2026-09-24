# ChatGPT Project Work And Architecture Handoff

Ngay lap: 2026-09-16 Asia/Tokyo

Muc dich file nay: cung cap cho ChatGPT/Codex mot ban tong hop ngan gon nhung du bang chung ve cac cong viec dang lam trong repo `WEB O TO DJANGO`, kien truc du an, trang thai Phase 6A, cac blocker, va cach tiep tuc an toan. File nay khong chua secret, khong chua gia tri `.env`, va khong thay the cac report chi tiet da co.

> Cap nhat checkpoint 2026-09-17: cac muc mo ta Phase 6A chua live-validate
> ben duoi la snapshot lich su tai thoi diem handoff ban dau. Trang thai hien tai
> duoc thay the boi cac report chuyen biet: Phase 6A, 6B, 6C va 6D deu PASS;
> Phase 6E la checkpoint chap nhan cuoi dang duoc thuc hien. Muc tieu van la
> `READY_FOR_PORTFOLIO_PRODUCTION_DEMO`, khong phai public-production certification.

## 1. Du an la gi

Du an la ung dung demo/portfolio production-like cho MecPrecision Vietnam, tap trung vao chuoi nghiep vu:

Customer/Product -> RFQ draft/lines/submission -> quotation creation/submission -> Manager approval/rejection -> customer acceptance/decline -> accepted quotation conversion -> order progress lifecycle -> entity timeline -> global audit.

Backend ung dung chinh la Django. Frontend chinh la React/Vite. PostgreSQL la database bat buoc cho integration/UAT/staging production-like. SQLite chi la fallback cho unit/development.

Muc tieu Phase 6 tong the: dat trang thai `READY_FOR_PORTFOLIO_PRODUCTION_DEMO`, khong phai tuyen bo certified public production.

## 2. Repo va baseline hien tai

- Project root: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Git remote: `https://github.com/hoangquocquan/Django-web-t-123.git`
- Branch: `codex/demo-database-validation`
- Baseline HEAD truoc Phase 6A: `01f15037e64d6c565e8444dc99eee6c9eb7c37f4`
- Subject baseline: `phase5e: repair progress reconciliation evidence matching`
- Trang thai hien tai: Phase 6A-D da PASS theo cac report rieng; toan bo thay doi Phase 5/6 van chua commit va Phase 6E chua tu dong phat hanh.

## 3. Kien truc thu muc chinh

```text
.
├── django_backend/              # Backend Django chinh; manage.py nam tai day
├── figma_make_frontend/         # Frontend React 19 + Vite chinh
├── docker-compose.phase6.yml    # Stack Phase 6A isolated: PostgreSQL, Redis, Django
├── scripts/phase6/              # Start/Stop/Init helper cho Phase 6A
├── docs/phase6/                 # Runbook full-stack local Phase 6A
├── backend/                     # Backend legacy, khong phai duong phat trien moi
├── frontend/                    # HTML/JS legacy, khong phai frontend chinh
├── mecprecision/                # Django prototype cu
├── docker-compose.yml           # Stack broader/base, co n8n; khong dung cho Phase 6A
├── Dockerfile                   # Image Django production-like
└── .github/workflows/ci.yml     # CI da duoc mo rong cho Phase 6A
```

Entrypoint backend: `django_backend/manage.py`, `config.wsgi:application`.

Entrypoint frontend: `figma_make_frontend/src/main.tsx`.

## 4. Kien truc runtime mong muon

Production-like Phase 6:

```text
Browser
  -> React/Vite or static frontend
  -> same-origin /api
  -> Django canonical API
  -> PostgreSQL
  -> Redis where production settings require it
```

Nguyen tac quan trong:

- Django la application backend duy nhat.
- Static server/reverse proxy duoc phep chi de serve asset/proxy `/api`, khong phai backend thu hai.
- Frontend dung root-relative API paths, vi du `/api/v1/canonical/` va `/api/v1/foundation/auth/`.
- Phase 6A Vite dev server proxy chi `/api` toi Django loopback.
- Phase 6A Docker resource phai co prefix `django-web-t-123-phase6`.
- Khong dung stack base `docker-compose.yml` cho Phase 6A vi stack do co cac service ngoai pham vi nhu n8n.

## 5. Backend architecture

Backend chinh nam trong `django_backend/`.

Thanh phan quan trong:

- `config/settings/base.py`, `development.py`, `production.py`, `test.py`: split settings.
- `apps/api/`: canonical API routes, views, permissions, command services.
- `apps/foundation/`: auth, roles, permissions, token/session domain.
- `apps/business_core/`: customer/product/material master data.
- `apps/sales/`: RFQ and quotation domain.
- `apps/transaction_domain/`: order domain and progress lifecycle.
- `apps/common/`: security, logging, observability, middleware, shared guards.
- `apps/core/`: health/liveness/readiness endpoints.

Canonical command/read model:

- Reads and commands are routed under `/api/v1/canonical/`.
- Commands enforce exact permissions, active user, active role, data-contract checks, idempotency, state validation, and audit evidence.
- Legacy write surfaces are being contained so MVP_V1 records cannot be changed through old routes/services.

## 6. Frontend architecture

Frontend chinh nam trong `figma_make_frontend/`.

Thanh phan quan trong:

- `src/main.tsx`: React entrypoint.
- `src/App.tsx`: current large app shell and workspaces.
- `src/api/canonical.ts`: canonical API transport/client.
- `src/api/foundation.ts`: auth/foundation client.
- Workspace/UI slices da co cho RFQ, quotation, order flow.
- `vite.config.ts`: imports Phase 6A server config.
- `phase6.config.ts`: loopback-only `/api` proxy config.
- `phase6.config.test.ts`: test cho routing/proxy config.

Trang thai frontend:

- Phase 5A-E frontend tests van pass theo report.
- Frontend da co canonical RFQ/quotation/order screens o muc dang ke.
- Mot so public/admin/CRM/dashboard screens con prototype/hard-coded, khong duoc xem la live canonical data trong Phase 6.

## 7. Phase roadmap tong quat

### Phase 3-4

Backend/domain foundation:

- Phase 3B/3C/3D: PostgreSQL validation, master data/RFQ, quotation, order progress/audit domain.
- Phase 4A-4D: canonical read/command API, quotation-to-order conversion, order progress audit API, write boundary analysis.

### Phase 5

Frontend canonical workflow foundation:

- Phase 5A: canonical frontend foundation.
- Phase 5B: login and RFQ read integration.
- Phase 5C: RFQ draft/line/submission UI.
- Phase 5D: quotation lifecycle UI.
- Phase 5E: order conversion, progress, audit UI.

### Phase 6

Production-like release hardening:

- Phase 6A: isolated full-stack foundation and legacy write-boundary closure.
- Phase 6B: complete canonical workflow UI and PostgreSQL browser E2E.
- Phase 6C: Owner UAT, accessibility, session validation.
- Phase 6D: staging, operations, release readiness.
- Phase 6E: final Owner acceptance/release checkpoint.

## 8. Phase 6A implemented work

Phase 6A source implementation has been added but not committed.

Main implemented items:

- Isolated Compose file: `docker-compose.phase6.yml`
- Env template: `.env.phase6.example`
- Phase 6A helpers:
  - `scripts/phase6/Initialize-Phase6Environment.ps1`
  - `scripts/phase6/Start-Phase6.ps1`
  - `scripts/phase6/Stop-Phase6.ps1`
- Frontend loopback proxy:
  - `figma_make_frontend/phase6.config.ts`
  - `figma_make_frontend/phase6.config.test.ts`
  - `figma_make_frontend/vite.config.ts`
- Backend liveness/readiness:
  - `django_backend/apps/core/views.py`
  - `django_backend/apps/core/urls.py`
- Legacy write boundary:
  - `django_backend/apps/common/legacy_write_boundary.py`
  - updates in business, sales, transaction services
- Production/development config hardening:
  - `django_backend/config/settings/production.py`
  - `django_backend/config/settings/development.py`
- Tests:
  - `django_backend/apps/api/tests/test_phase6a_legacy_write_boundary.py`
  - `django_backend/apps/core/tests/test_phase6a_configuration.py`
- Docs:
  - `docs/phase6/LOCAL_FULL_STACK.md`
  - `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`
  - `PHASE_6A_ACCIDENTAL_DOCKER_PRUNE_READ_ONLY_ASSESSMENT_REPORT.md`

## 9. Phase 6A validation status

Static/unit validation da pass theo report:

- `pnpm run test:phase6a`: 4 passed
- Full frontend tests: 124 passed
- Frontend typecheck/build/format checks passed
- Phase 6A backend focused tests: 17 passed
- Full backend pytest: 232 passed, 151 skipped
- Django check: passed
- Migration consistency: passed
- PowerShell parser: passed
- Compose config parser: passed
- CI YAML parser: passed
- `git diff --check`: passed voi CRLF warnings only

Live validation chua hoan tat:

- Docker/Phase 6A runtime validation bi block luc dau vi Docker engine khong dap ung.
- Sau do Owner vo tinh chay `wsl --shutdown` va Docker prune commands.
- Read-only assessment ngay 2026-09-15 cho thay Docker Desktop da responsive lai, cac volume quan trong cua `mecprecision-vietnam` va AI Factory staging con ton tai.
- Phase 6A containers/networks/volumes hien khong con ton tai; co the recreate.
- Phase 6A van chua co bang chung PostgreSQL migration smoke, `/api/v1/phase6/live/`, `/api/v1/phase6/ready/`, Vite browser-equivalent smoke.

Ket luan hien tai:

- Source: co ve intact.
- Static tests: pass.
- Runtime/live validation: chua pass.
- Verdict gan nhat cho Phase 6A implementation: `BLOCKED_PHASE_6A`.
- Verdict gan nhat sau Docker prune assessment: `SAFE_TO_PREPARE_RECOVERY`.

## 10. Docker/resource situation

Do not assume Docker state is clean.

Theo read-only assessment:

- Docker Desktop responsive lai.
- Running Compose project con thay: `mecprecision-vietnam`.
- Running containers:
  - `mecprecision-vietnam-web-1`
  - `mecprecision-vietnam-n8n-1`
  - `mecprecision-vietnam-database-1`
  - `mecprecision-vietnam-redis-1`
  - `mecprecision_phase10_dryrun_postgres`
- Phase 6A resources `django-web-t-123-phase6-*` khong con present.
- AI Factory staging named volumes con ton tai.
- Phase 6A default Django port 8000 co the conflict voi Docker-level published port cua `mecprecision-vietnam-web-1`; can Owner approve runtime/port coordination truoc khi retry live validation.

Forbidden without explicit Owner approval:

- Do not run prune.
- Do not run `wsl --shutdown`.
- Do not restart Docker Desktop.
- Do not stop/remove unrelated containers, networks, volumes.
- Do not run base `docker-compose.yml` for Phase 6A.
- Do not inspect/print `.env` values or secrets.

## 11. Current git/worktree state to preserve

Current intended dirty Phase 6A files include:

```text
.github/workflows/ci.yml
.gitignore
.env.phase6.example
README.md
PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md
PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md
PHASE_6A_ACCIDENTAL_DOCKER_PRUNE_READ_ONLY_ASSESSMENT_REPORT.md
docker-compose.phase6.yml
docs/phase6/
scripts/phase6/
django_backend/apps/common/legacy_write_boundary.py
django_backend/apps/business_core/services.py
django_backend/apps/transaction_domain/services.py
django_backend/apps/sales/services/sales_platform_service.py
django_backend/apps/foundation/services.py
django_backend/apps/core/views.py
django_backend/apps/core/urls.py
django_backend/config/settings/development.py
django_backend/config/settings/production.py
django_backend/apps/api/tests/test_phase6a_legacy_write_boundary.py
django_backend/apps/core/tests/
figma_make_frontend/.gitignore
figma_make_frontend/.env.example
figma_make_frontend/package.json
figma_make_frontend/vite.config.ts
figma_make_frontend/phase6.config.ts
figma_make_frontend/phase6.config.test.ts
```

Do not reset, restore, clean, stash, stage, or commit unless explicitly instructed.

## 12. Important reports to read before continuing

Read in this order:

1. `PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md`
2. `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`
3. `PHASE_6A_ACCIDENTAL_DOCKER_PRUNE_READ_ONLY_ASSESSMENT_REPORT.md`
4. `docs/phase6/LOCAL_FULL_STACK.md`
5. `README.md`

Historical context if needed:

- `PHASE_5_SCOPE_DISCOVERY_AND_IMPLEMENTATION_PLAN.md`
- `PHASE_5A_CANONICAL_FRONTEND_FOUNDATION_IMPLEMENTATION_REPORT.md`
- `PHASE_5B_FOUNDATION_LOGIN_AND_RFQ_READ_INTEGRATION_REPORT.md`
- `PHASE_5C_RFQ_DRAFT_LINE_AND_SUBMISSION_UI_IMPLEMENTATION_REPORT.md`
- `PHASE_5D_CANONICAL_QUOTATION_LIFECYCLE_UI_IMPLEMENTATION_REPORT.md`
- `PHASE_5E_ORDER_CONVERSION_PROGRESS_AND_AUDIT_UI_IMPLEMENTATION_REPORT.md`
- `PHASE_4A_CANONICAL_READ_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4B_MASTER_DATA_RFQ_COMMAND_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4C_QUOTATION_ORDER_CONVERSION_COMMAND_API_IMPLEMENTATION_REPORT.md`
- `PHASE_4D_ORDER_PROGRESS_AUDIT_API_AND_WRITE_BOUNDARY_REPORT.md`

## 13. How to continue safely

Recommended next task:

1. Keep task read-only until Docker/ports/resources are reclassified.
2. Confirm no unrelated container/volume would be affected.
3. Decide with Owner whether to:
   - keep `mecprecision-vietnam` running and use explicit alternate Phase 6A ports; or
   - schedule a safe window where `mecprecision-vietnam` can be paused by Owner.
4. Rerun Phase 6A live validation only through `scripts/phase6/Start-Phase6.ps1`.
5. Use only `scripts/phase6/Stop-Phase6.ps1` for Phase 6A cleanup.
6. If live validation passes, create a new live validation report before any review/checkpoint.

Important: do not silently choose new ports, do not stop unrelated processes, and do not mutate business workflow data during validation.

## 14. Commands commonly used

Static checks already used:

```powershell
Set-Location figma_make_frontend
pnpm run test:phase6a
pnpm run test
pnpm run typecheck
pnpm run build
pnpm run format:check:phase6a
```

```powershell
Set-Location django_backend
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
python -m pytest -q
```

Phase 6A helpers:

```powershell
.\scripts\phase6\Initialize-Phase6Environment.ps1
.\scripts\phase6\Start-Phase6.ps1
.\scripts\phase6\Stop-Phase6.ps1
```

Never print `.env.phase6` contents.

## 15. Security/auth policy

Current chosen policy for Phase 6 portfolio demo:

- Memory-only opaque Bearer token in frontend.
- No localStorage/sessionStorage token persistence.
- Server-enforced expiry.
- No silent refresh.
- Fixed fictional demo roles: Admin, Sales, Manager.
- Django cookies/CSRF remain configured for Django cookie-backed surfaces.
- 2FA exists only as future/dormant concept; do not claim it is active.
- All demo data must be fictional.
- No real customer credentials, PII, API keys, tokens, or passwords in repo or reports.

## 16. What is out of scope until Phase 6 is complete

Do not add or integrate:

- AI/OCR/chatbot/forecasting
- n8n/Zalo/AI FACTORY/external automation
- real payments
- microservices
- second application backend
- real customer data or production credentials
- unrelated public/CRM/dashboard product expansion

These exist historically in repo/docs but are explicitly excluded from current Phase 6 workflow unless Owner gives a separate task.

## 17. Open blockers and risks

- Phase 6A live PostgreSQL/runtime/browser smoke not completed.
- Docker state changed after accidental prune; runtime recovery must be cautious.
- `mecprecision-vietnam` currently owns broader Docker runtime and may conflict with Phase 6A default port 8000.
- Some Docker volumes are ambiguous/unrelated; no broad cleanup.
- Frontend still has prototype/hard-coded surfaces outside canonical workflow.
- Phase 6B still needs full browser E2E from customer/product through global audit.
- Phase 6C-D-E not started.

## 18. Suggested prompt for next ChatGPT/Codex task

Use this only after Owner decides how to handle current Docker runtime/ports:

```text
TASK: Continue Phase 6A live runtime validation only.

Read first:
- CHATGPT_PROJECT_WORK_AND_ARCHITECTURE_HANDOFF.md
- PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md
- PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md
- PHASE_6A_ACCIDENTAL_DOCKER_PRUNE_READ_ONLY_ASSESSMENT_REPORT.md
- docs/phase6/LOCAL_FULL_STACK.md

Rules:
- Do not read or print .env.phase6 values.
- Do not stop/remove unrelated Docker resources.
- Reclassify Docker containers/networks/volumes/ports before any mutation.
- If default ports conflict, stop and ask Owner; do not silently choose ports.
- Use only scripts/phase6/Start-Phase6.ps1 and Stop-Phase6.ps1 for Phase 6A runtime.
- If live validation passes, create PHASE_6A_LIVE_RUNTIME_VALIDATION_REPORT.md.
- Do not stage, commit, push, deploy, or start Phase 6B.
```

## 19. Final note

This repo is currently in a useful but delicate state: Phase 6A source work is present and static evidence is strong, but runtime evidence is incomplete. The safest posture is to preserve the worktree, avoid Docker cleanup, and finish Phase 6A live validation only after explicit Owner coordination on Docker/ports.
