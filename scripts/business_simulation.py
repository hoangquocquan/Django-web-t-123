"""End-to-end business simulation for the MEC Precision learning platform.

Script nay tao du lieu gia lap va chay luong CRM, Sales, Knowledge AI, AI Sales
va n8n local automation. No khong tao feature moi va khong dung du lieu khach
hang that.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_BACKEND = PROJECT_ROOT / "django_backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(DJANGO_BACKEND) not in sys.path:
    sys.path.insert(0, str(DJANGO_BACKEND))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
from django.apps import apps as django_apps

if not django_apps.ready:
    django.setup()

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.db import transaction

from apps.ai_agent.services.sales_assistant import SalesAssistantService
from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmCustomerProfile, CrmInteraction, CrmNote, CrmTask, CrmTimelineEvent
from apps.foundation.models import FoundationRole, FoundationUser, FoundationUserProfile
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.document_intelligence import DocumentIntelligenceService
from apps.sales.models import SalesActivity, SalesFollowUp, SalesLead, SalesOpportunity, SalesQuotation
from apps.sales.services.sales_platform_service import LEAD_STATUS_FLOW, SalesPlatformService
from scripts.n8n_business_wave2 import run_local_automation, sign_payload


SIMULATION_REPORT = PROJECT_ROOT / "docs" / "reviews" / "MEC_BUSINESS_SIMULATION_REPORT.md"
SIMULATION_EVIDENCE = PROJECT_ROOT / "ai-factory" / "evidence" / "business_simulation.json"
EXECUTIVE_DASHBOARD = PROJECT_ROOT / "docs" / "reviews" / "business_simulation_executive_dashboard.json"
AUTOMATION_OUTPUT_DIR = PROJECT_ROOT / "docs" / "reviews" / "business_simulation_automation"


def utc_now():
    """Return an ISO timestamp for simulation evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_default(value):
    """Serialize Decimal and Django objects safely for evidence files."""
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def ensure_role(name):
    """Create a simple role if migrations did not seed it yet."""
    role, _created = FoundationRole.objects.get_or_create(
        name=name,
        defaults={"description": f"Simulation {name} role"},
    )
    return role


def ensure_user(email, full_name, role_name):
    """Create or update one fictional internal user."""
    role = ensure_role(role_name)
    user, _created = FoundationUser.objects.update_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "password_hash": make_password("SecurePass123!"),
        },
    )
    FoundationUserProfile.objects.get_or_create(user=user)
    return user


