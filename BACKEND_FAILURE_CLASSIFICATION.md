# Backend failure classification

Initial reproduction on `integration/platform-current`:

- Command: `pytest -q`
- Result: **511 passed, 38 failed, 5 errors**
- Classification completed before production or test fixes.

Categories:

- **A** — Legacy immediate-indexing/governed-lifecycle assumption
- **B** — Missing local SQLite/config dependency
- **C** — Missing or retired legacy backend compatibility expectation
- **D** — Missing seed/fixture data
- **E** — Genuine integration regression
- **F** — Other test-infrastructure/contract drift

| Test | Category | Root cause | Fix target |
|---|---|---|---|
| `test_ai_document_intelligence.py::test_document_intelligence_ingests_txt_and_adds_metadata` | A | Upload ingestion now creates a draft; test expects chunks immediately | Governed knowledge test helper |
| `test_ai_enterprise_governance.py::test_knowledge_chat_blocks_dangerous_prompt_before_rag` | A | Caller lacks active pilot scope, so access gate returns 403 before prompt-governance assertion | Test pilot fixture |
| `test_ai_hardening_vector_search.py::test_reindex_keeps_old_index_when_embedding_fails` | A | Test reindexes an unapproved draft | Governed knowledge test helper |
| `test_ai_hardening_vector_search.py::test_reindex_is_idempotent_and_model_change_is_detected` | A | Test expects create-time indexing | Governed knowledge test helper |
| `test_ai_hardening_vector_search.py::test_vietnamese_and_english_retrieval_use_matching_provider` | A | Public drafts are not approved/indexed or public-released | Governed knowledge test helper |
| `test_ai_knowledge_assistant.py::test_document_service_creates_category_version_chunks_and_embeddings` | A | Test expects draft creation to embed immediately | Governed knowledge test helper |
| `test_ai_knowledge_assistant.py::test_document_create_and_list_api_for_admin` | A | Governed list excludes unapproved drafts | Test expectation plus lifecycle transition |
| `test_ai_knowledge_assistant.py::test_knowledge_search_returns_sources_and_confidence` | A | Search fixture is an unapproved draft | Governed knowledge test helper |
| `test_ai_knowledge_assistant.py::test_knowledge_search_api_returns_sources_and_confidence` | A | Search fixture is an unapproved draft and caller lacks pilot activation | Governed knowledge/pilot helper |
| `test_ai_knowledge_assistant.py::test_knowledge_chat_uses_context_sources_and_logs_answer` | A | Chat fixture is not approved/indexed | Governed knowledge/pilot helper |
| `test_ai_knowledge_assistant.py::test_knowledge_chat_api_returns_answer` | A | Chat fixture is not approved/indexed and caller lacks pilot activation | Governed knowledge/pilot helper |
| `test_ai_wave_1.py::test_rag_ingests_document_chunks_and_embeddings` | A | `ingest_text` now creates a draft | Governed knowledge test helper |
| `test_ai_wave_1.py::test_rag_semantic_search_returns_relevant_documents` | A | Search runs against unapproved draft | Governed knowledge test helper |
| `test_ai_wave_1.py::test_knowledge_search_api_returns_results` | A | API fixture is not approved/indexed and pilot-enabled | Governed knowledge/pilot helper |
| `test_business_simulation.py::test_business_simulation_creates_complete_fictional_flow` | A | Simulation creates knowledge but never performs approval/indexing lifecycle | Simulation fixture/runner lifecycle |
| `test_demo_data_generation.py::test_demo_knowledge_is_ai_search_compatible` | A | Demo knowledge seed remains draft/unindexed | Deterministic demo lifecycle |
| `test_ollama_real_inference.py::test_rag_generation_uses_ollama_and_logs_request` | A | Generation fixture has no governed searchable source | Governed knowledge/pilot helper |
| `test_ollama_real_inference.py::test_rag_generation_falls_back_when_ollama_is_down` | A | Fallback fixture has no governed searchable source | Governed knowledge/pilot helper |
| `test_sales_crm_ai.py::test_ai_sales_assistant_uses_rag_and_keeps_human_approval` | A | Sales AI fixture creates an unapproved/unindexed document | Governed knowledge helper |
| `test_phase12_2_performance.py::test_benchmark_helpers_can_run_in_isolation` | B | Helper opens a developer-local SQLite path instead of a generated DB | Temporary SQLite fixture |
| `test_phase12_3_monitoring.py::test_health_check_works` | B | Health check assumes `DATABASES["legacy"]` always exists | Optional legacy DB boundary/test settings |
| `test_phase14_1_django_ownership.py::test_legacy_newsletter_compatibility_remains_read_only` | B | Fixture copies ignored local legacy SQLite | Generated temporary legacy SQLite fixture |
| `test_phase14_1_django_ownership.py::test_no_unrelated_domain_ownership_changed` | B | Fixture copies ignored local legacy SQLite | Generated temporary legacy SQLite fixture |
| `test_wave1_django_foundation.py::test_legacy_auth_compatibility_remains_read_only` | B | Fixture copies ignored local legacy SQLite | Generated temporary legacy SQLite fixture |
| `test_wave2_business_core.py::test_legacy_product_and_customer_compatibility_remains_read_only` | B | Fixture copies ignored local legacy SQLite | Generated temporary legacy SQLite fixture |
| `test_wave3_transaction_domain.py::test_legacy_quote_compatibility_remains_read_only` | B | Fixture copies ignored local legacy SQLite | Generated temporary legacy SQLite fixture |
| `test_ai_legacy_cleanup.py::test_legacy_backend_no_longer_imports_ai_service` | C | Test opens removed `backend/app.py` and legacy localization module | Assert canonical Django boundary/archive state |
| `test_ai_legacy_cleanup.py::test_legacy_openapi_no_longer_contains_ai_chat` | C | Test imports removed legacy `backend/api` | Assert canonical Django routes/schema |
| `test_wave5_admin_migration.py::test_legacy_admin_compatibility_files_remain` | C | Test requires retired untracked legacy backend files | Assert canonical admin availability |
| `test_wave6_admin_ui.py::test_wave6_legacy_admin_compatibility_files_remain` | C | Test requires retired untracked legacy backend files | Assert canonical Django admin/UI boundary |
| `test_wave7_public_website.py::test_public_technology_page_renders` | C | Assertion expects retired English legacy copy | Assert current canonical page contract |
| `test_wave7_public_website.py::test_public_news_page_renders` | C | Assertion expects retired English legacy copy | Assert current canonical page contract |
| `test_wave7_public_website.py::test_wave7_legacy_public_files_remain` | C | Test requires retired `backend/app.py` and legacy frontend | Assert canonical Django/public frontend boundary |
| `test_wave1_django_foundation.py::test_foundation_migrations_seed_roles_permissions_and_legacy_users` | D | Test DB has no developer legacy rows to seed | Deterministic factory data/updated migration assertion |
| `test_wave2_business_core.py::test_wave2_migrations_seed_products_customers_and_inventory` | D | Test DB has no legacy product/customer rows | Deterministic fixtures |
| `test_wave2_business_core.py::test_inventory_service_adjusts_stock_transactionally` | D | Uses `BusinessProduct.objects.first()` without creating a product | Product fixture |
| `test_wave2_business_core.py::test_inventory_service_blocks_negative_stock` | D | Uses `BusinessProduct.objects.first()` without creating a product | Product fixture |
| `test_wave2_business_core.py::test_inventory_api_adjusts_stock` | D | Uses `BusinessProduct.objects.first()` without creating a product | Product fixture |
| `test_wave3_transaction_domain.py::test_wave3_migrations_seed_orders_and_transaction_history` | D | Test assumes local legacy quote/event seed rows | Deterministic order/history fixture |
| `test_prod03_security_upload_hardening.py::test_private_download_requires_auth_and_hides_storage_path` | E | Generic transition route shadows the specific `download/` route, yielding 405 | Production URL ordering plus regression assertion |
| `test_prod04_ai_runtime.py::test_rag_health_reports_empty_index_as_degraded` | F | Fake embedding provider omits required signature attributes | Test double contract |
| `test_prod04_ai_runtime.py::test_rag_health_reports_populated_index_as_ready` | F | Fake embedding provider omits required signature attributes | Test double plus governed indexed fixture |
| `test_phase12_1_security.py::test_dependency_audit_reports_unpinned_dependencies` | F | Dependency audit reads a retired/empty dependency source and misses Django | Audit input discovery/test fixture |

## Breakdown

| Category | Count |
|---|---:|
| A. Legacy immediate-indexing/governed lifecycle | 19 |
| B. Missing local SQLite/config dependency | 7 |
| C. Retired legacy backend compatibility | 7 |
| D. Missing seed/fixture data | 6 |
| E. Genuine regression | 1 |
| F. Other infrastructure/contract drift | 3 |
| **Total** | **43** |
