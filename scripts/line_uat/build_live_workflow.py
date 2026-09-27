"""Build the inactive, runtime-only LINE UAT workflow with a final send interlock."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VERIFY_NODE = "Verify APPROVED Safety State"
INTERLOCK_NODE = "Final Runtime Send Interlock"
SEND_NODE = "Django Kill Switch + LINE Send"
AUDIT_NODE = "Final Audit Output"


def build_runtime_workflow(source: Path, destination: Path) -> None:
    """Add a second runtime pause after approval verification and before send."""
    with source.open(encoding="utf-8") as handle:
        workflow = json.load(handle)

    serialized_source = json.dumps(workflow, ensure_ascii=False)
    if workflow.get("active") is not False:
        raise ValueError("Source workflow must be inactive.")
    if "api.line.me" in serialized_source:
        raise ValueError("Source workflow must not call LINE directly.")
    if "LINE_UAT_CHANNEL_ACCESS_TOKEN" in serialized_source:
        raise ValueError("Source workflow must not contain the LINE token variable.")

    nodes = workflow.get("nodes", [])
    nodes_by_name = {node.get("name"): node for node in nodes}
    required = {VERIFY_NODE, SEND_NODE, AUDIT_NODE}
    if not required.issubset(nodes_by_name):
        raise ValueError("Source workflow is missing a required safety node.")
    if INTERLOCK_NODE in nodes_by_name:
        raise ValueError("Runtime interlock already exists.")

    gate = {
        "parameters": {
            "resume": "form",
            "formTitle": "Final runtime interlock — single LINE UAT send",
            "formDescription": (
                "=APPROVED synthetic UAT record verified.\n\n"
                "Approval: {{ $json.approval_id }}\n"
                "Environment: {{ $json.environment }}\n"
                "Synthetic: {{ $json.synthetic }}\n\n"
                "Exact approved LINE message:\n"
                "{{ $json.proposed_message }}\n\n"
                "Do not submit until the operator has enabled the process-only "
                "UAT send switch."
            ),
            "formFields": {
                "values": [
                    {
                        "fieldLabel": (
                            "Proceed with the single controlled UAT provider send"
                        ),
                        "fieldName": "runtime_send_ready",
                        "fieldType": "checkbox",
                        "requiredField": True,
                    }
                ]
            },
            "options": {"limitWaitTime": False},
        },
        "id": "final-runtime-interlock",
        "name": INTERLOCK_NODE,
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [1010, 40],
        "webhookId": "line-uat-final-runtime-interlock",
    }
    nodes.append(gate)

    connections = workflow.get("connections", {})
    connections[VERIFY_NODE] = {
        "main": [[{"node": INTERLOCK_NODE, "type": "main", "index": 0}]]
    }
    connections[INTERLOCK_NODE] = {
        "main": [[{"node": SEND_NODE, "type": "main", "index": 0}]]
    }

    send_node = nodes_by_name[SEND_NODE]
    send_node["parameters"]["url"] = (
        "={{ $env.DJANGO_UAT_BASE_URL + "
        "'/api/v1/internal/line-uat/approvals/' + "
        "$('Verify APPROVED Safety State').item.json.approval_id + '/send/' }}"
    )
    send_node["position"] = [1240, 40]
    nodes_by_name[AUDIT_NODE]["position"] = [1470, 40]
    workflow["active"] = False

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(workflow, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: build_live_workflow.py SOURCE DESTINATION")
    build_runtime_workflow(Path(argv[1]), Path(argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
