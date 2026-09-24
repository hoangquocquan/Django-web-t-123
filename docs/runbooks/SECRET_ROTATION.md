# Secret Rotation

1. Inventory the affected secret and consumers without printing its value.
2. Create a replacement in the approved secret store and schedule a human-approved maintenance window.
3. Rotate one dependency at a time: Django, PostgreSQL, Redis, metrics, n8n encryption/webhook, then external integrations.
4. Restart only affected services and verify health, auth, metrics scrape, n8n signatures, and backup access.
5. Revoke the old value, record completion by secret name/version only, and scan Git/logs for accidental exposure.