def create_master_data():
    """Create users, customers, products, and demo documents."""
    users = {
        "ceo": ensure_user("ceo.demo@mecprecision.vn", "Demo CEO", "admin"),
        "sales_manager": ensure_user("sales.manager.demo@mecprecision.vn", "Demo Sales Manager", "admin"),
        "sales_staff": ensure_user("sales.staff.demo@mecprecision.vn", "Demo Sales Staff", "editor"),
        "technical_engineer": ensure_user("technical.engineer.demo@mecprecision.vn", "Demo Technical Engineer", "editor"),
    }

    customer_specs = [
        {
            "company_name": "ABC Automotive Manufacturing",
            "contact_name": "Ms. Anna Tran",
            "email": "anna.tran@abc-auto.example",
            "phone": "+84 900 111 222",
            "country": "Vietnam",
            "status": "active",
            "notes": "Fictional automotive customer for CNC precision component simulation.",
        },
        {
            "company_name": "XYZ Mechanical",
            "contact_name": "Mr. Minh Le",
            "email": "minh.le@xyz-mechanical.example",
            "phone": "+84 900 333 444",
            "country": "Vietnam",
            "status": "lead",
            "notes": "Fictional mechanical buyer.",
        },
        {
            "company_name": "Global Parts Co",
            "contact_name": "Ms. Sara Kim",
            "email": "sara.kim@global-parts.example",
            "phone": "+81 80 5555 0101",
            "country": "Japan",
            "status": "active",
            "notes": "Fictional international parts distributor.",
        },
    ]
    customers = {}
    for spec in customer_specs:
        customer, _created = BusinessCustomer.objects.update_or_create(
            email=spec["email"],
            defaults=spec,
        )
        customers[spec["company_name"]] = customer

    product_specs = [
        {
            "name": "CNC Precision Shaft",
            "slug": "simulation-cnc-precision-shaft",
            "sku": "SIM-CNC-SHAFT",
            "category_name": "Automotive Components",
            "price": Decimal("125.00"),
            "status": "published",
            "short_description": "Precision CNC shaft for automotive assemblies.",
            "description": "SCM440 alloy steel shaft with tight tolerance and CMM inspection.",
            "seo_title": "CNC Precision Shaft",
            "seo_description": "Fictional demo product for MEC Precision simulation.",
        },
        {
            "name": "Aluminum Housing",
            "slug": "simulation-aluminum-housing",
            "sku": "SIM-AL-HOUSING",
            "category_name": "Machined Housings",
            "price": Decimal("220.00"),
            "status": "published",
            "short_description": "Aluminum CNC housing for machine assemblies.",
            "description": "Anodized aluminum housing with inspection report.",
        },
        {
            "name": "Steel Component",
            "slug": "simulation-steel-component",
            "sku": "SIM-ST-COMP",
            "category_name": "Steel Components",
            "price": Decimal("95.00"),
            "status": "published",
            "short_description": "General steel component for manufacturing demo.",
            "description": "Milled steel component with documented process route.",
        },
    ]
    products = {}
    for spec in product_specs:
        product, _created = BusinessProduct.objects.update_or_create(
            slug=spec["slug"],
            defaults=spec,
        )
        products[spec["name"]] = product

    document_results = create_demo_documents(created_by_email=users["technical_engineer"].email)
    return {"users": users, "customers": customers, "products": products, "documents": document_results}


def create_demo_documents(created_by_email):
    """Upload demo documents through the Document Intelligence service."""
    service = DocumentIntelligenceService()
    documents = [
        (
            "MEC Product Catalogue",
            "product-catalogue.txt",
            "Product catalogue: CNC Precision Shaft, Aluminum Housing, Steel Component for manufacturing buyers.",
        ),
        (
            "CNC Precision Shaft Technical Specification",
            "cnc-shaft-technical-specification.txt",
            "CNC Precision Shaft material is SCM440 alloy steel. Tolerance target is +/- 0.01 mm after CNC turning and grinding.",
        ),
        (
            "MEC Quality Procedure",
            "quality-procedure.txt",
            "QC process applies: incoming material check, in-process CNC inspection, CMM final inspection, and quality record approval.",
        ),
        (
            "Manufacturing Guideline",
            "manufacturing-guideline.txt",
            "Manufacturing guideline: review drawing, confirm material, plan CNC process, inspect first article, then release production.",
        ),
    ]
    results = []
    for title, filename, content in documents:
        existing = None
        from apps.knowledge.models import KnowledgeDocument

        existing = KnowledgeDocument.objects.filter(title=title).first()
        if existing:
            metadata = existing.metadata.get("document_intelligence", {})
            results.append(
                {
                    "title": title,
                    "document_id": existing.id,
                    "classification": metadata.get("classification", "existing"),
                    "confidence": metadata.get("confidence", 0),
                    "approval_status": metadata.get("approval_status", "existing"),
                }
            )
            continue
        upload = ContentFile(content.encode("utf-8"), name=filename)
        result = service.ingest_uploaded_document(
            upload,
            title=title,
            created_by_email=created_by_email,
            permission_level="internal",
        )
        results.append(result.to_dict())
    return results


