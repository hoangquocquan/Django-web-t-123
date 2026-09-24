# CI/CD Security Model

## Secrets

Rules:

- Never commit `.env` files.
- Never store production secrets in repository.
- Use a secret manager for production.
- CI should inject secrets at runtime only.
- Logs must mask tokens, passwords, and connection strings.

## Credentials

Credential policy:

- Use least privilege.
- Separate development, staging, and production credentials.
- Rotate production credentials.
- Disable unused credentials.
- Use short-lived tokens when available.

## Permissions

Required permission boundaries:

- Developers can trigger CI.
- Maintainers can merge to `develop`.
- Release owners can approve staging.
- Production owners can approve production.
- AI and n8n cannot approve production.

## Artifact Security

Artifacts must:

- Be tied to a commit hash.
- Be stored in controlled storage.
- Be immutable after creation.
- Include build metadata.
- Be scanned before production release.

## Audit Logs

CI/CD must record:

- Who triggered the pipeline.
- Commit hash.
- Branch and tag.
- Test result.
- Approval decision.
- Deployment target.
- Rollback action if used.

## AI Safety

Ollama runs locally and is advisory only.

AI must not:

- receive secrets
- approve production
- deploy changes
- disable rollback
- bypass human review

