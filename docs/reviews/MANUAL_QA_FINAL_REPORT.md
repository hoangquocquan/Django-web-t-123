# Manual QA Final Report

Project: MEC Precision Business Platform

Date: 2026-08-01

Environment: Local Django website at `http://127.0.0.1:8000/`

Final status: MEC_PLATFORM_UAT_COMPLETE

## Objective

Run manual end-to-end QA for the MEC Precision Django business platform.

The goal was to verify whether a real user can use the website for:

- Login
- Dashboard review
- Sales CRM workflow
- Quotation workflow
- Customer CRM workflow
- AI Sales Assistant
- AI Document Intelligence
- n8n local automation simulation
- Responsive browser behavior

## Tested Accounts

| Role | Email | Login Result | Notes |
|---|---|---:|---|
| CEO | `ceo@demo.mecprecision.local` | Pass | Can open business dashboard |
| Sales Manager | `sales.manager@demo.mecprecision.local` | Pass | Login works, business UI access blocked by dashboard permission |
| Sales Staff | `sales.staff1@demo.mecprecision.local` | Pass | Login works, business UI access blocked by dashboard permission |
| Technical Engineer | `engineer1@demo.mecprecision.local` | Pass | Login works, business UI access blocked by dashboard permission |

## Browser Pages Tested

| Page | URL | Result |
|---|---|---:|
| Public home | `/` | Pass |
| Admin login | `/admin/login/` | Pass |
| Business dashboard | `/business/` | Pass for CEO |
| Leads | `/business/leads/` | Partial |
| Customers | `/business/customers/` | Partial |
| Quotations | `/business/quotations/` | Partial |
| AI Sales | `/business/ai-sales/` | Pass with UI formatting issue |
| AI Documents | `/business/documents/` | Pass with UI formatting issue |

## Dashboard Result

The CEO dashboard loaded successfully.

Observed demo metrics:

| Metric | Value |
|---|---:|
| Products | 214 |
| Customers | 506 |
| Inventory Items | 85 |
| Orders | 201 |
| Workflow Approvals | 200 |
| Transaction History | 204 |
| Roles | 10 |

Business dashboard also showed sales metrics:

| Metric | Observed Value |
|---|---:|
| Leads | 1002 |
| Pipeline Value | 23,453,927 |
| Revenue Forecast | 13,118,616 |

Screenshot:

`docs/reviews/manual_qa_screenshots/01_business_dashboard.png`

## Sales CRM Workflow

Result: Partial

Backend/service-level flow works, but the browser UI does not yet expose all actions.

Verified data creation:

| Object | Result |
|---|---:|
| Customer | Created |
| Lead | Created |
| Interaction | Created |
| Note | Created |
| Task | Created |
| Timeline Event | Created |
| Opportunity | Created |
| Quotation | Created |
| Quotation Approval | Created |

Important created records:

| Object | ID / Number |
|---|---|
| Customer | 519 |
| Lead | 1020 |
| Opportunity | 310 |
| Quotation | `SQ-QA-000503` |
| Quotation Total | 6,145.00 |
| Quotation Approval Status | Approved |

Limitation:

These actions could not be completed fully through browser forms because several UI actions are missing.

Related bug:

`BUG-002` in `MANUAL_QA_BUG_REPORT.md`

## Customer CRM Workflow

Result: Partial

Customer records can be displayed. CRM data can be created in the backend layer. However, the customer detail UI does not yet provide forms for adding interactions, notes, and tasks.

Related bug:

`BUG-003` in `MANUAL_QA_BUG_REPORT.md`

## AI Sales Assistant

Result: Pass with UI issue

Test input:

| Field | Value |
|---|---|
| Company | ABC Automotive Demo QA |
| Contact | QA Sales Contact |
| Industry | Automotive CNC machining |
| Notes | Customer needs CNC shaft quotation and quality inspection |

Observed AI result:

