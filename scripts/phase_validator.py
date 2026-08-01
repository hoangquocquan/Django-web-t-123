"""Validate migration phase artifacts before AI-assisted review.

The validator reads files and Git metadata only. It does not deploy, approve,
or modify production systems.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "phase_validation_result.json"


PHASE_REQUIREMENTS = {
    "aws-1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AWS_PHASE_1_ARCHITECTURE_AUDIT.md",
        "documents": [
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_COMPUTE_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_DATABASE_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_STORAGE_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_NETWORK_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_SECURITY_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_CICD_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_MONITORING_AUDIT.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "AWS_CURRENT_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "aws-audit" / "DJANGO_AWS_READINESS_REPORT.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "aws_phase_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "AWS_PHASE_1_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AWS_ARCHITECTURE_AUDIT_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_aws_phase1_audit.py",
        ],
        "expected_tag": "aws-phase-1-audit-complete",
    },
    "aws-learning-2": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AWS_PHASE_2_CLOUD_ARCHITECTURE_LEARNING_LAB.md",
        "documents": [
            PROJECT_ROOT / "docker" / "aws-lab" / "docker-compose.aws-lab.yml",
            PROJECT_ROOT / "docker" / "aws-lab" / "nginx" / "default.conf",
            PROJECT_ROOT / "docs" / "aws-lab" / "EC2_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "RDS_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "S3_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "LOAD_BALANCER_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "CICD_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "AWS_SECURITY_SIMULATION.md",
            PROJECT_ROOT / "docs" / "aws-lab" / "AWS_LEARNING_ARCHITECTURE.md",
            PROJECT_ROOT / ".github" / "workflows" / "aws-lab-ci.yml",
            PROJECT_ROOT / "ai-factory" / "evidence" / "aws_learning_phase_2.json",
            PROJECT_ROOT / "docs" / "reviews" / "AWS_LEARNING_PHASE_2_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AWS_LEARNING_LAB_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_aws_learning_lab.py",
        ],
        "expected_tag": "aws-learning-lab-complete",
    },
    "ai-1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AI_PHASE_1_OLLAMA_DJANGO_INTEGRATION.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "apps.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "services" / "ollama_client.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "services" / "prompt_manager.py",
            PROJECT_ROOT / "docs" / "ai" / "OLLAMA_SETUP.md",
            PROJECT_ROOT / "docs" / "ai" / "AI_SERVICE_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai" / "AI_CHAT_API.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "ai_phase_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "AI_PHASE_1_OLLAMA_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_PHASE_1_OLLAMA_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_ai_ollama.py",
        ],
        "expected_tag": "ai-phase-1-complete",
    },
    "ai-complete-1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AI_WAVE_1_COMPLETE_INTELLIGENCE_PLATFORM.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "knowledge_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "embedding_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "services" / "agent_controller.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "services" / "tools.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "views.py",
            PROJECT_ROOT / "docs" / "ai" / "RAG_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai" / "RAG_USAGE.md",
            PROJECT_ROOT / "docs" / "ai" / "AI_AGENT_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai" / "N8N_AI_AUTOMATION.md",
            PROJECT_ROOT / "docs" / "ai" / "AI_FACTORY_V2_ARCHITECTURE.md",
            PROJECT_ROOT / "n8n" / "workflows" / "ai_contact_classification.json",
            PROJECT_ROOT / "ai-factory" / "evidence" / "ai_wave_1_complete.json",
            PROJECT_ROOT / "docs" / "reviews" / "AI_WAVE_1_COMPLETE_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_WAVE_1_COMPLETE_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_ai_wave_1.py",
        ],
        "expected_tag": "ai-wave-1-complete",
    },
    "ai-knowledge-assistant": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AI_PROJECT_1_MEC_KNOWLEDGE_ASSISTANT.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "document_processor.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "knowledge_indexer.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "search_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "assistant_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "business_connector.py",
            PROJECT_ROOT / "docs" / "ai" / "MEC_KNOWLEDGE_MODEL.md",
            PROJECT_ROOT / "docs" / "ai" / "DOCUMENT_PIPELINE.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "ai_project_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "AI_PROJECT_1_KNOWLEDGE_ASSISTANT_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_PROJECT_1_KNOWLEDGE_ASSISTANT_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_ai_knowledge_assistant.py",
        ],
        "expected_tag": "ai-project-1-complete",
    },
    "business-sales-crm-ai": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "BUSINESS_WAVE_1_SALES_CRM_AI_PLATFORM.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "sales" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "sales" / "services" / "sales_platform_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "sales" / "migrations" / "0001_sales_platform.py",
            PROJECT_ROOT / "django_backend" / "apps" / "crm" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "crm" / "services" / "crm_platform_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "crm" / "migrations" / "0001_crm_platform.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "sales.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "crm.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "urls.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "services" / "sales_assistant.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "migrations" / "0004_seed_sales_crm_permissions.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "business_wave_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "BUSINESS_WAVE_1_SALES_CRM_AI_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "BUSINESS_WAVE_1_SALES_CRM_AI_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_sales_crm_ai.py",
        ],
        "expected_tag": "business-wave-1-complete",
    },
    "ai-cleanup": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AI_LEGACY_CLEANUP.md",
        "documents": [
            PROJECT_ROOT / "archive" / "legacy_ai" / "backend" / "services" / "ai_service.py",
            PROJECT_ROOT / "archive" / "legacy_ai" / "backend" / "repositories" / "ai_repository.py",
            PROJECT_ROOT / "archive" / "legacy_ai" / "backend" / "config" / "legacy_ai_settings.md",
            PROJECT_ROOT / "docs" / "ai" / "LEGACY_AI_INVENTORY.md",
            PROJECT_ROOT / "docs" / "ai" / "LEGACY_AI_ARCHIVE.md",
            PROJECT_ROOT / "docs" / "codex-prompts" / "AI_LEGACY_CLEANUP.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "ai_cleanup.json",
            PROJECT_ROOT / "docs" / "reviews" / "AI_LEGACY_CLEANUP_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_LEGACY_CLEANUP_FINAL_REPORT.md",
            PROJECT_ROOT / "tests" / "test_ai_legacy_cleanup.py",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_ai_legacy_cleanup.py",
            PROJECT_ROOT / "tests" / "test_ai_knowledge_assistant.py",
            PROJECT_ROOT / "tests" / "test_sales_crm_ai.py",
        ],
        "expected_tag": "ai-cleanup-complete",
    },
    "ai-core-upgrade": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "AI_CORE_UPGRADE_OLLAMA_REAL_INFERENCE.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "migrations" / "0001_ai_request_log.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "services" / "health_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "services" / "model_config.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "services" / "ollama_client.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "rag_pipeline.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "assistant_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "search_service.py",
            PROJECT_ROOT / "django_backend" / "apps" / "ai_agent" / "services" / "sales_assistant.py",
            PROJECT_ROOT / "docs" / "ai" / "OLLAMA_MODEL_GUIDE.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "ai_core_upgrade.json",
            PROJECT_ROOT / "docs" / "reviews" / "AI_CORE_UPGRADE_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_ollama_real_inference.py",
        ],
        "expected_tag": "ai-core-upgrade-complete",
    },
    "business-ai-wave-2": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "BUSINESS_AI_WAVE_2_PLATFORM_COMPLETION.md",
        "documents": [
            PROJECT_ROOT / "django_backend" / "apps" / "business_ui" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "business_ui" / "urls.py",
            PROJECT_ROOT / "django_backend" / "apps" / "business_ui" / "templates" / "business_ui" / "dashboard.html",
            PROJECT_ROOT / "django_backend" / "apps" / "knowledge" / "services" / "document_intelligence.py",
            PROJECT_ROOT / "scripts" / "n8n_business_wave2.py",
            PROJECT_ROOT / "n8n" / "workflows" / "business_wave2_automation.json",
            PROJECT_ROOT / "n8n" / "config" / "business_wave2_local.yml",
            PROJECT_ROOT / "ai-factory" / "v2_roles.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "business_ai_wave_2.json",
            PROJECT_ROOT / "docs" / "reviews" / "BUSINESS_UI_COMPLETION_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_DOCUMENT_INTELLIGENCE_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "N8N_AUTOMATION_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_FACTORY_V2_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "BUSINESS_AI_WAVE_2_FINAL_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "MEC_PRECISION_PLATFORM_COMPLETION_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_business_ui.py",
            PROJECT_ROOT / "tests" / "test_ai_document_intelligence.py",
            PROJECT_ROOT / "tests" / "test_n8n_automation.py",
            PROJECT_ROOT / "tests" / "test_ai_factory_v2.py",
        ],
        "expected_tag": "business-ai-wave-2-complete",
    },
    "business-simulation": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "MEC_BUSINESS_SIMULATION_PHASE.md",
        "documents": [
            PROJECT_ROOT / "scripts" / "business_simulation.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "business_simulation.json",
            PROJECT_ROOT / "docs" / "reviews" / "business_simulation_executive_dashboard.json",
            PROJECT_ROOT / "docs" / "reviews" / "MEC_BUSINESS_SIMULATION_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "BUSINESS_SIMULATION_AI_REVIEW.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_business_simulation.py",
        ],
        "expected_tag": "business-simulation-complete",
    },
    "12.4": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4_AI_DEVOPS_CONTROL_CENTER.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_DEVOPS_CONTROL_CENTER_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_REVIEW_RULES.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "N8N_PHASE_REVIEW_WORKFLOW.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "n8n_phase_review_workflow.json",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.4_REVIEW_SUMMARY.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase12_4_ai_devops.py",
        ],
        "expected_tag": "phase-12.4-ai-devops-ready",
    },
    "12.4.1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4.1_OLLAMA_CONNECTION_VALIDATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-devops" / "OLLAMA_TEST_PROMPT.md",
            PROJECT_ROOT / "docs" / "ai-devops" / "ollama_environment_check.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "AI_PHASE_REVIEW_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.4.1_OLLAMA_VALIDATION_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase12_4_1_ollama_connection.py",
        ],
        "expected_tag": "phase-12.4.1-ollama-ready",
    },
    "13.2": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.2_AUTOMATED_TEST_PIPELINE.md",
        "documents": [
            PROJECT_ROOT / "docs" / "cicd" / "TEST_PIPELINE_ARCHITECTURE.md",
            PROJECT_ROOT / "ci" / "test_pipeline_config.yml",
            PROJECT_ROOT / ".github" / "workflows" / "test_pipeline.yml",
            PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "TEST_PIPELINE_AI_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.2_TEST_PIPELINE_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_2_test_pipeline.py",
        ],
        "expected_tag": "phase-13.2-test-pipeline-ready",
    },
    "13.3": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.3_N8N_CICD_ORCHESTRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "n8n" / "N8N_CICD_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "n8n" / "n8n_cicd_pipeline_workflow.json",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_SETUP_GUIDE.md",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_NOTIFICATION_DESIGN.md",
            PROJECT_ROOT / "docs" / "n8n" / "n8n_execution_report.json",
            PROJECT_ROOT / "docs" / "ai-devops" / "N8N_AI_REVIEW_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.3_N8N_CICD_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_3_n8n.py",
        ],
        "expected_tag": "phase-13.3-n8n-ready",
    },
    "13.4": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.4_DEPLOYMENT_AUTOMATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_RUNBOOK.md",
            PROJECT_ROOT / "docs" / "deployment" / "DEPLOYMENT_SECURITY.md",
            PROJECT_ROOT / "docs" / "deployment" / "deployment_result.json",
            PROJECT_ROOT / "docs" / "deployment" / "health_result.json",
            PROJECT_ROOT / "docs" / "deployment" / "rollback_result.json",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_DEPLOYMENT_WORKFLOW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.4_DEPLOYMENT_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_4_deployment.py",
        ],
        "expected_tag": "phase-13.4-deployment-ready",
    },
    "13.5": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.5_AI_PHASE_REVIEW_ENGINE.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-review" / "AI_PHASE_REVIEW_ENGINE_ARCHITECTURE.md",
            PROJECT_ROOT / "ai-review" / "config.yml",
            PROJECT_ROOT / "ai-review" / "evidence_collector.py",
            PROJECT_ROOT / "ai-review" / "requirement_validator.py",
            PROJECT_ROOT / "ai-review" / "test_executor.py",
            PROJECT_ROOT / "ai-review" / "ollama_phase_reviewer.py",
            PROJECT_ROOT / "ai-review" / "report_generator.py",
            PROJECT_ROOT / "ai-review" / "run_phase_review.py",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_5_ai_review_engine.py",
        ],
        "expected_tag": "phase-13.5-ai-review-ready",
    },
    "13.6": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.6_AI_SELF_CORRECTION_LOOP.md",
        "documents": [
            PROJECT_ROOT / "ai-review" / "error_collector.py",
            PROJECT_ROOT / "ai-review" / "ollama_error_analyzer.py",
            PROJECT_ROOT / "ai-review" / "codex_fix_generator.py",
            PROJECT_ROOT / "ai-review" / "retry_controller.py",
            PROJECT_ROOT / "docs" / "ai-review" / "SELF_CORRECTION_SECURITY.md",
            PROJECT_ROOT / "docs" / "codex-prompts" / "AUTO_FIX_TASK.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.6_SELF_CORRECTION_REPORT.md",
            PROJECT_ROOT / "ai-review" / "results" / "error_report.json",
            PROJECT_ROOT / "ai-review" / "results" / "error_analysis.json",
            PROJECT_ROOT / "ai-review" / "results" / "self_correction_result.json",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_6_self_correction.py",
        ],
        "expected_tag": "phase-13.6-self-correction-ready",
    },
    "13.7": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.7_N8N_REAL_AUTOMATION_CONTROLLER.md",
        "documents": [
            PROJECT_ROOT / "docs" / "n8n" / "N8N_REAL_AUTOMATION_ARCHITECTURE.md",
            PROJECT_ROOT / "n8n" / "workflows" / "phase_automation_controller.json",
            PROJECT_ROOT / "n8n" / "config" / "n8n_phase_controller.yml",
            PROJECT_ROOT / "scripts" / "n8n_phase_trigger.py",
            PROJECT_ROOT / "docs" / "n8n" / "N8N_NOTIFICATION_DESIGN.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_13.7_N8N_AUTOMATION_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_7_n8n_controller.py",
        ],
        "expected_tag": "phase-13.7-n8n-controller-ready",
    },
    "13.8": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_13.8_AI_SOFTWARE_FACTORY_FINAL_INTEGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "ai-factory" / "AI_SOFTWARE_FACTORY_ARCHITECTURE.md",
            PROJECT_ROOT / "docs" / "ai-factory" / "AI_SOFTWARE_FACTORY_GUIDE.md",
            PROJECT_ROOT / "ai-factory" / "run_ai_factory.py",
            PROJECT_ROOT / "ai-factory" / "evidence_builder.py",
            PROJECT_ROOT / "ai-factory" / "final_report_generator.py",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_requirement_template.md",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_test_template.md",
            PROJECT_ROOT / "ai-factory" / "templates" / "phase_review_template.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_SOFTWARE_FACTORY_REPORT.md",
            PROJECT_ROOT / "docs" / "reviews" / "AI_SOFTWARE_FACTORY_FINAL_SUMMARY.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase13_8_ai_factory.py",
        ],
        "expected_tag": "phase-13.8-ai-factory-complete",
    },
    "14.1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_14.1_DJANGO_OWNERSHIP_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "PHASE_14.1_DOMAIN_SELECTION.md",
            PROJECT_ROOT / "docs" / "django-migration" / "DJANGO_OWNERSHIP_DESIGN.md",
            PROJECT_ROOT / "docs" / "django-migration" / "MIGRATION_RESULT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "newsletter" / "migrations" / "0002_import_legacy_subscribers.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "newsletter.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "newsletter.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_phase14_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_14.1_DJANGO_OWNERSHIP_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "PHASE_14.1_DJANGO_OWNERSHIP_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_phase14_1_django_ownership.py",
        ],
        "expected_tag": "phase-14.1-django-ownership-ready",
    },
    "django-wave-1": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_1_DJANGO_FOUNDATION_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_AUTH_AUDIT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_USER_PROFILE_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE1_PERMISSION_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "foundation" / "migrations" / "0002_seed_foundation_from_legacy.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "foundation.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "foundation.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_1.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_1_DJANGO_FOUNDATION_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_1_DJANGO_FOUNDATION_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave1_django_foundation.py",
        ],
        "expected_tag": "wave-1-django-foundation-complete",
    },
    "django-wave-2": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_2_DJANGO_BUSINESS_CORE_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE2_PRODUCT_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE2_CUSTOMER_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE2_INVENTORY_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE2_DATABASE_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "business_core" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "business_core" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "business_core" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "business_core" / "migrations" / "0002_seed_business_core_from_legacy.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "business_core.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "business_core.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_2.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_2_DJANGO_BUSINESS_CORE_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_2_DJANGO_BUSINESS_CORE_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave2_business_core.py",
        ],
        "expected_tag": "wave-2-business-core-complete",
    },
    "django-wave-3": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_3_DJANGO_TRANSACTION_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE3_ORDER_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE3_WORKFLOW_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE3_TRANSACTION_HISTORY_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE3_DATABASE_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "transaction_domain" / "models.py",
            PROJECT_ROOT / "django_backend" / "apps" / "transaction_domain" / "services.py",
            PROJECT_ROOT / "django_backend" / "apps" / "transaction_domain" / "migrations" / "0001_initial.py",
            PROJECT_ROOT / "django_backend" / "apps" / "transaction_domain" / "migrations" / "0002_seed_transaction_domain_from_legacy.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "transaction_domain.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "transaction_domain.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_3.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_3_DJANGO_TRANSACTION_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_3_DJANGO_TRANSACTION_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave3_transaction_domain.py",
        ],
        "expected_tag": "wave-3-transaction-complete",
    },
    "django-wave-4": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_4_DJANGO_LEGACY_REDUCTION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE4_LEGACY_DEPENDENCY_AUDIT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE4_PAYMENT_DECISION.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE4_DATABASE_OWNERSHIP_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE4_LEGACY_RETIREMENT_PLAN.md",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_4.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_4_DJANGO_FINAL_OWNERSHIP_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_4_DJANGO_LEGACY_REDUCTION_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave4_legacy_reduction.py",
        ],
        "expected_tag": "wave-4-django-ownership-final",
    },
    "django-wave-5": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_5_DJANGO_ADMIN_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE5_ADMIN_AUDIT_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE5_ADMIN_FOUNDATION_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE5_ADMIN_DOMAIN_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE5_LEGACY_ADMIN_REDUCTION_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "serializers" / "admin_interface.py",
            PROJECT_ROOT / "django_backend" / "apps" / "api" / "views" / "admin_interface.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_5.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_5_DJANGO_ADMIN_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_5_DJANGO_ADMIN_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave5_admin_migration.py",
        ],
        "expected_tag": "wave-5-django-admin-complete",
    },
    "django-wave-6": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_6_DJANGO_ADMIN_UI_CUTOVER.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE6_ADMIN_UI_AUDIT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE6_ADMIN_UI_FOUNDATION_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE6_ADMIN_DOMAIN_UI_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE6_CUTOVER_VALIDATION_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "admin_ui" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "admin_ui" / "forms.py",
            PROJECT_ROOT / "django_backend" / "apps" / "admin_ui" / "urls.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_6.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_6_DJANGO_ADMIN_UI_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_6_DJANGO_ADMIN_UI_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave6_admin_ui.py",
        ],
        "expected_tag": "wave-6-admin-ui-complete",
    },
    "django-wave-7": {
        "prompt": PROJECT_ROOT / "docs" / "codex-prompts" / "WAVE_7_DJANGO_PUBLIC_WEBSITE_MIGRATION.md",
        "documents": [
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_PUBLIC_AUDIT_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_WEBSITE_FOUNDATION_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_HOME_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_PRODUCT_WEB_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_TECHNOLOGY_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_CONTENT_CONTACT_REPORT.md",
            PROJECT_ROOT / "docs" / "django-migration" / "WAVE7_CUTOVER_REPORT.md",
            PROJECT_ROOT / "django_backend" / "apps" / "website" / "views.py",
            PROJECT_ROOT / "django_backend" / "apps" / "website" / "forms.py",
            PROJECT_ROOT / "django_backend" / "apps" / "website" / "urls.py",
            PROJECT_ROOT / "ai-factory" / "evidence" / "django_wave_7.json",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_7_DJANGO_PUBLIC_WEBSITE_REVIEW.md",
            PROJECT_ROOT / "docs" / "reviews" / "WAVE_7_DJANGO_PUBLIC_WEBSITE_FINAL_REPORT.md",
        ],
        "tests": [
            PROJECT_ROOT / "tests" / "test_wave7_public_website.py",
        ],
        "expected_tag": "wave-7-public-website-complete",
    }
}


def utc_now():
    """Return a timestamp for validation evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Run a safe read-only Git command and return stripped stdout."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def file_status(path):
    """Return existence and size information for one required file."""
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def validate_phase(phase="12.4.1", output_path=None):
    """Validate required artifacts for a migration phase."""
    requirements = PHASE_REQUIREMENTS.get(phase)
    missing = []
    warnings = []
    notes = []
    checked_files = []

    if not requirements:
        missing.append(f"No phase requirements configured for {phase}")
        requirements = {"prompt": None, "documents": [], "tests": [], "expected_tag": ""}

    required_paths = []
    if requirements.get("prompt"):
        required_paths.append(requirements["prompt"])
    required_paths.extend(requirements.get("documents", []))
    required_paths.extend(requirements.get("tests", []))

    for path in required_paths:
        status = file_status(path)
        checked_files.append(status)
        if not status["exists"]:
            missing.append(status["path"])
        elif status["size_bytes"] == 0:
            warnings.append(f"Empty file: {status['path']}")

    git_status = run_git(["status", "--short"])
    git_branch = run_git(["branch", "--show-current"])
    tag_result = run_git(["tag", "--list", requirements.get("expected_tag", "")])
    expected_tag = requirements.get("expected_tag", "")
    tag_present = bool(tag_result["stdout"]) if expected_tag else False
    if expected_tag and not tag_present:
        notes.append(f"Expected tag not found yet: {expected_tag}")

    unsafe_status_lines = []
    for line in git_status["stdout"].splitlines():
        if "docs.zip" in line:
            continue
        if "phase_validation_result.json" in line:
            continue
        unsafe_status_lines.append(line)
    if unsafe_status_lines:
        notes.append("Working tree has uncommitted phase changes.")

    status = "PASS" if not missing else "FAIL"
    result = {
        "phase": phase,
        "created_at": utc_now(),
        "status": status,
        "missing": missing,
        "warnings": warnings,
        "notes": notes,
        "checked_files": checked_files,
        "git": {
            "branch": git_branch["stdout"],
            "status_short": git_status["stdout"],
            "expected_tag": expected_tag,
            "expected_tag_present": tag_present,
        },
        "safety": {
            "production_modified": False,
            "auto_deploy": False,
            "auto_approve_production": False,
            "human_review_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    parser = argparse.ArgumentParser(description="Validate migration phase artifacts.")
    parser.add_argument("--phase", default="12.4.1")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = validate_phase(phase=args.phase, output_path=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
