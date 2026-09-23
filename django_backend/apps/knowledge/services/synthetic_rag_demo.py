"""Bounded local-only synthetic Product and RAG technical-demo workflow."""

from __future__ import annotations

import csv
import hashlib
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify

from apps.business_core.models import BusinessProduct
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy, content_hash
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService, document_to_dict
from apps.knowledge.services.rag_pipeline import RagContextBuilder, RagGenerationPipeline
from apps.knowledge.services.search_service import KnowledgeSearchService


DATASET_ID = "rag_synthetic_demo_v1"
SOURCE_SYSTEM = "RAG_SYNTHETIC_DEMO_V1"
SOURCE_TYPE = "SYNTHETIC_PRODUCT"
OWNER_EMAIL = "synthetic-rag-demo@localhost.invalid"
PART_CODE_RE = re.compile(r"^SYN-RAG-\d{4}$")
MAX_ROWS = 30
UNAVAILABLE_ANSWER = "The current demo knowledge base does not contain this information."
REQUIRED_HEADERS = {
    "Source System *", "Source Record ID *", "Part Code *", "Product Name *",
    "Revision", "Unit *", "Category Code *", "Public Title *",
    "Public Description *", "Material Code", "Material Grade",
    "Manufacturing Process", "Application", "Industry",
    "Publication Approved? (YES/NO)", "Dataset ID *", "Source Type *",
    "Synthetic *", "Production Eligible *", "Authoritative *", "Created For *",
}
FORMULA_PREFIXES = ("=", "+", "-", "@")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    rows: list[dict[str, str]]
    valid: int
    warnings: int
    rejected: int
    duplicates: int
    errors: list[str]


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def validate_source(path: str | Path, max_rows: int = MAX_ROWS) -> ValidationResult:
    """Validate one bounded CSV without mutating application state."""

    source_path = Path(path)
    if max_rows < 1 or max_rows > MAX_ROWS:
        raise ValueError(f"max_rows must be between 1 and {MAX_ROWS}")
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_HEADERS - headers)
        if missing:
            return ValidationResult([], 0, 0, 1, 0, [f"missing headers: {', '.join(missing)}"])
        raw_rows = list(reader)
    if len(raw_rows) > max_rows:
        return ValidationResult([], 0, 0, len(raw_rows), 0, [f"row count {len(raw_rows)} exceeds bound {max_rows}"])

    valid_rows: list[dict[str, str]] = []
    errors: list[str] = []
    seen_source_ids: set[str] = set()
    seen_codes: set[str] = set()
    duplicate_count = 0
    for number, raw in enumerate(raw_rows, start=2):
        row = {key: _normalized(value) for key, value in raw.items() if key is not None}
        row_errors: list[str] = []
        code = row.get("Part Code *", "")
        source_id = row.get("Source Record ID *", "")
        fixed_values = {
            "Source System *": SOURCE_SYSTEM,
            "Dataset ID *": DATASET_ID,
            "Source Type *": "SYNTHETIC",
            "Synthetic *": "TRUE",
            "Production Eligible *": "FALSE",
            "Authoritative *": "FALSE",
            "Created For *": "technical_rag_demo",
            "Publication Approved? (YES/NO)": "NO",
        }
        for field, expected in fixed_values.items():
            if row.get(field, "").upper() != expected.upper():
                row_errors.append(f"{field} must be {expected}")
        for field in ("Source Record ID *", "Part Code *", "Product Name *", "Revision", "Unit *", "Category Code *", "Public Title *", "Public Description *"):
            if not row.get(field):
                row_errors.append(f"{field} is required")
        if code and not PART_CODE_RE.fullmatch(code):
            row_errors.append("Part Code must match SYN-RAG-####")
        if source_id != code:
            row_errors.append("Source Record ID must equal the bounded synthetic Part Code")
        if row.get("Unit *") not in {"PCS", "KG", "M", "MM"}:
            row_errors.append("Unit is invalid")
        if not row.get("Product Name *", "").startswith("[SYNTHETIC DEMO]"):
            row_errors.append("Product Name lacks the synthetic marker")
        if not row.get("Public Description *", "").startswith("[SYNTHETIC / NOT REAL COMPANY DATA]"):
            row_errors.append("Public Description lacks the synthetic warning")
        for field, value in row.items():
            if value.startswith(FORMULA_PREFIXES):
                row_errors.append(f"{field} contains a formula-like value")
        if source_id in seen_source_ids or code in seen_codes:
            duplicate_count += 1
            row_errors.append("duplicate source ID or Part Code")
        seen_source_ids.add(source_id)
        seen_codes.add(code)
        if row_errors:
            errors.append(f"row {number}: {'; '.join(row_errors)}")
        else:
            valid_rows.append(row)
    return ValidationResult(
        rows=valid_rows,
        valid=len(valid_rows),
        warnings=0,
        rejected=len(raw_rows) - len(valid_rows),
        duplicates=duplicate_count,
        errors=errors,
    )


