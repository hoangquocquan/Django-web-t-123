import json

import pytest
from django.test import override_settings

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmInteraction, CrmTask
from apps.foundation.models import FoundationUser
from apps.knowledge.models import KnowledgeDocument
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation
from scripts import business_simulation


@pytest.mark.django_db
def test_business_simulation_creates_complete_fictional_flow(tmp_path, monkeypatch):
    """Simulation phai tao du lieu gia va chay du CRM/Sales/AI/Automation."""
    monkeypatch.setattr(business_simulation, "SIMULATION_REPORT", tmp_path / "MEC_BUSINESS_SIMULATION_REPORT.md")
    monkeypatch.setattr(business_simulation, "SIMULATION_EVIDENCE", tmp_path / "business_simulation.json")
    monkeypatch.setattr(business_simulation, "EXECUTIVE_DASHBOARD", tmp_path / "executive_dashboard.json")

    with override_settings(MEDIA_ROOT=tmp_path / "media"):
        result = business_simulation.run_simulation()

    assert result["status"] == "MEC_BUSINESS_SIMULATION_COMPLETE"
    assert result["fictional_data_only"] is True
    assert result["safety"]["production_deployed"] is False
    assert result["safety"]["real_customer_data_used"] is False
    assert result["safety"]["human_approval_required"] is True

    assert FoundationUser.objects.filter(email="ceo.demo@mecprecision.vn").exists()
    assert BusinessCustomer.objects.filter(company_name="ABC Automotive Manufacturing").exists()
    assert BusinessProduct.objects.filter(name="CNC Precision Shaft").exists()
    assert KnowledgeDocument.objects.filter(title="CNC Precision Shaft Technical Specification").exists()

    abc = BusinessCustomer.objects.get(company_name="ABC Automotive Manufacturing")
    assert CrmInteraction.objects.filter(customer=abc).count() >= 4
    assert CrmTask.objects.filter(customer=abc).exists()

    lead = SalesLead.objects.get(company="ABC Automotive Manufacturing")
    assert lead.status == "won"
    assert SalesOpportunity.objects.filter(customer=abc, status="won").exists()
    quotation = SalesQuotation.objects.get(quotation_number="SIM-ABC-2026-001")
    assert quotation.status == "accepted"
    assert quotation.approval_status == "approved"
    assert quotation.total > 0

    assert result["ai"]["knowledge"]["material_question"]["sources"]
    assert result["ai"]["knowledge"]["material_question"]["confidence"] > 0
    assert result["ai"]["sales_assistant"]["email_draft"]["human_approval_required"] is True
    assert result["ai"]["sales_assistant"]["email_draft"]["delivery_status"] == "draft_only_not_sent"

    assert result["automation"]["website_lead"]["status"] == "N8N_LOCAL_AUTOMATION_READY"
    assert result["automation"]["document_update"]["status"] == "N8N_LOCAL_AUTOMATION_READY"
    assert result["automation"]["sales_follow_up"]["status"] == "N8N_LOCAL_AUTOMATION_READY"

    dashboard = result["executive_dashboard"]
    assert "sales_overview" in dashboard
    assert "automation_status" in dashboard
    assert dashboard["ai_activity"]["sales_human_approval_required"] is True


@pytest.mark.django_db
def test_business_simulation_writes_report_and_evidence(tmp_path, monkeypatch):
    """Simulation phai tao report va evidence de reviewer/doc gia xem lai."""
    report = tmp_path / "report.md"
    evidence = tmp_path / "business_simulation.json"
    dashboard = tmp_path / "dashboard.json"
    monkeypatch.setattr(business_simulation, "SIMULATION_REPORT", report)
    monkeypatch.setattr(business_simulation, "SIMULATION_EVIDENCE", evidence)
    monkeypatch.setattr(business_simulation, "EXECUTIVE_DASHBOARD", dashboard)

    with override_settings(MEDIA_ROOT=tmp_path / "media"):
        business_simulation.run_simulation()

    assert report.exists()
    assert evidence.exists()
    assert dashboard.exists()
    assert "MEC_BUSINESS_SIMULATION_COMPLETE" in report.read_text(encoding="utf-8")
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert evidence_payload["status"] == "MEC_BUSINESS_SIMULATION_COMPLETE"
    assert evidence_payload["safety"]["external_ai_api_used"] is False

