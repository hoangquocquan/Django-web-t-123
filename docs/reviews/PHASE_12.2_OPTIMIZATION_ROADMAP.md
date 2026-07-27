# Phase 12.2 Optimization Roadmap

## Backend

| Priority | Issue | Impact | Recommendation |
| --- | --- | --- | --- |
| High | Docker still starts legacy backend | Deployment confusion | Decide Django runtime cutover path before production |
| High | No production auth/performance boundary | Unsafe public exposure | Keep APIs internal until auth and monitoring are complete |
| Medium | Large legacy backend remains | Maintenance cost | Avoid new legacy features; continue Django migration |

## Database

| Priority | Issue | Impact | Recommendation |
| --- | --- | --- | --- |
| High | SQLite remains primary legacy source | Production scalability limit | Continue PostgreSQL ownership planning |
| Medium | Query timing only local | Unknown production latency | Add real monitoring after production-like environment exists |
| Medium | No cache layer | Repeated read latency | Add cache only after slow endpoint evidence |

## API

| Priority | Issue | Impact | Recommendation |
| --- | --- | --- | --- |
| High | No production latency SLO | Cannot judge regressions | Define p95/p99 targets per endpoint |
| Medium | Pagination exists but search/filter performance is not baselined | Future slow queries | Benchmark search/filter when implemented |
| Medium | POST replacement APIs are write-intent only | Not a real production write benchmark | Add transactional write tests after ownership cutover |

## Infrastructure

| Priority | Issue | Impact | Recommendation |
| --- | --- | --- | --- |
| High | Monitoring not deployed | Production blind spots | Add metrics and alerting in Phase 12.3 |
| Medium | CI does not run dedicated performance smoke tests | Performance regressions can slip | Add a lightweight benchmark threshold in CI later |
| Medium | Nginx config is sample-only | Unknown proxy latency | Benchmark behind Nginx in staging |

## Roadmap Result

Optimization should wait until baseline metrics are reviewed. The next logical
phase is monitoring so future performance changes can be measured continuously.
