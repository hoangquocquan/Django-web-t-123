# BÁO CÁO TỔNG HỢP DỰ ÁN DÀNH CHO CHATGPT

Ngày tổng hợp: 2026-09-18 (Asia/Tokyo)  
Dự án: **MecPrecision Vietnam / WEB Ô TÔ DJANGO**  
Repository: `https://github.com/hoangquocquan/Django-web-t-123`  
Project root: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`

## 1. Mục đích của tài liệu

Tài liệu này là bản handoff tổng hợp để gửi cho một phiên ChatGPT/Codex mới. Nó
gom các thông tin quan trọng nhất về sản phẩm, kiến trúc, lịch sử triển khai,
kiểm thử, Git/CI, giới hạn release và các việc nên làm tiếp theo.

Khi dùng tài liệu này, cần phân biệt rõ:

- **trạng thái hiện tại đã xác minh** trong báo cáo này;
- **báo cáo lịch sử** của từng phase, có thể mô tả trạng thái tại thời điểm cũ;
- **portfolio production-like demo**, không đồng nghĩa với public production.

Không đưa giá trị thật của secret, password, bearer token, database dump hoặc
dữ liệu cá nhân vào prompt hay báo cáo tiếp theo.

## 2. Tóm tắt điều hành

Dự án là một nền tảng quản trị và mô phỏng quy trình kinh doanh cho doanh nghiệp
cơ khí chính xác. Backend chính là Django; frontend nghiệp vụ canonical là
React/Vite. Quy trình chính đã được triển khai và kiểm tra xuyên suốt:

```text
Đăng nhập
  -> tạo và gửi RFQ
  -> Manager tiếp nhận/hoàn tất review
  -> tạo quotation
  -> duyệt và gửi quotation
  -> khách hàng chấp nhận hoặc từ chối
  -> chuyển quotation thành order
  -> cập nhật tiến độ/hold/resume/complete/cancel
  -> kiểm tra entity timeline và global audit
```

Phase 5 hoàn thiện giao diện canonical cho workflow. Phase 6 hoàn thiện runtime
PostgreSQL/Redis cô lập, browser E2E, Owner UAT, accessibility, vận hành,
backup/restore và release checkpoint.

Trạng thái release hiện tại:

```text
PUSHED_RECONCILED_RELEASE_CANDIDATE_REMOTE_CI_PASS
READY_FOR_PORTFOLIO_PRODUCTION_DEMO
NOT_PUBLIC_PRODUCTION_CERTIFIED
```

## 3. Trạng thái Git và CI đã xác minh

| Hạng mục | Giá trị |
|---|---|
| Branch | `codex/demo-database-validation` |
| Candidate commit | `eca707aa701afd09037bae24b850c1c9adc6380b` |
| Merge/reconciled HEAD | `8458ab7be25a3efd1c553b10d9875fdc484c5816` |
| Remote HEAD đã xác minh | `8458ab7be25a3efd1c553b10d9875fdc484c5816` |
| Safety branch local | `backup/phase6-pre-remote-merge` |
| Push | Normal push; không force |
| GitHub Actions | PASS |
| CI run | `https://github.com/hoangquocquan/Django-web-t-123/actions/runs/35237995504` |

Quá trình reconcile dùng merge `--no-ff`, không dùng rebase, reset, clean,
stash, amend hoặc history rewrite. Merge không phát sinh Git conflict.

Remote CI đã pass toàn bộ bốn job:

1. Phase 6A runtime syntax;
2. React production build;
3. Django checks and tests;
4. Phase 6A PostgreSQL migration smoke.

CI có cảnh báo không blocking rằng một số GitHub Actions phiên bản `v4`/`v5`
còn khai báo Node.js 20 và đang được runner ép chạy bằng Node.js 24. Đây là việc
nên bảo trì sau, không phải lỗi của release candidate hiện tại.

## 4. Phạm vi sản phẩm

### 4.1 Chức năng nghiệp vụ canonical

- Authentication bằng token trong bộ nhớ trình duyệt.
- Role/permission cho Sales, Manager và Admin.
- Master data: customer, part, material và các selector liên quan.
- RFQ:
  - danh sách và chi tiết;
  - tạo draft;
  - cập nhật header;
  - thêm/sửa/xóa line;
  - submit;
  - review và lifecycle transition.
- Quotation:
  - tạo revision đầu tiên;
  - tạo revision tiếp theo;
  - cập nhật commercial data;
  - submit, approve/reject, send, accept/decline.
