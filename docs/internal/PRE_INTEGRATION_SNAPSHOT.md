# Pre-integration snapshot

Generated: 2026-09-23T18:16:31.117Z

This report is intentionally uncommitted. It records the source worktree before creating `integration/platform-current`.

## Current branch

```text
codex/demo-database-validation
```

## Branches

```text
  backup/phase6-pre-remote-merge                eca707a phase6: finalize portfolio production-demo release candidate
+ codex/ai-assistant-update                     af309f1 (C:/Users/hoang/Documents/ChatGPT/ai-assistant-update) feat: add canonical AI assistant workspaces
* codex/demo-database-validation                8458ab7 [origin/codex/demo-database-validation] Merge remote-tracking branch 'origin/codex/demo-database-validation' into codex/demo-database-validation
  remotes/origin/HEAD                           -> origin/codex/demo-database-validation
  remotes/origin/codex/ai-assistant-update      af309f1 feat: add canonical AI assistant workspaces
  remotes/origin/codex/demo-database-validation 8458ab7 Merge remote-tracking branch 'origin/codex/demo-database-validation' into codex/demo-database-validation
  remotes/origin/main                           5a015e8 chore: initialize migration git workflow
```

## Dirty files (porcelain status)

```text
 M django_backend/apps/ai_agent/services/sales_assistant.py
 M django_backend/apps/ai_agent/views.py
 M django_backend/apps/api/serializers/business_core.py
 M django_backend/apps/api/serializers/transaction_domain.py
MM django_backend/apps/api/urls.py
 M django_backend/apps/api/views/admin_interface.py
 M django_backend/apps/business_core/models.py
 M django_backend/apps/business_core/services.py
A  django_backend/apps/knowledge/management/commands/import_public_chatbot_draft.py
A  django_backend/apps/knowledge/management/commands/prepare_public_chatbot_demo.py
 M django_backend/apps/knowledge/management/commands/reindex_knowledge_embeddings.py
A  django_backend/apps/knowledge/management/commands/verify_public_chatbot_demo.py
A  django_backend/apps/knowledge/management/commands/verify_public_chatbot_draft.py
 M django_backend/apps/knowledge/models.py
 M django_backend/apps/knowledge/services/assistant_service.py
 M django_backend/apps/knowledge/services/business_connector.py
 M django_backend/apps/knowledge/services/knowledge_indexer.py
 M django_backend/apps/knowledge/services/knowledge_service.py
AM django_backend/apps/knowledge/services/public_assistant_service.py
MM django_backend/apps/knowledge/services/rag_pipeline.py
 M django_backend/apps/knowledge/services/runtime_health.py
MM django_backend/apps/knowledge/services/search_service.py
A  django_backend/apps/knowledge/tests/__init__.py
AM django_backend/apps/knowledge/tests/test_public_assistant.py
MM django_backend/apps/knowledge/views.py
 M django_backend/apps/transaction_domain/models.py
 M django_backend/config/settings/base.py
MM django_backend/config/settings/development.py
A  django_backend/config/settings/public_chatbot_demo.py
 M figma_make_frontend/.env.example
MM figma_make_frontend/package.json
MM figma_make_frontend/src/App.tsx
AM figma_make_frontend/src/api/aiDemo.ts
 M figma_make_frontend/src/api/phase6c.test.ts
A  figma_make_frontend/src/api/publicChatbot.test.ts
 M tests/test_sales_crm_ai.py
?? BAO_CAO_TONG_THE_DU_AN.md
?? CHATGPT_AI_DEMO_FINAL_REPORT.md
?? CHATGPT_AI_DEMO_HANDOFF_REPORT.md
?? CHATGPT_PHASE3A_ADMIN_CONTRACT_HANDOFF_REPORT.md
?? CHATGPT_PHASE3B_ADMIN_QUERY_HANDOFF_REPORT.md
?? CHATGPT_PUBLIC_CHATBOT_STAGING_HANDOFF_REPORT.md
?? CHATGPT_RAG_CHATBOT_DEMO_REPORT.md
?? MERGE_READINESS_RAG_CHATBOT_REPORT.md
?? PHASE1_5_ADMIN_RUNTIME_VALIDATION_REPORT.md
?? PHASE1_ADMIN_API_INTEGRATION_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md
?? PRODUCTION_LIKE_DATA_SEED_PLAN.md
?? PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md
?? PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md
?? PROJECT_MASTER_REPORT_FOR_CHATGPT.md
?? PUBLIC_CHATBOT_API_UI_VERIFICATION_REPORT.md
?? PUBLIC_CHATBOT_CONTENT_APPROVAL_TABLE.md
?? PUBLIC_RAG_CHATBOT_HOMEPAGE_REPORT.md
?? REPOSITORY_BASELINE_AUDIT_REPORT.md
?? SAFE_MAIN_MERGE_REPORT.md
?? SYSTEM_DATA_FLOW_AUDIT.md
?? django_backend/apps/ai_agent/services/sales_access.py
?? django_backend/apps/api/admin_query.py
?? django_backend/apps/api/serializers/capabilities.py
?? django_backend/apps/api/serializers/public_products.py
?? django_backend/apps/api/tests/test_capability_cms.py
?? django_backend/apps/api/tests/test_phase3a_admin_contract.py
?? django_backend/apps/api/tests/test_phase3b_admin_queries.py
?? django_backend/apps/api/tests/test_public_product_permission_security.py
?? django_backend/apps/api/tests/test_public_product_security.py
?? django_backend/apps/api/views/capabilities.py
?? django_backend/apps/api/views/public_products.py
?? django_backend/apps/business_core/capabilities.py
?? django_backend/apps/business_core/migrations/0006_public_product_projection.py
?? django_backend/apps/business_core/migrations/0007_capability.py
?? django_backend/apps/business_core/publication.py
?? django_backend/apps/core/management/commands/ensure_local_ai_demo_user.py
?? django_backend/apps/core/management/commands/seed_production_demo.py
?? django_backend/apps/core/production_demo_seed/
?? django_backend/apps/core/tests/test_production_demo_seed.py
?? django_backend/apps/foundation/migrations/0011_phase5c_public_product_permissions.py
?? django_backend/apps/foundation/migrations/0012_phase6a_capability_permissions.py
?? django_backend/apps/knowledge/management/commands/run_synthetic_rag_demo.py
?? django_backend/apps/knowledge/management/commands/sync_database_knowledge_candidates.py
?? django_backend/apps/knowledge/migrations/0004_governance_access.py
?? django_backend/apps/knowledge/migrations/0005_department_scope.py
?? django_backend/apps/knowledge/migrations/0006_controlled_pilot_evaluation.py
?? django_backend/apps/knowledge/migrations/0007_owner_review_and_gap_analysis.py
?? django_backend/apps/knowledge/migrations/0008_pilot_program_launch_gate.py
?? django_backend/apps/knowledge/migrations/0009_document_quality_review.py
?? django_backend/apps/knowledge/migrations/0010_onboarding_and_confidentiality_evidence.py
?? django_backend/apps/knowledge/services/access_policy.py
?? django_backend/apps/knowledge/services/database_knowledge_adapter.py
?? django_backend/apps/knowledge/services/governance.py
?? django_backend/apps/knowledge/services/pilot_batch_ingestion.py
?? django_backend/apps/knowledge/services/pilot_governance.py
?? django_backend/apps/knowledge/services/pilot_monitoring.py
?? django_backend/apps/knowledge/services/pilot_program.py
?? django_backend/apps/knowledge/services/public_synthetic_rag_demo.py
?? django_backend/apps/knowledge/services/synthetic_rag_demo.py
?? django_backend/apps/knowledge/tests/test_controlled_pilot_execution.py
?? django_backend/apps/knowledge/tests/test_database_knowledge_adapter.py
?? django_backend/apps/knowledge/tests/test_governance_access.py
?? django_backend/apps/knowledge/tests/test_pilot_acceptance_matrix.py
?? django_backend/apps/knowledge/tests/test_pilot_security_validation.py
?? django_backend/apps/knowledge/tests/test_public_synthetic_rag_demo.py
?? django_backend/apps/knowledge/tests/test_synthetic_rag_demo.py
?? django_backend/apps/knowledge/tests/test_synthetic_rag_web_demo.py
?? django_backend/tests/test_phase5c_migrations.py
?? django_backend/tests/test_phase6a_capability_migrations.py
?? figma_make_frontend/src/api/publicComponentDemo.test.ts
?? figma_make_frontend/src/api/ragChat.test.ts
?? figma_make_frontend/src/api/ragDemo.test.ts
?? figma_make_frontend/src/components/PublicComponentChatWidget.tsx
?? figma_make_frontend/src/components/RagChatPage.tsx
?? figma_make_frontend/src/components/RagDemoPage.tsx
?? figma_make_frontend/src/hooks/
?? figma_make_frontend/src/services/
?? figma_make_frontend/src/types/
?? reports/
```

