import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  canonicalApiBaseUrl,
  createCanonicalClient,
} from "./canonical.ts"

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  })

const neverSettlingFetch: typeof fetch = () => new Promise(() => undefined)

const rejectingFetch: typeof fetch = (_input, init) =>
  new Promise((_resolve, reject) => {
    init?.signal?.addEventListener(
      "abort",
      () => reject(new DOMException("aborted", "AbortError")),
      { once: true },
    )
  })

test("normalizes only the single canonical API base URL namespace", () => {
  assert.equal(
    canonicalApiBaseUrl("https://example.invalid/api/v1/canonical"),
    "https://example.invalid/api/v1/canonical/",
  )
  assert.equal(
    canonicalApiBaseUrl("http://127.0.0.1:8000/api/v1/canonical/"),
    "http://127.0.0.1:8000/api/v1/canonical/",
  )
  assert.equal(canonicalApiBaseUrl(""), "/api/v1/canonical/")

  for (const value of [
    "//example.invalid/api/v1/canonical",
    "api/v1/canonical",
    "https://example.invalid/prefix/api/v1/canonical",
    "https://user@example.invalid/api/v1/canonical",
    "ftp://example.invalid/api/v1/canonical",
    "/api/v1/canonical?next=/legacy",
    "/api/v1/canonical#fragment",
    "/api/v1/legacy/",
  ]) {
    assert.throws(() => canonicalApiBaseUrl(value), {
      code: "invalid_canonical_base_url",
    })
  }
})

test("injects bearer authentication from the in-memory session and strips caller authorization", async () => {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken("unit-test-sentinel")
  const seenAuthorizations: Array<string | null> = []
  const fetchImplementation: typeof fetch = async (_input, init) => {
    seenAuthorizations.push(new Headers(init?.headers).get("authorization"))
    return jsonResponse({ success: true, data: { id: 7 } })
  }
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: fetchImplementation,
  })

  for (const headers of [
    { authorization: "caller-controlled-value" },
    [["AUTHORIZATION", "caller-controlled-value"]],
    new Headers({ Authorization: "caller-controlled-value" }),
  ] satisfies HeadersInit[]) {
    const result = await client.request<{ id: number }>("customers/", {
      headers,
    })
    assert.deepEqual(result, { id: 7 })
  }
  assert.deepEqual(seenAuthorizations, [
    "Bearer unit-test-sentinel",
    "Bearer unit-test-sentinel",
    "Bearer unit-test-sentinel",
  ])

  auth.clear()
  await client.request("customers/")
  assert.equal(seenAuthorizations.at(-1), null)
  assert.equal(auth.getAccessToken(), null)
})

test("rejects malformed tokens and auth-session failures before fetch", async () => {
  for (const value of ["", " whitespace", "line\nbreak", "tab\tvalue"]) {
    const auth = new InMemoryAuthSession()
    assert.throws(() => auth.setAccessToken(value), {
      code: "invalid_access_token",
    })
  }

  let fetchCalls = 0
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: { getAccessToken: () => "line\nbreak" },
    fetch: async () => {
      fetchCalls += 1
      return jsonResponse({ success: true, data: null })
    },
  })
  await assert.rejects(client.request("orders/"), {
    code: "invalid_access_token",
  })
  assert.equal(fetchCalls, 0)

  const throwingSession = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: {
      getAccessToken: () => {
        throw new Error("private auth diagnostic")
      },
    },
    fetch: async () => jsonResponse({ success: true, data: null }),
  })
  await assert.rejects(
    throwingSession.request("orders/"),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "protocol" &&
      error.code === "invalid_request_headers" &&
      !error.message.includes("private auth diagnostic"),
  )
})

test("parses canonical success and rejects malformed or mismatched envelopes", async () => {
  const auth = new InMemoryAuthSession()
  const success = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () => jsonResponse({ success: true, data: [1, 2] }),
  })
  assert.deepEqual(await success.request<number[]>("orders/"), [1, 2])

  for (const [status, body] of [
    [200, { data: "unexpected" }],
    [200, { success: false, error: { code: "bad", message: "Bad." } }],
    [400, { success: true, data: null }],
    [400, { success: false, error: { code: "", message: "Bad." } }],
    [400, { success: false, error: { code: "bad", message: "   " } }],
  ] as const) {
    const malformed = createCanonicalClient({
      baseUrl: "/api/v1/canonical/",
      auth,
      fetch: async () => jsonResponse(body, status),
    })
    await assert.rejects(
      malformed.request("orders/"),
      (error: unknown) =>
        error instanceof CanonicalClientError &&
        error.kind === "protocol" &&
        error.code === "invalid_response_envelope" &&
        error.status === status,
    )
  }

  const invalidJson = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () =>
      new Response("raw secret text must not escape", {
        status: 500,
        headers: { "content-type": "text/plain" },
      }),
  })
  await assert.rejects(
    invalidJson.request("orders/"),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "protocol" &&
      !error.message.includes("raw secret"),
  )
})

test("maps canonical authentication, permission, validation, conflict, not-found, and server errors", async () => {
  const cases = [
    [401, "authentication_failed", "authentication"],
    [403, "permission_denied", "permission"],
    [400, "field_error", "validation"],
    [409, "conflict", "conflict"],
    [404, "not_found", "not_found"],
    [500, "internal_error", "server"],
  ] as const

  for (const [status, code, kind] of cases) {
    const client = createCanonicalClient({
      baseUrl: "/api/v1/canonical/",
      auth: new InMemoryAuthSession(),
      fetch: async () =>
        jsonResponse(
          {
            success: false,
            error: { code, message: "Safe message.", details: { status } },
          },
          status,
        ),
    })
    await assert.rejects(
      client.request("orders/"),
      (error: unknown) =>
        error instanceof CanonicalClientError &&
        error.kind === kind &&
        error.code === code &&
        error.message === "Safe message." &&
        error.status === status,
    )
  }
})

