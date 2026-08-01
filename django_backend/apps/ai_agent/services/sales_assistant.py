"""AI Sales Assistant that suggests sales actions without executing them."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.business_core.models import BusinessCustomer
from apps.crm.services.crm_platform_service import CrmPlatformService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation


class SalesAssistantService:
    """Read sales/CRM/knowledge data and return human-approved suggestions."""

    def __init__(self, knowledge_search=None):
        """Allow tests to inject a deterministic knowledge search service."""
        self.knowledge_search = knowledge_search or KnowledgeSearchService()

    def handle(self, action, payload, user=None):
        """Dispatch one supported AI sales action."""
        handlers = {
            "lead_analysis": self.analyze_lead,
            "customer_summary": self.customer_summary,
            "email_draft": self.email_draft,
            "weekly_recommendation": self.weekly_recommendation,
        }
        if action not in handlers:
            raise ValidationError("Unsupported AI sales action.")
        result = handlers[action](payload, user=user)
        result.setdefault("response_quality", self._response_quality(result.get("knowledge")))
        result.update(
            {
                "action": action,
                "human_approval_required": True,
                "autonomous_action": False,
                "safety_note": "AI chi dua ra goi y. Nhan vien phai duyet truoc khi gui email, sua CRM hoac duyet bao gia.",
            }
        )
        return result

    def analyze_lead(self, payload, user=None):
        """Score a lead by fit, urgency, and available technical knowledge."""
        lead = self._lead_from_payload(payload)
        query = " ".join([lead.company, lead.industry, lead.notes, "CNC quotation product fit"])
        knowledge = self.knowledge_search.search(query, limit=3, user=user)
        score = self._lead_score(lead, knowledge)
        return {
            "lead": self._lead_snapshot(lead),
            "score": score,
            "grade": self._grade(score),
            "analysis": self._lead_analysis_text(lead, score),
            "recommendations": self._lead_recommendations(lead, score),
            "knowledge": self._knowledge_snapshot(knowledge),
            "response_quality": self._response_quality(knowledge),
        }

    def customer_summary(self, payload, user=None):
        """Summarize one customer with CRM timeline and open sales context."""
        customer_id = payload.get("customer_id")
        if not customer_id:
            raise ValidationError("customer_id is required.")
        context = CrmPlatformService().get_customer_context(customer_id)
        customer = context["customer"]
        knowledge = self.knowledge_search.search(customer.company_name or customer.contact_name, limit=3, user=user)
        open_opportunities = SalesOpportunity.objects.filter(customer=customer).exclude(status__in=["won", "lost"])
        open_quotations = SalesQuotation.objects.filter(customer=customer).exclude(status__in=["accepted", "lost"])
        return {
            "customer": self._customer_snapshot(customer),
            "summary": {
                "interactions": context["interactions"].count(),
                "notes": context["notes"].count(),
                "tasks": context["tasks"].count(),
                "open_opportunities": open_opportunities.count(),
                "open_quotations": open_quotations.count(),
            },
            "recommendations": [
                "Kiem tra nhu cau hien tai truoc khi gui bao gia moi.",
                "Uu tien lien he lai neu co co hoi dang mo hoac bao gia chua phan hoi.",
            ],
            "knowledge": self._knowledge_snapshot(knowledge),
            "response_quality": self._response_quality(knowledge),
        }

    def email_draft(self, payload, user=None):
        """Generate a draft email that a human can review and send manually."""
        purpose = payload.get("purpose", "follow_up")
        lead = None
        customer = None
        if payload.get("lead_id"):
            lead = SalesLead.objects.get(id=payload["lead_id"])
        if payload.get("customer_id"):
            customer = BusinessCustomer.objects.get(id=payload["customer_id"])
        recipient_name = payload.get("recipient_name") or self._recipient_name(lead, customer)
        company = payload.get("company") or self._company_name(lead, customer)
        product_interest = payload.get("product_interest", "giai phap gia cong co khi chinh xac")
        knowledge = self.knowledge_search.search(f"{company} {product_interest}", limit=2, user=user)
        return {
            "draft": {
                "subject": f"MecPrecision VIETNAM - Trao doi ve {product_interest}",
                "body": (
                    f"Xin chao {recipient_name},\n\n"
                    f"Cam on {company} da quan tam den {product_interest}. "
                    "Doi ngu MecPrecision co the ho tro gia cong CNC, do ga va kiem tra chat luong theo yeu cau.\n\n"
                    "Neu anh/chi co ban ve ky thuat, so luong du kien hoac thoi han can giao, vui long gui lai de chung toi tu van phuong an phu hop.\n\n"
                    "Tran trong,\nMecPrecision VIETNAM"
                ),
                "purpose": purpose,
            },
            "knowledge": self._knowledge_snapshot(knowledge),
            "delivery_status": "draft_only_not_sent",
            "response_quality": self._response_quality(knowledge),
        }

    def weekly_recommendation(self, payload, user=None):
        """Recommend leads and opportunities that need human sales attention."""
        leads = SalesLead.objects.exclude(status__in=["won", "lost"]).order_by("-updated_at", "-id")[:5]
        opportunities = SalesOpportunity.objects.exclude(status__in=["won", "lost"]).order_by("-value", "-id")[:5]
        return {
            "leads_to_contact": [self._lead_snapshot(lead) for lead in leads],
            "opportunities_to_review": [
                {
                    "id": opportunity.id,
                    "title": opportunity.title,
                    "value": str(opportunity.value),
                    "probability": opportunity.probability,
                    "status": opportunity.status,
                }
                for opportunity in opportunities
            ],
            "recommendations": [
                "Lien he truoc voi lead uu tien cao hoac da chuyen sang Contacted/Meeting.",
                "Kiem tra cac co hoi co gia tri lon nhung xac suat con thap de bo sung thong tin ky thuat.",
            ],
            "response_quality": {
                "confidence": 0.7,
                "source_relevance_score": 0,
                "hallucination_warning": "",
                "evaluation": "Operational recommendation from CRM and Sales database, not autonomous execution.",
            },
        }

    def _lead_from_payload(self, payload):
        """Return a database lead or a temporary lead-like object from payload."""
        if payload.get("lead_id"):
            return SalesLead.objects.get(id=payload["lead_id"])
        required = ["company", "contact_person"]
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValidationError(f"Missing lead fields: {', '.join(missing)}")
        return SalesLead(
            company=payload["company"],
            contact_person=payload["contact_person"],
            email=payload.get("email", ""),
            phone=payload.get("phone", ""),
            industry=payload.get("industry", ""),
            status=payload.get("status", "new"),
            priority=payload.get("priority", "medium"),
            notes=payload.get("notes", ""),
        )

    def _lead_score(self, lead, knowledge):
        """Calculate a simple explainable score instead of opaque automation."""
        score = 40
        if lead.priority == "high":
            score += 20
        if lead.status in {"meeting", "quotation", "negotiation"}:
            score += 15
        if any(word in f"{lead.industry} {lead.notes}".lower() for word in ["cnc", "fixture", "do ga", "truc"]):
            score += 15
        score += int(knowledge.get("confidence", 0) * 10)
        return min(score, 100)

    def _grade(self, score):
        """Convert score into a compact business grade."""
        if score >= 80:
            return "A"
        if score >= 65:
            return "B"
        if score >= 50:
            return "C"
        return "D"

    def _lead_analysis_text(self, lead, score):
        """Explain why a lead is useful for sales follow-up."""
        if score >= 80:
            return f"{lead.company} la lead tiem nang cao, nen uu tien lien he va thu thap ban ve ky thuat."
        if score >= 60:
            return f"{lead.company} co dau hieu phu hop, can hoi them nhu cau, so luong va vat lieu."
        return f"{lead.company} can bo sung them thong tin truoc khi dau tu nhieu thoi gian ban hang."

    def _lead_recommendations(self, lead, score):
        """Return next-step suggestions that still require human approval."""
        recommendations = ["Ghi lai nhu cau ky thuat va nguoi quyet dinh mua hang."]
        if score >= 70:
            recommendations.append("Dat lich tu van ky thuat hoac moi khach gui ban ve.")
        else:
            recommendations.append("Gui email gioi thieu nang luc va hoi lai thong tin san pham can gia cong.")
        return recommendations

    def _knowledge_snapshot(self, knowledge):
        """Return compact RAG evidence without exposing unnecessary internals."""
        return {
            "confidence": knowledge.get("confidence", 0),
            "sources": [
                {
                    "id": source.get("id"),
                    "title": source.get("title"),
                    "relevance_score": source.get("relevance_score", 0),
                }
                for source in knowledge.get("sources", [])
            ],
        }

    def _response_quality(self, knowledge):
        """Explain how reliable an AI sales suggestion is."""
        if not knowledge:
            return {
                "confidence": 0.5,
                "source_relevance_score": 0,
                "hallucination_warning": "",
                "evaluation": "No RAG source was required for this operational suggestion.",
            }
        sources = knowledge.get("sources", [])
        best_relevance = max([source.get("relevance_score", 0) for source in sources] or [0])
        confidence = knowledge.get("confidence", 0)
        warning = "" if sources else "No knowledge source found; sales user should verify manually."
        return {
            "confidence": confidence,
            "source_relevance_score": best_relevance,
            "hallucination_warning": warning,
            "evaluation": "Suggestion is advisory only and still requires human approval.",
        }

    def _lead_snapshot(self, lead):
        """Return a safe lead summary for AI output."""
        return {
            "id": lead.id,
            "company": lead.company,
            "contact_person": lead.contact_person,
            "industry": lead.industry,
            "status": lead.status,
            "priority": lead.priority,
        }

    def _customer_snapshot(self, customer):
        """Return a safe customer summary for AI output."""
        return {
            "id": customer.id,
            "company_name": customer.company_name,
            "contact_name": customer.contact_name,
            "email": customer.email,
            "status": customer.status,
        }

    def _recipient_name(self, lead, customer):
        """Pick the best recipient name from lead/customer context."""
        if lead:
            return lead.contact_person
        if customer:
            return customer.contact_name
        return "anh/chi"

    def _company_name(self, lead, customer):
        """Pick the best company name from lead/customer context."""
        if lead:
            return lead.company
        if customer:
            return customer.company_name or customer.contact_name
        return "quy cong ty"
