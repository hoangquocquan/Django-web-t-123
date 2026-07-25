# Quote File Lifecycle Strategy

## Current State

Legacy table: `quote_files`

Fields:

- `id`
- `quote_request_id`
- `file_name`
- `file_url`
- `file_type`
- `uploaded_at`

The database stores file metadata and path/URL. It does not guarantee that the physical file exists.

## Phase 6.1 Rule

Do not migrate physical files.

Do not rewrite file paths.

Do not move files into Django media storage.

## Future Upload Flow

Recommended future flow:

1. Receive upload.
2. Store file in temporary location.
3. Validate extension and MIME type.
4. Validate size limit.
5. Optional malware scan.
6. Create quote records inside database transaction.
7. Create file metadata.
8. Move file to permanent storage after database success.
9. Queue cleanup for temporary files.

## Storage Migration

Future storage options:

- local Django `MEDIA_ROOT`,
- S3-compatible object storage,
- CDN-backed storage,
- private document storage with signed URLs.

Storage decision must be separate from Phase 6.1.

## Cleanup Strategy

Cleanup should handle:

- temporary files older than retention window,
- metadata rows pointing to missing files,
- files without metadata rows,
- failed upload attempts,
- duplicate uploads.

## Orphan File Handling

Database orphan:

- `quote_files.quote_request_id` points to missing quote.
- Current data review found 0 orphan quote file rows.

Physical orphan:

- file exists on disk/storage but has no database row.
- Phase 6.1 does not scan physical storage.

## Recommendation

Preserve legacy file metadata as read-only for now.

Before upload migration, approve file validation, storage backend, cleanup job and rollback behavior.
