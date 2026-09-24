"""AI Sales Assistant that suggests sales actions without executing them."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.ai_agent.services.sales_facts import SalesFactsService
from apps.ai_agent.services.sales_synthesis import GroundedSalesSynthesisService
from apps.business_core.models import BusinessCustomer
from apps.crm.services.crm_platform_service import CrmPlatformService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.synthetic_rag_demo import SyntheticRagWebDemoService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation, SalesRfq


class SalesAssistantService:
    """Read sales/CRM/knowledge data and return human-approved suggestions."""

    def __init__(
        self,
        knowledge_search=None,
        facts_service=None,
        synthesis_service=None,
        component_rag=None,
    ):
        """Allow tests to inject a deterministic knowledge search service."""
        self.knowledge_search = knowledge_search or KnowledgeSearchService()
        self.facts_service = facts_service or SalesFactsService()
        self.synthesis_service = synthesis_service or GroundedSalesSynthesisService()
        self.component_rag = component_rag or SyntheticRagWebDemoService()

    def analyze(self, payload, user=None):
        """Return the internal AI Sales MVP contract without taking business action."""
        context = self._analysis_context(payload)
        missing = self._missing_information(context)
        query = self._analysis_query(context)

        if self._is_out_of_scope(query):
            return self._analysis_result(
                status="UNAVAILABLE",
                context=context,
                priority="NEEDS_REVIEW",
                priority_reasons=["The request is outside the manufacturing sales scope."],
                missing_information=[],
                next_action="NO_ACTION",
                next_action_reason="No grounded sales or component recommendation is available.",
            )

        if self._is_insufficient(context):
            return self._analysis_result(
                status="NEEDS_MORE_INFORMATION",
                context=context,
                priority="NEEDS_REVIEW",
                priority_reasons=["Core technical requirements are incomplete."],
                missing_information=missing,
                next_action="REQUEST_TECHNICAL_DETAILS",
                next_action_reason="Material and manufacturing process are required before product matching.",
            )

        rag = self.component_rag.query(query, user=user, limit=3)
        sources = self._sales_sources(rag)
        matched_products = self._matched_products(sources)
        if rag.get("status") != "SUPPORTED" or not matched_products:
            return self._analysis_result(
                status="UNAVAILABLE",
                context=context,
                priority="NEEDS_REVIEW",
                priority_reasons=["No governed component evidence supports a product match."],
                missing_information=missing,
                next_action="ESCALATE_ENGINEERING_REVIEW",
                next_action_reason="Engineering must review the request because RAG returned no supported component.",
                risks=["Do not claim product capability without an approved source."],
            )

        priority, reasons = self._priority(context, matched_products, missing)
        next_action = "REQUEST_TECHNICAL_DETAILS" if missing else "REVIEW_PRODUCT_MATCH"
        next_reason = (
            "A human should collect the listed technical details before quotation preparation."
            if missing
            else "A human should validate the grounded component match before preparing a quotation."
        )
        return self._analysis_result(
            status="SUPPORTED",
            context=context,
            priority=priority,
            priority_reasons=reasons,
            missing_information=missing,
            next_action=next_action,
            next_action_reason=next_reason,
            matched_products=matched_products,
            sources=sources,
            risks=[
                "Component matching is advisory and does not confirm price, stock, delivery, certification, or manufacturability."
            ],
        )

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
        grade = self._grade(score)
        facts = self.facts_service.build_lead_facts(lead, score, grade, knowledge)
        synthesis = self.synthesis_service.synthesize(facts, task="lead_analysis")
        return {
            "lead": self._lead_snapshot(lead),
            "score": score,
            "grade": grade,
            "analysis": self._lead_analysis_text(lead, score),
            "recommendations": self._lead_recommendations(lead, score),
            "knowledge": self._knowledge_snapshot(knowledge),
            "facts": facts,
            "synthesis": synthesis,
            "generation_mode": synthesis["generation_mode"],
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
        facts = self.facts_service.build_email_facts(
            lead=lead,
            customer=customer,
            product_interest=product_interest,
            purpose=purpose,
            knowledge=knowledge,
        )
        synthesis = self.synthesis_service.synthesize(facts, task="email_draft")
        return {
            "draft": {**synthesis["draft_email"], "purpose": purpose},
            "knowledge": self._knowledge_snapshot(knowledge),
            "facts": facts,
            "synthesis": synthesis,
            "generation_mode": synthesis["generation_mode"],
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

    def _analysis_context(self, payload):
        """Load one canonical RFQ or normalize the controlled synthetic input."""
        if payload.get("rfq_id"):
            rfq = (
                SalesRfq.objects.select_related("customer", "assigned_to", "created_by")
                .prefetch_related("lines__material", "lines__part", "documents")
                .get(pk=payload["rfq_id"])
            )
            lines = list(rfq.lines.all())
            material = ", ".join(
                dict.fromkeys(
                    f"{line.material.material_code} {line.material.grade}".strip()
                    for line in lines
                    if line.material_id
                )
            )
            return {
                "input_reference": f"rfq:{rfq.pk}",
                "synthetic": False,
                "customer_name": rfq.customer.company_name or rfq.customer.contact_name,
                "known_customer": True,
                "request": " ".join(
                    value
                    for value in [
                        rfq.project_name,
                        rfq.notes,
                        *[f"{line.description} {line.technical_notes}" for line in lines],
                    ]
                    if value
                ),
                "material": material,
                "quantity": sum((line.quantity for line in lines), 0) if lines else None,
                "process": self._first_value(lines, "technical_notes"),
                "tolerance": self._first_value(lines, "tolerance"),
                "surface_treatment": "",
                "drawing_available": rfq.documents.exists(),
                "deadline": str(rfq.required_delivery_date or ""),
                "rfq_number": rfq.rfq_number,
            }
        return {
            "input_reference": "synthetic:ad-hoc",
            "synthetic": True,
            "customer_name": str(payload.get("customer_name", "")).strip(),
            "known_customer": bool(str(payload.get("customer_name", "")).strip()),
            "request": str(payload.get("request", "")).strip(),
            "material": str(payload.get("material", "")).strip(),
            "quantity": payload.get("quantity"),
            "process": str(payload.get("process", "")).strip(),
            "tolerance": str(payload.get("tolerance", "")).strip(),
            "surface_treatment": str(payload.get("surface_treatment", "")).strip(),
            "drawing_available": payload.get("drawing_available"),
            "deadline": str(payload.get("deadline", "")).strip(),
            "rfq_number": "",
        }

    @staticmethod
    def _first_value(lines, field):
        return next((str(getattr(line, field, "")).strip() for line in lines if getattr(line, field, "")), "")

    @staticmethod
    def _analysis_query(context):
        return " ".join(
            str(context.get(field) or "")
            for field in ("request", "material", "process", "surface_treatment", "tolerance")
        ).strip()

    @staticmethod
    def _is_out_of_scope(query):
        lowered = query.casefold()
        out_of_scope = {"weather", "forecast", "temperature", "thời tiết", "nhiệt độ"}
        manufacturing = {
            "cnc", "machining", "precision", "component", "part", "material",
            "sus", "steel", "aluminium", "aluminum", "electropolish", "milling",
            "turning", "grinding", "edm", "gia công", "chi tiết", "dung sai",
        }
        return any(term in lowered for term in out_of_scope) and not any(
            term in lowered for term in manufacturing
        )

    @staticmethod
    def _is_insufficient(context):
        query = str(context.get("request", "")).casefold()
        material = str(context.get("material", "")).strip()
        process = " ".join(
            [str(context.get("process", "")), str(context.get("surface_treatment", ""))]
        ).strip()
        material_tokens = ("sus", "steel", "aluminium", "aluminum", "bronze", "pom", "titanium", "nhôm", "thép")
        process_tokens = ("cnc", "machin", "milling", "turning", "grinding", "edm", "polish", "anod", "gia công", "mài")
        has_material = bool(material) or any(token in query for token in material_tokens)
        has_process = bool(process) or any(token in query for token in process_tokens)
        return not (has_material and has_process)

    @staticmethod
    def _missing_information(context):
        fields = [
            ("quantity", "requested quantity"),
            ("tolerance", "drawing tolerance"),
            ("surface_treatment", "surface finish requirement"),
            ("drawing_available", "drawing/document availability"),
            ("deadline", "required delivery deadline"),
        ]
        missing = [label for field, label in fields if context.get(field) in (None, "", False)]
        if not context.get("material") and not any(
            term in str(context.get("request", "")).casefold()
            for term in ("sus", "steel", "aluminium", "aluminum", "bronze", "pom", "titanium", "nhôm", "thép")
        ):
            missing.insert(0, "requested material")
        if not context.get("process") and not any(
            term in str(context.get("request", "")).casefold()
            for term in ("cnc", "machin", "milling", "turning", "grinding", "edm", "polish", "anod", "gia công", "mài")
        ):
            missing.insert(0, "manufacturing process")
        return missing

    @staticmethod
    def _sales_sources(rag):
        return [
            {
                "id": source.get("document_id", source.get("id")),
                "title": source.get("title", ""),
                "product_code": source.get("product_code", ""),
                "citation": source.get("citation", ""),
                "version": source.get("version"),
                "revision": source.get("revision"),
                "relevance_score": source.get("relevance_score", 0),
            }
            for source in rag.get("sources", [])
        ]

    @staticmethod
    def _matched_products(sources):
        return [
            {
                "product_code": source["product_code"],
                "title": source["title"],
                "reason": "The governed RAG result contains matching material/process evidence.",
                "source_id": source["id"],
            }
            for source in sources
            if source.get("product_code")
        ]

    @staticmethod
    def _priority(context, matched_products, missing):
        reasons = []
        if context.get("known_customer"):
            reasons.append("known customer/company context")
        if context.get("quantity"):
            reasons.append("requested quantity is provided")
        if context.get("material") or "sus" in str(context.get("request", "")).casefold():
            reasons.append("material requirement is clear")
        if context.get("process") or context.get("surface_treatment") or "polish" in str(context.get("request", "")).casefold():
            reasons.append("manufacturing or surface process is clear")
        if matched_products:
            reasons.append("governed component evidence was found")
        if len(reasons) >= 4 and len(missing) <= 3:
            return "HIGH", reasons
        if len(reasons) >= 3:
            return "MEDIUM", reasons
        return "LOW", reasons or ["Limited business and technical context is available."]

    def _analysis_result(
        self,
        *,
        status,
        context,
        priority,
        priority_reasons,
        missing_information,
        next_action,
        next_action_reason,
        matched_products=None,
        sources=None,
        risks=None,
    ):
        company = context.get("customer_name") or "customer"
        request = context.get("request") or "the precision-component request"
        summary = f"{company}: {request[:400]}"
        if status == "UNAVAILABLE":
            draft = "No customer response should be prepared because the request is not supported by governed sales evidence."
        elif missing_information:
            draft = (
                f"Hello {company},\n\nThank you for your request. Before our team reviews a possible component match, "
                f"please provide: {', '.join(missing_information)}. We will review the information and respond after human technical approval."
            )
        else:
            draft = (
                f"Hello {company},\n\nThank you for your request. Our team found a potentially relevant component record. "
                "A sales and engineering colleague will review the technical fit before any quotation or commitment is made."
            )
        return {
            "status": status,
            "summary": summary,
            "priority": priority,
            "priority_reasons": priority_reasons,
            "matched_products": matched_products or [],
            "recommended_next_action": next_action,
            "recommended_next_action_reason": next_action_reason,
            "draft_response": draft,
            "risks": risks or [],
            "missing_information": missing_information,
            "sources": sources or [],
            "input_reference": context["input_reference"],
            "synthetic_input": context["synthetic"],
            "human_approval_required": True,
            "autonomous_action": False,
            "safety_note": "AI recommendation — human review required. No email, quotation, order, price, RFQ, or customer action was executed.",
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
