# Full-history secret scan procedure

CI checks out full history and runs Gitleaks. For an operator rerun, use a clean clone and the repository's pinned CI action/tool configuration; scan all refs without exporting secret contents. Report only finding type, path, commit and remediation owner. A confirmed credential is a release blocker: rotate/revoke it first, assess exposure, then plan any history rewrite as a separate coordinated operation. This task never rewrites history.
