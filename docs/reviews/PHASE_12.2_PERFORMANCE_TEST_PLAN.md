# Phase 12.2 Performance Test Plan

## Testing Objectives

Measure the current local performance baseline before optimization. This phase
does not change business logic, production systems, routes or database schema.

Goals:

- measure API response time
- measure API throughput
- measure local memory peak during benchmark
- measure database query execution time
- identify bottlenecks
- document optimization priorities

## Test Environment

| Item | Value |
| --- | --- |
| Environment | Local migration test environment |
| API runtime | Django test client with `config.settings.test` |
| Database | Legacy SQLite in read-only access pattern |
| Production traffic | Not used |
| External calls | Not used |

## Metrics

| Metric | Source |
| --- | --- |
| Response time | API benchmark script |
| Throughput | API benchmark script |
| CPU | Process CPU time delta from benchmark script |
| Memory | Python `tracemalloc` peak memory |
| Database latency | SQLite read-only query timing |
| Error rate | API benchmark status/error count |

## Scenarios

| Scenario | Coverage |
| --- | --- |
| Health endpoints | `/api/health/`, `/api/v1/health/` |
| GET endpoints | public home, catalog, CRM, sales, CMS, auth, news |
| POST endpoints | contact, quote, AI chat and product write-intent |
| Authentication endpoints | profile and permissions read endpoints |
| Database queries | table counts, joins, filtered reads and integrity check |
| Load simulation | 10, 50 and 100 synthetic users in local worker threads |

## Success Criteria

| Criterion | Target |
| --- | --- |
| Benchmark produces JSON output | Required |
| API error rate | 0% for measured endpoints |
| P95 latency | Recorded for every scenario |
| P99 latency | Recorded for every scenario |
| Database report | Generated |
| Production modification | Must remain false |

## Baseline Decision

This phase creates measurement visibility only. Optimization must happen in a
future phase after reviewers accept the baseline.
