# Bao Cao Tong The Du An MecPrecision Vietnam

Ngay lap: 2026-09-19  
Du an: `WEB O TO DJANGO` / `MecPrecision Vietnam`  
Project root: `C:\Users\hoang\Documents\ChatGPT\WEB O TO DJANGO`  
Branch hien tai: `codex/demo-database-validation`  
HEAD hien tai: `8458ab7be25a3efd1c553b10d9875fdc484c5816`

## 1. Tom Tat Dieu Hanh

Day la nen tang Django + React/Vite cho demo portfolio production-like cua MecPrecision Vietnam, mo phong va van hanh cac quy trinh kinh doanh chinh cua mot doanh nghiep co khi chinh xac:

- quan ly nguoi dung, role, permission;
- master data: customer, material, part/product, warehouse;
- CRM/sales pipeline;
- RFQ lifecycle;
- quotation lifecycle;
- order conversion va order progress;
- audit/timeline;
- knowledge/RAG va AI Sales Assistant advisory-only;
- Phase 6 local production-like runtime voi PostgreSQL, Redis, Django va static frontend gateway.

Trang thai tong quan moi nhat:

```text
READY_FOR_PORTFOLIO_PRODUCTION_DEMO
LOCAL_PRODUCTION_LIKE_DEMO_DATA_READY
NOT_PUBLIC_PRODUCTION_CERTIFIED
```

Du an da co release candidate Phase 6 pass local/remote CI theo bao cao truoc, va gan day da duoc bo sung bo du lieu FULL production-like vao local demo DB, sau do sua cac blocker RAG/timestamp/reporting de dat verdict:

```text
LOCAL_PRODUCTION_LIKE_DEMO_DATA_READY
```

Du an chua nen duoc goi la public production certified vi chua co cac bang chung ve hosting that, TLS/domain, off-host encrypted backup, monitoring/alerting that, formal security/compliance assessment va production data/accounts.

## 2. Cau Truc Repository

Thu muc chinh:

```text
.
├── django_backend/          # Backend Django chinh
├── figma_make_frontend/     # Frontend React 19 + Vite chinh
├── docs/                    # Tai lieu migration, operations, review
├── scripts/                 # Script Phase 6 va van hanh
├── docker/                  # Docker/Nginx config
├── docker-compose.yml       # Stack production-like chung co Django/Postgres/Redis/n8n
├── docker-compose.phase6.yml# Stack Phase 6 isolated demo
├── backend/                 # Legacy/cache/history, khong phai duong phat trien moi
├── frontend/                # Legacy HTML/JS
└── mecprecision/            # Django prototype cu
```

Entrypoint quan trong:

- Backend: `django_backend/manage.py`
- Django settings development: `config.settings.development`
- Django settings production: `config.settings.production`
- WSGI: `config.wsgi:application`
- Frontend entrypoint: `figma_make_frontend/src/main.tsx`
- Canonical frontend app: `figma_make_frontend/src/App.tsx`
- Phase 6 runtime: `docker-compose.phase6.yml`

## 3. Cong Nghe Su Dung

Backend:

- Python 3.12 target
- Django 5.2.x
- Django REST Framework
- PostgreSQL 16 cho production-like runtime
- Redis 7 cho cache/readiness
- Gunicorn, WhiteNoise
- pytest, pytest-django, Faker

Frontend:

- React 19
- TypeScript
- Vite 8
- React Router
- Tailwind/Vite integration
- Node test runner
- oxfmt
- pnpm lockfile

Operations/runtime:

- Docker Compose
- Nginx static gateway Phase 6D
- PowerShell operational scripts
- GitHub Actions CI
- n8n trong stack base

AI/Knowledge:

- KnowledgeDocument/KnowledgeChunk/KnowledgeEmbedding
- Local deterministic development hash embedding for local demo
- Ollama integration paths remain present for production-like/AI scenarios
- AI Agent tools are read-only/advisory by design for sales/knowledge paths

## 4. Pham Vi San Pham

### 4.1 Workflow canonical

Workflow nghiep vu chinh da duoc trien khai va kiem thu qua cac phase:

```text
Login
  -> RFQ draft
  -> add/update RFQ lines
  -> submit RFQ
  -> Manager technical review
  -> READY_TO_QUOTE
  -> create quotation
  -> submit quotation
  -> approve/reject
  -> send quotation
  -> customer accept/decline
  -> convert accepted quotation to order
  -> order progress / hold / resume / complete / cancel
  -> entity timeline va global audit
```