- Order:
  - convert từ accepted quotation đúng một lần;
  - progress, hold, resume, complete và cancel;
  - reconciliation sau lỗi mạng/timeout không rõ kết quả.
- Audit:
  - entity-scoped timeline;
  - global audit cho role được phép;
  - không có mutation transport trong audit UI.

### 4.2 Website và bề mặt khác

Repository còn có:

- website public bằng Django templates tại `django_backend/apps/website/`;
- frontend HTML/CSS lịch sử tại `frontend/`;
- các bề mặt admin, business UI, CMS, knowledge và AI có từ các wave trước.

Các bề mặt này không được tự động coi là canonical Phase 6 workflow. Khi sửa
code phải xác định rõ đang làm canonical React app, Django public website hay
một bề mặt legacy/prototype.

## 5. Kiến trúc hiện tại

### 5.1 Thành phần chính

```text
Browser
  |
  |  production-like: http://127.0.0.1:8443
  v
Nginx static gateway (read-only, non-root)
  |-- phục vụ React/Vite production build
  |-- /api/* -> Django:8000
  |-- /media/* -> read-only media volume
  v
Django 5.2 + Django REST Framework
  |-- canonical API và permission/lifecycle contracts
  |-- PostgreSQL là database production-like bắt buộc
  |-- Redis là cache/readiness dependency bắt buộc
  |-- JSON logging và health endpoints
  v
PostgreSQL 16 + Redis 7
```

### 5.2 Runtime source of truth

- Backend chính: `django_backend/`.
- Django entrypoint: `django_backend/manage.py`.
- WSGI entrypoint: `config.wsgi:application`.
- Canonical API root: `/api/v1/canonical/`.
- Health endpoints:
  - `/api/v1/phase6/live/`;
  - `/api/v1/phase6/ready/`.
- Canonical frontend: `figma_make_frontend/`.
- Phase 6 Compose: `docker-compose.phase6.yml`.
- Static gateway: `Dockerfile.phase6-frontend` và
  `docker/phase6/nginx.conf`.

### 5.3 Lưu ý về thư mục legacy `backend/`

Commit remote được merge vào release candidate đã xóa toàn bộ source được Git
theo dõi dưới `backend/`. Nếu máy local vẫn hiện `backend/`, phần còn lại chỉ là
cache Python bị ignore, ví dụ `__pycache__/*.pyc`; đó không phải application
source và không được dùng làm backend.

Một số tài liệu lịch sử như `README.md` và
`CHATGPT_PROJECT_WORK_AND_ARCHITECTURE_HANDOFF.md` vẫn có câu nói `backend/`
được giữ lại. Sau merge, mô tả đó đã cũ. Không khôi phục legacy backend chỉ để
khớp tài liệu; nếu được Owner cho phép, hãy cập nhật tài liệu ở một task riêng.

## 6. Công nghệ

### Backend

- Python;
- Django `5.2.16`;
- Django REST Framework `3.17.1`;
- PostgreSQL qua `psycopg`;
- Redis;
- Gunicorn;
- WhiteNoise;
- pytest + pytest-django.

### Frontend

- React 19;
- TypeScript;
- Vite 8;
- React Router;
- Tailwind/Vite integration;
- Node test runner;
- Oxfmt;
- pnpm lockfile.

### Runtime và CI

- Docker Compose;
- PostgreSQL 16 Alpine;
- Redis 7 Alpine;
- Nginx static gateway;
- PowerShell startup/stop/backup helpers;
- GitHub Actions.

## 7. Backend domain map

Các Django app quan trọng gồm:

- `foundation`: user/session/auth foundation;
- `business_core`: customer, part, material và master data;
- `sales`: RFQ, quotation và sales lifecycle;
- `transaction_domain`: order, workflow, progress và transaction history;
- `api`: canonical và legacy API adapters;
- `core`: health, readiness, metrics và operation endpoints;
- `website`: public Django website;
- `admin_ui`, `business_ui`, `catalog`, `cms`, `crm`, `knowledge`, `ai`,
  `ai_agent`, `newsletter`: các module từ phạm vi rộng hơn của repository.

Canonical read/write logic phải đi qua API và domain service đã định nghĩa.
Không thêm đường ghi song song vào legacy API. Phase 6A đã bổ sung
`legacy_write_boundary.py` để chặn write không canonical trong phạm vi đã khóa.

## 8. Frontend canonical

