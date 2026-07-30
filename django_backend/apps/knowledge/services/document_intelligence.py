"""Document Intelligence service cho Knowledge Assistant.

Service nay gom cac buoc upload, trich xuat text, phan loai tai lieu, tao
metadata, dua vao Knowledge Base va tra ve citation/confidence. Tat ca xu ly
local, khong gui tai lieu ra API ben ngoai.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.knowledge_service import KnowledgeService, document_to_dict
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.text_processing import TextProcessor


@dataclass(frozen=True)
class DocumentIntelligenceResult:
    """Ket qua gon de UI/API de doc va hien thi."""

    document: KnowledgeDocument
    classification: str
    confidence: float
    approval_status: str
    citations: list[dict]

    def to_dict(self):
        """Chuyen ket qua thanh dict de test va JSON co the dung lai."""
        return {
            "document": document_to_dict(self.document),
            "classification": self.classification,
            "confidence": self.confidence,
            "approval_status": self.approval_status,
            "citations": self.citations,
        }


class DocumentIntelligenceService:
    """Xu ly tai lieu ky thuat thanh tri thuc co the tim kiem."""

    def __init__(self, knowledge_service=None, text_processor=None, search_service=None):
        """Cho phep test inject service gia lap neu can."""
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.text_processor = text_processor or TextProcessor()
        self.search_service = search_service or KnowledgeSearchService()

    @transaction.atomic
    def ingest_uploaded_document(self, uploaded_file, *, title="", created_by_email="", permission_level="internal"):
        """Luu file upload, trich text, phan loai va nap vao Knowledge Base."""
        safe_name = Path(uploaded_file.name or "uploaded-document.txt").name
        storage_path = default_storage.save(f"knowledge/uploads/{safe_name}", uploaded_file)
        absolute_path = Path(settings.MEDIA_ROOT) / storage_path
        extracted_text = self.text_processor.extract_text(absolute_path)
        cleaned_text = self.text_processor.clean_text(extracted_text)
        classification = self.classify_document(safe_name, cleaned_text)
        confidence = self.confidence_score(cleaned_text, classification)
        approval_status = "pending_review" if confidence < 0.65 else "ready_for_review"
        metadata = {
            "document_intelligence": {
                "classification": classification,
                "confidence": confidence,
                "approval_status": approval_status,
                "version_status": "current",
                "source_citation": safe_name,
                "extraction_method": self.extraction_method(safe_name, cleaned_text),
                "human_approval_required": True,
            }
        }
        document = self.knowledge_service.create_document(
            title=title or safe_name,
            content=cleaned_text,
            description=f"Document Intelligence import: {classification}",
            category_name=classification,
            source_type=Path(safe_name).suffix.lower().lstrip(".") or "text",
            source_path=storage_path,
            permission_level=permission_level,
            created_by_email=created_by_email,
            metadata=metadata,
        )
        citations = self.build_citations(document)
        return DocumentIntelligenceResult(
            document=document,
            classification=classification,
            confidence=confidence,
            approval_status=approval_status,
            citations=citations,
        )

    def classify_document(self, filename, content):
        """Phan loai tai lieu bang keyword de minh bach va de giai thich."""
        text = f"{filename} {content}".lower()
        rules = [
            ("quality", ["quality", "iso", "inspection", "kiem tra", "qc", "procedure"]),
            ("technical", ["drawing", "tolerance", "specification", "cnc", "fixture", "ban ve", "dung sai"]),
            ("product", ["product", "sku", "catalogue", "catalog", "san pham"]),
        ]
        for label, keywords in rules:
            if any(keyword in text for keyword in keywords):
                return label
        return "general"

    def confidence_score(self, content, classification):
        """Tinh diem tin cay don gian dua tren do dai text va loai tai lieu."""
        text_length = len(str(content or "").strip())
        base = 0.35 if classification == "general" else 0.55
        length_bonus = min(text_length / 2000, 0.35)
        return round(min(base + length_bonus, 0.95), 2)

    def extraction_method(self, filename, content):
        """Gan nhan cach trich xuat de nhan vien biet tai lieu co can OCR khong."""
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf" and len(str(content or "").strip()) < 40:
            return "ocr_review_required"
        if suffix == ".pdf":
            return "pdf_text_extraction"
        if suffix == ".docx":
            return "docx_text_extraction"
        return "plain_text_extraction"

    def build_citations(self, document):
        """Tao citation tu cac chunk dau tien cua tai lieu."""
        citations = []
        for chunk in document.chunks.all().order_by("chunk_index")[:3]:
            citations.append(
                {
                    "document_id": document.id,
                    "title": document.title,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "preview": chunk.content[:180],
                }
            )
        return citations

    def answer_with_sources(self, question, *, user=None, limit=5):
        """Tim tri thuc va tra ve cau tra loi co nguon/citation/confidence."""
        result = self.search_service.search(question, limit=limit, user=user)
        sources = result.get("sources", [])
        confidence = result.get("confidence", 0)
        if sources:
            answer = "Tim thay tai lieu lien quan. Hay kiem tra citation truoc khi dung cho khach hang."
        else:
            answer = "Chua tim thay tai lieu phu hop trong Knowledge Base."
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "human_approval_required": True,
        }