def simulate_crm(master):
    """Create the fictional ABC Automotive customer journey."""
    customer = master["customers"]["ABC Automotive Manufacturing"]
    owner = master["users"]["sales_manager"]
    CrmCustomerProfile.objects.update_or_create(
        customer=customer,
        defaults={
            "segment": "strategic",
            "lifecycle_stage": "opportunity",
            "preferred_contact_method": "email",
            "assigned_owner": owner,
            "summary": "ABC Automotive needs precision CNC components for automotive assemblies.",
        },
    )
    interactions = [
        ("first_contact", "First contact", "Customer asked about CNC precision shaft capability."),
        ("technical_discussion", "Technical discussion", "Engineer discussed material, tolerance, and inspection approach."),
        ("requirement_collection", "Requirement collection", "Sales collected quantity, deadline, drawing status, and QC requirements."),
        ("follow_up", "Follow-up", "Sales prepared follow-up email and quotation plan."),
    ]
    created_interactions = []
    for interaction_type, subject, content in interactions:
        interaction, _created = CrmInteraction.objects.get_or_create(
            customer=customer,
            subject=subject,
            defaults={
                "interaction_type": interaction_type,
                "content": content,
                "created_by": owner.email,
            },
        )
        created_interactions.append(interaction)
        CrmTimelineEvent.objects.get_or_create(
            customer=customer,
            event_type=interaction_type,
            title=subject,
            defaults={"payload": {"interaction_id": interaction.id}},
        )
    CrmNote.objects.get_or_create(
        customer=customer,
        note="ABC Automotive is high potential because the requirement matches CNC Precision Shaft capability.",
        defaults={"created_by": owner.email},
    )
    CrmTask.objects.get_or_create(
        customer=customer,
        title="Send quotation and request drawing confirmation",
        defaults={"due_date": "2026-08-05", "status": "open", "owner": owner},
    )
    return {
        "customer_id": customer.id,
        "interactions": len(created_interactions),
        "notes": customer.crm_notes.count(),
        "tasks": customer.crm_tasks.count(),
        "timeline": customer.crm_timeline_events.count(),
    }


def simulate_sales_pipeline(master):
    """Move ABC Automotive through the complete sales pipeline."""
    service = SalesPlatformService()
    owner = master["users"]["sales_manager"]
    customer = master["customers"]["ABC Automotive Manufacturing"]
    shaft = master["products"]["CNC Precision Shaft"]
    housing = master["products"]["Aluminum Housing"]

    lead, created = SalesLead.objects.get_or_create(
        company="ABC Automotive Manufacturing",
        defaults={
            "lead_source": "Website",
            "contact_person": "Ms. Anna Tran",
            "email": customer.email,
            "phone": customer.phone,
            "industry": "Automotive Components",
            "status": "new",
            "priority": "high",
            "owner": owner,
            "notes": "Customer needs precision CNC components.",
        },
    )
    if not created:
        lead.contact_person = "Ms. Anna Tran"
        lead.email = customer.email
        lead.industry = "Automotive Components"
        lead.priority = "high"
        lead.owner = owner
        lead.notes = "Customer needs precision CNC components."
        lead.save()

    start_index = LEAD_STATUS_FLOW.index(lead.status) if lead.status in LEAD_STATUS_FLOW else 0
    for status in LEAD_STATUS_FLOW[start_index: LEAD_STATUS_FLOW.index("won") + 1]:
        if lead.status != status:
            lead = service.advance_lead(lead.id, status, actor=owner.email)

    opportunity, _created = SalesOpportunity.objects.update_or_create(
        title="ABC Automotive CNC precision component program",
        defaults={
            "lead": lead,
            "customer": customer,
            "value": Decimal("18500.00"),
            "probability": 95,
            "expected_close_date": "2026-08-30",
            "sales_owner": owner,
            "status": "won",
            "notes": "Won demo opportunity after quotation negotiation.",
        },
    )

    quotation = SalesQuotation.objects.filter(quotation_number="SIM-ABC-2026-001").first()
    if not quotation:
        quotation = service.create_quotation(
            {
                "opportunity_id": opportunity.id,
                "customer_id": customer.id,
                "quotation_number": "SIM-ABC-2026-001",
                "status": "accepted",
                "approval_status": "approved",
                "lines": [
                    {
                        "product_id": shaft.id,
                        "description": "CNC Precision Shaft - SCM440 alloy steel",
                        "quantity": "100",
                        "unit_price": "125",
                        "discount": "500",
                    },
                    {
                        "product_id": housing.id,
                        "description": "Aluminum Housing prototype batch",
                        "quantity": "20",
                        "unit_price": "220",
                        "discount": "0",
                    },
                ],
            },
            user=owner,
        )
    else:
        quotation.status = "accepted"
        quotation.approval_status = "approved"
        quotation.save(update_fields=["status", "approval_status", "updated_at"])

    SalesFollowUp.objects.get_or_create(
        lead=lead,
        opportunity=opportunity,
        customer=customer,
        title="Confirm production kickoff with ABC Automotive",
        defaults={
            "due_date": "2026-08-06",
            "status": "open",
            "owner": owner,
            "note": "Confirm drawing revision, delivery plan, and QC report format.",
        },
    )
    SalesActivity.objects.get_or_create(
        lead=lead,
        opportunity=opportunity,
        customer=customer,
        subject="Quotation accepted by ABC Automotive",
        defaults={
            "activity_type": "quotation",
            "content": "Customer accepted the fictional quotation in the simulation.",
            "created_by": owner.email,
        },
    )
    return {
        "lead_id": lead.id,
        "lead_status": lead.status,
        "opportunity_id": opportunity.id,
        "opportunity_status": opportunity.status,
        "quotation_id": quotation.id,
        "quotation_number": quotation.quotation_number,
        "quotation_status": quotation.status,
        "approval_status": quotation.approval_status,
        "quotation_total": quotation.total,
    }


