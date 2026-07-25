# Module Dependency Graph - mecprecision-vietnam

Phase: 1 - Migration Planning  
Rule: Planning only. No code, no Django models, no database migration.

## 1. Purpose

This document maps module dependencies before Django migration.

The goal is to prevent unsafe migration order, especially for modules that depend on shared tables, authentication, media, events, or cross-module database relationships.

## 2. Target Module Groups

Target Django architecture groups:

```text
config
apps
  core
  accounts
  catalog
    products
    categories
  crm
    customers
    contacts
  sales
    quotation
    orders
  content
    news
  ai
  dashboard
  common
```

## 3. High-Level Dependency Graph

```text
core
  -> common
  -> catalog.categories
  -> catalog.products
  -> crm.customers
  -> crm.contacts
  -> sales.quotation
  -> content.news
  -> ai
  -> dashboard
  -> accounts
  -> admin_cms
```

Recommended interpretation:

- `core` must exist first.
- Data modules should move before dashboard and AI.
- Authentication cutover should happen late.
- Admin CMS write workflows should happen after data modules and auth/permission strategy.

## 4. Module Dependency Table

| Module | Depends On | Reason |
|---|---|---|
| `core` | none | Health check, base settings, logging, response/error conventions. |
| `common.settings` | `core` | System settings are read by auth/security/email/captcha. |
| `common.events` | `core` | Event publishing is cross-cutting. |
| `common.queue` | `common.events`, `common.notifications`, `common.email` | Events can enqueue jobs; jobs can send emails/create notifications. |
| `common.notifications` | `core` | Notifications are used by event/queue/admin dashboard. |
| `common.pages` | `core`, `media` optional | Dynamic pages may reference media URLs. |
| `common.menus` | `core`, `common.pages` optional | Menu items may link to dynamic pages. |
| `common.banners` | `core`, `media` optional | Banners may include uploaded images. |
| `catalog.categories` | `core` | Product categories are a product dependency. |
| `catalog.materials` | `core` | Product and quote items can reference materials. |
| `catalog.machines` | `core` | Capabilities can reference machines. |
| `catalog.processes` | `core` | Product process workflow references manufacturing processes. |
| `catalog.products` | `catalog.categories`, `catalog.materials`, `catalog.processes`, `media` optional | Products require category and may reference materials/processes/images/files. |
| `catalog.capabilities` | `catalog.machines` | Capabilities can be linked to machines. |
| `crm.customers` | `core` | Customers are standalone but used by quotes and notes. |
| `crm.customer_notes` | `crm.customers`, `accounts` optional | Notes belong to customers; created_by may relate to admin later. |
| `crm.contacts` | `core`, `common.events`, `common.queue`, `common.notifications` | Contact submission can publish event and create notification/email jobs. |
| `sales.quotation` | `crm.customers`, `catalog.products`, `catalog.materials`, `common.events`, `media` optional | Quote request belongs to customer; quote items can reference product/material; files use media. |
| `content.news_categories` | `core` | News category master. |
| `content.tags` | `core` | Tags support news filtering/search. |
| `content.news` | `content.news_categories`, `content.tags`, `media` optional | News belongs to category and may use tags/images. |
| `media` | `core`, `accounts` optional | Media is cross-cutting and may require admin permissions. |
| `ai.chatbot` | `core`, `catalog.products`, `content.news` | Business context uses products/news. |
| `ai.translation` | `core` | Translation cache/history only requires AI tables. |
| `ai.product_content` | `catalog.products`, `catalog.categories` | Product SEO generation needs product/category context. |
| `ai.contacts_summary` | `crm.contacts` | Summarizes contact requests. |
| `ai.quote_analysis` | `sales.quotation`, `crm.customers`, `catalog.products`, `catalog.materials` | Quote analysis needs quote/customer/item/file data. |
| `ai.smart_search` | `catalog.products`, `content.news` | Searches across products and news. |
| `ai.dashboard_insights` | `dashboard`, `crm.contacts`, `sales.quotation`, `common.queue` | Insight uses dashboard counts and operational data. |
| `dashboard` | `catalog.products`, `content.news`, `crm.customers`, `crm.contacts`, `sales.quotation`, `accounts.sessions`, `page_visits` | Dashboard aggregates many modules. |
| `accounts.users` | `core`, `common.settings`, `media` optional | Users need settings/password policy and optional avatar media. |
| `accounts.sessions` | `accounts.users` | Sessions belong to admin users. |
| `accounts.password_reset` | `accounts.users`, `common.email`, `common.settings` | Reset token uses user and settings/email outbox. |
| `accounts.permissions` | `accounts.users` | Role/group/permission model depends on user accounts. |
| `admin_cms` | `accounts`, all migrated modules | Admin UI must enforce auth/authorization and use module services. |
| `developer_tools` | `accounts`, `common.queue`, `common.events`, `common.settings`, `database`, `cache` | Sensitive operations require strict permissions and audit. |

## 5. Database Table Dependency Graph

### 5.1 Product/Catalog

```text
product_categories
  -> products
      -> product_images
      -> product_specs
      -> product_materials -> materials
      -> product_processes -> manufacturing_processes

machines
  -> capability_machines -> capabilities
```

Migration order:

1. `product_categories`
2. `materials`
3. `manufacturing_processes`
4. `machines`
5. `products`
6. `product_images`
7. `product_specs`
8. `product_materials`
9. `product_processes`
10. `capabilities`
11. `capability_machines`

### 5.2 CRM and Sales

```text
customers
  -> customer_notes
  -> quote_requests
      -> quote_request_items
          -> products
          -> materials
      -> quote_files

contact_requests
  -> enterprise_events
      -> job_queue
      -> notifications
```

Migration order:

