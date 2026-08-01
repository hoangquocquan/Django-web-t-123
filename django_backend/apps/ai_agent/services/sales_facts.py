"""Build deterministic, source-grounded facts for the AI Sales synthesizer."""

from __future__ import annotations


class SalesFactsService:
    """Keep business facts and lead scoring outside the language model."""

    def build_lead_facts(self, lead, score, grade, knowledge, action="lead_analysis", extra=None):
        """Return the only facts that the language model may use."""
        return {
            "lead_facts": {
                "id": lead.id,
                "company": lead.company,
                "contact_person": lead.contact_person,
                "industry": lead.industry,
                "status": lead.status,
                "priority": lead.priority,
                "notes": lead.notes,
            },
            "score_facts": {
                "score": int(score),
                "grade": grade,
                "factors": self._score_factors(lead, knowledge),
            },
            "crm_facts": {},
            "sales_facts": {"action": action, **(extra or {})},
            "knowledge_sources": self._knowledge_sources(knowledge),
        }

    def build_email_facts(self, lead, customer, product_interest, purpose, knowledge):
        """Build safe email drafting facts without asking the model to send anything."""
        company = lead.company if lead else getattr(customer, "company_name", "")
        contact = lead.contact_person if lead else getattr(customer, "contact_name", "")
        return {
            "lead_facts": {
                "id": getattr(lead, "id", None),
                "company": company,
                "contact_person": contact,
                "industry": getattr(lead, "industry", ""),
                "status": getattr(lead, "status", ""),
                "priority": getattr(lead, "priority", ""),
                "notes": getattr(lead, "notes", ""),
            },
            "score_facts": {},
            "crm_facts": {"customer_id": getattr(customer, "id", None)},
            "sales_facts": {
                "action": "email_draft",
                "purpose": purpose,
                "product_interest": product_interest,
            },
            "knowledge_sources": self._knowledge_sources(knowledge),
        }

    def _score_factors(self, lead, knowledge):
        """Explain score inputs with the same deterministic rules used by SalesAssistantService."""
        factors = ["base_score:40"]
        if lead.priority == "high":
            factors.append("high_priority:+20")
        if lead.status in {"meeting", "quotation", "negotiation"}:
            factors.append("advanced_pipeline:+15")
        text = f"{lead.industry} {lead.notes}".lower()
        if any(word in text for word in ["cnc", "fixture", "do ga", "truc"]):
            factors.append("technical_fit:+15")
        factors.append(f"knowledge_confidence:+{int(knowledge.get('confidence', 0) * 10)}")
        return factors

    def _knowledge_sources(self, knowledge):
        """Attach short source excerpts so generated claims can remain grounded."""
        source_by_id = {source.get("id"): source for source in knowledge.get("sources", [])}
        excerpts = {}
        for result in knowledge.get("results", []):
            document = result.get("document", {})
            source_id = document.get("id")
            if source_id not in excerpts:
                excerpts[source_id] = str(result.get("chunk", {}).get("content", ""))[:600]

        return [
            {
                "id": source_id,
                "title": source.get("title", ""),
                "relevance_score": source.get("relevance_score", 0),
                "excerpt": excerpts.get(source_id, ""),
            }
            for source_id, source in source_by_id.items()
        ]