### 4.2 Module backend chinh

- `foundation`: user, role, permission, auth/session primitives
- `business_core`: customer, material, part/product, inventory primitives
- `sales`: RFQ, RFQ lines/documents, technical review, quotation lifecycle
- `transaction_domain`: order conversion, progress events, audit events
- `api`: REST/canonical API adapters
- `knowledge`: document ingestion, chunking, embeddings, search, health
- `ai_agent`: read-only tools, sales assistant, agent orchestration
- `core`: health, seed command, demo DB validation, production-like seed
- `crm`: customer profile, interactions, notes, tasks, timeline
- `website`, `admin_ui`, `business_ui`, `catalog`, `cms`, `newsletter`: cac be mat bo tro/legacy/domain khac

### 4.3 Frontend canonical

Frontend chinh nam trong `figma_make_frontend/` voi cac workspace quan trong:

- RFQ workspace
- Quotation workspace
- Order workspace
- Phase 5/6 canonical API client/tests

Nguyen tac frontend:

- token auth luu trong memory;
- API root-relative/proxy-safe;
- khong retry mutation mu quang;
- idempotency key chi dung cho command can idempotency;
- ambiguous write can reconciliation bang read authoritative;
- khong hien raw diagnostics/secret cho user.

## 5. Trang Thai Phase Va Lich Su Trien Khai

### Phase 1-2

- On dinh project.
- Dong baseline tests.
- Xac lap business domain contract.

### Phase 3

- Master data, RFQ, quotation, order/progress/audit domain.
- Schema va migration plan.
- PostgreSQL validation.

### Phase 4

- Canonical read API.
- Canonical command API cho master data/RFQ/quotation/order.
- Write boundary chan cac duong legacy khong canonical.

### Phase 5

- React canonical frontend foundation.
- Login va RFQ read integration.
- RFQ draft/line/submit UI.
- Quotation lifecycle UI.
- Order conversion/progress/audit UI.

### Phase 6

- Local full-stack runtime voi PostgreSQL/Redis/Django/static gateway.
- Browser E2E canonical workflow.
- Owner UAT, accessibility, responsive/session/role validation.
- Staging-like operations, backup/restore, recovery drills.
- Final acceptance checkpoint.

Trang thai Phase 6 theo report:

```text
READY_FOR_PORTFOLIO_PRODUCTION_DEMO
```

## 6. Production-Like FULL Local Demo Data

Gan day du an duoc bo sung bo seed production-like profile FULL:

- 30 production-demo users
- 200 customers
- 100 materials
- 600 parts/products
- 4 warehouses
- 900 inventory items
- 3,000 inventory transactions
- 700 leads
- 350 opportunities
- 4,000 sales activities
- 2,000 follow-ups
- 1,500 RFQs
- 5,000 RFQ lines
- 1,585 RFQ documents
- 990 quotations
- 450 canonical orders
- 1,935 order progress events
- 200 knowledge documents
- 10,601 knowledge chunks
- 10,601 knowledge embeddings
- 150 FULL AI eval cases

Owner decision:

- 450 canonical orders duoc chap nhan.
- Khong tao them 50 order chi de dat target 500.
- RFQ `QUOTED` van omitted.
- Quotation `EXPIRED` van omitted.
- Knowledge `admin` vs `Admin` role casing van la issue rieng.

Local corrective verification moi nhat:

```text
FINAL VERDICT: LOCAL_PRODUCTION_LIKE_DEMO_DATA_READY
```

Da sua cac blocker:

- 2 quotation timestamps o tuong lai: da sua, con 0.
- RAG provider/index/search mismatch: da can chinh ve deterministic local hash provider trong development.
- `actual_ai_eval_cases`: da dung FULL profile, report 150.

RAG local demo hien tai:

- active provider: `development-hash-fallback`
- model: `local-hash-embedding`
- dimension: 32
- threshold: 0.33
- required searches return owned relevant sources:
  - CNC first article inspection
  - SUS304 quotation requirements
  - RFQ drawing requirement
  - quotation approval policy
  - order delivery procedure

## 7. AI, Knowledge Va RAG

Knowledge stack gom:

- `KnowledgeDocument`
- `KnowledgeChunk`
- `KnowledgeEmbedding`
- `KnowledgeService`
- `KnowledgeSearchService`
- `KnowledgeRuntimeHealthService`
- `KnowledgeIndexer`

Da bo sung behavior moi:

