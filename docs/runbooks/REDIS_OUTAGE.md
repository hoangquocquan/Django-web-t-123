# Redis Outage

1. Confirm `mecprecision_dependency_up{dependency="redis"}` and container health.
2. Preserve Redis logs, disk state, and correlation IDs. Do not disable authentication.
3. Pause AI-heavy traffic and session-changing operations if cache/session consistency is uncertain.
4. Restart or restore Redis only after operator approval; verify `PING`, session behavior, rate limiting, and AI capacity leases.
5. Keep the incident open until metrics remain healthy for 15 minutes.
