# Wave 6 Cutover Validation Report

## Validation Scope

Wave 6 validates browser-facing Django admin UI ownership for migrated domains.

## Checks

| Check | Result |
| --- | --- |
| Admin login page renders | PASS |
| Admin session is created from Foundation token | PASS |
| Dashboard requires login | PASS |
| CSRF blocks missing token on login | PASS |
| CSRF allows valid token login | PASS |
| Product create/update | PASS |
| Customer create/update | PASS |
| Inventory create/adjust | PASS |
| Order create/update support | PASS |
| Workflow transition | PASS |
| Transaction history renders | PASS |
| Viewer write restriction | PASS |
| Legacy files remain | PASS |

## Required Test Commands

- `python manage.py check`: PASS.
- `pytest tests/test_wave6_admin_ui.py`: PASS, 10 passed.
- `pytest`: PASS, 242 passed.
- `python ai-factory/run_ai_factory.py --wave django-wave-6`: PASS, `AI_SOFTWARE_FACTORY_COMPLETE`.

## Cutover Recommendation

Use Django `/admin/` for migrated modules after human review. Keep legacy admin available for rollback and unmigrated modules.
