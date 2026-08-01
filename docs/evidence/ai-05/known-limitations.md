# AI-05 Known Limitations

- Local `llama3` repeatedly treats the required later human-approval gate as a technical blocker.
- The final mandatory review exhausted three retries and returned `BLOCKED`; fallback was not used.
- Ruff reports inherited formatting/import-order debt in older orchestration files.
- Bandit reports Low subprocess warnings for local command runners; no Medium/High finding exists.
- AI-06 must not start until an independent local review model produces a valid technical PASS.
