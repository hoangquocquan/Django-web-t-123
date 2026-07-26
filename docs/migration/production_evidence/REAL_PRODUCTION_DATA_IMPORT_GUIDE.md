# Real Production Data Import Guide

## Purpose

Guide operators to import real production evidence before legacy API shutdown.

## Supported Sources

- Nginx logs
- Load balancer logs
- API gateway logs
- Application logs
- CSV export
- JSON export

## Required Fields

| Field | Description |
|---|---|
| `timestamp` | Request timestamp |
| `client` | Client name, client ID, user-agent or source |
| `endpoint` | Requested path or URL |
| `status_code` | HTTP status code |
| `request_count` | Count represented by the row or log entry |

## Accepted Input Examples

CSV:

```csv
timestamp,client,endpoint,status_code,request_count
2026-08-01T10:00:00+07:00,frontend,/api/v1/public/home/,200,120
```

JSON:

```json
{"timestamp":"2026-08-01T10:00:00+07:00","client":"frontend","endpoint":"/api/v1/public/home/","status_code":200,"request_count":120}
```

Text log:

```text
2026-08-01T10:00:00+07:00 client=frontend GET /api/v1/public/home/ 200
```

## Import Command

```powershell
python scripts\phase11_1_5_4_production_evidence_loader.py --input <path-to-log-or-export>
```

Multiple inputs:

```powershell
python scripts\phase11_1_5_4_production_evidence_loader.py --input nginx.log --input gateway.csv --input app.jsonl
```

## Output

The loader writes:

```text
docs/migration/production_evidence/reports/REAL_PRODUCTION_TRAFFIC_REPORT.json
```

## Current Status

```text
INCOMPLETE_EVIDENCE_PACKAGE
```

No real production data is stored in this repository.
