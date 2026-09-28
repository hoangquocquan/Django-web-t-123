# AI, Redis and provider failure drill

Status: `MANUAL_EXECUTION_REQUIRED` in controlled staging. With synthetic data, disable Redis, Ollama/AI and each approved external provider separately. Confirm sanitized degradation, bounded timeout, no autonomous send/mutation/fallback, fail-closed advisory behavior, recovery and alerts. Keep `LINE_SEND_ENABLED=false`; retain timings and metrics without payloads or credentials.
