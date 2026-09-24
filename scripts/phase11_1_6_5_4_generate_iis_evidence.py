"""Compatibility wrapper for the renamed Phase 11.1.6.5.4 IIS log generator."""

from __future__ import annotations

try:
    from scripts.phase11_1_6_5_4_generate_iis_logs import generate_iis_logs as generate_iis_evidence
    from scripts.phase11_1_6_5_4_generate_iis_logs import main
except ModuleNotFoundError:
    from phase11_1_6_5_4_generate_iis_logs import generate_iis_logs as generate_iis_evidence
    from phase11_1_6_5_4_generate_iis_logs import main


if __name__ == "__main__":
    raise SystemExit(main())