- development settings mac dinh dung deterministic hash embedding cho local demo;
- search co lexical rerank nho de giam hash-collision trong demo;
- runtime health bao cao active embedding signature, stored signatures va incompatible signatures.

AI/Sales behavior da verify:

- customer summary: populated
- lead summary: populated
- sales pipeline summary: populated
- inventory summary: populated
- knowledge search: populated
- Sales Assistant lead analysis/email draft/weekly recommendation: populated
- `human_approval_required=true`
- `autonomous_action=false`
- email draft chi la `draft_only_not_sent`
- AI read smoke khong lam doi DB hash

Gioi han:

- deterministic hash provider phu hop demo local, khong phai semantic retrieval production-grade.
- Production-grade RAG nen dung provider/model/index nhat quan nhu Ollama/pgvector sau khi co runtime health va reindex bang cung provider.

## 8. Runtime Va Operations

### 8.1 Base Compose

`docker-compose.yml` gom:

- Django web container
- PostgreSQL database
- Redis
- n8n
- media/postgres/redis/n8n volumes

Stack nay dung production settings va yeu cau cac secret qua environment. Khong nen in `.env` hoac secret ra report.

### 8.2 Phase 6 Compose

`docker-compose.phase6.yml` la stack isolated cho portfolio demo:

- `postgres`: PostgreSQL 16
- `redis`: Redis 7 authenticated
- `django`: production settings, read-only container, non-root, healthcheck ready
- `frontend`: Nginx static gateway, read-only, non-root
- private network: `django-web-t-123-phase6-internal`
- named volumes: postgres data va media

Ports mac dinh co the map loopback:

- Django: 8000 hoac 8001 theo script
- Frontend static gateway: 8443

Runbook quan trong:

- `docs/phase6/LOCAL_FULL_STACK.md`
- `docs/phase6/OPERATIONS.md`
- `docs/phase6/BACKUP_RESTORE.md`
- `docs/phase6/RELEASE_CHECKLIST.md`

Nguyen tac operations:

- khong Docker prune;
- khong dung base compose khi Phase 6 procedure yeu cau stack rieng;
- khong dung/cham resource Docker khong thuoc Phase 6;
- cleanup giu volumes khi can bao ton DB/media.

## 9. Test Va Validation

Bang chung lich su tu master report:

- frontend full suite: 142 passed
- typecheck: PASS
- Vite build: PASS
- backend focused suite: 86 passed, 8 skipped
- backend full pytest lich su: 242 passed, 151 skipped
- remote CI commit `8458ab7be25a3efd1c553b10d9875fdc484c5816`: PASS

