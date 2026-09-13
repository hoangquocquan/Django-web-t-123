import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  createCanonicalClient,
} from "./canonical.ts"
import {
  canonicalBaseUrlForPhase5b,
  createFoundationAuthClient,
  foundationAuthBaseUrl,
} from "./foundation.ts"
import {
  createLatestRequestGuard,
  fetchRfqPage,
  rfqListPath,
  rfqRows,
  rfqStateFromError,
  rfqStatusText,
  type CanonicalRfq,
  type CanonicalRfqPage,
} from "./rfq.ts"

const safeToken = "phase5b-unit-token"

const user = {
  id: 7,
  email: "user@example.test",
  full_name: "Unit User",
  role: "Sales",
  is_active: true,
}

const rfq: CanonicalRfq = {
  id: 10,
  data_contract: "MVP_V1",
  rfq_number: "RFQ-UNIT-001",
  quotation_family_number: null,
  customer_id: 42,
  status: "DRAFT",
  project_name: "Fixture Project",
  notes: "",
  quote_due_at: "2026-09-20",
  required_delivery_date: "2026-10-15",
  assigned_to_id: null,
  closure_reason: "",
  created_by_id: 7,
  updated_by_id: null,
  created_at: "2026-09-13T00:00:00+09:00",
  updated_at: "2026-09-13T00:00:00+09:00",
  compatibility: {},
}

const page = (results: CanonicalRfq[]): CanonicalRfqPage => ({
  count: results.length,
  limit: 20,
  offset: 0,
  next_offset: null,
  previous_offset: null,
  results,
})

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  })

const neverSettlingFetch: typeof fetch = () => new Promise(() => undefined)

test("App.tsx contains only the five mechanical inline prop-type repairs", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  assert.equal(source.includes("{ children: any tone?: string }"), false)
  assert.equal(source.includes("{ label: string placeholder: string }"), false)
  assert.equal(source.includes("{ headers: string[] rows: string[][] }"), false)
  assert.equal(
    source.includes("{ route: string go: (v: string) => void }"),
    false,
  )
  assert.match(source, /children: ReactNode\s+tone\?: string/)
  assert.match(source, /label: string\s+placeholder: string/)
  assert.match(source, /headers: string\[\]\s+rows: string\[\]/)
  assert.match(source, /route: string\s+go: \(v: string\) => void/)
})

test("successful Foundation login stores only the returned token in memory", async () => {
  const auth = new InMemoryAuthSession()
  let requestBody: unknown
  const client = createFoundationAuthClient({
    auth,
    fetch: async (input, init) => {
      assert.equal(input, "/api/v1/foundation/auth/login/")
      assert.equal(init?.method, "POST")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({
        success: true,
        data: {
          token: safeToken,
          expires_at: "2026-09-14T00:00:00+09:00",
          user,
        },
      })
    },
  })

  const result = await client.login({
    email: " user@example.test ",
    password: "unit-password",
  })
  assert.deepEqual(requestBody, {
    email: "user@example.test",
    password: "unit-password",
  })
  assert.equal(auth.getAccessToken(), safeToken)
  assert.deepEqual(result, {
    expires_at: "2026-09-14T00:00:00+09:00",
    user,
  })
})

test("Phase 5B resolves documented API-root topology without a Vite proxy", () => {
  assert.equal(
    foundationAuthBaseUrl(undefined, "http://127.0.0.1:8000"),
    "http://127.0.0.1:8000/api/v1/foundation/auth/",
  )
  assert.equal(
    canonicalBaseUrlForPhase5b(undefined, "http://127.0.0.1:8000"),
    "http://127.0.0.1:8000/api/v1/canonical/",
  )
  assert.equal(
    foundationAuthBaseUrl("https://example.test/api/v1/foundation/auth/", ""),
    "https://example.test/api/v1/foundation/auth/",
  )
  assert.equal(canonicalBaseUrlForPhase5b(undefined, ""), "/api/v1/canonical/")

  for (const value of [
    "https://user@example.test/api/v1/foundation/auth/",
    "https://example.test/api/v1/foundation/auth/?token=x",
    "https://example.test/api/v1/canonical/",
  ]) {
    assert.throws(() => foundationAuthBaseUrl(value, ""), {
      code: "invalid_foundation_auth_base_url",
    })
  }
})

