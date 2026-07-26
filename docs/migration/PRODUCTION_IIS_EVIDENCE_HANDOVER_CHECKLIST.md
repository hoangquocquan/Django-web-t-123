# Production IIS Evidence Handover Checklist

## Server Information

- [ ] Server name:
- [ ] IIS site name:
- [ ] Site ID:
- [ ] Environment:

## Log Information

- [ ] Log period:
- [ ] Log files count:
- [ ] File size:
- [ ] Hash verification:
- [ ] Logs copied to `docs/migration/production_evidence/input/iis_logs/`
- [ ] CSV exported to `docs/migration/production_evidence/input/iis_api_evidence.csv`

## Required W3C Fields

- [ ] `date`
- [ ] `time`
- [ ] `c-ip`
- [ ] `cs-uri-stem`
- [ ] `sc-status`
- [ ] `cs(User-Agent)`

## Traffic Validation

- [ ] Legacy API checked
- [ ] Django API checked
- [ ] Unknown clients reviewed
- [ ] Legacy `/api/*` request count:
- [ ] Django `/api/v1/*` request count:
- [ ] Unknown clients count:

## Security

- [ ] Credentials removed
- [ ] Tokens removed
- [ ] Cookies removed
- [ ] Customer data removed or approved for review
- [ ] Raw logs stored outside Git when required
- [ ] Sanitized CSV approved for review

## Delivery

- [ ] `collection_metadata.json` completed
- [ ] Acceptance validator executed
- [ ] `EVIDENCE_ACCEPTED` or `EVIDENCE_REJECTED` recorded
- [ ] Review report delivered to architecture reviewer

## Safety Confirmation

- [ ] Legacy API was not shut down
- [ ] IIS routes were not disabled
- [ ] IIS configuration was not modified
- [ ] Proxy was not modified
- [ ] Database was not modified
- [ ] Production code was not changed