def _provenance_text(row: dict[str, str]) -> str:
    return (
        "SYNTHETIC / DEMO ONLY — NOT REAL COMPANY DATA — DO NOT USE FOR PRODUCTION\n"
        f"dataset_id={DATASET_ID}\nsource_system={SOURCE_SYSTEM}\nsource_type=SYNTHETIC\n"
        "synthetic=true\nproduction_eligible=false\nauthoritative=false\n"
        "human_business_approved=false\ncreated_for=technical_rag_demo\n"
        f"category_code={row['Category Code *']}\nmaterial_code={row['Material Code']}\n"
        f"material_grade={row['Material Grade']}\nprocess={row['Manufacturing Process']}\n"
        f"application={row['Application']}\nindustry={row['Industry']}"
    )


@transaction.atomic
def import_products(rows: list[dict[str, str]]) -> dict:
    """Create only new synthetic Products; refuse collisions with other data."""

    created = existing = conflicts = 0
    product_ids: dict[str, int] = {}
    for row in rows:
        code = row["Part Code *"]
        product = BusinessProduct.objects.filter(part_code=code).first()
        expected_name = row["Product Name *"]
        if product is not None:
            if (
                product.status != "synthetic_demo"
                or product.sku != DATASET_ID
                or product.name != expected_name
                or DATASET_ID not in product.description
            ):
                conflicts += 1
                continue
            existing += 1
            product_ids[code] = product.id
            continue
        product = BusinessProduct.objects.create(
            data_contract="LEGACY",
            part_code=code,
            revision=row["Revision"],
            unit=row["Unit *"],
            name=expected_name,
            slug=slugify(f"synthetic-rag-demo-{code}"),
            sku=DATASET_ID,
            status="synthetic_demo",
            category_name=f"[SYNTHETIC] {row['Category Code *']}",
            short_description=row["Public Description *"],
            description=_provenance_text(row),
            technical_requirements="SYNTHETIC TECHNICAL DEMO ONLY. NOT PRODUCTION ELIGIBLE.",
            tolerance="SYNTHETIC; see controlled dataset specification",
            is_active=True,
            price=0,
        )
        created += 1
        product_ids[code] = product.id
    return {"created": created, "existing": existing, "conflicts": conflicts, "product_ids": product_ids}


def _specifications(row: dict[str, str]) -> list[dict[str, str]]:
    result = []
    for index in range(1, 4):
        label = row.get(f"Public Specification {index} - Label", "")
        value = row.get(f"Public Specification {index} - Value", "")
        if label and value:
            result.append({"label": label, "value": value})
    return result


def _knowledge_content(row: dict[str, str]) -> str:
    specs = "\n".join(f"- {item['label']}: {item['value']}" for item in _specifications(row))
    return "\n\n".join([
        f"# {row['Public Title *']}",
        "SYNTHETIC / DEMO ONLY. NOT REAL COMPANY DATA. DO NOT USE FOR PRODUCTION.",
        row["Public Description *"],
        f"Synthetic part code: {row['Part Code *']}",
        f"Category: {row['Category Code *']}",
        f"Material: {row['Material Code']} ({row['Material Grade']})",
        f"Manufacturing process: {row['Manufacturing Process']}",
        f"Application: {row['Application']}",
        f"Industry context: {row['Industry']}",
        f"Public specifications:\n{specs}",
        f"Provenance: dataset_id={DATASET_ID}; source_system={SOURCE_SYSTEM}; source_type=SYNTHETIC; synthetic=true; production_eligible=false; authoritative=false; created_for=technical_rag_demo; revision={row['Source Revision']}",
    ])


