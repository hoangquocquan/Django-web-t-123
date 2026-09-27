import assert from "node:assert/strict"
import test from "node:test"

import {
  initialAdminTableQuery,
  reduceAdminTableQuery,
} from "./useAdminTableQuery.ts"
import type { AdminTableQueryAction } from "./useAdminTableQuery.ts"

test("admin query starts bounded and deterministic", () => {
  assert.deepEqual(initialAdminTableQuery<"products">(), {
    page: 1,
    pageSize: 20,
    search: "",
    filters: {},
    ordering: "",
  })
})

test("search filter ordering and page-size changes reset the page", () => {
  let state = { ...initialAdminTableQuery<"products">(), page: 4 }
  state = reduceAdminTableQuery("products", state, {
    type: "search",
    search: "  shaft ",
  })
  assert.equal(state.page, 1)
  assert.equal(state.search, "shaft")
  state = { ...state, page: 3 }
  state = reduceAdminTableQuery("products", state, {
    type: "filter",
    name: "material",
    value: " SCM440 ",
  })
  assert.deepEqual(state.filters, { material: "SCM440" })
  assert.equal(state.page, 1)
  state = { ...state, page: 2 }
  state = reduceAdminTableQuery("products", state, {
    type: "ordering",
    ordering: "-name",
  })
  assert.equal(state.ordering, "-name")
  assert.equal(state.page, 1)
  state = { ...state, page: 5 }
  state = reduceAdminTableQuery("products", state, {
    type: "pageSize",
    pageSize: 1000,
  })
  assert.equal(state.pageSize, 100)
  assert.equal(state.page, 1)
})

test("pagination clamps invalid page and page size input", () => {
  let state = initialAdminTableQuery<"customers">()
  state = reduceAdminTableQuery("customers", state, { type: "page", page: -9 })
  assert.equal(state.page, 1)
  state = reduceAdminTableQuery("customers", state, {
    type: "pageSize",
    pageSize: 0,
  })
  assert.equal(state.pageSize, 1)
  state = reduceAdminTableQuery("customers", state, {
    type: "pageSize",
    pageSize: Number.NaN,
  })
  assert.equal(state.pageSize, 20)
})

test("resource contract ignores unapproved filter and ordering keys", () => {
  const state = initialAdminTableQuery<"products">()
  const unsafeFilter = {
    type: "filter",
    name: "customer__email",
    value: "x",
  } as unknown as AdminTableQueryAction<"products">
  assert.equal(reduceAdminTableQuery("products", state, unsafeFilter), state)
  const unsafeOrdering = {
    type: "ordering",
    ordering: "user__password",
  } as unknown as AdminTableQueryAction<"products">
  assert.equal(reduceAdminTableQuery("products", state, unsafeOrdering), state)
})

test("reset returns the initial query", () => {
  const changed = {
    page: 3,
    pageSize: 50,
    search: "x",
    filters: { status: "draft" },
    ordering: "name",
  } as const
  assert.deepEqual(
    reduceAdminTableQuery("products", changed, { type: "reset" }),
    initialAdminTableQuery<"products">(),
  )
})
