# Known Limitations

- Live PostgreSQL/media/n8n backup and isolated restore remain unverified because Docker API access was denied by the execution environment.
- Dependency audit could not reach PyPI; pinned dependencies are unchanged from the successful PROD-04 audit.
- Prometheus and Grafana definitions are deployment contracts only and were not deployed.
- Backup packages are transient local artifacts; production storage must add approved off-host encryption and retention.
- The real Ollama review was schema-valid but returned `BLOCKED`; its raw response listed implementation requirements as missing while also reporting no defects. The fail-closed normalized decision controls, and no protected action was authorized.
- PROD-06 and PROD-07 remain blocked until live backup/restore and a final schema-valid PASS review complete.