test("invalid login payload fails before request", async () => {
  const auth = new InMemoryAuthSession()
  let calls = 0
  const client = createFoundationAuthClient({
    auth,
    fetch: async () => {
      calls += 1
      return jsonResponse({ success: true, data: null })
    },
  })

  await assert.rejects(client.login({ email: "", password: "" }), {
    code: "login_validation_failed",
  })
  assert.equal(calls, 0)
  assert.equal(auth.getAccessToken(), null)
})

test("authentication rejection is sanitized and leaves no token", async () => {
  const auth = new InMemoryAuthSession()
  const client = createFoundationAuthClient({
    auth,
    fetch: async () =>
      jsonResponse(
        {
          success: false,
          error: { code: "permission_denied", message: "Invalid credentials." },
        },
        403,
      ),
  })

  await assert.rejects(
    client.login({ email: "user@example.test", password: "wrong" }),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "permission" &&
      error.message === "Login was rejected." &&
      !error.message.includes("wrong"),
  )
  assert.equal(auth.getAccessToken(), null)
})

test("Foundation login is cancellable and does not store a cancelled response", async () => {
  const auth = new InMemoryAuthSession()
  const controller = new AbortController()
  const client = createFoundationAuthClient({
    auth,
    fetch: neverSettlingFetch,
    defaultTimeoutMs: 1_000,
  })
  const request = client.login(
    { email: "user@example.test", password: "unit-password" },
    { signal: controller.signal },
  )
  controller.abort()

  await assert.rejects(
    request,
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "cancelled" &&
      error.code === "request_cancelled",
  )
  assert.equal(auth.getAccessToken(), null)
})

test("Foundation login timeout is bounded and sanitized", async () => {
  const auth = new InMemoryAuthSession()
  const client = createFoundationAuthClient({
    auth,
    fetch: neverSettlingFetch,
    defaultTimeoutMs: 5,
  })

  await assert.rejects(
    client.login({ email: "user@example.test", password: "unit-password" }),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "timeout" &&
      error.message === "The request timed out.",
  )
  assert.equal(auth.getAccessToken(), null)
})

test("App login clears password input and guards stale authentication responses", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  assert.match(source, /const submittedPassword = password\s+setPassword\(""\)/)
  assert.match(source, /loginAbort\.current\?\.abort\(\)/)
  assert.match(source, /const requestId = loginGuard\.next\(\)/)
  assert.match(source, /if \(!loginGuard\.isLatest\(requestId\)\) return/)
})

test("logout caller can clear memory immediately while endpoint receives bearer token", async () => {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(safeToken)
  let authorization: string | null = null
  const client = createFoundationAuthClient({
    auth,
    fetch: async (input, init) => {
      assert.equal(input, "/api/v1/foundation/auth/logout/")
      authorization = new Headers(init?.headers).get("authorization")
      return jsonResponse({ success: true, data: { logged_out: true } })
    },
  })

  const tokenForRevocation = auth.getAccessToken()
  auth.clear()
  if (tokenForRevocation) await client.logout(tokenForRevocation)
  assert.equal(auth.getAccessToken(), null)
  assert.equal(authorization, `Bearer ${safeToken}`)
})

test("logout failure is sanitized after local memory has already been cleared", async () => {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(safeToken)
  const client = createFoundationAuthClient({
    auth,
    fetch: async () =>
      jsonResponse(
        {
          success: false,
          error: {
            code: "server_failed",
            message: "private logout diagnostic",
          },
        },
        500,
      ),
  })

  const tokenForRevocation = auth.getAccessToken()
  auth.clear()
  await assert.rejects(
    tokenForRevocation ? client.logout(tokenForRevocation) : Promise.resolve(),
    (error: unknown) =>
      error instanceof CanonicalClientError &&
      error.kind === "server" &&
      error.message === "Logout request was rejected." &&
      !error.message.includes("private logout diagnostic"),
  )
  assert.equal(auth.getAccessToken(), null)
})

test("401 maps to unauthenticated state, clears memory, and does not retry", async () => {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(safeToken)
  let calls = 0
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () => {
      calls += 1
      return jsonResponse(
        {
          success: false,
          error: {
            code: "authentication_failed",
            message: "Authentication credentials are invalid or inactive.",
          },
        },
        401,
      )
    },
  })

  await assert.rejects(fetchRfqPage(client), (error: unknown) => {
    if (!(error instanceof CanonicalClientError)) return false
    const state = rfqStateFromError(error)
    if (state.status === "unauthenticated") auth.clear()
    return state.status === "unauthenticated"
  })
  assert.equal(auth.getAccessToken(), null)
  assert.equal(calls, 1)
})

