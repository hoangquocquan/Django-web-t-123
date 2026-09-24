# Phase Test Template

## Test Scope

Describe what the tests must prove.

## Required Commands

```text
python scripts/phase_validator.py --phase <phase>
pytest tests/<phase_test_file>.py
pytest
```

## Safety Checks

- Production deployment is false.
- Auto merge is false.
- Human approval is required.
- Failed tests are visible.

## Expected Result

PASS
