# Wave 3 Workflow Report

## Ownership Result

Django now owns workflow status transitions and approvals for transaction orders.

Implemented:

- `WorkflowApproval`
- `OrderStatusHistory`
- `WorkflowService`
- `/api/v1/workflows/`

## Status Flow

Allowed transitions:

- `new` -> `approved`, `cancelled`
- `approved` -> `processing`, `cancelled`
- `processing` -> `completed`, `cancelled`

Terminal states:

- `completed`
- `cancelled`

## Permission Integration

Workflow APIs require Wave 1 foundation bearer token and `workflows` permission.

## Safety

Invalid transitions raise validation errors and do not mutate the order.