1. `customers`
2. `customer_notes`
3. `contact_requests`
4. `quote_requests`
5. `quote_request_items`
6. `quote_files`
7. event/job/notification side effects

### 5.3 Content

```text
news_categories
  -> news
      -> news_tags -> tags
```

Migration order:

1. `news_categories`
2. `tags`
3. `news`
4. `news_tags`

### 5.4 Accounts/Auth

```text
admin_users
  -> admin_sessions
  -> password_reset_tokens
  -> admin_2fa_challenges
  -> admin_activity_logs

login_attempts
auth_email_outbox
system_settings
```

Migration order:

1. `system_settings`
2. `admin_users`
3. `login_attempts`
4. `admin_sessions`
5. `password_reset_tokens`
6. `admin_2fa_challenges`
7. `auth_email_outbox`
8. `admin_activity_logs`

Important: actual auth cutover should be later than read-only model mapping.

### 5.5 CMS Common

```text
cms_pages
cms_menu_items -> cms_menu_items.parent_id
cms_banners
page_visits
newsletter_subscribers
```

Migration order:

1. `cms_pages`
2. `cms_menu_items`
3. `cms_banners`
4. `page_visits`
5. `newsletter_subscribers`

### 5.6 System/AI

```text
enterprise_events
  -> job_queue
  -> notifications

ai_conversations
ai_translation_cache
```

Migration order:

1. `enterprise_events`
2. `job_queue`
3. `notifications`
4. `ai_conversations`
5. `ai_translation_cache`

## 6. App Dependency Graph

```text
apps.core
  -> apps.common
      -> apps.catalog
      -> apps.crm
      -> apps.content
      -> apps.sales
      -> apps.ai
      -> apps.dashboard
      -> apps.accounts
```

More specific:

```text
apps.catalog.categories
  -> apps.catalog.products

apps.catalog.materials
  -> apps.catalog.products
  -> apps.sales.quotation

apps.crm.customers
  -> apps.sales.quotation

apps.crm.contacts
  -> apps.ai.contacts_summary
  -> apps.dashboard

apps.content.news
  -> apps.ai.smart_search
  -> apps.dashboard

apps.sales.quotation
  -> apps.ai.quote_analysis
  -> apps.dashboard

apps.accounts
  -> admin_cms
  -> developer_tools

apps.common.events
  -> apps.common.queue
  -> apps.common.notifications
```

## 7. Migration Order Based on Dependencies

### Stage A - Independent Foundation

1. `core`
2. `common.settings`
3. `common.health`
4. `common.error_format`

### Stage B - Reference Data

1. `catalog.categories`
2. `catalog.materials`
3. `catalog.machines`
4. `catalog.processes`
5. `content.news_categories`
6. `content.tags`

### Stage C - Primary Business Data

1. `catalog.products`
2. `catalog.capabilities`
3. `crm.customers`
4. `crm.contacts`
5. `content.news`

### Stage D - Transactional Data

1. `sales.quotation`
2. `newsletter`
3. `cms.pages`
4. `cms.menus`
5. `cms.banners`

### Stage E - Cross-Cutting Systems

1. `media`
2. `common.events`
3. `common.queue`
4. `common.notifications`
5. `ai`
6. `dashboard`

### Stage F - Admin/Security

1. `accounts` read-only mapping.
2. auth compatibility design.
3. permissions mapping.
4. admin CMS read workflows.
5. admin CMS write workflows.

## 8. Circular/Hidden Dependencies

Potential hidden dependencies:

| Hidden Dependency | Why It Matters |
|---|---|
| Products use media paths but media is a separate feature. | Keep fields as text URLs initially; migrate storage later. |
| News uses image/thumbnail URLs but no formal media FK. | Same media strategy as products. |
| Quotes create events/jobs/notifications. | Preserve side effects when moving write APIs. |
| Contacts create events/jobs/notifications. | Write migration requires event parity. |
| AI reads products/news/contacts/quotes. | Migrate AI after read models exist. |
| Dashboard counts sessions and visits. | Auth/session and analytics mappings affect dashboard accuracy. |
| Developer tools can run migrations/backups/workers. | Must wait for permission/audit hardening. |

## 9. Modules That Must Not Migrate First

Do not migrate these first:

| Module | Reason |
|---|---|
| `accounts/auth` | High risk; affects all admin security. |
| `admin_cms` writes | Depends on auth, CSRF, permissions, services, media. |
| `developer_tools` | Sensitive operations: migrations/backups/workers/logs. |
| `media` writes | Upload path/security concerns and cross-module references. |
| `sales.quotation` writes | Multi-table transaction and side effects. |

## 10. Safe First Modules

Safe first candidates:

| Module | Why Safe |
|---|---|
| `core` | No business data. |
| `catalog.categories` | Small reference table. |
| `catalog.materials` | Small reference table. |
| `catalog.products` read-only | High value, can compare with legacy API. |
| `content.news` read-only | Mostly independent. |
| `crm.customers` read-only | Needed by quotes but safe to read. |

## 11. Dependency Review Checklist

Before migrating a module:

1. List all database tables used by the module.
2. List all services called by the module.
3. List all repositories used by the module.
4. List all write side effects.
5. List all cache keys touched.
6. List all events/jobs/notifications triggered.
7. List all admin permissions required.
8. List all file upload/media paths used.
9. Confirm rollback route.
10. Confirm legacy route remains available.

## 12. Conclusion

The dependency graph supports a gradual migration that starts with read-only reference data and public APIs. Authentication, admin writes, media writes, and developer tools should migrate late because they are high-risk and cross-cutting.

Next planning reference:

- `DATABASE_MIGRATION_STRATEGY.md`
- `API_MIGRATION_PLAN.md`
