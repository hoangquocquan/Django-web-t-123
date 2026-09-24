# Production Readiness Dependency Graph

```text
AI-06 Handover
  -> PROD-00 Baseline
    -> PROD-01 Business UI and UAT
      -> PROD-02 Production Infrastructure
        -> PROD-03 Security and Uploads
          -> PROD-04 AI Runtime
            -> PROD-05 Operations and Recovery
              -> PROD-06 Staging UAT
                -> PROD-07 Controlled Deployment Handover
```

No phase may consume an unvalidated output from a later phase.
