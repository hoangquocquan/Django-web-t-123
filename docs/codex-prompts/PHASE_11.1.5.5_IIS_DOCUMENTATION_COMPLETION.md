# TASK: Phase 11.1.5.5 Documentation Completion - IIS Production Evidence Deployment Guide


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.5_IIS_DOCUMENTATION_COMPLETION.md



====================================================
CURRENT STATUS
====================================================


Completed:


Phase 11.1.1
Django API Replacement


Phase 11.1.2
Legacy API Traffic Verification


Phase 11.1.3
Legacy API Decommission Gate


Phase 11.1.4
Production Evidence Framework


Phase 11.1.5
Shutdown Readiness Framework


Phase 11.1.5.1
Evidence Completion


Phase 11.1.5.2
Evidence Collection


Phase 11.1.5.3
Production Evidence Package


Phase 11.1.5.4
Real Production Data Validation Framework


Phase 11.1.5.5
IIS Production Evidence Automation



====================================================
OBJECTIVE
====================================================


Complete Phase 11.1.5.5 documentation.


Create operational deployment guide for running
IIS evidence collection on real Windows Server IIS.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- create new phase

- modify IIS configuration

- restart IIS

- change routing

- disable Legacy API

- modify production traffic



ONLY:


- create documentation

- document deployment procedure

- document evidence collection workflow



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/reviews/PHASE_11.1.5.5_REVIEW_SUMMARY.md


docs/migration/production_evidence/


docs/migration/FINAL_SHUTDOWN_EVIDENCE_CHECKLIST.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md



====================================================
TASK 1
====================================================


Create IIS Production Deployment Guide.



Create:


docs/migration/IIS_PRODUCTION_EVIDENCE_DEPLOYMENT_GUIDE.md



Include:



1.

Purpose


Explain:

Phase 11.1.5.5 IIS evidence collection purpose.



2.

Requirements


Environment:


Windows Server

IIS

Administrator PowerShell



3.

IIS Site Detection



Document:


Get-Website


How to identify:

Website name

Site ID

Physical path

W3SVC log folder



4.

IIS Logging Verification



Document:


IIS Manager

Logging settings

Required W3C fields:



date

time

c-ip

cs-uri-stem

sc-status

cs(User-Agent)



5.

Script Deployment



Document:



scripts/windows/


Files:


detect_iis_site.ps1


export_iis_api_evidence.ps1


validate_iis_api_evidence.ps1



6.

Evidence Export Workflow



Document:



IIS Logs


↓

PowerShell Collector


↓

iis_api_evidence.csv


↓

Phase 11.1.5.4 Loader



7.

CSV Format



Document:


timestamp

source

client

endpoint

status_code

user_agent



8.

Validation Procedure



Document commands:


detect_iis_site.ps1


export_iis_api_evidence.ps1


validate_iis_api_evidence.ps1



9.

Troubleshooting



Include:


No IIS logs found


Wrong W3SVC folder


Empty CSV


No /api traffic


API hosted outside IIS



10.

Security



Include:


No sensitive data export

Mask tokens

Protect customer data

Read-only evidence collection



====================================================
TASK 2
====================================================


Update Phase Review Documentation.



Update:


docs/reviews/PHASE_11.1.5.5_REVIEW_SUMMARY.md



Add section:


Documentation Completion


Include:


IIS deployment guide created


Operational workflow documented


Production execution ready



====================================================
TASK 3
====================================================


Testing.


Verify:


Documentation exists


Links are valid


Scripts referenced exist



Run:


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


PASS



====================================================
TASK 4
====================================================


Git Requirements.



Create branch:


migration/phase-11.1.5.5-iis-documentation-completion



Commit:


git add .


git commit -m "docs: add IIS production evidence deployment guide"



Create tag:


phase-11.1.5.5-iis-documentation-complete



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Commit hash


3.

Documentation location


4.

Testing result


5.

Git tag


6.

Phase readiness status



Final status:


READY FOR PHASE 11.1.6 REVIEW


STOP.

DO NOT START PHASE 11.1.6.