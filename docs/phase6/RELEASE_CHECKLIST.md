# Phase 6D portfolio-demo release checklist

- [ ] Exact repository/worktree and dirty-state baseline recorded; nothing staged.
- [ ] Read-only Docker, volume, network, and port preflight completed.
- [ ] `.env.phase6` exists, is ignored, and required names pass fail-closed checks.
- [ ] Production settings check passes with PostgreSQL and Redis only.
- [ ] Current Django and static frontend images build from current source.
- [ ] Migrations apply and `migrate --check` passes before application startup.
- [ ] PostgreSQL, Redis, Django liveness/readiness, and gateway health pass.
- [ ] Static frontend and root-relative canonical `/api` access pass on 8443.
- [ ] Bounded fictional authentication/workflow/audit smoke passes.
- [ ] Isolated backup/restore drill passes without exposing credentials.
- [ ] PostgreSQL/Redis/config/readiness/port/stale-image recovery evidence recorded.
- [ ] No real PII, secrets, bearer tokens, or backup artifacts are tracked/reported.
- [ ] Memory-only token, exact permissions, canonical contract, and legacy write block remain intact.
- [ ] Phase 5A-5E, Phase 6A-6D, full frontend, build/typecheck/format gates pass.
- [ ] Django check, migration consistency, focused canonical/boundary/6D tests pass.
- [ ] Broader pytest outcome and any known legacy failures are reported separately.
- [ ] `git diff --check` passes; no stage/commit/push/deploy occurred.
- [ ] Owner receives the Phase 6D report and exact verdict; Phase 6E is not started.