## Staged files

```text
django_backend/apps/api/urls.py
django_backend/apps/knowledge/management/commands/import_public_chatbot_draft.py
django_backend/apps/knowledge/management/commands/prepare_public_chatbot_demo.py
django_backend/apps/knowledge/management/commands/verify_public_chatbot_demo.py
django_backend/apps/knowledge/management/commands/verify_public_chatbot_draft.py
django_backend/apps/knowledge/services/public_assistant_service.py
django_backend/apps/knowledge/services/rag_pipeline.py
django_backend/apps/knowledge/services/search_service.py
django_backend/apps/knowledge/tests/__init__.py
django_backend/apps/knowledge/tests/test_public_assistant.py
django_backend/apps/knowledge/views.py
django_backend/config/settings/development.py
django_backend/config/settings/public_chatbot_demo.py
figma_make_frontend/package.json
figma_make_frontend/src/App.tsx
figma_make_frontend/src/api/aiDemo.ts
figma_make_frontend/src/api/publicChatbot.test.ts
```

## Unstaged files

```text
warning: in the working copy of 'django_backend/apps/ai_agent/services/sales_assistant.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/ai_agent/views.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/api/serializers/business_core.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/api/serializers/transaction_domain.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/api/urls.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/api/views/admin_interface.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/business_core/models.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/business_core/services.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/management/commands/reindex_knowledge_embeddings.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/models.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/assistant_service.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/business_connector.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/knowledge_indexer.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/knowledge_service.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/public_assistant_service.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/rag_pipeline.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/runtime_health.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/services/search_service.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/tests/test_public_assistant.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/knowledge/views.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/apps/transaction_domain/models.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/config/settings/base.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'django_backend/config/settings/development.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'figma_make_frontend/.env.example', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'figma_make_frontend/package.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'figma_make_frontend/src/App.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'figma_make_frontend/src/api/aiDemo.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'figma_make_frontend/src/api/phase6c.test.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/test_sales_crm_ai.py', LF will be replaced by CRLF the next time Git touches it
django_backend/apps/ai_agent/services/sales_assistant.py
django_backend/apps/ai_agent/views.py
django_backend/apps/api/serializers/business_core.py
django_backend/apps/api/serializers/transaction_domain.py
django_backend/apps/api/urls.py
django_backend/apps/api/views/admin_interface.py
django_backend/apps/business_core/models.py
django_backend/apps/business_core/services.py
django_backend/apps/knowledge/management/commands/reindex_knowledge_embeddings.py
django_backend/apps/knowledge/models.py
django_backend/apps/knowledge/services/assistant_service.py
django_backend/apps/knowledge/services/business_connector.py
django_backend/apps/knowledge/services/knowledge_indexer.py
django_backend/apps/knowledge/services/knowledge_service.py
django_backend/apps/knowledge/services/public_assistant_service.py
django_backend/apps/knowledge/services/rag_pipeline.py
django_backend/apps/knowledge/services/runtime_health.py
django_backend/apps/knowledge/services/search_service.py
django_backend/apps/knowledge/tests/test_public_assistant.py
django_backend/apps/knowledge/views.py
django_backend/apps/transaction_domain/models.py
django_backend/config/settings/base.py
django_backend/config/settings/development.py
figma_make_frontend/.env.example
figma_make_frontend/package.json
figma_make_frontend/src/App.tsx
figma_make_frontend/src/api/aiDemo.ts
figma_make_frontend/src/api/phase6c.test.ts
tests/test_sales_crm_ai.py
```

