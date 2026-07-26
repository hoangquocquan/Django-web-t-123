# Legacy API Shutdown Readiness Checklist

## Current Decision

```text
KEEP_LEGACY_API_ACTIVE
```

Technical preparation is mostly complete, but production traffic evidence and
final approvals are still missing.

## Technical

- [x] Django APIs available
- [x] API compatibility completed
- [ ] Legacy traffic verified
- [ ] Monitoring ready

## Operational

- [ ] Maintenance window approved
- [ ] Rollback owner assigned
- [ ] Support team notified

## Business

- [ ] Business owner approval
- [ ] User impact reviewed

## Required Command

```powershell
python scripts\phase11_1_5_shutdown_readiness_check.py
```

Default result without production evidence:

```text
KEEP_LEGACY_API_ACTIVE
```

## Approval Inputs

| Requirement | Environment variable |
|---|---|
| Technical approval | `PHASE11_1_5_TECHNICAL_APPROVED=approved` |
| Business approval | `PHASE11_1_5_BUSINESS_APPROVED=approved` |
| Rollback readiness | `PHASE11_1_5_ROLLBACK_READY=approved` |
| Rollback owner | `PHASE11_1_5_ROLLBACK_OWNER=<owner>` |
| Maintenance window | `PHASE11_1_5_MAINTENANCE_WINDOW_APPROVED=approved` |
| Monitoring ready | `PHASE11_1_5_MONITORING_READY=ready` |
| Support notified | `PHASE11_1_5_SUPPORT_NOTIFIED=yes` |
| User impact reviewed | `PHASE11_1_5_USER_IMPACT_REVIEWED=verified` |
| Final approval ID | `PHASE11_1_5_APPROVAL_ID=<approval-id>` |