@transaction.atomic
def create_and_index_knowledge(rows: list[dict[str, str]], product_ids: dict[str, int]) -> dict:
    """Create and index internal-only documents under a strict synthetic identity."""

    service = KnowledgeService()
    indexer = KnowledgeIndexer()
    created = existing = indexed = chunks = embeddings = conflicts = 0
    document_ids: list[int] = []
    for row in rows:
        code = row["Part Code *"]
        content = _knowledge_content(row)
        document = KnowledgeDocument.objects.filter(
            source_type=SOURCE_TYPE,
            metadata__dataset_id=DATASET_ID,
            metadata__source_record_id=code,
        ).first()
        if document is not None:
            normalized_content = service.text_processor.clean_text(content)
            if document.content != normalized_content or document.metadata.get("source_product_id") != product_ids.get(code):
                conflicts += 1
                continue
            existing += 1
        else:
            document = service.create_document(
                title=row["Public Title *"],
                content=content,
                description=row["Public Description *"],
                category_name="Synthetic Technical RAG Demo",
                source_type=SOURCE_TYPE,
                source_path=f"synthetic://{DATASET_ID}/{code}?revision={row['Source Revision']}",
                permission_level="internal",
                department="ENGINEERING",
                owner_email=OWNER_EMAIL,
                effective_date=timezone.localdate(),
                created_by_email=OWNER_EMAIL,
                metadata={
                    "dataset_id": DATASET_ID,
                    "source_system": SOURCE_SYSTEM,
                    "source_type": "SYNTHETIC_PRODUCT",
                    "source_record_id": code,
                    "source_revision": row["Source Revision"],
                    "source_product_id": product_ids[code],
                    "synthetic": True,
                    "production_eligible": False,
                    "authoritative": False,
                    "human_business_approved": False,
                    "created_for": "technical_rag_demo",
                },
            )
            digest = content_hash(document.content)
            document.status = "APPROVED"
            document.approved_version = document.version
            document.approved_at = timezone.now()
            document.approved_by_email = OWNER_EMAIL
            document.approval_hash = digest
            document.ai_public_approved = False
            document.owner_reviewed_at = timezone.now()
            document.owner_reviewed_by_email = OWNER_EMAIL
            document.owner_review_hash = digest
            document.quality_review_status = "APPROVED"
            document.quality_reviewed_at = timezone.now()
            document.quality_reviewed_by_email = OWNER_EMAIL
            document.confidentiality_checked_at = timezone.now()
            document.confidentiality_checked_by_email = OWNER_EMAIL
            document.pilot_corpus_approved = False
            document.save()
            created += 1
        if indexer.needs_reindex(document):
            indexer.reindex(document, created_by_email=OWNER_EMAIL, change_note="Synthetic technical RAG demo")
        else:
            document.refresh_from_db()
        indexed += int(document.status == "INDEXED")
        chunks += document.chunks.count()
        embeddings += document.chunks.filter(embedding__isnull=False).count()
        document_ids.append(document.id)
    return {
        "created": created, "existing": existing, "indexed": indexed,
        "chunks": chunks, "embeddings": embeddings, "conflicts": conflicts,
        "document_ids": document_ids,
    }


