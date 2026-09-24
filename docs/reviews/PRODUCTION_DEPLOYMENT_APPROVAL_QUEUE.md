# Production Deployment Approval Queue

| Gate | Owner | Required Evidence | State |
| --- | --- | --- | --- |
| Architecture review | Human architect | Final report, cumulative diff, Ollama result | WAITING |
| Security review | Human security owner | Dependency/source/private image scan | WAITING |
| Data/recovery review | Human database owner | Backup checksum and isolated restore | WAITING |
| Staging acceptance | Human product/operations owner | Target staging UAT and load evidence | WAITING |
| Release approval | Human release manager | Immutable commit/image manifest | WAITING |
| Production deployment | Human authorized operator | Separate approved change window | WAITING |

AI and n8n may summarize evidence but cannot change any row to approved. No
automatic merge or deployment is configured.