def simulate_ai(master):
    """Ask Knowledge AI and AI Sales using the demo data."""
    user = master["users"]["sales_manager"]
    customer = master["customers"]["ABC Automotive Manufacturing"]
    lead = SalesLead.objects.get(company="ABC Automotive Manufacturing")
    knowledge_service = KnowledgeAssistantService()
    material_answer = knowledge_service.answer("What material is used for CNC Precision Shaft?", user=user)
    qc_answer = knowledge_service.answer("What QC process applies?", user=user)
    sales_service = SalesAssistantService()
    customer_summary = sales_service.handle("customer_summary", {"customer_id": customer.id}, user=user)
    email_draft = sales_service.handle(
        "email_draft",
        {
            "lead_id": lead.id,
            "purpose": "follow_up",
            "product_interest": "CNC Precision Shaft quotation",
        },
        user=user,
    )
    return {
        "knowledge": {
            "material_question": material_answer,
            "qc_question": qc_answer,
        },
        "sales_assistant": {
            "customer_summary": customer_summary,
            "email_draft": email_draft,
        },
    }


def simulate_automation(master):
    """Run all local n8n-style workflows with signed demo payloads."""
    payloads = {
        "website_lead": {"company": "ABC Automotive Manufacturing", "need": "precision CNC components"},
        "document_update": {"title": "CNC Precision Shaft Technical Specification"},
        "sales_follow_up": {"customer": "ABC Automotive Manufacturing", "task": "Confirm production kickoff"},
    }
    results = {}
    for workflow_name, payload in payloads.items():
        results[workflow_name] = run_local_automation(
            workflow_name,
            payload,
            sign_payload(payload),
            output_path=AUTOMATION_OUTPUT_DIR / f"{workflow_name}.json",
        )
    return results