def build_test_questions(rows: list[dict[str, str]]) -> list[dict]:
    """Create a deterministic 40-question gold set with 20% unknowns."""

    questions: list[dict] = []
    for row in rows[:10]:
        code = row["Part Code *"]
        questions.append({
            "category": "A. Exact lookup", "question": f"What synthetic technical record is identified by {code}?",
            "expected_source_product": [code], "expected_answer_facts": [code, row["Material Grade"]],
            "expected_citation": f"synthetic://{DATASET_ID}/{code}", "allowed_unknown_behavior": False,
        })
    semantic_prompts = [
        ("Which fictional component is a passivated dosing spindle for laboratory equipment?", "SYN-RAG-0005"),
        ("Find the hardened indexing shaft with two bearing journals and a keyed end.", "SYN-RAG-0006"),
        ("Which synthetic fixture uses a locating-hole grid for camera inspection?", "SYN-RAG-0007"),
        ("Find the polymer nest intended to avoid scratching delicate components.", "SYN-RAG-0009"),
        ("Which demonstration item is a sealed compact controller enclosure?", "SYN-RAG-0010"),
        ("Find the electropolished cylindrical optical sensor body.", "SYN-RAG-0011"),
        ("Which record describes a glass-filled nylon cable junction enclosure?", "SYN-RAG-0012"),
        ("Find the high-strength cylindrical spacer for a compact servo stack.", "SYN-RAG-0013"),
        ("Which synthetic item is a tumbled brass instrument panel spacer?", "SYN-RAG-0014"),
        ("Find the oil-impregnated bronze pivot bushing.", "SYN-RAG-0015"),
        ("Which component is the low-noise dry-running polymer bushing?", "SYN-RAG-0016"),
        ("Find the ground block for aligning a compact linear guide rail.", "SYN-RAG-0017"),
        ("Which red anodized block has G1/8 pneumatic ports?", "SYN-RAG-0018"),
        ("Find the passivated camera adapter with two metric interface threads.", "SYN-RAG-0019"),
        ("Which gray pocketed adapter is intended for a robot end effector?", "SYN-RAG-0020"),
    ]
    rows_by_code = {row["Part Code *"]: row for row in rows}
    for prompt, code in semantic_prompts:
        row = rows_by_code[code]
        questions.append({
            "category": "B. Semantic lookup", "question": prompt,
            "expected_source_product": [code], "expected_answer_facts": [row["Application"], row["Material Grade"]],
            "expected_citation": f"synthetic://{DATASET_ID}/{code}", "allowed_unknown_behavior": False,
        })
    extra = [
        ("C. Material query", "Which synthetic product combines SUS316 with an electropolished finish?", ["SYN-RAG-0011"], ["SUS316", "Electropolished"]),
        ("D. Manufacturing process query", "Which record uses wire EDM and surface grinding for slot inspection?", ["SYN-RAG-0021"], ["Wire EDM", "12.000 mm"]),
        ("E. Specification/tolerance query", "Which synthetic guide has a fit clearance of 0.008 mm?", ["SYN-RAG-0023"], ["0.008 mm", "HRC 58-60"]),
        ("F. Application query", "Which record is used for connector position inspection?", ["SYN-RAG-0022"], ["Connector position inspection", "Gold anodized"]),
        ("G. Multi-document comparison", "Compare the bronze pivot bushing and the dry-running POM bushing.", ["SYN-RAG-0015", "SYN-RAG-0016"], ["C93200", "POM-C"]),
        ("I. Wrong-category distractor", "Which fixture plate is made from POM-C rather than tool steel?", ["SYN-RAG-0009"], ["POM-C", "Delicate component nest"]),
        ("J. Citation validation", "Cite the synthetic record with a 25 mm grid pitch and blue anodized finish.", ["SYN-RAG-0007"], ["25 mm", "Blue anodized"]),
    ]
    for category, question, expected, facts in extra:
        questions.append({
            "category": category, "question": question, "expected_source_product": expected,
            "expected_answer_facts": facts, "expected_citation": [f"synthetic://{DATASET_ID}/{code}" for code in expected],
            "allowed_unknown_behavior": False,
        })
    unknowns = [
        ("Is any synthetic product made from Titanium Grade 5?", ["Titanium Grade 5"]),
        ("What is the sales price of SYN-RAG-0001?", ["sales price"]),
        ("Which customer ordered the optical sensor housing?", ["customer"]),
        ("What RFQ number covers the blue fixture plate?", ["RFQ number"]),
        ("Which product has an aerospace AS9100 release certificate?", ["AS9100 release certificate"]),
        ("What private drawing number defines the robot adapter?", ["private drawing number"]),
        ("Which supplier provides the bronze bushing?", ["supplier"]),
        ("What inventory quantity is available for the nylon chain guide?", ["inventory quantity"]),
    ]
    for question, facts in unknowns:
        questions.append({
            "category": "H. Unknown / unsupported", "question": question,
            "expected_source_product": [], "expected_answer_facts": facts,
            "expected_citation": None, "allowed_unknown_behavior": True,
        })
    return questions


def _search_scoped(query: str, limit: int = 3) -> list[dict]:
    search = KnowledgeSearchService()
    documents = KnowledgeDocument.objects.filter(
        source_type=SOURCE_TYPE, metadata__dataset_id=DATASET_ID,
        metadata__synthetic=True, metadata__production_eligible=False,
        permission_level="internal", ai_public_approved=False,
    )
    chunks = list(KnowledgeChunk.objects.select_related("document", "revision", "embedding").filter(
        document__in=documents, revision__version=F("document__version"),
        revision__content_hash=F("document__approval_hash"),
    ))
    vector_results = search.vector_store.search(
        query_vector=search.embedding_service.embed(query), queryset=chunks,
        limit=max(limit, 100), provider=search.embedding_service,
    )
    reranked = search._rerank_with_lexical_overlap(query, chunks, vector_results, max(limit * 4, 12))
    normalized_query = query.casefold()
    for item in reranked:
        source_id = str(item["chunk"].document.metadata.get("source_record_id", ""))
        if source_id and source_id.casefold() in normalized_query:
            item["score"] = 1.0
    reranked.sort(key=lambda item: (item["score"], -item["chunk"].document_id), reverse=True)
    unique_documents = []
    seen = set()
    for item in reranked:
        document_id = item["chunk"].document_id
        if document_id in seen:
            continue
        seen.add(document_id)
        unique_documents.append(item)
        if len(unique_documents) == limit:
            break
    return unique_documents


