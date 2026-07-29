# Wave 2 Customer Report

## Ownership Result

Django now owns new customer writes through `apps.business_core`.

Implemented:

- `BusinessCustomer`
- `BusinessCustomerService`
- `/api/v1/business/customers/`
- `/api/v1/business/customers/<id>/`

## Legacy Compatibility

Legacy CRM models in `apps.crm` remain unmanaged and read-only. Existing CRM read endpoints remain available.

## Data Migration

Migration `business_core.0002_seed_business_core_from_legacy` copies legacy `customers` rows into `business_customers` using `legacy_customer_id`.

## Safety

Legacy customer tables are not updated or deleted. New customer operations write only to Django-owned tables.