## Untracked files

```text
BAO_CAO_TONG_THE_DU_AN.md
CHATGPT_AI_DEMO_FINAL_REPORT.md
CHATGPT_AI_DEMO_HANDOFF_REPORT.md
CHATGPT_PHASE3A_ADMIN_CONTRACT_HANDOFF_REPORT.md
CHATGPT_PHASE3B_ADMIN_QUERY_HANDOFF_REPORT.md
CHATGPT_PUBLIC_CHATBOT_STAGING_HANDOFF_REPORT.md
CHATGPT_RAG_CHATBOT_DEMO_REPORT.md
MERGE_READINESS_RAG_CHATBOT_REPORT.md
PHASE1_5_ADMIN_RUNTIME_VALIDATION_REPORT.md
PHASE1_ADMIN_API_INTEGRATION_REPORT.md
PRODUCTION_LIKE_DATA_SEED_MILESTONE_1_REPORT.md
PRODUCTION_LIKE_DATA_SEED_MILESTONE_2_REPORT.md
PRODUCTION_LIKE_DATA_SEED_MILESTONE_3_FULL_REPORT.md
PRODUCTION_LIKE_DATA_SEED_PLAN.md
PRODUCTION_LIKE_FULL_LOCAL_APPLY_VERIFICATION_REPORT.md
PRODUCTION_LIKE_FULL_LOCAL_CORRECTIVE_VERIFICATION_REPORT.md
PROJECT_MASTER_REPORT_FOR_CHATGPT.md
PUBLIC_CHATBOT_API_UI_VERIFICATION_REPORT.md
PUBLIC_CHATBOT_CONTENT_APPROVAL_TABLE.md
PUBLIC_RAG_CHATBOT_HOMEPAGE_REPORT.md
REPOSITORY_BASELINE_AUDIT_REPORT.md
SAFE_MAIN_MERGE_REPORT.md
SYSTEM_DATA_FLOW_AUDIT.md
django_backend/apps/ai_agent/services/sales_access.py
django_backend/apps/api/admin_query.py
django_backend/apps/api/serializers/capabilities.py
django_backend/apps/api/serializers/public_products.py
django_backend/apps/api/tests/test_capability_cms.py
django_backend/apps/api/tests/test_phase3a_admin_contract.py
django_backend/apps/api/tests/test_phase3b_admin_queries.py
django_backend/apps/api/tests/test_public_product_permission_security.py
django_backend/apps/api/tests/test_public_product_security.py
django_backend/apps/api/views/capabilities.py
django_backend/apps/api/views/public_products.py
django_backend/apps/business_core/capabilities.py
django_backend/apps/business_core/migrations/0006_public_product_projection.py
django_backend/apps/business_core/migrations/0007_capability.py
django_backend/apps/business_core/publication.py
django_backend/apps/core/management/commands/ensure_local_ai_demo_user.py
django_backend/apps/core/management/commands/seed_production_demo.py
django_backend/apps/core/production_demo_seed/__init__.py
django_backend/apps/core/production_demo_seed/ai_eval_cases.py
django_backend/apps/core/production_demo_seed/generators.py
django_backend/apps/core/production_demo_seed/historical.py
django_backend/apps/core/production_demo_seed/lifecycle.py
django_backend/apps/core/production_demo_seed/ownership.py
django_backend/apps/core/production_demo_seed/profiles.py
django_backend/apps/core/production_demo_seed/report.py
django_backend/apps/core/production_demo_seed/safety.py
django_backend/apps/core/production_demo_seed/validators.py
django_backend/apps/core/tests/test_production_demo_seed.py
django_backend/apps/foundation/migrations/0011_phase5c_public_product_permissions.py
django_backend/apps/foundation/migrations/0012_phase6a_capability_permissions.py
django_backend/apps/knowledge/management/commands/run_synthetic_rag_demo.py
django_backend/apps/knowledge/management/commands/sync_database_knowledge_candidates.py
django_backend/apps/knowledge/migrations/0004_governance_access.py
django_backend/apps/knowledge/migrations/0005_department_scope.py
django_backend/apps/knowledge/migrations/0006_controlled_pilot_evaluation.py
django_backend/apps/knowledge/migrations/0007_owner_review_and_gap_analysis.py
django_backend/apps/knowledge/migrations/0008_pilot_program_launch_gate.py
django_backend/apps/knowledge/migrations/0009_document_quality_review.py
django_backend/apps/knowledge/migrations/0010_onboarding_and_confidentiality_evidence.py
django_backend/apps/knowledge/services/access_policy.py
django_backend/apps/knowledge/services/database_knowledge_adapter.py
django_backend/apps/knowledge/services/governance.py
django_backend/apps/knowledge/services/pilot_batch_ingestion.py
django_backend/apps/knowledge/services/pilot_governance.py
django_backend/apps/knowledge/services/pilot_monitoring.py
django_backend/apps/knowledge/services/pilot_program.py
django_backend/apps/knowledge/services/public_synthetic_rag_demo.py
django_backend/apps/knowledge/services/synthetic_rag_demo.py
django_backend/apps/knowledge/tests/test_controlled_pilot_execution.py
django_backend/apps/knowledge/tests/test_database_knowledge_adapter.py
django_backend/apps/knowledge/tests/test_governance_access.py
django_backend/apps/knowledge/tests/test_pilot_acceptance_matrix.py
django_backend/apps/knowledge/tests/test_pilot_security_validation.py
django_backend/apps/knowledge/tests/test_public_synthetic_rag_demo.py
django_backend/apps/knowledge/tests/test_synthetic_rag_demo.py
django_backend/apps/knowledge/tests/test_synthetic_rag_web_demo.py
django_backend/tests/test_phase5c_migrations.py
django_backend/tests/test_phase6a_capability_migrations.py
figma_make_frontend/src/api/publicComponentDemo.test.ts
figma_make_frontend/src/api/ragChat.test.ts
figma_make_frontend/src/api/ragDemo.test.ts
figma_make_frontend/src/components/PublicComponentChatWidget.tsx
figma_make_frontend/src/components/RagChatPage.tsx
figma_make_frontend/src/components/RagDemoPage.tsx
figma_make_frontend/src/hooks/useAdminTableQuery.test.ts
figma_make_frontend/src/hooks/useAdminTableQuery.ts
figma_make_frontend/src/services/adminApi.test.ts
figma_make_frontend/src/services/adminApi.ts
figma_make_frontend/src/services/publicApi.test.ts
figma_make_frontend/src/services/publicApi.ts
figma_make_frontend/src/types/admin.ts
figma_make_frontend/src/types/public.ts
reports/phase2/01_REAL_PRODUCT_SOURCE_DISCOVERY.md
reports/phase2/02_REAL_PRODUCT_SOURCE_CLASSIFICATION.md
reports/phase2/03_REAL_PRODUCT_PROVENANCE_REPORT.md
reports/phase2/04_REAL_PRODUCT_SCHEMA_MAPPING.md
reports/phase2/05_REAL_PRODUCT_DUPLICATE_MATCHING_POLICY.md
reports/phase2/06_REAL_PRODUCT_IMPORT_VALIDATION_POLICY.md
reports/phase2/07_REAL_PRODUCT_IMPORT_DRY_RUN_REPORT.md
reports/phase2/08_FIRST_REAL_PRODUCT_DATASET_PLAN.md
reports/phase2/09_REAL_PRODUCT_DATA_SECURITY_REPORT.md
reports/phase2/10_PHASE2_FINAL_REPORT.md
reports/phase2/ADMIN_TABLE_PERFORMANCE_REPORT.md
reports/phase2/CUSTOMER_DATA_MODEL_REPORT.md
reports/phase2/INVENTORY_DATA_MODEL_REPORT.md
reports/phase2/ORDER_DATA_MODEL_REPORT.md
reports/phase2/PHASE2_SUMMARY_REPORT.md
reports/phase2/PRODUCT_DATA_MODEL_REPORT.md
reports/phase2/REAL_PRODUCT_IMPORT_MAPPING.md
reports/phase2/REAL_PRODUCT_IMPORT_TEMPLATE.csv
reports/phase2/REAL_PRODUCT_IMPORT_TEMPLATE.xlsx
reports/phase2/ROLE_PERMISSION_ALIGNMENT_REPORT.md
reports/phase2/TRANSACTION_DOMAIN_REPORT.md
reports/phase4/CAPABILITY_CONTENT_DESIGN.md
reports/phase4/PHASE4_SUMMARY_REPORT.md
reports/phase4/PROJECT_CASE_STUDY_DOMAIN_REPORT.md
reports/phase4/PUBLIC_API_CONTRACT_DESIGN.md
reports/phase4/PUBLIC_CONTENT_AUDIT_REPORT.md
reports/phase4/PUBLIC_DATA_SECURITY_REVIEW.md
reports/phase4/PUBLIC_NEWS_DESIGN.md
reports/phase4/PUBLIC_PRODUCT_API_DESIGN.md
reports/phase5a/PHASE5A_DECISION_GATE_REPORT.md
reports/phase5a/PHASE5A_SUMMARY_REPORT.md
reports/phase5a/PUBLIC_FRONTEND_INTEGRATION_PLAN.md
reports/phase5a/PUBLIC_PRODUCT_API_CONTRACT.md
reports/phase5a/PUBLIC_PRODUCT_PROJECTION_DESIGN.md
reports/phase5a/PUBLIC_PRODUCT_PUBLICATION_AUDIT.md
reports/phase5a/PUBLIC_PRODUCT_SECURITY_TEST_PLAN.md
reports/phase5b/HOW_TO_CREATE_FIRST_PUBLIC_PRODUCT.md
reports/phase5b/PHASE5B_IMPLEMENTATION_REPORT.md
reports/phase5b/PHASE5B_PERMISSION_GAP_REPORT.md
reports/phase5b/PUBLIC_FRONTEND_INTEGRATION_REPORT.md
reports/phase5b/PUBLIC_PRODUCT_API_RUNTIME_REPORT.md
reports/phase5b/PUBLIC_PRODUCT_SECURITY_TEST_REPORT.md
reports/phase5b1/CURRENT_PERMISSION_MATRIX.md
reports/phase5b1/PHASE5B1_SUMMARY_REPORT.md
reports/phase5b1/PUBLIC_PRODUCT_APPROVAL_GOVERNANCE_OPTIONS.md
reports/phase5b1/PUBLIC_PRODUCT_PERMISSION_DESIGN.md
reports/phase5b1/PUBLIC_PRODUCT_PERMISSION_TEST_PLAN.md
reports/phase5b1/PUBLIC_PRODUCT_PUBLICATION_SECURITY_CHECKLIST.md
reports/phase5b1/PUBLIC_PRODUCT_ROLE_MAPPING_PROPOSAL.md
reports/phase5b1/PUBLIC_PRODUCT_STATE_MACHINE_REPORT.md
reports/phase5c/BREAK_GLASS_POLICY_REPORT.md
reports/phase5c/PERMISSION_MIGRATION_REPORT.md
reports/phase5c/PHASE5C_SUMMARY_REPORT.md
reports/phase5c/PUBLIC_PRODUCT_AUDIT_LOG_REPORT.md
reports/phase5c/PUBLIC_PRODUCT_PERMISSION_SECURITY_TEST_REPORT.md
reports/phase5c/ROLE_PERMISSION_IMPLEMENTATION_REPORT.md
reports/phase6a/CAPABILITY_API_RUNTIME_REPORT.md
reports/phase6a/CAPABILITY_IMPLEMENTATION_REPORT.md
reports/phase6a/CAPABILITY_PERMISSION_TEST_REPORT.md
reports/phase6a/CAPABILITY_PUBLIC_INTEGRATION_REPORT.md
reports/phase6a/PHASE6A_FINAL_REPORT.md
reports/phase6b/CUSTOMER_VISIBILITY_GOVERNANCE_REPORT.md
reports/phase6b/PHASE6B_SUMMARY_REPORT.md
reports/phase6b/PROJECT_ADMIN_CMS_DESIGN.md
reports/phase6b/PROJECT_CURRENT_STATE_REPORT.md
reports/phase6b/PROJECT_DOMAIN_DEFINITION_REPORT.md
reports/phase6b/PROJECT_IMPLEMENTATION_ROADMAP.md
reports/phase6b/PROJECT_PUBLICATION_WORKFLOW_DESIGN.md
reports/phase6b/PROJECT_SECURITY_REVIEW.md
reports/phase6b/PUBLIC_CASE_STUDY_MODEL_DESIGN.md
reports/phase6b/PUBLIC_PROJECT_API_DESIGN.md
reports/phase6c/NEWS_ADMIN_CMS_DESIGN.md
reports/phase6c/NEWS_CONTENT_GOVERNANCE_REPORT.md
reports/phase6c/NEWS_CURRENT_STATE_REPORT.md
reports/phase6c/NEWS_DOMAIN_DEFINITION_REPORT.md
reports/phase6c/NEWS_IMPLEMENTATION_ROADMAP.md
reports/phase6c/NEWS_MODEL_DESIGN.md
reports/phase6c/NEWS_PUBLICATION_WORKFLOW_DESIGN.md
reports/phase6c/NEWS_SECURITY_REVIEW.md
reports/phase6c/NEWS_SEO_REQUIREMENT_REPORT.md
reports/phase6c/PHASE6C_SUMMARY_REPORT.md
reports/phase6c/PUBLIC_NEWS_API_DESIGN.md
reports/phase7/PHASE7_SUMMARY_REPORT.md
reports/phase7/PUBLIC_RFQ_API_DESIGN.md
reports/phase7/QUOTATION_DOMAIN_DESIGN.md
reports/phase7/RFQ_ADMIN_DESIGN.md
reports/phase7/RFQ_CURRENT_STATE_REPORT.md
reports/phase7/RFQ_CUSTOMER_DATA_GOVERNANCE.md
reports/phase7/RFQ_DOMAIN_DEFINITION_REPORT.md
reports/phase7/RFQ_FILE_SECURITY_DESIGN.md
reports/phase7/RFQ_IMPLEMENTATION_ROADMAP.md
reports/phase7/RFQ_MODEL_DESIGN.md
reports/phase7/RFQ_SECURITY_REVIEW.md
reports/phase7/RFQ_WORKFLOW_DESIGN.md
reports/phase7b/PHASE7B_FINAL_REPORT.md
reports/phase7b/PUBLIC_RFQ_DOMAIN_MAPPING_REPORT.md
reports/phase8a/AI_CURRENT_STATE_REPORT.md
reports/phase8a/AI_DATA_PREPARATION_ROADMAP.md
reports/phase8a/AI_DOCUMENT_GOVERNANCE_REPORT.md
reports/phase8a/AI_DOCUMENT_MODEL_DESIGN.md
reports/phase8a/AI_IMPLEMENTATION_ROADMAP.md
reports/phase8a/AI_KNOWLEDGE_DOMAIN_DESIGN.md
reports/phase8a/AI_PERMISSION_MODEL_DESIGN.md
reports/phase8a/AI_RETRIEVAL_ARCHITECTURE_REPORT.md
reports/phase8a/AI_SECURITY_REVIEW.md
reports/phase8a/AI_SOURCE_GROUNDING_DESIGN.md
reports/phase8a/PHASE8A_SUMMARY_REPORT.md
reports/phase8a1/AI_BUSINESS_DATA_SECURITY_REPORT.md
reports/phase8a1/AI_CITATION_GOVERNANCE_REPORT.md
reports/phase8a1/AI_CONFIDENCE_MODEL_REPORT.md
reports/phase8a1/AI_DOCUMENT_APPROVAL_GOVERNANCE_REPORT.md
reports/phase8a1/AI_GOVERNANCE_IMPLEMENTATION_ROADMAP.md
reports/phase8a1/AI_PERMISSION_HARDENING_REPORT.md
reports/phase8a1/AI_SECURITY_TEST_PLAN.md
reports/phase8a1/AI_VECTOR_STORAGE_REVIEW.md
reports/phase8a1/PHASE8A1_SUMMARY_REPORT.md
reports/phase8a1/PUBLIC_AI_RELEASE_POLICY.md
reports/phase8a1/RAG_INGESTION_CONTROL_DESIGN.md
reports/phase8a2/AI_APPROVAL_GATE_IMPLEMENTATION_REPORT.md
reports/phase8a2/AI_AUDIT_EVENT_IMPLEMENTATION_REPORT.md
reports/phase8a2/AI_BUSINESS_CONNECTOR_SECURITY_REPORT.md
reports/phase8a2/AI_CITATION_IMPLEMENTATION_REPORT.md
reports/phase8a2/AI_DOCUMENT_VERSION_CONTROL_REPORT.md
reports/phase8a2/AI_GOVERNANCE_SECURITY_TEST_REPORT.md
reports/phase8a2/AI_KNOWLEDGE_POLICY_IMPLEMENTATION_REPORT.md
reports/phase8a2/AI_VECTOR_STORAGE_NEXT_STEP_REPORT.md
reports/phase8a2/PHASE8A2_FINAL_REPORT.md
reports/phase8a2/RAG_ACCESS_CONTROL_IMPLEMENTATION_REPORT.md
reports/phase8b/AI_ADMIN_MONITORING_DESIGN.md
reports/phase8b/AI_FEEDBACK_LOOP_DESIGN.md
reports/phase8b/AI_PILOT_IMPLEMENTATION_ROADMAP.md
reports/phase8b/AI_PILOT_KNOWLEDGE_SET_REPORT.md
reports/phase8b/AI_RESPONSE_QUALITY_EVALUATION_REPORT.md
reports/phase8b/AI_SALES_USE_CASE_VALIDATION_REPORT.md
reports/phase8b/INTERNAL_AI_ACCESS_MODEL_REPORT.md
reports/phase8b/INTERNAL_AI_CHAT_DESIGN_REPORT.md
reports/phase8b/INTERNAL_AI_SECURITY_TEST_REPORT.md
reports/phase8b/PHASE8B_SUMMARY_REPORT.md
reports/phase8b1/AI_CONTROLLED_PILOT_CORPUS_REPORT.md
reports/phase8b1/AI_DEPARTMENT_SCOPE_IMPLEMENTATION_REPORT.md
reports/phase8b1/AI_PILOT_FEEDBACK_IMPLEMENTATION_REPORT.md
reports/phase8b1/AI_PILOT_GO_NO_GO_REPORT.md
reports/phase8b1/AI_PILOT_MONITORING_REPORT.md
reports/phase8b1/AI_PILOT_SECURITY_TEST_REPORT.md
reports/phase8b1/AI_PILOT_USER_ACCESS_REPORT.md
reports/phase8b1/AI_SALES_ASSISTANT_SECURITY_REPORT.md
reports/phase8b1/INTERNAL_AI_ACCEPTANCE_TEST_REPORT.md
reports/phase8b1/PHASE8B1_FINAL_REPORT.md
reports/phase8b1/RAG_DEPARTMENT_ACCESS_REPORT.md
reports/phase8b2/AI_HUMAN_EVALUATION_FRAMEWORK.md
reports/phase8b2/AI_PILOT_FEEDBACK_ANALYSIS_REPORT.md
reports/phase8b2/AI_PILOT_FINAL_GO_NO_GO_REPORT.md
reports/phase8b2/AI_PILOT_INGESTION_EXECUTION_REPORT.md
reports/phase8b2/AI_PILOT_MONITORING_REPORT.md
reports/phase8b2/AI_PILOT_QUALITY_ANALYSIS_REPORT.md
reports/phase8b2/AI_PILOT_QUESTION_BANK.md
reports/phase8b2/AI_PILOT_USER_APPROVAL_REPORT.md
reports/phase8b2/INTERNAL_AI_USER_GUIDE.md
reports/phase8b2/PHASE8B2_FINAL_REPORT.md
reports/phase8b2/REAL_PILOT_KNOWLEDGE_CORPUS_REPORT.md
reports/phase8b3/AI_KNOWLEDGE_GAP_ANALYSIS_REPORT.md
reports/phase8b3/AI_PILOT_IMPROVEMENT_LOOP_REPORT.md
reports/phase8b3/INTERNAL_AI_PILOT_EXECUTION_REPORT.md
reports/phase8b3/KNOWLEDGE_OWNER_APPROVAL_REPORT.md
reports/phase8b3/PHASE8B3_FINAL_REPORT.md
reports/phase8b3/REAL_AI_PILOT_FINAL_DECISION_REPORT.md
reports/phase8b3/REAL_AI_QUALITY_EVALUATION_REPORT.md
reports/phase8b3/REAL_CORPUS_INGESTION_REPORT.md
reports/phase8b3/REAL_KNOWLEDGE_INVENTORY_REPORT.md
reports/phase8b3/REAL_PILOT_CORPUS_PREPARATION_REPORT.md
reports/phase8b3/REAL_PILOT_USER_ACTIVATION_REPORT.md
reports/phase8b4/AI_KNOWLEDGE_IMPROVEMENT_LOOP_REPORT.md
reports/phase8b4/BUSINESS_DOCUMENT_APPROVAL_EXECUTION_REPORT.md
reports/phase8b4/FIRST_AI_HUMAN_REVIEW_REPORT.md
reports/phase8b4/FIRST_AI_PILOT_CORPUS_REPORT.md
reports/phase8b4/FIRST_AI_PILOT_METRICS_REPORT.md
reports/phase8b4/FIRST_INTERNAL_AI_PILOT_EXECUTION_REPORT.md
reports/phase8b4/FIRST_INTERNAL_AI_PILOT_FINAL_DECISION_REPORT.md
reports/phase8b4/FIRST_INTERNAL_AI_PILOT_USER_REPORT.md
reports/phase8b4/PHASE8B4_FINAL_REPORT.md
reports/phase8b4/REAL_BUSINESS_KNOWLEDGE_INVENTORY_REPORT.md
reports/phase8b4/REAL_KNOWLEDGE_INGESTION_EXECUTION_REPORT.md
reports/phase8b5/AI_OPERATION_FINAL_DECISION_REPORT.md
reports/phase8b5/AI_OPERATION_HUMAN_REVIEW_REPORT.md
reports/phase8b5/AI_OPERATION_IMPROVEMENT_REPORT.md
reports/phase8b5/AI_OPERATION_MONITORING_REPORT.md
reports/phase8b5/BUSINESS_DOCUMENT_QUALITY_REVIEW_REPORT.md
reports/phase8b5/BUSINESS_KNOWLEDGE_LOADING_REPORT.md
reports/phase8b5/BUSINESS_KNOWLEDGE_SELECTION_REPORT.md
reports/phase8b5/FIRST_AI_OPERATION_ACTIVATION_REPORT.md
reports/phase8b5/PHASE8B5_FINAL_REPORT.md
reports/phase8b5/REAL_BUSINESS_AI_TEST_REPORT.md
reports/phase8b6/FIRST_REAL_AI_HUMAN_EVALUATION_REPORT.md
reports/phase8b6/FIRST_REAL_AI_OPERATION_REPORT.md
reports/phase8b6/INTERNAL_AI_PILOT_ACTIVATION_REPORT.md
reports/phase8b6/INTERNAL_AI_USER_ONBOARDING_REPORT.md
reports/phase8b6/PHASE8B6_FINAL_REPORT.md
reports/phase8b6/REAL_AI_KNOWLEDGE_IMPROVEMENT_REPORT.md
reports/phase8b6/REAL_AI_OPERATION_FINAL_DECISION_REPORT.md
reports/phase8b6/REAL_AI_OPERATION_MONITORING_REPORT.md
reports/phase8b6/REAL_DOCUMENT_APPROVAL_EXECUTION_REPORT.md
reports/phase8b6/REAL_KNOWLEDGE_MIGRATION_REPORT.md
reports/phase8b6/REAL_KNOWLEDGE_SOURCE_REGISTRATION_REPORT.md
reports/phase8b7/CONTROLLED_AI_PILOT_OPERATION_REPORT.md
reports/phase8b7/CONTROLLED_PILOT_USER_ACTIVATION_REPORT.md
reports/phase8b7/PHASE8B7_FINAL_REPORT.md
reports/phase8b7/REAL_AI_HUMAN_REVIEW_REPORT.md
reports/phase8b7/REAL_AI_IMPROVEMENT_LOOP_REPORT.md
reports/phase8b7/REAL_AI_PILOT_FINAL_DECISION_REPORT.md
reports/phase8b7/REAL_AI_PILOT_METRICS_REPORT.md
reports/phase8b7/REAL_AI_QUESTION_EVALUATION_REPORT.md
reports/phase8b7/REAL_DOCUMENT_COLLECTION_REPORT.md
reports/phase8b7/REAL_DOCUMENT_GOVERNANCE_REVIEW_REPORT.md
reports/phase8b7/REAL_KNOWLEDGE_INGESTION_EXECUTION_REPORT.md
reports/phase8c0/DATABASE_KNOWLEDGE_REALITY_AUDIT.md
reports/phase8c0/DATABASE_RAG_PERMISSION_SECURITY_REPORT.md
reports/phase8c0/DATABASE_SOURCE_OF_TRUTH_CLASSIFICATION.md
reports/phase8c0/DATABASE_TO_RAG_SYNC_STRATEGY.md
reports/phase8c0/FIRST_REAL_KNOWLEDGE_APPROVAL_REPORT.md
reports/phase8c0/FIRST_REAL_KNOWLEDGE_CANDIDATE_REPORT.md
reports/phase8c0/FIRST_REAL_RAG_DEMO_REPORT.md
reports/phase8c0/FIRST_REAL_RAG_RETRIEVAL_TEST_REPORT.md
reports/phase8c0/FIRST_REAL_RAG_SEED_INGESTION_REPORT.md
reports/phase8c0/KNOWLEDGE_MIGRATION_SAFETY_REPORT.md
reports/phase8c0/PHASE8C0_FINAL_REPORT.md
reports/phase8c0/RAG_PROVENANCE_VALIDATION_REPORT.md
reports/rag_data_phase1/FIRST_PRODUCT_RAG_CANDIDATES.md
reports/rag_data_phase1/FIRST_REAL_PRODUCT_KNOWLEDGE_DATASET.json
reports/rag_data_phase1/FIRST_REAL_PRODUCT_KNOWLEDGE_DATASET_REPORT.md
reports/rag_data_phase1/PRODUCT_601_RECORD_AUDIT.md
reports/rag_data_phase1/PRODUCT_DATA_CLEANUP_EXECUTION_REPORT.md
reports/rag_data_phase1/PRODUCT_DATA_CLEANUP_PLAN.md
reports/rag_data_phase1/PRODUCT_DATA_COMPLETENESS_REPORT.md
reports/rag_data_phase1/PRODUCT_DATA_ORIGIN_REPORT.md
reports/rag_data_phase1/PRODUCT_DATA_QUALITY_VALIDATION.md
reports/rag_data_phase1/PRODUCT_DUPLICATE_ANALYSIS.md
reports/rag_data_phase1/PRODUCT_HUMAN_ACTION_TABLE.md
reports/rag_data_phase1/PRODUCT_PUBLIC_RAG_FIELD_POLICY.md
reports/rag_data_phase1/PRODUCT_SCHEMA_AUDIT.md
reports/rag_data_phase1/RAG_DATA_PHASE1_FINAL_REPORT.md
reports/rag_data_phase3/01_SYNTHETIC_DATASET_DESIGN.md
reports/rag_data_phase3/02_SYNTHETIC_PRODUCT_DATA_REPORT.md
reports/rag_data_phase3/03_SYNTHETIC_IMPORT_DRY_RUN_REPORT.md
reports/rag_data_phase3/04_SYNTHETIC_IMPORT_EXECUTION_REPORT.md
reports/rag_data_phase3/05_SYNTHETIC_KNOWLEDGE_CANDIDATE_REPORT.md
reports/rag_data_phase3/06_SYNTHETIC_INDEXING_REPORT.md
reports/rag_data_phase3/07_SYNTHETIC_RAG_TEST_SET.md
reports/rag_data_phase3/08_SYNTHETIC_RETRIEVAL_EVALUATION.md
reports/rag_data_phase3/09_SYNTHETIC_CITATION_VALIDATION.md
reports/rag_data_phase3/10_SYNTHETIC_SECURITY_SEPARATION_REPORT.md
reports/rag_data_phase3/11_RAG_DATA_PHASE3_FINAL_REPORT.md
reports/rag_data_phase3/RAG_SYNTHETIC_PRODUCT_DATASET.csv
reports/rag_data_phase3/RAG_SYNTHETIC_PRODUCT_DATASET.xlsx
reports/rag_web_demo/01_RAG_WEB_DEMO_IMPLEMENTATION.md
reports/rag_web_demo/02_RAG_WEB_DEMO_SECURITY_TEST.md
reports/rag_web_demo/03_RAG_WEB_DEMO_FUNCTIONAL_TEST.md
reports/rag_web_demo/04_RAG_WEB_DEMO_FINAL_REPORT.md
```