class _NoBusinessContext:
    """Prevent this Product-only demo from attaching business-domain context."""

    def build_context(self, question, user=None):
        del question, user
        return ""


class SyntheticRagPromptTemplate:
    """Keep the local model grounded in the explicitly fictional demo corpus."""

    def build(self, question, context):
        return (
            "You are an internal source-grounded product knowledge assistant.\n"
            "The supplied records are fictional synthetic test data, but their facts are "
            "authoritative inside this demo.\n"
            "Answer only with facts explicitly present in the knowledge context.\n"
            "Cite the relevant source title. Do not invent price, customer, stock, policy, "
            "or technical data. If context is insufficient, state that it is unavailable.\n\n"
            f"CONTEXT:\n{context['knowledge_context']}\n\n"
            f"QUESTION:\n{question}"
        )


class SyntheticRagWebDemoService:
    """Expose the existing RAG components over one isolated synthetic corpus."""

    sensitive_fact_tokens = {
        "price", "cost", "margin", "customer", "rfq", "quotation", "order",
        "supplier", "inventory", "drawing", "certificate", "as9100",
    }
    generic_tokens = {
        "which", "what", "find", "synthetic", "demo", "product", "record",
        "uses", "use", "with", "from", "this", "that", "does", "any", "the",
        "for", "and", "made", "information", "current", "knowledge", "base",
    }

    def __init__(self, search_service=None, generation_pipeline=None):
        self.search_service = search_service or KnowledgeSearchService()
        self.generation_pipeline = generation_pipeline or RagGenerationPipeline(
            context_builder=RagContextBuilder(business_connector=_NoBusinessContext()),
            prompt_template=SyntheticRagPromptTemplate(),
            answer_transformer=self._ensure_synthetic_citation,
        )

    def query(self, question: str, *, user=None, limit: int = 3) -> dict:
        started = time.perf_counter()
        normalized_question = " ".join(str(question or "").split())
        raw_results = self._search(normalized_question, limit=min(max(limit, 1), 5))
        provider = self.search_service.embedding_service.provider_name
        if not self._has_grounded_support(normalized_question, raw_results):
            result = {
                "answer": UNAVAILABLE_ANSWER,
                "status": "UNAVAILABLE",
                "sources": [],
                "retrieval": {
                    "result_count": 0,
                    "candidate_chunks_considered": len(raw_results),
                    "provider": provider,
                    "provider_mode": self._provider_mode(provider),
                    "dataset_id": DATASET_ID,
                    "corpus_documents": self._documents().count(),
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "llm_success": False,
                    "fallback_used": True,
                },
            }
            self._log_runtime(normalized_question, result)
            return result

        retrieval = self._retrieval_payload(raw_results)
        generated = self.generation_pipeline.generate(
            normalized_question,
            retrieval,
            user=user,
            fallback_builder=self._fallback_answer,
        )
        result = {
            "answer": generated["answer"],
            "status": "SUPPORTED",
            "sources": [self._citation(result) for result in raw_results],
            "retrieval": {
                "result_count": len(raw_results),
                "candidate_chunks_considered": len(raw_results),
                "provider": provider,
                "provider_mode": self._provider_mode(provider),
                "dataset_id": DATASET_ID,
                "corpus_documents": self._documents().count(),
                "confidence": generated.get("confidence", 0),
                "generation_provider": generated.get("provider", "source-fallback"),
                "generation_status": generated.get("generation_status", "fallback"),
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "llm_success": generated.get("generation_status") == "generated",
                "fallback_used": generated.get("generation_status") != "generated",
            },
        }
        self._log_runtime(normalized_question, result)
        return result

    @staticmethod
    def _log_runtime(question: str, result: dict) -> None:
        """Log bounded diagnostics without retaining the raw user question."""

        retrieval = result["retrieval"]
        logger.info(
            "synthetic_rag_chat question_hash=%s retrieval_count=%s scores=%s "
            "latency_ms=%s llm_success=%s fallback_used=%s",
            hashlib.sha256(question.encode("utf-8")).hexdigest(),
            retrieval.get("result_count", 0),
            [source.get("relevance_score", 0) for source in result.get("sources", [])],
            retrieval.get("latency_ms", 0),
            retrieval.get("llm_success", False),
            retrieval.get("fallback_used", False),
        )

    def _documents(self):
        return KnowledgeDocument.objects.filter(
            source_type=SOURCE_TYPE,
            metadata__dataset_id=DATASET_ID,
            metadata__synthetic=True,
            metadata__production_eligible=False,
            metadata__authoritative=False,
            permission_level="internal",
            ai_public_approved=False,
            pilot_corpus_approved=False,
            active_version=True,
            status="INDEXED",
        )

    def _search(self, question: str, limit: int):
        documents = self._documents()
        chunks = list(KnowledgeChunk.objects.select_related(
            "document", "revision", "embedding",
        ).filter(
            document__in=documents,
            revision__version=F("document__version"),
            revision__content_hash=F("document__approval_hash"),
        ))
        vector_results = self.search_service.vector_store.search(
            query_vector=self.search_service.embedding_service.embed(question),
            queryset=chunks,
            limit=max(limit, 100),
            provider=self.search_service.embedding_service,
        )
        reranked = self.search_service._rerank_with_lexical_overlap(
            question, chunks, vector_results, max(limit * 4, 12),
        )
        query_folded = question.casefold()
        for item in reranked:
            source_id = str(item["chunk"].document.metadata.get("source_record_id", ""))
            if source_id and source_id.casefold() in query_folded:
                item["score"] = 1.0
        reranked.sort(key=lambda item: (item["score"], -item["chunk"].document_id), reverse=True)
        unique = []
        seen = set()
        for item in reranked:
            if item["chunk"].document_id in seen:
                continue
            seen.add(item["chunk"].document_id)
            unique.append(item)
            if len(unique) == limit:
                break
        return unique

    def _has_grounded_support(self, question: str, results: list[dict]) -> bool:
        if not results:
            return False
        evidence = " ".join(item["chunk"].content.casefold() for item in results)
        tokens = {
            token for token in re.findall(r"[a-z0-9]+", question.casefold())
            if len(token) >= 3 and token not in self.generic_tokens
        }
        requested_sensitive = tokens.intersection(self.sensitive_fact_tokens)
        if any(token not in evidence for token in requested_sensitive):
            return False
        if not tokens:
            return False
        matched = sum(token in evidence for token in tokens)
        return matched / len(tokens) >= 0.6

    def _retrieval_payload(self, raw_results: list[dict]) -> dict:
        results = []
        sources = []
        for item in raw_results:
            chunk = item["chunk"]
            document = chunk.document
            document_data = document_to_dict(document)
            results.append({
                "score": item["score"],
                "document": document_data,
                "chunk": {
                    "id": chunk.id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "revision_id": chunk.revision_id,
                },
            })
            sources.append({
                **document_data,
                "relevance_score": round(item["score"], 4),
                "revision_id": chunk.revision_id,
            })
        return {
            "results": results,
            "sources": sources,
            "confidence": round(max(item["score"] for item in raw_results), 4),
        }

    def _citation(self, item: dict) -> dict:
        chunk = item["chunk"]
        document = chunk.document
        metadata = document.metadata
        return {
            "title": document.title,
            "product_code": metadata.get("source_record_id"),
            "citation": document.source_path,
            "document_id": document.id,
            "version": document.version,
            "revision": metadata.get("source_revision"),
            "chunk_id": chunk.id,
            "relevance_score": round(item["score"], 4),
        }

    def _fallback_answer(self, question, retrieval):
        del question
        result = retrieval["results"][0]
        title = result["document"]["title"]
        content = result["chunk"]["content"]
        return f"SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA\n\n{content}\n\nSource: {title}"

    def _ensure_synthetic_citation(self, answer, retrieval, status):
        del status
        title = retrieval["sources"][0]["title"] if retrieval.get("sources") else ""
        warning = "SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA"
        transformed = str(answer or "").strip()
        if warning not in transformed:
            transformed = f"{warning}\n\n{transformed}"
        if title and title not in transformed:
            transformed = f"{transformed}\n\nSource: {title}"
        return transformed

    @staticmethod
    def _provider_mode(provider):
        return "development-hash-plus-lexical" if provider == "development-hash-fallback" else "semantic-embedding"


