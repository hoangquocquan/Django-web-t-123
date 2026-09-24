# Workstream Dependency Graph

```mermaid
flowchart TD
    Foundation["Completed Foundation: Django + Admin + Website + Ollama + RAG"]
    A["A: Django Full Frontend Ownership"]
    B["B: Sales Business Application"]
    C["C: CRM System"]
    D["D: AI Sales Assistant"]
    E["E: AI Document Intelligence"]
    F["F: n8n Automation Platform"]
    G["G: AI Software Factory V2"]
    Complete["Platform Completion Gate"]

    Foundation --> A
    A --> B
    B --> C
    C --> D
    Foundation --> E
    D --> F
    E --> F
    F --> G
    G --> Complete
```

## Dependency Notes

Workstream A depends on completed Django website and admin UI.

Workstream B depends on stable Django UI/API ownership.

Workstream C depends on customer, order, product, and sales integration points.

Workstream D depends on Sales, CRM, and Knowledge Assistant data.

Workstream E depends on the existing Knowledge Assistant and document model.

Workstream F depends on stable Django APIs and approved AI behaviors.

Workstream G depends on mature project workflows and review evidence.

