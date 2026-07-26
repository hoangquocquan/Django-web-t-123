# Production Evidence Input Template

## Traffic Period

Start date:

```text
PENDING
```

End date:

```text
PENDING
```

## Log Sources

- [ ] Nginx
- [ ] Load balancer
- [ ] API gateway
- [ ] Application logs
- [ ] CDN

## Metrics

Legacy API requests:

```text
/api/ = PENDING
```

Django API requests:

```text
/api/v1/ = PENDING
```

Unknown clients:

```text
PENDING
```

## Evidence Owner

```text
PENDING
```

## Evidence Timestamp

```text
PENDING
```

## Validation Command

```powershell
python scripts\phase11_1_5_2_evidence_approval_validator.py --package <evidence-package.json>
```
