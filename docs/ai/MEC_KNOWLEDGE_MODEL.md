# MEC Knowledge Model

## Purpose

The MEC Knowledge Assistant organizes internal documents so AI can answer with
source references instead of guessing.

## Models

`DocumentCategory`

Groups documents by business topic such as product, quality, customer, or
manufacturing process.

`KnowledgeDocument`

Stores searchable document metadata and extracted text:

- title
- description
- file
- category
- source type
- version
- created by
- permission level

`DocumentPermission`

Adds optional document-level access rules by user email or role name.

`DocumentVersion`

Stores immutable content snapshots for audit and rollback.

`KnowledgeAssistantLog`

Stores safe AI response audit data:

- question
- retrieved sources
- answer
- confidence
- warning
- user email

## Permission Levels

- `public`: visible to authenticated users when endpoint allows it.
- `internal`: visible to internal authenticated users.
- `restricted`: requires admin or explicit document permission.

