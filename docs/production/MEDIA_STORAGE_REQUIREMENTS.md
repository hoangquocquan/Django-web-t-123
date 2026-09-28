# Durable media storage requirements

Production media requires a durable mounted volume or object-backed Django storage, encryption, recoverability/versioning, restricted identity, lifecycle policy, monitoring and tested backup. `MEDIA_STORAGE_DURABLE=true` and `MEDIA_BACKUP_ENABLED=true` are attestations, not proof; platform evidence is `MANUAL_EXECUTION_REQUIRED`. Ephemeral container filesystems are prohibited.
