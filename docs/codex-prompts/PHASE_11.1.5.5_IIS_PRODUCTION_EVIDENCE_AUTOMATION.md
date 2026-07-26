# TASK: Phase 11.1.5.5 - IIS Production Evidence Automation


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.5_IIS_PRODUCTION_EVIDENCE_AUTOMATION.md



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
Evidence Approval Collection


Phase 11.1.5.3
Evidence Package Structure


Phase 11.1.5.4
Real Production Evidence Validation Framework



Current environment:


Windows Server + IIS



Current blocker:


Real IIS production traffic data has not been imported.



====================================================
OBJECTIVE
====================================================


Build IIS production evidence automation.



Goal:


Collect IIS access logs.


Convert IIS logs into standardized evidence CSV.


Feed result into Phase 11.1.5.4 validation process.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- modify IIS configuration

- restart IIS

- change routing

- disable Legacy API

- modify production traffic



ONLY:


- read IIS logs

- export evidence

- validate traffic



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/production_evidence/


docs/migration/FINAL_SHUTDOWN_EVIDENCE_CHECKLIST.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_REPORT.md



====================================================
TASK 1
====================================================


Create IIS Evidence Collector.



Create:


scripts/windows/export_iis_api_evidence.ps1



Requirements:


Input:


Default IIS location:


C:\inetpub\logs\LogFiles



Support:


W3C IIS logs



Extract:


date

time

client IP

URI

HTTP status

User agent



Filter:


Legacy API:


/api/*



Django API:


/api/v1/*



Output:


docs/migration/production_evidence/input/iis_api_evidence.csv



CSV format:


timestamp

source

client

endpoint

status_code

user_agent



====================================================
TASK 2
====================================================


Create IIS Site Detector.



Create:


scripts/windows/detect_iis_site.ps1



Requirements:


Run:


Get-Website



Output:


Website name

Site ID

Physical path

Log location



Purpose:


Identify correct W3SVC log folder.



====================================================
TASK 3
====================================================


Create IIS Evidence Validation Script.



Create:


scripts/windows/validate_iis_api_evidence.ps1



Validate:


File exists


CSV readable


Legacy endpoints detected


Django endpoints detected



Output:


IIS_EVIDENCE_READY


or


IIS_EVIDENCE_INCOMPLETE



====================================================
TASK 4
====================================================


Create Documentation.



Create:


docs/migration/IIS_PRODUCTION_EVIDENCE_GUIDE.md



Include:


IIS log location


How to enable logging


How to export logs


How to run collector


How to verify CSV


How to import into Phase 11.1.5.4



====================================================
TASK 5
====================================================


Integrate with Phase 11.1.5.4.



Update documentation only.


Do not modify existing validator logic.


Document:


IIS CSV input format


Expected output


Validation workflow



====================================================
TASK 6
====================================================


Create Tests.



Create:


tests/test_phase11_1_5_5_iis_evidence.ps1



Test:


- missing IIS logs

- empty log folder

- valid IIS log parsing

- legacy API detection

- django API detection



====================================================
TASK 7
====================================================


Testing.



Run:


powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1


powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1


powershell -ExecutionPolicy Bypass -File scripts\windows\validate_iis_api_evidence.ps1



Run:


python scripts\phase11_1_5_4_production_evidence_loader.py



Expected:



Without production IIS logs:


IIS_EVIDENCE_INCOMPLETE



With valid IIS logs:


IIS_EVIDENCE_READY



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5.5_REVIEW_SUMMARY.md


PHASE_11.1.5.5_CHANGESET.patch



Include:


IIS detection result

Log collection result

CSV output

Validation result

Testing result



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5.5-iis-production-evidence



Commit:


git add .


git commit -m "feat: add IIS production evidence automation"



Create tag:


phase-11.1.5.5-iis-evidence-ready



====================================================
FINAL OUTPUT
====================================================


Return:


1. Branch

2. Commit hash

3. IIS site detected

4. Log location

5. CSV output location

6. Evidence status

7. Testing result

8. Review package location

9. Git tag



FINAL STATUS:


WAITING_FOR_ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.1.6.