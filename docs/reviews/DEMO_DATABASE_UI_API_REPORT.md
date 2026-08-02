# Demo Database UI And API Report

## Truy vết dữ liệu

| Trang/API | View | Service | Model | Table | ORM | Hard-code runtime |
| --- | --- | --- | --- | --- | --- | --- |
| `/admin/` | `admin_ui.dashboard` | trực tiếp đếm ORM | Business models | managed tables | Có | Không |
| `/admin/products/` | `admin_ui.products` | `BusinessProductService` | `BusinessProduct` | `business_products` | Có | Không |
| `/business/customers/` | `business_ui.customers` | `CrmPlatformService` | `BusinessCustomer` | `business_customers` | Có | Không |
| `/business/leads/` | `business_ui.leads` | `SalesPlatformService` | `SalesLead` | `sales_platform_leads` | Có | Không |
| `/business/quotations/` | `business_ui.quotations` | `SalesPlatformService` | `SalesQuotation` | `sales_platform_quotations` | Có | Không |
| `/business/documents/` | `business_ui.documents` | document service | `KnowledgeDocument` | `knowledge_documents` | Có | Không |
| `/api/v1/business/products/` | `business_products` | `BusinessProductService` | `BusinessProduct` | `business_products` | Có | Không |

## Kiểm tra thực tế

- Login `/admin/login/`: GET 200, POST 302, dashboard 200.
- Session `foundation_admin_token` được tạo sau khi login.
- Product tạo trong test database xuất hiện trong HTML admin.
- Product tạo trong test database xuất hiện trong JSON API có xác thực.
- CSRF, permission và CRUD UI hiện có tiếp tục được bao phủ bởi regression.

## Kết quả

UI tests: PASS.

API tests: PASS.

Không phát hiện danh sách sản phẩm hoặc số dashboard hard-code thay cho ORM ở
các luồng đã kiểm tra.