Frontend tại `figma_make_frontend/` sử dụng API root-relative, không hard-code
remote origin cho browser production. Vite development proxy chỉ cho phép
loopback Django target đã validate.

Các nguyên tắc quan trọng:

- token chỉ lưu trong memory, không localStorage/sessionStorage;
- client tự gắn bearer token và loại bỏ authorization do caller truyền vào;
- path không được thoát khỏi canonical API base;
- timeout và cancellation có giới hạn;
- không retry mutation một cách mù quáng;
- idempotency key chỉ dùng ở command cần idempotency;
- ambiguous write phải reconciliation bằng authoritative reads;
- logout/auth failure phải xóa mutable session state;
- UI không hiển thị raw backend diagnostics hoặc credential.

Các workspace chính:

- `RfqWorkspace.tsx`;
- `QuotationWorkspace.tsx`;
- `OrderWorkspace.tsx`.

## 9. Authentication, role và security boundary

### Role chính

- Sales: tạo và quản lý dữ liệu bán hàng trong phạm vi được giao.
- Manager: review/approval, order progress và audit theo permission.
- Admin: quyền quản trị/canonical được allowlist.

Backend vẫn là nơi quyết định cuối cùng cho permission, ownership, lifecycle và
maker-checker. Việc ẩn nút ở frontend không được coi là security control.

### Security đã xác minh

- production settings fail closed;
- `DEBUG=False` trong production profile;
- PostgreSQL và Redis bắt buộc cho runtime production-like;
- `ALLOWED_HOSTS`, CSRF origins và CORS được validate chặt;
- secure cookie/HSTS/proxy header/security headers đã cấu hình;
- container chạy non-root và read-only;
- database/cache không publish ra host;
- browser token memory-only;
- không có strong-secret signature trong release candidate;
- không commit `.env.phase6`, dumps, SQLite DB, runtime logs, build output,
  sourcemaps, node_modules hoặc cache.

Giới hạn đã biết: Sales logout có thể nhận `permission_denied` do thiếu
`auth:read`; client vẫn xóa token memory trước, server TTL vẫn được áp dụng và
fixture tokens đã được revoke. Phải xử lý dứt điểm trước khi tuyên bố public
production.

## 10. Lịch sử triển khai cô đọng

### Phase 1–4: nền tảng backend canonical

- ổn định dự án và đóng regression;
- xác định business-domain contract;
- schema/migration và PostgreSQL validation;
- triển khai master data, RFQ, quotation, order/progress/audit;
- tạo canonical read API;
- tạo canonical command API;
- khóa write boundary đối với các đường legacy.

### Phase 5: frontend canonical

- 5A: canonical frontend client foundation;
- 5B: Foundation login và RFQ read integration;
- 5C: RFQ draft, line commands và submit;
- 5D: quotation lifecycle UI;
- 5E: order conversion, progress và audit UI;
- independent review/repair đã được thực hiện ở nhiều phase.

### Phase 6: production-like portfolio demo

- 6A: full-stack foundation, PostgreSQL/Redis, proxy, config hardening, legacy
  write boundary và runtime isolation;
- 6B: canonical browser E2E với fictional fixtures và DB reconciliation;
- 6C: Owner UAT, accessibility, session/role isolation và responsive checks;
- 6D: staging-like operations, production-static gateway, backup/restore,
  outage/recovery và release readiness;
- 6E: Owner acceptance, final smoke, regression, hygiene và release checkpoint;
- final: atomic commit, merge remote divergence, rerun toàn bộ regression,
  normal push và remote CI pass.

## 11. Kết quả kiểm thử cuối cùng sau merge

### Frontend local

- full suite: **142 passed, 0 failed**;
- TypeScript typecheck: PASS;
- Vite production build: PASS, 25 modules transformed;
- Phase 6A: 5 passed;
- Phase 6B: 8 passed;
- Phase 6C: 5 passed;
- Phase 6D/release config: 10 passed;
- Phase 6A và 6D format checks: PASS;
- production sourcemaps: 0.

### Backend local

- Django system check: 0 issue;
- `makemigrations --check --dry-run`: no changes detected;
- focused canonical/config/write-boundary/fixture/release suite:
  **86 passed, 8 skipped**;
- full pytest: **242 passed, 151 skipped, 0 failed**.

Các skip là conditional legacy-artifact coverage đã được báo cáo, không phải test
failure bị che giấu.

### Operations local

