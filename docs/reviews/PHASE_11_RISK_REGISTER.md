# Phase 11 Risk Register

| Risk | Impact | Probability | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Legacy dependency remains active | Ongoing maintenance and security exposure | Medium | Keep governance gates active until real evidence is complete | Architect | Open |
| Missing evidence | Production shutdown could affect unknown clients | High | Require real IIS/API evidence with `simulation = false` | DevOps | Open |
| Rollback failure | Customer-facing API outage could persist | Medium | Keep rollback route/proxy plan and owner approval | Operations | Open |
| Data inconsistency | Writes may behave differently across legacy and Django | Medium | Keep write decommission blocked until production contract validation | Engineering | Open |
| Monitoring failure | Incidents may be missed during cutover | Medium | Require monitoring owner, metrics and escalation path | Operations | Open |
| Simulation confused with production | Incorrect approval of shutdown | Low after hardening | Evidence classification standard and `TRAINING_ONLY` status | Engineering | Controlled |
| Approval bypass | Production change without business/technical sign-off | Medium | Real approval documents remain mandatory | Project Owner | Open |

## Risk Position

Phase 11 is safe for training review. Production remains blocked until evidence,
approval, rollback and monitoring risks are closed.
