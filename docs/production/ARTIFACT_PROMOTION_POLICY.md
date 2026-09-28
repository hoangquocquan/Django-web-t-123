# Artifact promotion policy

Only signed immutable digests built by CI may be promoted. Staging and production use the same digest. Required gates are tests, migrations, dependency audit, secret scan, SAST, filesystem vulnerability scan and SBOM. Mutable tags, workstation builds, unreviewed workflows and runtime data are rejected. Promotion is `MANUAL_EXECUTION_REQUIRED` with two-person approval and retained provenance.