- 5/5 PowerShell helper parse không lỗi;
- Phase 6D Compose config render: PASS;
- `git diff --check`: PASS;
- không có forbidden artifact mới trong candidate/merge;
- không có strong-secret signature;
- worktree sạch tại thời điểm push/verify;
- local HEAD bằng remote branch SHA.

### Remote CI

Toàn bộ workflow của commit
`8458ab7be25a3efd1c553b10d9875fdc484c5816` đã PASS, bao gồm full Django tests,
frontend typecheck/tests/build, Phase 6 contracts và PostgreSQL migration smoke.

## 12. Runtime Phase 6

`docker-compose.phase6.yml` định nghĩa:

- `postgres`: PostgreSQL 16, private network, named persistent volume;
- `redis`: Redis 7 có password, private network;
- `django`: production settings, read-only container, non-root, media volume;
- `frontend`: Phase 6D profile, Nginx static build, read-only/non-root;
- network riêng `django-web-t-123-phase6-internal`;
- volumes `django-web-t-123-phase6-postgres-data` và
  `django-web-t-123-phase6-media`.

Port mặc định trong Compose là biến môi trường. Runbook Phase 6D dùng port cô
lập để coexist với stack khác:

- Django: `127.0.0.1:8001`;
- static gateway: `127.0.0.1:8443`;
- PostgreSQL và Redis không publish ra host.

Startup order:

```text
PostgreSQL/Redis healthy
  -> build current source
  -> migrate
  -> migrate --check
  -> Django ready
  -> frontend gateway ready
```

Các script chính:

- `scripts/phase6/Initialize-Phase6Environment.ps1`;
- `scripts/phase6/Start-Phase6.ps1`;
- `scripts/phase6/Start-Phase6D.ps1`;
- `scripts/phase6/Stop-Phase6.ps1`;
- `scripts/phase6/Invoke-Phase6DBackupRestoreDrill.ps1`.

Không dùng Docker prune, không restart Docker Desktop, không shutdown WSL và
không tác động stack không thuộc Phase 6.

## 13. Backup, restore và vận hành

Phase 6D đã xác minh:

- custom PostgreSQL dump tạo thành công;
- restore vào temporary isolated database;
- 61 public tables đọc được;
- migration fingerprint khớp;
- temporary restore database được xóa sau kiểm tra;
- PostgreSQL outage/recovery;
- Redis outage/readiness 503-to-200 recovery;
- stale-image và bounded restart recovery;
- cleanup chỉ xóa container/network Phase 6, giữ named volumes.

Runbook liên quan:

- `docs/phase6/LOCAL_FULL_STACK.md`;
- `docs/phase6/OPERATIONS.md`;
- `docs/phase6/BACKUP_RESTORE.md`;
- `docs/phase6/PHASE_6B_BROWSER_E2E.md`;
- `docs/phase6/RELEASE_CHECKLIST.md`.

## 14. Những giới hạn chưa hoàn thành

Các điểm sau không chặn portfolio demo nhưng chặn tuyên bố public production:

1. Chưa triển khai public hosting và TLS termination thực tế.
2. Chưa có load balancer/object storage production đã xác minh.
3. Chưa có encrypted off-host backup destination và retention automation.
4. Chưa có external monitoring/alerting được kiểm chứng trong môi trường thật.
5. Chưa có formal security/compliance assessment.
6. Chưa dùng production accounts hoặc production data.
7. Sales server-side logout revocation cần được hoàn thiện.
8. GitHub Actions dependencies cần nâng cấp để loại bỏ cảnh báo Node.js 20.
9. Một số tài liệu cũ cần chỉnh lại sau khi tracked legacy `backend/` bị xóa.
10. Public Django website, legacy HTML frontend và canonical React frontend cần
    được mô tả rõ ownership để tránh sửa nhầm bề mặt.

Không được gọi trạng thái hiện tại là “production certified”. Cụm từ đúng là
“portfolio production-like demo release candidate đã pass local và remote CI”.

## 15. File nên đọc trước khi làm tiếp

Ưu tiên theo thứ tự:

1. `PROJECT_MASTER_REPORT_FOR_CHATGPT.md` — tài liệu hiện tại;
2. `PHASE_6E_FINAL_OWNER_ACCEPTANCE_AND_RELEASE_CHECKPOINT_REPORT.md`;
3. `PHASE_6D_STAGING_OPERATIONS_RELEASE_READINESS_REPORT.md`;
4. `PHASE_6C_OWNER_UAT_ACCESSIBILITY_SESSION_VALIDATION_REPORT.md`;
5. `PHASE_6B_CANONICAL_BROWSER_E2E_IMPLEMENTATION_REPORT.md`;
6. `PHASE_6A_FULL_STACK_FOUNDATION_IMPLEMENTATION_REPORT.md`;
7. `PHASE_6_SCOPE_DISCOVERY_AND_RELEASE_PLAN.md`;
8. `docs/phase6/RELEASE_CHECKLIST.md`;
9. `django_backend/apps/api/canonical_urls.py`;
10. `figma_make_frontend/package.json`.