test("classifies bounded timeout, caller cancellation, and network failure without raw diagnostics", async () => {
  const auth = new InMemoryAuthSession()
  const timeoutClient = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: rejectingFetch,
    defaultTimeoutMs: 10,
  })
  await assert.rejects(
    timeoutClient.request("orders/"),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "timeout" &&
      error.code === "request_timeout",
  )

  const caller = new AbortController()
  const cancellation = timeoutClient.request("orders/", {
    signal: caller.signal,
    timeoutMs: 1_000,
  })
  caller.abort()
  await assert.rejects(
    cancellation,
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "cancelled" &&
      error.code === "request_cancelled",
  )

  const networkClient = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () => {
      throw new TypeError("diagnostic text must not escape")
    },
  })
  await assert.rejects(
    networkClient.request("orders/"),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "network" &&
      error.message === "The server could not be reached." &&
      !error.message.includes("diagnostic text"),
  )
})

test("enforces first abort reason and bounds fetch adapters that ignore abort", async () => {
  const auth = new InMemoryAuthSession()
  const timeoutFirst = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: neverSettlingFetch,
    defaultTimeoutMs: 5,
  })
  const lateCaller = new AbortController()
  const lateCallerTimer = setTimeout(() => lateCaller.abort(), 50)
  await assert.rejects(
    timeoutFirst.request("orders/", {
      signal: lateCaller.signal,
    }),
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "timeout",
  )
  clearTimeout(lateCallerTimer)

  const callerFirst = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: neverSettlingFetch,
    defaultTimeoutMs: 50,
  })
  const earlyCaller = new AbortController()
  const request = callerFirst.request("orders/", {
    signal: earlyCaller.signal,
  })
  earlyCaller.abort()
  await assert.rejects(
    request,
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "cancelled",
  )
})

test("does not call fetch for an already-aborted caller signal", async () => {
  const auth = new InMemoryAuthSession()
  const signal = new AbortController()
  signal.abort()
  let fetchCalls = 0
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () => {
      fetchCalls += 1
      return jsonResponse({ success: true, data: null })
    },
  })

  await assert.rejects(
    client.request("orders/", { signal: signal.signal }),
    (error: unknown) =>
      error instanceof CanonicalClientError && error.kind === "cancelled",
  )
  assert.equal(fetchCalls, 0)
})

test("cleans external abort listener and timeout after settled request", async () => {
  const controller = new AbortController()
  let added = 0
  let removed = 0
  const originalAdd = controller.signal.addEventListener.bind(controller.signal)
  const originalRemove = controller.signal.removeEventListener.bind(
    controller.signal,
  )
  controller.signal.addEventListener = (((
    ...args: Parameters<AbortSignal["addEventListener"]>
  ) => {
    added += 1
    return originalAdd(...args)
  }) as AbortSignal["addEventListener"])
  controller.signal.removeEventListener = (((
    ...args: Parameters<AbortSignal["removeEventListener"]>
  ) => {
    removed += 1
    return originalRemove(...args)
  }) as AbortSignal["removeEventListener"])

  let requestSignal: AbortSignal | null | undefined
  let internalAbortCount = 0
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: new InMemoryAuthSession(),
    fetch: async (_input, init) => {
      requestSignal = init?.signal
      requestSignal?.addEventListener("abort", () => {
        internalAbortCount += 1
      })
      return jsonResponse({ success: true, data: null })
    },
    defaultTimeoutMs: 20,
  })

  await client.request("orders/", { signal: controller.signal })
  await new Promise((resolve) => setTimeout(resolve, 40))
  assert.equal(added, 1)
  assert.equal(removed, 1)
  assert.equal(internalAbortCount, 0)
})

test("rejects unbounded timeouts and paths that could escape the canonical base", async () => {
  let requestedUrl: string | URL | Request | null = null
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: new InMemoryAuthSession(),
    fetch: async (input) => {
      requestedUrl = input
      return jsonResponse({ success: true, data: null })
    },
  })

  await assert.rejects(client.request("orders/", { timeoutMs: 0 }), {
    code: "invalid_timeout",
  })

  for (const path of [
    "",
    "/orders/",
    "https://example.invalid/",
    "//example.invalid/orders/",
    "../legacy/",
    "orders/../legacy/",
    "orders/%2e%2e/legacy/",
    "orders/%252e%252e/legacy/",
    "orders/%2Flegacy/",
    "orders\\legacy",
    "orders/#fragment",
  ]) {
    await assert.rejects(client.request(path), {
      code: "invalid_canonical_path",
    })
  }

  await client.request("orders/?page=1&next=https%3A%2F%2Fexample.invalid")
  assert.equal(
    requestedUrl,
    "/api/v1/canonical/orders/?page=1&next=https%3A%2F%2Fexample.invalid",
  )
})

test("does not retry requests", async () => {
  let calls = 0
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: new InMemoryAuthSession(),
    fetch: async () => {
      calls += 1
      throw new TypeError("transient")
    },
  })

  await assert.rejects(client.request("orders/"), {
    code: "network_error",
  })
  assert.equal(calls, 1)
})

test("keeps the canonical client free of browser storage and console output", async () => {
  const source = await readFile(
    new URL("./canonical.ts", import.meta.url),
    "utf8",
  )
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/console\.(log|warn|error|debug|info)/.test(source), false)
})
