# Capacity test plan

Status: `MANUAL_EXECUTION_REQUIRED` on isolated staging. Use synthetic traffic at expected, 2x and controlled saturation rates. Measure throughput, p50/p95/p99, errors, database connections/locks, Redis, queues, CPU and memory. Include large reads and migration-lock observation. Abort before shared-service impact; define thresholds in the release ticket and retain sanitized results.

Scenarios must cover products, customers, inventory, orders, admin search/filter, RFQ, quotation/order commands, RAG retrieval, AI inference, Redis and PostgreSQL connections. Approval fields are intentionally unset: p50 `TO_BE_APPROVED`, p95 `TO_BE_APPROVED`, p99 `TO_BE_APPROVED`, error rate `TO_BE_APPROVED`, slow query/lock wait `TO_BE_APPROVED`, CPU/memory `TO_BE_APPROVED`, Ollama concurrency `TO_BE_APPROVED`, Redis latency `TO_BE_APPROVED`.
