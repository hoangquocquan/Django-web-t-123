"""Import IIS production evidence for Phase 11.1.6.2.x.

This compatibility wrapper runs the Phase 11.1.6.2 evidence workflow against
the production evidence input directory. It exists so the IIS import command in
the runbooks has a stable entrypoint. It only reads evidence files and writes
the JSON report; it does not touch IIS, routing, proxy settings or shutdown.
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    from scripts.phase11_1_6_2_real_production_evidence import validate_real_production_evidence
except ModuleNotFoundError:
    from phase11_1_6_2_real_production_evidence import validate_real_production_evidence


def main():
    """Command line entrypoint for IIS evidence import."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.2.1 IIS production evidence import")
    parser.add_argument("--input-dir", default=None, help="Directory containing IIS CSV/log evidence.")
    parser.add_argument("--output", default=None, help="Report output path.")
    parser.add_argument("--period", default=None, help="Collection period label.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when evidence is incomplete. Default incomplete state exits 0.",
    )
    args = parser.parse_args()
    result = validate_real_production_evidence(
        input_dir=args.input_dir,
        output_path=args.output,
        period=args.period,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "COMPLETE_EVIDENCE_PACKAGE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
