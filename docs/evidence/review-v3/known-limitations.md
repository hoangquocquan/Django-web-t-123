# REVIEW-V3 Known Limitations

- The local `llama3` review is a technical gate and cannot authorize merge, release, deployment, or production.
- Human approval is still mandatory after a technical PASS.
- GPG/Sigstore signing was unavailable, so the package records `SIGNATURE_NOT_AVAILABLE`.
- Tests and documentation are represented by deterministic contracts rather than raw bodies to reduce prompt-injection risk.
- Three pre-existing ZIP files remain untracked and excluded from all evidence and commits.
