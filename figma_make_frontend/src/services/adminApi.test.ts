import assert from "node:assert/strict"
import test from "node:test"

import { CanonicalClientError, InMemoryAuthSession } from "../api/canonical.ts"
import { initialAdminTableQuery } from "../hooks/useAdminTableQuery.ts"
import type { AdminTableQuery } from "../types/admin.ts"
import { createAdminApi, serializeAdminQuery } from "./adminApi.ts"

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  })
}
function productPage() {
  return {
    success: true,
    data: {
      count: 1,
      limit: 20,
      offset: 0,
      next_offset: null,
      results: [
        {
          id: 1,
          sku: "SKU-1",
          name: "Fixture",
          status: "draft",
          price: "10.00",
          category_name: "CNC",
        },
      ],
    },
  }
}
function authenticated() {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken("test-access-token")
  return auth
}

test("serializes only endpoint-specific allowlisted query names with bounded pagination", () => {
  const unsafe = {
    page: 2,
    pageSize: 1000,
    search: " fixture ",
    ordering: "-name",
    filters: {
      status: "draft",
      material: "SCM440",
      customer__email: "leak",
      role__permissions: "*",
      user__password: "x",
    },
  } as unknown as AdminTableQuery<"products">
  const parameters = new URLSearchParams(
    serializeAdminQuery("products", unsafe),
  )
  assert.deepEqual(Object.fromEntries(parameters), {
    limit: "100",
    offset: "100",
    search: "fixture",
    ordering: "-name",
    status: "draft",
    material: "SCM440",
  })
  assert.equal(parameters.has("customer__email"), false)
  assert.equal(parameters.has("role__permissions"), false)
  assert.equal(parameters.has("user__password"), false)
})

test("constructs the exact endpoint URL and bearer authorization", async () => {
  let capturedUrl = ""
  let capturedAuthorization = ""
  const api = createAdminApi({
    auth: authenticated(),
    fetch: async (input, init) => {
      capturedUrl = String(input)
      capturedAuthorization =
        new Headers(init?.headers).get("authorization") ?? ""
      return response(productPage())
    },
  })
  const result = await api.getProducts(initialAdminTableQuery<"products">())
  assert.equal(capturedUrl, "/api/v1/admin/products/?limit=20&offset=0")
  assert.equal(capturedAuthorization, "Bearer test-access-token")
  assert.deepEqual(result.results[0], {
    id: 1,
    sku: "SKU-1",
    name: "Fixture",
    status: "draft",
    price: "10.00",
    categoryName: "CNC",
  })
})

test("does not send an admin request without an access token", async () => {
  let called = false
  const api = createAdminApi({
    auth: new InMemoryAuthSession(),
    fetch: async () => {
      called = true
      return response(productPage())
    },
  })
  await assert.rejects(
    api.getProducts(initialAdminTableQuery<"products">()),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "authentication" &&
      error.code === "missing_access_token",
  )
  assert.equal(called, false)
})

for (const [status, kind] of [
  [400, "validation"],
  [401, "authentication"],
  [403, "permission"],
  [500, "server"],
] as const) {
  test(`classifies HTTP ${status} as ${kind}`, async () => {
    const api = createAdminApi({
      auth: authenticated(),
      fetch: async () =>
        response(
          {
            success: false,
            error: { code: `error_${status}`, message: "hidden server detail" },
          },
          status,
        ),
    })
    await assert.rejects(
      api.getProducts(initialAdminTableQuery<"products">()),
      (error: unknown) =>
        error instanceof CanonicalClientError &&
        error.kind === kind &&
        error.status === status,
    )
  })
}

test("distinguishes caller cancellation", async () => {
  const controller = new AbortController()
  const api = createAdminApi({
    auth: authenticated(),
    fetch: async (_input, init) =>
      new Promise<Response>((_resolve, reject) =>
        init?.signal?.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        ),
      ),
  })
  const pending = api.getProducts(
    initialAdminTableQuery<"products">(),
    controller.signal,
  )
  controller.abort()
  await assert.rejects(
    pending,
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "cancelled",
  )
})

test("classifies timeout and network failures", async () => {
  const timeoutApi = createAdminApi({
    auth: authenticated(),
    timeoutMs: 1,
    fetch: async (_input, init) =>
      new Promise<Response>((_resolve, reject) =>
        init?.signal?.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        ),
      ),
  })
  await assert.rejects(
    timeoutApi.getProducts(initialAdminTableQuery<"products">()),
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "timeout",
  )
  const networkApi = createAdminApi({
    auth: authenticated(),
    fetch: async () => {
      throw new TypeError("offline")
    },
  })
  await assert.rejects(
    networkApi.getProducts(initialAdminTableQuery<"products">()),
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "network",
  )
})

test("rejects malformed success responses instead of rendering partial sensitive data", async () => {
  const api = createAdminApi({
    auth: authenticated(),
    fetch: async () =>
      response({
        success: true,
        data: { count: 1, results: [{ password: "not allowed" }] },
      }),
  })
  await assert.rejects(
    api.getProducts(initialAdminTableQuery<"products">()),
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "protocol",
  )
})
