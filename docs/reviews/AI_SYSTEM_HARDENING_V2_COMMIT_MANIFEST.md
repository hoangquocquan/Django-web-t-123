# AI System Hardening V2 Commit Manifest

Baseline: `e0af74650ca3670589f482ff7fe44804d6ff41f7`

| Phase | Task/Integration | Commit | Message | Tests | Ollama review | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AI-00 | Baseline | `dbea8b20122a7cd4766c387ac763d8ca14edf0e7` | `docs(ai): establish hardening v2 reproducible baseline` | 21 focused + 342 regression PASS | PASS (`llama3`) | PASS |
| AI-01 | Vector search | `a2751c3e33e0c55cec50045fe6d131701a7a1d15` | `feat(ai): implement real ollama embeddings and vector retrieval` | 35 focused + 354 regression PASS | PASS (`llama3`) | PASS |
| AI-02 | Governance V2 | `5e10202a70164f410acc9e5bb273d1d1dc3661c7` | `feat(ai): add multilingual governance v2 controls` | 18 focused + 367 regression PASS | PASS (`llama3`, correction attempt 1) | PASS |
| AI-03 | Grounded Sales synthesis | `03b17e404374de75afa569d69e3a18fd38ca03c0` | `feat(ai-sales): add grounded ollama sales synthesis` | 16 focused + 380 regression PASS | PASS (`llama3`) | PASS |
| AI-04 | Safe agent controller | `a5175d9f9c03daf9e6cf1e06ab0c64329d9802c2` | `feat(ai-agent): add safe structured read-only agent controller` | 27 focused + 395 regression PASS | PASS (`llama3`) | PASS |
| AI-05 | Mandatory review implementation | `fbf594f4f9a017a46b6d7049fe258e0204af9fc2` | `feat(ai-factory): enforce mandatory ollama phase review` | 55 focused + 422 regression PASS | BLOCKED (`llama3`, 3 retries, no fallback) | BLOCKED_REQUIRES_HUMAN |
| AI-05 V2 | Mandatory review semantic hardening | `81232332776fd30f22d607b61ac8aec9706d7f38` | `fix(ai-factory): correct mandatory Ollama review semantics` | 85 focused + 446 regression PASS | PASS (`llama3`, schema valid) | PASS |
| AI-06 | Ollama endpoint integration fix | `8e4a592e8b11ac21d18ccfe4598585f64737ec3c` | `fix(ai): harden local ollama endpoint validation` | 18 targeted + 455 regression PASS | Included in cumulative review | PASS |
| AI-06 | Final integration and handover | Recorded after documentation commit | `docs(ai): hoan tat tich hop va ban giao AI hardening v2` | 163 focused + 455 regression PASS | PASS (`llama3`, no fallback) | WAITING_FOR_HUMAN_APPROVAL |

Commit hash được cập nhật sau khi Git tạo commit thật; không có remote được tự tạo và không push.
