"""Models for AI knowledge documents, permissions, and local vector search."""

from django.db import models


class DocumentCategory(models.Model):
    """Business category used to organize internal knowledge documents."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_categories"
        ordering = ["name"]

    def __str__(self):
        """Return the category name."""
        return self.name


class KnowledgeDocument(models.Model):
    """A source document that can be searched by the AI platform."""

    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="knowledge/documents/", blank=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        related_name="documents",
        blank=True,
        null=True,
    )
    source_type = models.CharField(max_length=32, default="text")
    source_path = models.TextField(blank=True)
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, default="DRAFT", choices=[
        ("DRAFT", "Draft"), ("REVIEW", "Review"),
        ("APPROVED", "Approved"), ("INDEXED", "Indexed"),
        ("ARCHIVED", "Archived"),
    ])
    active_version = models.BooleanField(default=True)
    approved_version = models.PositiveIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by_email = models.EmailField(blank=True)
    approval_hash = models.CharField(max_length=64, blank=True)
    ai_public_approved = models.BooleanField(default=False)
    created_by_email = models.EmailField(blank=True)
    permission_level = models.CharField(max_length=32, default="internal")
    department = models.CharField(max_length=16, blank=True, default="", choices=[
        ("", "Unassigned"), ("SALES", "Sales"),
        ("ENGINEERING", "Engineering"), ("QC", "QC"),
        ("MANAGEMENT", "Management"),
    ])
    owner_email = models.EmailField(blank=True)
    effective_date = models.DateField(null=True, blank=True)
    owner_reviewed_at = models.DateTimeField(null=True, blank=True)
    owner_reviewed_by_email = models.EmailField(blank=True)
    owner_review_hash = models.CharField(max_length=64, blank=True)
    quality_review_status = models.CharField(max_length=16, default="PENDING", choices=[
        ("PENDING", "Pending"), ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ])
    quality_review_reason = models.CharField(max_length=32, blank=True, choices=[
        ("INCOMPLETE", "Incomplete"), ("OUTDATED", "Outdated"),
        ("CONFIDENTIAL", "Confidential"), ("INVALID_METADATA", "Invalid metadata"),
    ])
    quality_reviewed_at = models.DateTimeField(null=True, blank=True)
    quality_reviewed_by_email = models.EmailField(blank=True)
    confidentiality_checked_at = models.DateTimeField(null=True, blank=True)
    confidentiality_checked_by_email = models.EmailField(blank=True)
    pilot_corpus_approved = models.BooleanField(default=False)
    pilot_approved_at = models.DateTimeField(null=True, blank=True)
    pilot_approved_by_email = models.EmailField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_documents"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["source_type"], name="knowledge_source_type_idx"),
            models.Index(fields=["permission_level"], name="knowledge_permission_idx"),
        ]

    def __str__(self):
        """Return the document title."""
        return self.title


class DocumentPermission(models.Model):
    """Optional document-level access control rule."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="permissions")
    role_name = models.CharField(max_length=80, blank=True)
    user_email = models.EmailField(blank=True)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_permissions"
        indexes = [
            models.Index(fields=["role_name"], name="knowledge_perm_role_idx"),
            models.Index(fields=["user_email"], name="knowledge_perm_user_idx"),
        ]

    def __str__(self):
        """Return a short permission label."""
        return self.role_name or self.user_email or f"document-{self.document_id}"


class KnowledgeUserScope(models.Model):
    """Explicit, default-disabled internal AI department entitlement."""

    user = models.OneToOneField("foundation.FoundationUser", on_delete=models.CASCADE, related_name="knowledge_scope")
    department = models.CharField(max_length=16, choices=[
        ("SALES", "Sales"), ("ENGINEERING", "Engineering"),
        ("QC", "QC"), ("MANAGEMENT", "Management"),
    ])
    pilot_enabled = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=16, default="PENDING", choices=[
        ("PENDING", "Pending"), ("APPROVED", "Approved"),
        ("REVOKED", "Revoked"),
    ])
    approved_by = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.SET_NULL,
        related_name="approved_knowledge_scopes", null=True, blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    training_acknowledged_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_user_scopes"