Bang chung moi nhat sau corrective local demo:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest apps/core/tests/test_production_demo_seed.py -q
```

Ket qua:

```text
System check identified no issues (0 silenced).
No changes detected
15 passed in 355.45s (0:05:55)
```

Nhung test moi/quan trong:

- profile-specific AI eval counts: TEST 20, SMALL 60, FULL 150
- FULL future quotation timestamp guard
- representative chronology RFQ -> quotation -> decision/sent -> order
- RAG retrieval validation set
- no-answer probes
- embedding compatibility health diagnostic
- FULL apply/history/idempotency

## 10. Git Status Hien Tai

Hien tai co dirty/untracked worktree. Chua co staged files.

Modified tracked files:

- `django_backend/apps/knowledge/services/runtime_health.py`
- `django_backend/apps/knowledge/services/search_service.py`
- `django_backend/config/settings/development.py`
- `figma_make_frontend/src/App.tsx`
- `figma_make_frontend/src/api/phase6c.test.ts`

Untracked files/folders chinh:

- `PROJECT_MASTER_REPORT_FOR_CHATGPT.md`
- `PRODUCTION_LIKE_DATA_SEED_PLAN.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md`
- `PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md`
- `PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md`
- `PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md`
- `BAO_CAO_TONG_THE_DU_AN.md`
- `django_backend/apps/core/management/commands/seed_production_demo.py`
- `django_backend/apps/core/production_demo_seed/`
- `django_backend/apps/core/tests/test_production_demo_seed.py`

Local database:

- `django_backend/db.sqlite3` la ignored file.
- Git check-ignore xac nhan ignored theo `django_backend/.gitignore`.

Khuyen nghi truoc khi commit:

- tach rieng commit cho production-like seed/report/corrective;
- tach rieng hoac review ky cac thay doi frontend dang modified tu truoc;
- chay lai test phu hop;
- khong add local SQLite DB.

## 11. Security Va Data Hygiene

Da duoc kiem tra trong cac report gan day:

- seed data dung `.invalid` emails;
- khong co real personal emails trong seed-owned values da check;
- khong phat hien secret-like pattern trong seed package;
- khong track dump/database file;
- AI reads khong mutate business DB;
- command apply yeu cau local/disposable gates:
  - `PRODUCTION_DEMO_SEED_ALLOWED=true`
  - `PRODUCTION_DEMO_SEED_DATABASE_CONFIRMED=local-disposable`

Nhung dieu can tiep tuc tranh:

- khong in secret/env ra terminal/report;
- khong push `.env`, DB dump, SQLite DB, logs;
- khong chay seed apply neu DB target khong ro local/disposable;
- khong flush/drop/reset DB neu chua co yeu cau ro;
- khong sua phase fixture/legacy demo data ngoai scope.

## 12. Han Che Con Lai

Khong block portfolio demo:

- RFQ `QUOTED` omitted do chua co canonical transition xac nhan.
- Quotation `EXPIRED` omitted do chua co canonical V1 transition xac nhan.
- 450 orders accepted theo owner decision.
- Knowledge role casing `admin` vs `Admin` la issue rieng.
- Deterministic hash RAG la local-demo strategy, khong phai production semantic retrieval.

Block public production certification:

- chua co public hosting/domain/TLS validation that;
- chua co off-host encrypted backup/retention automation;
- chua co external monitoring/alerting production;
- chua co formal security/compliance assessment;
- chua co production accounts/data;
- can harden tiep session/logout/revocation theo master report;
- can reconcile mot so tai lieu legacy cu.

## 13. Tai Lieu Quan Trong

Nen doc theo thu tu:

1. `BAO_CAO_TONG_THE_DU_AN.md`
2. `PROJECT_MASTER_REPORT_FOR_CHATGPT.md`
3. `PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md`
4. `PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md`
5. `PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md`
6. `PHASE_6E_FINAL_OWNER_ACCEPTANCE_AND_RELEASE_CHECKPOINT_REPORT.md`
7. `PHASE_6D_STAGING_OPERATIONS_RELEASE_READINESS_REPORT.md`
8. `PHASE_6C_OWNER_UAT_ACCESSIBILITY_SESSION_VALIDATION_REPORT.md`
9. `PHASE_6B_CANONICAL_BROWSER_E2E_IMPLEMENTATION_REPORT.md`
10. `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`
11. `docs/phase6/OPERATIONS.md`
12. `docs/phase6/BACKUP_RESTORE.md`
13. `figma_make_frontend/package.json`
14. `django_backend/apps/api/canonical_urls.py`

## 14. De Xuat Viec Tiep Theo

### Uu tien 1: Git hygiene va commit planning

- Xac dinh file nao thuoc seed/corrective task.
- Xac dinh file frontend modified co lien quan task nao.
- Chay test tuong ung.
- Commit theo nhom hop ly neu owner cho phep.

### Uu tien 2: Documentation reconciliation

- Cap nhat README va handoff cu de phan biet:
  - canonical React app;
  - Django public website;
  - legacy frontend/backend/prototype.
- Cap nhat trang thai local demo FULL ready.

### Uu tien 3: Knowledge/Admin role casing

- Xu ly rieng issue `admin` vs `Admin`.
- Them regression permission cho knowledge restricted/internal access.

### Uu tien 4: Production-grade RAG option

- Neu can demo AI semantic tot hon deterministic hash:
  - confirm Ollama health;
  - reindex owned knowledge bang cung Ollama provider;
  - verify dimensions/model/provider match;
  - them no-answer confidence behavior.

### Uu tien 5: Public production planning

Chi lam khi owner muon vuot qua portfolio demo:

- TLS/domain/load balancer;
- managed DB/cache;
- object storage/media;
- encrypted off-host backups;
- monitoring/alerting;
- formal security review;
- rollback rehearsal.

## 15. Ket Luan

Du an hien co nen tang backend/frontend kha day du cho portfolio production-like demo. Canonical workflow RFQ -> quotation -> order da duoc trien khai qua nhieu phase, Phase 6 runtime da co bang chung operations, va local FULL production-like dataset hien da dat verdict ready.

Trang thai dung de truyen thong:

```text
Portfolio production-like demo: READY
Local FULL demo data: READY
Public production certification: NOT YET
```

Khuyen nghi khong mo rong claim thanh public production neu chua hoan thanh cac muc operations/security/hosting that neu tren.