test("successful and empty RFQ pages render deterministic table states", async () => {
  const auth = new InMemoryAuthSession()
  const populatedClient = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async (input) => {
      assert.equal(input, `/api/v1/canonical/${rfqListPath()}`)
      return jsonResponse({ success: true, data: page([rfq]) })
    },
  })
  const populated = await fetchRfqPage(populatedClient)
  assert.deepEqual(rfqRows(populated), [
    ["RFQ-UNIT-001", "Customer #42", "2026-09-20", "Fixture Project", "DRAFT"],
  ])

  const emptyClient = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: async () => jsonResponse({ success: true, data: page([]) }),
  })
  const empty = await fetchRfqPage(emptyClient)
  assert.equal(empty.results.length, 0)
  assert.equal(
    rfqStatusText({ status: "empty", page: empty }),
    "Chưa có RFQ canonical.",
  )
})

test("RFQ row mapping tolerates null and optional backend fields", () => {
  assert.deepEqual(
    rfqRows(
      page([
        {
          ...rfq,
          id: 11,
          rfq_number: "RFQ-NULL-001",
          status: null,
          project_name: "",
          quote_due_at: null,
          assigned_to_id: null,
          created_by_id: null,
          updated_by_id: null,
          created_at: null,
          updated_at: null,
        },
      ]),
    ),
    [["RFQ-NULL-001", "Customer #42", "Chưa có hạn", "Không tên", "LEGACY"]],
  )
})

test("App invalidates in-flight RFQ requests on logout or authentication change", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  assert.match(
    source,
    /rfqAbort\.current\?\.abort\(\)\s+requestGuard\.next\(\)/,
  )
  assert.match(
    source,
    /loginAbort\.current\?\.abort\(\)\s+loginGuard\.next\(\)/,
  )
})

test("RFQ error states cover permission, timeout, network, malformed protocol, and server", async () => {
  const cases = [
    [
      new CanonicalClientError({
        kind: "permission",
        code: "permission_denied",
        message: "x",
      }),
      "permission_denied",
    ],
    [
      new CanonicalClientError({
        kind: "timeout",
        code: "request_timeout",
        message: "x",
      }),
      "timeout",
    ],
    [
      new CanonicalClientError({
        kind: "network",
        code: "network_error",
        message: "x",
      }),
      "network",
    ],
    [
      new CanonicalClientError({
        kind: "protocol",
        code: "invalid_response_envelope",
        message: "x",
      }),
      "protocol",
    ],
    [
      new CanonicalClientError({
        kind: "server",
        code: "internal_error",
        message: "x",
      }),
      "server",
    ],
  ] as const

  for (const [error, status] of cases) {
    assert.equal(rfqStateFromError(error).status, status)
  }

  const malformedClient = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: new InMemoryAuthSession(),
    fetch: async () =>
      jsonResponse({
        success: true,
        data: { count: 1, limit: 20, offset: 0, results: [{}] },
      }),
  })
  await assert.rejects(fetchRfqPage(malformedClient), {
    code: "invalid_rfq_page",
  })
})

test("latest request guard prevents stale RFQ responses from overwriting newer state", () => {
  const guard = createLatestRequestGuard()
  const first = guard.next()
  const second = guard.next()
  assert.equal(guard.isLatest(first), false)
  assert.equal(guard.isLatest(second), true)
})

test("integrated RFQ slice has no mock fallback data", async () => {
  const appSource = await readFile(
    new URL("../App.tsx", import.meta.url),
    "utf8",
  )
  const salesQuotesStart = appSource.indexOf('route === "sales-quotes"')
  const salesAiStart = appSource.indexOf('route === "sales-ai"')
  const slice = appSource.slice(salesQuotesStart, salesAiStart)
  assert.match(slice, /<RfqPanel/)
  assert.equal(slice.includes("QT-2026-082"), false)
  assert.equal(slice.includes("Samsung SDI"), false)
})

test("Phase 5B frontend code does not persist tokens or log credentials", async () => {
  const files = await Promise.all([
    readFile(new URL("../App.tsx", import.meta.url), "utf8"),
    readFile(new URL("./foundation.ts", import.meta.url), "utf8"),
    readFile(new URL("./rfq.ts", import.meta.url), "utf8"),
  ])
  const source = files.join("\n")
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/console\.(log|warn|error|debug|info)/.test(source), false)
  assert.equal(/Bearer [A-Za-z0-9_\-.]{24,}/.test(source), false)
})
