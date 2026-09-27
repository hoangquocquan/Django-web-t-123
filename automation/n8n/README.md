# UAT - AI Sales LINE Approval Demo

This workflow is **UAT only**. Never connect real customer data or enable production sending.

Import `line_uat_approval_demo.json` into n8n, keep it inactive while configuring, and expose these variables to the n8n process:

- `DJANGO_UAT_BASE_URL` — for example `http://django:8000`
- `DJANGO_UAT_BEARER_TOKEN` — a short-lived Manager/Admin foundation token

The workflow intentionally does not hold a LINE access token. After explicit form approval, n8n asks Django to perform the send. Django re-checks the approval state, synthetic/UAT markers, approved-content hash, recipient allowlist and kill switch, then commits an at-most-once send claim before calling LINE with the approval UUID as `X-Line-Retry-Key`.

The Wait node has no automatic timeout approval. An abandoned or expired execution sends nothing. A decision other than explicit `APPROVE` plus the UAT acknowledgement follows the reject branch.

Keep `LINE_SEND_ENABLED=false` for import and dry-run validation. See `docs/N8N_LINE_UAT_DEMO.md` for the complete setup and demo procedure.

For the isolated Windows runtime, run `start_live_runtime.ps1`, complete n8n's supported owner setup, and then run `attach_runtime_workflow.ps1`. The second script imports this workflow into the resolved personal project with `active=false` and verifies ownership. Do not import into the fresh database before its owner exists.