def evaluate_retrieval(rows: list[dict[str, str]]) -> dict:
    """Measure retrieval, grounding rejection, and citation chains."""

    questions = build_test_questions(rows)
    answerable = [q for q in questions if not q["allowed_unknown_behavior"]]
    unknown = [q for q in questions if q["allowed_unknown_behavior"]]
    top1 = top3 = citation_presence = citation_correct = contamination = rejected_unknown = 0
    details = []
    corpus_text = "\n".join(KnowledgeDocument.objects.filter(
        source_type=SOURCE_TYPE, metadata__dataset_id=DATASET_ID,
    ).values_list("content", flat=True)).casefold()
    citation_chains = 0
    for question in questions:
        results = _search_scoped(question["question"], limit=3)
        codes = [item["chunk"].document.metadata.get("source_record_id") for item in results]
        expected = question["expected_source_product"]
        if question["allowed_unknown_behavior"]:
            unsupported = all(str(fact).casefold() not in corpus_text for fact in question["expected_answer_facts"])
            rejected_unknown += int(unsupported)
            details.append({**question, "retrieved": codes, "result": "UNAVAILABLE" if unsupported else "FAILED_TO_REJECT"})
            continue
        top1_hit = bool(codes and codes[0] in expected)
        top3_hit = any(code in expected for code in codes[:3])
        top1 += int(top1_hit)
        top3 += int(top3_hit)
        citation_presence += int(bool(results))
        citation_correct += int(top1_hit)
        if results:
            doc = results[0]["chunk"].document
            revision = results[0]["chunk"].revision
            expected_paths = question["expected_citation"]
            if isinstance(expected_paths, str):
                expected_paths = [expected_paths]
            chain_valid = (
                doc.metadata.get("dataset_id") == DATASET_ID
                and doc.metadata.get("source_product_id") is not None
                and doc.metadata.get("source_revision") == "1"
                and revision is not None
                and revision.content_hash == doc.approval_hash
                and results[0]["chunk"].document_id == doc.id
                and any(doc.source_path.startswith(path) for path in expected_paths)
            )
            citation_chains += int(chain_valid and top1_hit)
        expected_categories = {
            row["Category Code *"] for row in rows if row["Part Code *"] in expected
        }
        if results and results[0]["chunk"].document.metadata.get("source_record_id") not in expected:
            actual_code = results[0]["chunk"].document.metadata.get("source_record_id")
            actual_category = next((row["Category Code *"] for row in rows if row["Part Code *"] == actual_code), None)
            contamination += int(actual_category not in expected_categories)
        details.append({**question, "retrieved": codes, "top1": top1_hit, "top3": top3_hit})

    policy = KnowledgeAccessPolicy()
    public_visible = policy.eligible_documents(None).filter(
        source_type=SOURCE_TYPE, metadata__dataset_id=DATASET_ID,
    ).count()
    synthetic_docs = KnowledgeDocument.objects.filter(source_type=SOURCE_TYPE, metadata__dataset_id=DATASET_ID)
    security = {
        "products_marked_synthetic": BusinessProduct.objects.filter(
            part_code__startswith="SYN-RAG-", status="synthetic_demo", sku=DATASET_ID,
        ).count(),
        "documents_marked_synthetic": synthetic_docs.filter(
            metadata__synthetic=True, metadata__production_eligible=False,
            metadata__authoritative=False, ai_public_approved=False,
            pilot_corpus_approved=False, permission_level="internal",
        ).count(),
        "public_visible_synthetic_documents": public_visible,
        "non_product_source_types_in_demo": synthetic_docs.exclude(source_type=SOURCE_TYPE).count(),
    }
    return {
        "questions": questions, "details": details,
        "question_count": len(questions), "answerable": len(answerable), "unanswerable": len(unknown),
        "top1_success": top1, "top3_success": top3,
        "citation_presence": citation_presence, "citation_correctness": citation_correct,
        "citation_chains_validated": citation_chains,
        "unsupported_answer_rejection": rejected_unknown,
        "cross_category_contamination": contamination,
        "security": security,
    }