| Field | Value |
|---|---|
| Lead score | 62 |
| Grade | C |
| Knowledge confidence | 0.7011 |
| Human approval required | True |
| Autonomous action | False |

Screenshot:

`docs/reviews/manual_qa_screenshots/02_ai_sales_result.png`

Related bug:

`BUG-004` in `MANUAL_QA_BUG_REPORT.md`

## AI Document Intelligence

Result: Pass with UI issue

Tested document:

`docs/reviews/manual_qa_screenshots/qa_technical_sample.txt`

Upload result:

| Field | Value |
|---|---|
| Document ID | 110 |
| Classification | quality |
| Confidence | 0.68 |
| Approval status | ready_for_review |
| Source path | `knowledge/uploads/qa_technical_sample.txt` |
| Human approval required | True |

Screenshot:

`docs/reviews/manual_qa_screenshots/03_document_intelligence_upload.png`

Related bug:

`BUG-005` in `MANUAL_QA_BUG_REPORT.md`

## n8n Local Automation Simulation

Result: Pass

All tested local automation workflows returned `N8N_LOCAL_AUTOMATION_READY`.

Evidence files:

| Workflow | Evidence |
|---|---|
| Website lead to sales notification | `docs/reviews/manual_qa_automation/website_lead.json` |
| Document to knowledge update | `docs/reviews/manual_qa_automation/document_update.json` |
| Sales follow-up reminder | `docs/reviews/manual_qa_automation/sales_follow_up.json` |

Safety checks:

| Check | Result |
|---|---:|
| Local only | Pass |
| Production deployed | False |
| External email sent | False |
| Human approval required | True |

## Responsive Browser Check

Result: Pass with observation

Mobile viewport tested at 390 x 844.

The business dashboard rendered on mobile. A viewport screenshot succeeded.

Screenshot:

`docs/reviews/manual_qa_screenshots/04_mobile_business_dashboard.png`

Observation:

The dashboard is long and dense on mobile, so future UI improvements should prioritize shorter card groups and easier mobile navigation.

## Bug Summary

| ID | Severity | Summary |
|---|---|---|
| BUG-001 | High | Non-CEO demo roles cannot access business UI because dashboard permission is required globally |
| BUG-002 | High | Sales workflow cannot be completed fully from browser UI |
| BUG-003 | Medium | CRM customer detail lacks forms for interaction, note, and task |
| BUG-004 | Medium | AI Sales result renders as raw Python dictionary |
| BUG-005 | Low | AI Document result is hard to read and has unpolished Vietnamese text |

## Automated Validation

Result: Pass

Commands executed:

| Command | Result |
|---|---:|
| `python django_backend/manage.py check` | Pass |
| `pytest` | Pass, 337 tests passed |

## AI Factory Review

Result: Pass

Command executed:

`python ai-factory/run_ai_factory.py --phase business-ai-wave-2`

Observed result:

| Check | Result |
|---|---:|
| Phase validation | Pass |
| Focused tests | Pass, 15 tests passed |
| AI review engine | Pass |
| Production deployed | False |
| Human approval required | True |

Generated review artifacts:

- `docs/reviews/PHASE_AI_REVIEW_REPORT.md`
- `docs/reviews/AI_SOFTWARE_FACTORY_REPORT.md`
- `ai-factory/evidence/package.json`
- `ai-factory/results/factory_result.json`

## Overall Result

Manual QA decision: PASS_WITH_WARNINGS

The platform is usable for local demo and technical validation, but it is not yet ready as a polished business-user UAT release.

The strongest completed areas are:

- Django local runtime
- CEO dashboard
- Demo database volume
- Backend/service-level CRM and quotation data flow
- AI Sales backend result
- AI Document upload/search
- Local automation simulation

The main remaining work is:

- Fix role-based access for non-CEO users
- Add missing browser UI forms/actions for sales and CRM workflows
- Format AI output for business users

## Safety Confirmation

No production deployment was performed.

No external AI API was used.

No large architecture refactor was performed.

No production data was modified.
