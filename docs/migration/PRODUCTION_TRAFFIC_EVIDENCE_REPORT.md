# Production Traffic Evidence Report

## Phase

Phase 11.1.4 - Production Traffic Evidence Collection

## Verification Period

```text
NOT_PROVIDED
```

## Data Sources

| Source | Status |
|---|---|
| Nginx access logs | Not provided |
| Load balancer logs | Not provided |
| API gateway logs | Not provided |
| Application access logs | Not provided |
| CDN logs | Not provided |

## Logs Checked

```text
0
```

## Traffic Result

```text
legacy_api_count: not verified
django_api_v1_count: not verified
unknown_clients: not verified
```

## Decision

```text
KEEP_LEGACY_API_ACTIVE
```

## Reason

No production log export is available in this repository. The system must keep
legacy `/api/...` routes active until evidence proves:

- legacy `/api/...` traffic is zero
- Django `/api/v1/...` traffic is active
- unknown client count is zero

## Evidence Command

```powershell
python scripts\phase11_1_4_production_traffic_evidence.py --log <production-log> --period <YYYY-MM-DD_to_YYYY-MM-DD>
```

## Security Review

- Credentials are masked by the evidence collector.
- Raw logs must remain outside Git.
- Report samples must be redacted before sharing.
- Evidence files are read-only inputs.
