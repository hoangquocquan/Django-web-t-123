import json
from pathlib import Path

from scripts import n8n_business_wave2


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_n8n_business_wave2_artifacts_exist():
    required = [
        PROJECT_ROOT / "n8n" / "workflows" / "business_wave2_automation.json",
        PROJECT_ROOT / "n8n" / "config" / "business_wave2_local.yml",
        PROJECT_ROOT / "docs" / "n8n" / "BUSINESS_WAVE2_N8N_AUTOMATION.md",
    ]
    for path in required:
        assert path.exists()
        assert path.stat().st_size > 0


def test_webhook_signature_validation():
    payload = {"company": "Demo", "need": "CNC quotation"}
    signature = n8n_business_wave2.sign_payload(payload)

    assert n8n_business_wave2.validate_webhook_signature(payload, signature)
    assert not n8n_business_wave2.validate_webhook_signature(payload, "bad-signature")


def test_local_automation_blocks_invalid_signature(tmp_path):
    result = n8n_business_wave2.run_local_automation(
        "website_lead",
        {"company": "Demo"},
        signature="bad",
        output_path=tmp_path / "result.json",
    )

    assert result["status"] == "BLOCKED"
    assert "signature" in result["reason"].lower()


def test_local_automation_runs_all_required_workflows(tmp_path):
    workflows = ["website_lead", "document_update", "sales_follow_up"]
    for workflow in workflows:
        payload = {"id": workflow}
        result = n8n_business_wave2.run_local_automation(
            workflow,
            payload,
            signature=n8n_business_wave2.sign_payload(payload),
            output_path=tmp_path / f"{workflow}.json",
        )
        assert result["status"] == "N8N_LOCAL_AUTOMATION_READY"
        assert result["safety"]["human_approval_required"] is True

    workflow_json = json.loads((PROJECT_ROOT / "n8n" / "workflows" / "business_wave2_automation.json").read_text(encoding="utf-8"))
    assert workflow_json["active"] is False
    assert workflow_json["meta"]["localOnly"] is True

