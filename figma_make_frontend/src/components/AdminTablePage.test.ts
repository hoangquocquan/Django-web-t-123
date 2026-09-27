import assert from "node:assert/strict"
import test from "node:test"

import {
  ADMIN_TABLE_CONFIGS,
  adminTableErrorMessage,
  adminTableStateText,
} from "./adminTableView.ts"

test("representative admin states distinguish loading empty populated and error", () => {
  assert.equal(adminTableStateText({ status: "loading" }), "Đang tải dữ liệu…")
  assert.equal(
    adminTableStateText({ status: "empty" }),
    "Không có dữ liệu phù hợp.",
  )
  assert.equal(
    adminTableStateText({
      status: "error",
      kind: "permission",
      message: "Không có quyền.",
    }),
    "Không có quyền.",
  )
  assert.equal(
    adminTableStateText({
      status: "ready",
      page: {
        count: 21,
        limit: 20,
        offset: 20,
        nextOffset: null,
        results: [
          {
            id: 1,
            sku: "P1",
            name: "Part",
            status: "draft",
            price: "0.00",
            categoryName: "",
          },
        ],
      },
    }),
    "21–21 / 21",
  )
})

test("admin UI keeps validation authentication and permission failures explicit", () => {
  assert.match(adminTableErrorMessage("validation"), /Truy vấn/)
  assert.match(adminTableErrorMessage("authentication"), /đăng nhập/)
  assert.match(adminTableErrorMessage("permission"), /quyền/)
  assert.notEqual(
    adminTableErrorMessage("permission"),
    adminTableStateText({ status: "empty" }),
  )
})

test("all admin controls use endpoint-approved keys", () => {
  assert.deepEqual(
    ADMIN_TABLE_CONFIGS.products.filters.map((filter) => filter.key),
    ["status", "active", "material"],
  )
  assert.deepEqual(
    ADMIN_TABLE_CONFIGS.inventory.ordering.map(([value]) => value),
    ["quantity", "updated_at"],
  )
  assert.deepEqual(
    ADMIN_TABLE_CONFIGS.orders.filters.map((filter) => filter.key),
    ["workflow_status", "status"],
  )
  assert.deepEqual(
    ADMIN_TABLE_CONFIGS.workflows.filters.map((filter) => filter.key),
    ["decision", "requested_status"],
  )
  assert.deepEqual(
    ADMIN_TABLE_CONFIGS.transactions.filters.map((filter) => filter.key),
    ["entity_type", "action"],
  )
})

test("rendered column contracts do not depend on deferred serializer fields", () => {
  const allHeaders = Object.values(ADMIN_TABLE_CONFIGS)
    .flatMap((config) => config.headers)
    .join(" ")
    .toLowerCase()
  for (const deferred of [
    "tolerance",
    "available_quantity",
    "progress",
    "expected delivery",
  ])
    assert.equal(allHeaders.includes(deferred), false)
})
