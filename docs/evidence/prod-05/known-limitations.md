# Known Limitations

- The production-like media volume was empty at backup time, so media archive and restore mechanics passed but no customer media file was available to exercise content-level validation.
- The host development database reports `foundation.0006_add_login_audit_and_two_factor_challenges` as unapplied. The isolated restored PostgreSQL database passed `migrate --check`; no migration was applied to the host database during PROD-05.
- Prometheus and Grafana definitions are deployment contracts only and were not deployed.
- Backup packages are transient local artifacts; production storage must add approved off-host encryption and retention.
- A host HTTP request receives the expected production HTTPS redirect. The container's internal healthcheck continues to return HTTP 200 and remains healthy.
- Ruff has no repository configuration file; the machine-wide Ruff settings produce RUF100 noise. The reproducible isolated F/E4/E7/E9 check and format check pass for the PROD-05 scope.
- The real backup package, PostgreSQL dump, n8n runtime archive, and media archive remain outside Git by policy.