## Worktrees

```text
"C:/Users/hoang/Documents/ChatGPT/WEB \303\224 T\303\224 DJANGO" 8458ab7 [codex/demo-database-validation]
C:/Users/hoang/Documents/ChatGPT/ai-assistant-update             af309f1 [codex/ai-assistant-update]
```

## Recent history

```text
8458ab7 (HEAD -> codex/demo-database-validation, origin/codex/demo-database-validation, origin/HEAD) Merge remote-tracking branch 'origin/codex/demo-database-validation' into codex/demo-database-validation
eca707a (backup/phase6-pre-remote-merge) phase6: finalize portfolio production-demo release candidate
01f1503 phase5e: repair progress reconciliation evidence matching
3cc5b24 phase5e: add order conversion progress and audit UI
f05c4b4 phase5d: add canonical quotation lifecycle UI
7de1a79 phase5c: add RFQ draft line and submission UI
2f4d8d8 phase5b: connect foundation login and rfq read screen
fc244cb phase5a: add canonical frontend transport foundation
27002cb phase4d: add order progress audit command APIs
86e2a0f phase4c: add quotation and order conversion command APIs
b6a9763 phase4b: add master data and RFQ command APIs
d6fded5 phase4a: add canonical read API boundary
2d90dd0 phase3: complete canonical business workflow domain
41753f4 chore: stabilize project and define MVP business contract
2ebcb30 feat(ui): upgrade B2B design system, typography, hero section and fix UTF-8 encoding
13af7f6 refactor: remove legacy /backend, add /api/home endpoint in django_backend
df14dc5 feat(frontend): add Figma Make prototype
d1d4786 docs: record database mutation investigation and recovery
128ecb0 docs: record demo database validation evidence
a3214a8 test(data): validate local demo database and business workflows
```

