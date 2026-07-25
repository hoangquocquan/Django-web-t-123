# Auth Permission Matrix

## Purpose

Map legacy roles to future Django-compatible permission decisions.

## Legacy Roles

| Role | Meaning |
| --- | --- |
| `admin` | Full system access |
| `editor` | Write access to content/business modules |
| `viewer` | Read-only access |

## Matrix

| Module | Admin | Editor | Viewer |
| --- | --- | --- | --- |
| dashboard | read/write | read/write | read |
| products | read/write | read/write | read |
| categories | read/write | read/write | read |
| news | read/write | read/write | read |
| media | read/write | read/write | read |
| pages | read/write | read/write | read |
| menus | read/write | read/write | read |
| banners | read/write | read/write | read |
| contacts | read/write | read/write | read |
| quotes | read/write | read/write | read |
| customers | read/write | read/write | read |
| newsletter | read/write | read/write | read |
| ai | read/write | read/write | read |
| developer | read/write | read/write | read |
| settings | read/write | denied | read |

## Future Django Mapping

Recommended approach:

- Keep legacy role values during transition.
- Add Django groups later: `Admin`, `Editor`, `Viewer`.
- Map group permissions from this matrix.
- Do not change role behavior silently during cutover.

## Test Coverage

Phase 8 tests validate:

- admin can write all modules,
- editor can write allowed modules,
- editor cannot write settings,
- viewer can read,
- viewer cannot write,
- unknown role is denied.