class DocumentVersion(models.Model):
    """Immutable snapshot of document content at one version."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64, blank=True)
    change_note = models.TextField(blank=True)
    created_by_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_versions"
        ordering = ["document_id", "-version"]
        unique_together = [("document", "version")]

    def __str__(self):
        """Return a document version label."""
        return f"{self.document_id}:v{self.version}"


class KnowledgeChunk(models.Model):
    """Searchable text chunk derived from a knowledge document."""

    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    revision = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name="chunks", null=True, blank=True)
    content = models.TextField()
    chunk_index = models.PositiveIntegerField(default=0)
    section = models.CharField(max_length=240, blank=True)
    page = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_chunks"
        ordering = ["document_id", "chunk_index"]
        unique_together = [("document", "chunk_index")]

    def __str__(self):
        """Return a short chunk label."""
        return f"{self.document_id}:{self.chunk_index}"


class KnowledgeEmbedding(models.Model):
    """Local embedding vector for one knowledge chunk."""

    chunk = models.OneToOneField(KnowledgeChunk, on_delete=models.CASCADE, related_name="embedding")
    vector = models.JSONField(default=list)
    provider = models.CharField(max_length=80, default="development-hash-fallback")
    model_name = models.CharField(max_length=120, default="local-hash-embedding")
    dimension = models.PositiveIntegerField(default=32)
    embedding_version = models.CharField(max_length=40, default="v1")
    content_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    indexed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_embeddings"
        indexes = [
            models.Index(fields=["model_name"], name="knowledge_embedding_model_idx"),
        ]

    def __str__(self):
        """Return the related chunk label."""
        return str(self.chunk)


class KnowledgeAssistantLog(models.Model):
    """Audit log for internal AI knowledge assistant responses."""

    question = models.TextField()
    answer = models.TextField(blank=True)
    sources = models.JSONField(default=list)
    confidence = models.FloatField(default=0)
    warning = models.TextField(blank=True)
    user_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_assistant_logs"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["created_at"], name="knowledge_log_created_idx"),
            models.Index(fields=["user_email"], name="knowledge_log_user_idx"),
        ]

    def __str__(self):
        """Return a safe log label without exposing the full question."""
        return f"knowledge-assistant-log-{self.id or 'new'}"


class KnowledgeAuditEvent(models.Model):
    """Content-free document and retrieval audit trail."""

    event = models.CharField(max_length=32)
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.SET_NULL, null=True, blank=True)
    document_id_snapshot = models.PositiveIntegerField(null=True, blank=True)
    version = models.PositiveIntegerField(null=True, blank=True)
    actor_id = models.PositiveIntegerField(null=True, blank=True)
    decision = models.CharField(max_length=16, default="allowed")
    query_hash = models.CharField(max_length=64, blank=True)
    source_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_audit_events"
        indexes = [models.Index(fields=["event", "created_at"], name="knowledge_audit_event_idx")]


class KnowledgeAssistantFeedback(models.Model):
    """Structured pilot feedback without storing question or answer content."""

    CATEGORY_CHOICES = [
        ("HELPFUL", "Helpful"),
        ("INCORRECT", "Incorrect"),
        ("MISSING_SOURCE", "Missing source"),
        ("NEED_DOCUMENT", "Need document"),
    ]

    interaction = models.ForeignKey(
        KnowledgeAssistantLog, on_delete=models.CASCADE, related_name="feedback"
    )
    submitted_by = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="knowledge_feedback",
    )
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_assistant_feedback"
        constraints = [
            models.UniqueConstraint(
                fields=["interaction", "submitted_by"],
                name="knowledge_feedback_once_per_user",
            )
        ]


class KnowledgeHumanEvaluation(models.Model):
    """Content-free human rating linked to the separately controlled interaction."""

    RATING_CHOICES = [
        ("CORRECT", "Correct"),
        ("PARTIALLY_CORRECT", "Partially correct"),
        ("INCORRECT", "Incorrect"),
    ]
    CATEGORY_CHOICES = [
        ("PRODUCT", "Product"), ("CAPABILITY", "Capability"),
        ("RFQ", "RFQ"), ("TECHNICAL", "Technical"),
        ("QUALITY", "Quality"),
    ]

    interaction = models.OneToOneField(
        KnowledgeAssistantLog, on_delete=models.CASCADE, related_name="human_evaluation"
    )
    reviewer = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="knowledge_human_evaluations",
    )
    question_category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    rating = models.CharField(max_length=24, choices=RATING_CHOICES)
    citation_valid = models.BooleanField(default=False)
    permission_correct = models.BooleanField(default=False)
    missing_information = models.BooleanField(default=False)
    hallucination = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_human_evaluations"


class KnowledgeGapReview(models.Model):
    """Structured root-cause classification for a failed pilot interaction."""

    CATEGORY_CHOICES = [
        ("MISSING_DOCUMENT", "Missing document"),
        ("WRONG_DOCUMENT", "Wrong document"),
        ("POOR_DOCUMENT_QUALITY", "Poor document quality"),
        ("RETRIEVAL_ISSUE", "Retrieval issue"),
        ("PERMISSION_ISSUE", "Permission issue"),
    ]

    interaction = models.OneToOneField(
        KnowledgeAssistantLog, on_delete=models.CASCADE, related_name="gap_review"
    )
    reviewer = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.PROTECT,
        related_name="knowledge_gap_reviews",
    )
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_gap_reviews"


class KnowledgePilotProgram(models.Model):
    """Global launch state for one bounded internal AI pilot."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"), ("RUNNING", "Running"),
        ("SUSPENDED", "Suspended"), ("COMPLETED", "Completed"),
    ]

    name = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=16, default="DRAFT", choices=STATUS_CHOICES)
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    launched_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "foundation.FoundationUser", on_delete=models.SET_NULL,
        related_name="approved_knowledge_pilot_programs", null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_pilot_programs"