Các báo cáo Phase 1–5 cung cấp lịch sử chi tiết nhưng không được dùng để ghi đè
trạng thái post-merge trong tài liệu này.

## 16. Nguyên tắc an toàn cho task tiếp theo

- Bắt đầu bằng `git status`, branch, HEAD và remote sync check.
- Không tự ý rebase, reset, clean, stash, amend hoặc force push.
- Không commit/push/tag/release/deploy nếu Owner chưa cho phép rõ ràng.
- Không sửa hoặc xóa resource Docker ngoài Phase 6.
- Không in secret hoặc nội dung `.env.phase6` ra terminal/report.
- Chỉ dùng fictional `.invalid` data cho demo/E2E.
- Mọi write phải đi qua canonical contract và backend permission/lifecycle.
- Sau thay đổi phải chạy test tương xứng, `git diff --check` và hygiene scan.
- Không khôi phục tracked legacy `backend/` nếu chưa có yêu cầu và lý do mới.
- Nếu thay đổi release/runtime/security, phải chạy lại full frontend, full pytest,
  config/migration checks và remote CI sau push được phép.

## 17. Đề xuất roadmap tiếp theo

### Ưu tiên 1 — Documentation reconciliation

- cập nhật `README.md` và handoff cũ để phản ánh tracked `backend/` đã bị xóa;
- phân loại rõ canonical React app, Django public website và legacy frontend;
- cập nhật trạng thái remote CI từ limitation thành PASS.

### Ưu tiên 2 — Security/session hardening

- sửa quyền logout/revocation cho Sales;
- bổ sung regression cho server-side token revocation;
- rà soát token TTL và audit evidence.

### Ưu tiên 3 — CI maintenance

- nâng GitHub Actions lên phiên bản runtime không cảnh báo Node.js 20;
- giữ nguyên các gate hiện có;
- xác minh lại toàn bộ workflow.

### Ưu tiên 4 — Public-production planning

Chỉ thực hiện khi Owner quyết định chuyển từ portfolio demo sang môi trường thật:

- TLS/domain/load balancer;
- managed PostgreSQL/Redis;
- object storage/media strategy;
- encrypted off-host backup và retention;
- monitoring/alerting;
- threat model, security review và rollback rehearsal.

## 18. Prompt sẵn dùng để gửi cho ChatGPT/Codex

Sao chép phần dưới đây cùng file báo cáo này:

```text
Bạn đang tiếp quản dự án WEB Ô TÔ DJANGO / MecPrecision Vietnam.

Hãy đọc toàn bộ PROJECT_MASTER_REPORT_FOR_CHATGPT.md trước khi hành động. Xem
tài liệu đó là trạng thái handoff post-merge hiện tại; các phase report khác là
bằng chứng lịch sử. Project root là:
C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO

Trước tiên chỉ làm read-only preflight:
1. kiểm tra git status, branch, HEAD và remote tracking;
2. xác nhận HEAD dự kiến là 8458ab7be25a3efd1c553b10d9875fdc484c5816,
   trừ khi Owner thông báo có thay đổi mới;
3. đọc các file liên quan trực tiếp tới task;
4. nêu rõ phạm vi, rủi ro và test plan;
5. không rebase/reset/clean/stash/amend/force push;
6. không commit, push, tag, release hoặc deploy nếu chưa được Owner cho phép.

Mục tiêu tiếp theo của tôi là: [ĐIỀN YÊU CẦU MỚI Ở ĐÂY]
```

## 19. Kết luận

Dự án đã hoàn thành một release candidate production-like dành cho portfolio,
được reconcile với remote, push bình thường và pass GitHub Actions. Canonical
workflow, PostgreSQL/Redis runtime, browser E2E, accessibility, operations và
backup/restore đều có bằng chứng kiểm thử.

Bước tiếp theo nên là một task mới có phạm vi rõ ràng. Không cần lặp lại Phase 6
từ đầu và không được mở rộng claim thành public production nếu chưa hoàn thành
các giới hạn tại mục 14.
