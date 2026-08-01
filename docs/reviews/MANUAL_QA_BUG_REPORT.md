# Manual QA Bug Report

Project: MEC Precision Business Platform

Date: 2026-08-01

Environment: Local Django website at `http://127.0.0.1:8000/`

## Summary

Manual QA found that the main Django business platform can run, login works for demo users, dashboard data is visible, AI Sales and AI Document Intelligence can return results, and local n8n automation simulations are available.

The main blockers are in the browser workflow: several business actions exist in backend/data layers but are not yet exposed as usable forms/buttons in the web UI. This means some end-to-end user scenarios cannot be completed by a normal user from the browser.

## Bugs

### BUG-001: Non-CEO Demo Roles Cannot Access Business UI Pages

Severity: High

Status: Open

Affected area: Authentication, Authorization, Business UI

Observed:

- CEO account can login and open the business dashboard.
- Sales Manager, Sales Staff, and Technical Engineer accounts can login successfully.
- Those non-CEO roles do not have `dashboard:read`.
- The Business UI checks `dashboard:read` globally before allowing access to business pages.

Impact:

Sales Manager, Sales Staff, and Technical Engineer user journeys are blocked even though those roles have domain-specific permissions such as sales, CRM, or knowledge permissions.

Evidence:

- Login checks confirmed through Django authentication.
- Role permissions inspected during manual QA:
  - `ceo@demo.mecprecision.local`: dashboard access available
  - `sales.manager@demo.mecprecision.local`: dashboard access missing
  - `sales.staff1@demo.mecprecision.local`: dashboard access missing
  - `engineer1@demo.mecprecision.local`: dashboard access missing

Expected:

Business pages should allow access based on the relevant module permission. For example:

- Sales pages should use sales permissions.
- CRM pages should use CRM permissions.
- Knowledge/document pages should use knowledge permissions.

Suggested fix:

Adjust the Business UI permission guard so each page checks the permission needed for that page instead of requiring `dashboard:read` for every page.

---

### BUG-002: Sales Workflow Cannot Be Completed From Browser UI

Severity: High

Status: Open

Affected area: Business UI, Sales CRM

Observed:

The backend/data layer supports creating sales workflow records, but the browser UI does not provide enough forms/actions for the full sales workflow.

Missing or incomplete browser actions:

- Create lead from the sales page
- Move lead pipeline status
- Create opportunity from lead/customer
- Create quotation from UI
- Approve quotation from UI
- Schedule follow-up from UI

Impact:

The Sales Manager and Sales Staff UAT scenarios cannot be completed end-to-end through the website. QA had to use Django ORM/service-level checks to confirm the backend can create the workflow data.

Evidence:

- `/business/leads/` shows a kanban/list style view.
- `/business/quotations/` shows quotation records.
- Data creation through ORM succeeded:
  - QA customer created
  - QA lead created
  - QA opportunity created
  - QA quotation created and approved

Expected:

A business user should be able to perform the full sales workflow in the browser without using backend scripts.

Suggested fix:

Add UI forms/buttons for lead creation, lead status update, opportunity creation, quotation creation, quotation approval, and follow-up scheduling.

---

### BUG-003: CRM Customer Detail Has No Browser Forms For Interaction, Note, Task

Severity: Medium

Status: Open

Affected area: CRM UI

Observed:

The customer detail page can display CRM-related information, but it does not provide browser forms to add:

- Customer interaction
- Internal note
- Follow-up task

Impact:

The CRM workflow is readable but not fully operable from the UI.

Evidence:

Service-level workflow data creation succeeded:

- Interaction ID: 517
- Note ID: 514
- Task ID: 514
- Timeline event ID: 517

Expected:

Customer detail should allow authorized CRM users to add interaction history, notes, and tasks directly from the browser.

Suggested fix:

Add CRM action forms to customer detail pages and connect them to Django endpoints/services.

---

### BUG-004: AI Sales Result Is Rendered As Raw Python Dictionary

Severity: Medium

Status: Open

Affected area: AI Sales UI

Observed:

AI Sales returns useful data, but the UI displays the result as a raw Python dictionary string.

Impact:

The feature works technically, but the result is hard for business users to read.

Evidence:

Screenshot:

`docs/reviews/manual_qa_screenshots/02_ai_sales_result.png`

Expected:

AI result should be shown as structured UI sections, for example:

- Lead score
- Grade
- Recommendation
- Sources
- Confidence
- Human approval required

Suggested fix:

Render AI response fields into cards/tables instead of printing the raw dictionary.

---

### BUG-005: AI Document Intelligence Result Is Hard To Read

Severity: Low

Status: Open

Affected area: AI Document Intelligence UI

Observed:

Document upload and search work, but the result is displayed as raw data. Some Vietnamese output is also missing accents, for example `Tim thay tai lieu lien quan`.

Impact:

The feature is usable for technical testing but not polished for business users.

Evidence:

Screenshot:

`docs/reviews/manual_qa_screenshots/03_document_intelligence_upload.png`

Expected:

Document AI result should display clean sections:

- Classification
- Confidence
- Extracted text preview
- Approval status
- Source file
- Human review status

Suggested fix:

Improve frontend formatting and language text for AI document results.

## Notes

No production deployment was performed.

No external AI API was used.

No architecture refactor was performed.

