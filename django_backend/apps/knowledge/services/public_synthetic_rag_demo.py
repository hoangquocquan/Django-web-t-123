"""Public-shaped output for the explicitly local synthetic RAG demo."""

from __future__ import annotations

import re

from apps.knowledge.services.synthetic_rag_demo import (
    PART_CODE_RE,
    SyntheticRagWebDemoService,
)

PUBLIC_UNAVAILABLE_ANSWER = (
    "Hiện tại tôi chưa tìm thấy thông tin phù hợp trong dữ liệu để trả lời "
    "chính xác câu hỏi này."
)


class PublicSyntheticRagDemoService:
    """Reuse the internal synthetic RAG engine but expose no technical metadata."""

    def __init__(self, rag_service=None):
        self.rag_service = rag_service or SyntheticRagWebDemoService()

    def answer(self, message: str) -> dict:
        result = self.rag_service.query(message, user=None, limit=3)
        sources = [
            {
                "title": source["title"],
                "product_code": source["product_code"],
            }
            for source in result.get("sources", [])
            if isinstance(source, dict)
            and isinstance(source.get("title"), str)
            and source["title"].startswith("[SYNTHETIC DEMO]")
            and isinstance(source.get("product_code"), str)
            and PART_CODE_RE.fullmatch(source["product_code"])
            and isinstance(source.get("citation"), str)
            and re.match(
                rf"^synthetic://rag_synthetic_demo_v1/{re.escape(source['product_code'])}(?:\?|$)",
                source["citation"],
            )
        ]
        answer = str(result.get("answer") or "")
        # Keep only the short answer paragraph. The internal RAG response may
        # append verbatim source chunks and retrieval scores for admin review.
        answer = re.sub(
            r"^\s*SYNTHETIC DEMO DATA\s*[—-]\s*NOT REAL COMPANY DATA\s*",
            "",
            answer,
            flags=re.IGNORECASE,
        )
        answer = re.split(
            r"\n\s*\n|^\s*(?:The relevant source is:|Sources?:|\[\d+\])",
            answer,
            maxsplit=1,
            flags=re.MULTILINE | re.IGNORECASE,
        )[0].strip()
        answer = re.sub(r"\s*\|\s*relevance\s*=\s*(?:0?\.\d+|1(?:\.0+)?)\b", "", answer, flags=re.IGNORECASE)
        forbidden_metadata = re.search(
            r"synthetic://|\b(?:document_id|chunk_id|revision_id|provider_mode|"
            r"development-hash-fallback|relevance_score|dataset_id|source_system|"
            r"source_type|production_eligible|authoritative|created_from|"
            r"permission_level|ai_public_approved|pilot_corpus_approved|"
            r"approval_hash|embedding|retrieval|provenance)\b|"
            r"\brelevance\s*=|\bsynthetic\s*=",
            answer,
            flags=re.IGNORECASE,
        )
        if result.get("status") != "SUPPORTED" or not sources or not answer or len(answer) > 700 or forbidden_metadata:
            return {
                "answer": PUBLIC_UNAVAILABLE_ANSWER,
                "status": "UNAVAILABLE",
                "sources": [],
            }
        return {"answer": answer, "status": "SUPPORTED", "sources": sources}