def executive_dashboard(crm_result, sales_result, ai_result, automation_result):
    """Generate the executive dashboard data requested by the simulation."""
    dashboard = SalesPlatformService().dashboard()
    return {
        "sales_overview": dashboard,
        "pipeline_value": dashboard["pipeline_value"],
        "customer_status": {
            "active": BusinessCustomer.objects.filter(status="active").count(),
            "lead": BusinessCustomer.objects.filter(status="lead").count(),
        },
        "crm_activity": crm_result,
        "sales_flow": sales_result,
        "ai_activity": {
            "material_confidence": ai_result["knowledge"]["material_question"]["confidence"],
            "qc_confidence": ai_result["knowledge"]["qc_question"]["confidence"],
            "sales_human_approval_required": ai_result["sales_assistant"]["email_draft"]["human_approval_required"],
        },
        "automation_status": {
            key: value["status"] for key, value in automation_result.items()
        },
    }


def write_report(result):
    """Write human-readable Markdown report."""
    report = f"""# MEC Business Simulation Report

## Status

MEC_BUSINESS_SIMULATION_COMPLETE

## Demo Data Created

- Users: CEO, Sales Manager, Sales Staff, Technical Engineer
- Customers: ABC Automotive Manufacturing, XYZ Mechanical, Global Parts Co
- Products: CNC Precision Shaft, Aluminum Housing, Steel Component
- Documents: Product catalogue, Technical specification, Quality procedure, Manufacturing guideline

## CRM Flow Result

ABC Automotive journey created with interactions, notes, tasks, and timeline.

```json
{json.dumps(result["crm"], indent=2, ensure_ascii=False, default=json_default)}
```

## Sales Flow Result

ABC Automotive moved through lead pipeline to Won and received accepted quotation.

```json
{json.dumps(result["sales"], indent=2, ensure_ascii=False, default=json_default)}
```

## AI Knowledge Result

Material and QC questions were answered with source retrieval, confidence, and warnings when applicable.

```json
{json.dumps(result["ai"]["knowledge"], indent=2, ensure_ascii=False, default=json_default)}
```

## AI Sales Result

AI Sales generated customer summary and follow-up email draft. Human approval is required.

## Automation Result

Local n8n-style workflows ran for new lead, document update, and sales reminder.

```json
{json.dumps(result["automation"], indent=2, ensure_ascii=False, default=json_default)}
```

## Problems Found

- Real OCR is still local best-effort. Scanned PDFs require an OCR engine before production use.
- AI answers should remain source-grounded and human reviewed.

## Improvement Suggestions

- Add richer demo charts to Business UI.
- Add real n8n runtime when Docker is available.
- Add OCR engine integration for scanned drawings/catalogues.
"""
    SIMULATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SIMULATION_REPORT.write_text(report, encoding="utf-8")


@transaction.atomic
def run_simulation():
    """Run the complete fictional business scenario."""
    master = create_master_data()
    crm_result = simulate_crm(master)
    sales_result = simulate_sales_pipeline(master)
    ai_result = simulate_ai(master)
    automation_result = simulate_automation(master)
    dashboard = executive_dashboard(crm_result, sales_result, ai_result, automation_result)
    result = {
        "created_at": utc_now(),
        "status": "MEC_BUSINESS_SIMULATION_COMPLETE",
        "fictional_data_only": True,
        "master_data": {
            "users": [user.email for user in master["users"].values()],
            "customers": [customer.company_name for customer in master["customers"].values()],
            "products": [product.name for product in master["products"].values()],
            "documents": master["documents"],
        },
        "crm": crm_result,
        "sales": sales_result,
        "ai": ai_result,
        "automation": automation_result,
        "executive_dashboard": dashboard,
        "safety": {
            "production_deployed": False,
            "real_customer_data_used": False,
            "external_ai_api_used": False,
            "human_approval_required": True,
        },
    }
    for output_path in [SIMULATION_EVIDENCE, EXECUTIVE_DASHBOARD]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    SIMULATION_EVIDENCE.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=json_default), encoding="utf-8")
    EXECUTIVE_DASHBOARD.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False, default=json_default), encoding="utf-8")
    write_report(result)
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = run_simulation()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=json_default))


if __name__ == "__main__":
    main()
