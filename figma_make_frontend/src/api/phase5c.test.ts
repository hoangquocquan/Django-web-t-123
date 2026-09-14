import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  createCanonicalClient,
} from "./canonical.ts"
import {
  addRfqLine,
  commandStateFromError,
  createCommandGate,
  createRfqCreateAttemptManager,
  createRfqRequestGuards,
  createRfqDraft,
  executeRfqCreateAttempt,
  fetchRfqDetail,
  fetchRfqLines,
  loadRfqSelectors,
  removeRfqLine,
  rfqLifecyclePermissions,
  shouldRetainCreateAttempt,
  submitRfq,
  updateRfqDraft,
  updateRfqLine,
  validateRfqCreatePayload,
  validateRfqLineCreatePayload,
  validateRfqLineUpdatePayload,
  validateRfqUpdatePayload,
  type CanonicalCustomer,
  type CanonicalMaterial,
  type CanonicalPart,
  type CanonicalRfqLine,
  type RfqCreatePayload,
} from "./rfqCommands.ts"
import {
  createLatestRequestGuard,
  type CanonicalPage,
  type CanonicalRfq,
} from "./rfq.ts"

const token = "phase5c-unit-token"

const customer: CanonicalCustomer = {
  id: 11,
  data_contract: "MVP_V1",
  customer_code: "CUS-001",
  company_name: "Canonical Customer",
  status: "ACTIVE",
}

const part: CanonicalPart = {
  id: 21,
  data_contract: "MVP_V1",
  part_code: "PART-001",
  name: "Bracket",
  revision: "A",
  unit: "PCS",
  default_material_id: 31,
  tolerance: "+/-0.01",
  technical_requirements: "Deburr all edges.",
  is_active: true,
}

const material: CanonicalMaterial = {
  id: 31,
  data_contract: "MVP_V1",
  material_code: "MAT-001",
  name: "SUS304",
  standard: "JIS",
  grade: "304",
  is_active: true,
}

const rfq: CanonicalRfq = {
  id: 41,
  data_contract: "MVP_V1",
  rfq_number: "RFQ-2026-0001",
  quotation_family_number: null,
  customer_id: customer.id,
  status: "DRAFT",
  project_name: "Phase 5C fixture",
  notes: "Need fast quote.",
  quote_due_at: "2026-09-20",
  required_delivery_date: "2026-10-10",
  assigned_to_id: null,
  closure_reason: "",
  created_by_id: 7,
  updated_by_id: null,
  created_at: "2026-09-13T00:00:00+09:00",
  updated_at: "2026-09-13T00:00:00+09:00",
  compatibility: {},
}

const line: CanonicalRfqLine = {
  id: 51,
  rfq_id: rfq.id,
  line_number: 1,
  part_id: part.id,
  material_id: material.id,
  description: "Machined bracket",
  quantity: "12.5000",
  unit: "PCS",
  required_delivery_date: "2026-10-10",
  tolerance: "+/-0.01",
  technical_notes: "Inspect critical bores.",
  drawing_required: false,
  created_at: "2026-09-13T00:00:00+09:00",
  updated_at: "2026-09-13T00:00:00+09:00",
}

const page = <T>(results: T[]): CanonicalPage<T> => ({
  count: results.length,
  limit: 100,
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

function client(fetchImplementation: typeof fetch) {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(token)
  return createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: fetchImplementation,
    defaultTimeoutMs: 25,
  })
}

test("Phase 5C loads only canonical selector read endpoints", async () => {
  const paths: string[] = []
  const result = await loadRfqSelectors(
    client(async (input, init) => {
      assert.equal(init?.method, undefined)
      paths.push(String(input))
      if (String(input).includes("/customers/")) {
        return jsonResponse({ success: true, data: page([customer]) })
      }
      if (String(input).includes("/parts/")) {
        return jsonResponse({ success: true, data: page([part]) })
      }
      return jsonResponse({ success: true, data: page([material]) })
    }),
  )

  assert.deepEqual(paths.sort(), [
    "/api/v1/canonical/customers/?data_contract=MVP_V1&status=ACTIVE&limit=100&ordering=company_name",
    "/api/v1/canonical/materials/?data_contract=MVP_V1&is_active=true&limit=100&ordering=material_code",
    "/api/v1/canonical/parts/?data_contract=MVP_V1&is_active=true&limit=100&ordering=part_code",
  ])
  assert.deepEqual(result, {
    customers: [customer],
    parts: [part],
    materials: [material],
  })
})

test("create draft posts the canonical payload with an opaque idempotency key", async () => {
  const payload = validateRfqCreatePayload({
    customer_id: customer.id,
    project_name: " Phase 5C fixture ",
    notes: " Need fast quote. ",
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  })
  let requestBody: unknown
  let idempotencyKey: string | null = null
  const created = await createRfqDraft(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/commands/create/")
      assert.equal(init?.method, "POST")
      const headers = new Headers(init?.headers)
      assert.equal(headers.get("authorization"), `Bearer ${token}`)
      idempotencyKey = headers.get("idempotency-key")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({ success: true, data: rfq })
    }),
    payload,
    "phase5c.opaque-key-001",
  )

  assert.equal(idempotencyKey, "phase5c.opaque-key-001")
  assert.deepEqual(requestBody, payload)
  assert.equal(created.id, rfq.id)
})

test("create attempt manager reuses the same key for the same logical retry", () => {
  const payload: RfqCreatePayload = {
    customer_id: customer.id,
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  }
  let sequence = 0
  const manager = createRfqCreateAttemptManager(
    () => `phase5c-key-${++sequence}`,
  )

  assert.equal(manager.begin(payload).key, "phase5c-key-1")
  assert.equal(manager.begin({ ...payload }).key, "phase5c-key-1")
  manager.fail(
    manager.begin(payload),
    new CanonicalClientError({
      kind: "network",
      code: "network_error",
      message: "x",
    }),
  )
  assert.equal(manager.begin(payload).key, "phase5c-key-1")
  assert.equal(
    manager.begin({ ...payload, project_name: "Changed after timeout" }).key,
    "phase5c-key-1",
  )
})

test("active create attempt locks the customer selector to its retained payload", async () => {
  const payload: RfqCreatePayload = {
    customer_id: customer.id,
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  }
  const manager = createRfqCreateAttemptManager(() => "phase5c-key-1")

  manager.begin(payload)
  assert.equal(manager.hasActiveAttempt(), true)
  assert.deepEqual(manager.activePayload(), payload)

  const source = await readFile(
    new URL("../components/RfqWorkspace.tsx", import.meta.url),
    "utf8",
  )
  const customerSelector = source.slice(
    source.indexOf('<Labeled label="Khách hàng">'),
    source.indexOf('<FieldError state={command} name="customer_id" />'),
  )

  assert.match(
    customerSelector,
    /disabled=\{[\s\S]*activeCreateAttempt[\s\S]*\}/,
  )
})

test("create attempt manager issues a new key after definitive completion", () => {
  const payload: RfqCreatePayload = {
    customer_id: customer.id,
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  }
  let sequence = 0
  const manager = createRfqCreateAttemptManager(
    () => `phase5c-key-${++sequence}`,
  )

  const attempt = manager.begin(payload)
  assert.equal(attempt.key, "phase5c-key-1")
  manager.complete(attempt)
  assert.equal(manager.begin(payload).key, "phase5c-key-2")
})

test("create success followed by failed reconciliation retries GET without duplicate POST", async () => {
  const payload: RfqCreatePayload = {
    customer_id: customer.id,
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  }
  let createPosts = 0
  let reconciliations = 0
  const reconciledIds: number[] = []
  const manager = createRfqCreateAttemptManager(() => "phase5c-key-1")
  const api = client(async (input) => {
    assert.equal(input, "/api/v1/canonical/rfqs/commands/create/")
    createPosts += 1
    return jsonResponse({ success: true, data: rfq })
  })
  const reconcile = async (rfqId: number) => {
    reconciliations += 1
    reconciledIds.push(rfqId)
    if (reconciliations === 1) {
      throw new CanonicalClientError({
        kind: "timeout",
        code: "request_timeout",
        message: "private timeout detail",
      })
    }
    return { rfq, lines: [line] }
  }

  await assert.rejects(
    executeRfqCreateAttempt(api, manager, payload, reconcile),
    { code: "request_timeout" },
  )
  assert.equal(manager.hasUnreconciledCreate(), true)

  const result = await executeRfqCreateAttempt(api, manager, payload, reconcile)
  assert.equal(result.rfq.id, rfq.id)
  assert.equal(createPosts, 1)
  assert.deepEqual(reconciledIds, [rfq.id, rfq.id])
  assert.equal(manager.hasUnreconciledCreate(), false)
})

test("a fully reconciled create allows a new logical attempt with a new key", async () => {
  const keys: string[] = []
  let sequence = 0
  const manager = createRfqCreateAttemptManager(
    () => `phase5c-key-${++sequence}`,
  )
  const api = client(async (_input, init) => {
    keys.push(new Headers(init?.headers).get("idempotency-key")!)
    return jsonResponse({ success: true, data: rfq })
  })
  const first: RfqCreatePayload = {
    customer_id: customer.id,
    quote_due_at: "2026-09-20",
    required_delivery_date: "2026-10-10",
  }

  await executeRfqCreateAttempt(api, manager, first, async () => rfq)
  await executeRfqCreateAttempt(
    api,
    manager,
    { ...first, project_name: "New logical draft" },
    async () => rfq,
  )

  assert.deepEqual(keys, ["phase5c-key-1", "phase5c-key-2"])
})

test("create draft rejects malformed idempotency keys before transport", async () => {
  await assert.rejects(
    createRfqDraft(
      client(async () => jsonResponse({ success: true, data: rfq })),
      {
        customer_id: customer.id,
        quote_due_at: "2026-09-20",
        required_delivery_date: "2026-10-10",
      },
      "bad key",
    ),
    { code: "client_validation_error" },
  )
})

test("header update posts only the allowed draft header fields", async () => {
  const payload = validateRfqUpdatePayload({
    project_name: "Updated project",
    notes: "Updated notes",
    quote_due_at: "2026-09-21",
    required_delivery_date: "2026-10-11",
    assigned_to_id: null,
  })
  let requestBody: unknown
  const updated = await updateRfqDraft(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/41/commands/update/")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({ success: true, data: { ...rfq, ...payload } })
    }),
    rfq.id,
    payload,
  )

  assert.deepEqual(requestBody, payload)
  assert.equal(updated.project_name, "Updated project")
})

test("header validation rejects unsupported fields and bad dates", () => {
  assert.throws(
    () =>
      validateRfqCreatePayload({
        customer_id: 0,
        quote_due_at: "2026-09-20",
        required_delivery_date: "2026-10-10",
        status: "SUBMITTED",
      }),
    { code: "client_validation_error" },
  )
  assert.throws(
    () =>
      validateRfqUpdatePayload({
        quote_due_at: "not-a-date",
      }),
    { code: "client_validation_error" },
  )
})

test("header update rejects invalid effective date ordering before transport", async () => {
  let apiCalls = 0
  const api = client(async () => {
    apiCalls += 1
    return jsonResponse({ success: true, data: rfq })
  })

  await assert.rejects(
    async () => {
      const payload = validateRfqUpdatePayload(
        { quote_due_at: "2026-10-11" },
        {
          quote_due_at: rfq.quote_due_at,
          required_delivery_date: rfq.required_delivery_date,
        },
        "2026-09-13",
      )
      await updateRfqDraft(api, rfq.id, payload)
    },
    { code: "client_validation_error" },
  )
  assert.equal(apiCalls, 0)
})

test("line add posts the canonical line command and no write outside RFQ lines", async () => {
  const payload = validateRfqLineCreatePayload({
    part_id: part.id,
    material_id: material.id,
    description: line.description,
    quantity: line.quantity,
    unit: line.unit,
    required_delivery_date: line.required_delivery_date,
    tolerance: line.tolerance,
    technical_notes: line.technical_notes,
    drawing_required: false,
  })
  let requestBody: unknown
  const createdLine = await addRfqLine(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/41/lines/commands/add/")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({ success: true, data: line })
    }),
    rfq.id,
    payload,
  )

  assert.deepEqual(requestBody, payload)
  assert.equal(createdLine.id, line.id)
})

test("line update posts the exact RFQ line update command", async () => {
  const payload = validateRfqLineUpdatePayload({
    description: "Revised bracket",
    quantity: "24",
    unit: "PCS",
    required_delivery_date: "2026-10-12",
    tolerance: "+/-0.02",
    technical_notes: "Updated notes.",
    drawing_required: false,
  })
  let requestBody: unknown
  await updateRfqLine(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/41/lines/51/commands/update/")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({ success: true, data: { ...line, ...payload } })
    }),
    rfq.id,
    line.id,
    payload,
  )

  assert.deepEqual(requestBody, payload)
})

test("line remove accepts only the canonical removed acknowledgement", async () => {
  let requestBody: unknown
  await removeRfqLine(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/41/lines/51/commands/remove/")
      requestBody = JSON.parse(String(init?.body))
      return jsonResponse({
        success: true,
        data: { id: line.id, removed: true },
      })
    }),
    rfq.id,
    line.id,
  )

  assert.deepEqual(requestBody, {})
})

test("line validation enforces description, quantity, unit, tolerance, notes, and drawing scope", () => {
  assert.throws(
    () =>
      validateRfqLineCreatePayload({
        description: "",
        quantity: "0",
        unit: "BOX",
        required_delivery_date: "2026-10-10",
        tolerance: "",
        technical_notes: "",
        drawing_required: true,
      }),
    { code: "client_validation_error" },
  )
})

test("submit posts only the draft-to-submitted RFQ command", async () => {
  const submitted = await submitRfq(
    client(async (input, init) => {
      assert.equal(input, "/api/v1/canonical/rfqs/41/commands/submit/")
      assert.equal(init?.method, "POST")
      assert.deepEqual(JSON.parse(String(init?.body)), {})
      return jsonResponse({
        success: true,
        data: { ...rfq, status: "SUBMITTED" },
      })
    }),
    rfq.id,
  )

  assert.equal(submitted.status, "SUBMITTED")
})

test("submit rejects non-submitted backend responses as protocol errors", async () => {
  await assert.rejects(
    submitRfq(
      client(async () => jsonResponse({ success: true, data: rfq })),
      rfq.id,
    ),
    { code: "invalid_rfq_submit_response" },
  )
})

test("detail and lines reconciliation uses canonical read endpoints", async () => {
  const paths: string[] = []
  const api = client(async (input) => {
    paths.push(String(input))
    if (String(input).endsWith("/lines/?limit=100&ordering=line_number")) {
      return jsonResponse({ success: true, data: page([line]) })
    }
    return jsonResponse({ success: true, data: rfq })
  })

  assert.equal((await fetchRfqDetail(api, rfq.id)).id, rfq.id)
  assert.deepEqual(await fetchRfqLines(api, rfq.id), [line])
  assert.deepEqual(paths, [
    "/api/v1/canonical/rfqs/41/",
    "/api/v1/canonical/rfqs/41/lines/?limit=100&ordering=line_number",
  ])
})

test("authentication, permission, lifecycle, and idempotency failures map to deterministic UI states", () => {
  const cases = [
    [
      new CanonicalClientError({
        kind: "authentication",
        code: "authentication_failed",
        message: "private token detail",
      }),
      "authentication_failure",
    ],
    [
      new CanonicalClientError({
        kind: "permission",
        code: "permission_denied",
        message: "private permission detail",
      }),
      "permission_denied",
    ],
    [
      new CanonicalClientError({
        kind: "conflict",
        code: "invalid_state",
        message: "private lifecycle detail",
      }),
      "lifecycle_conflict",
    ],
    [
      new CanonicalClientError({
        kind: "conflict",
        code: "idempotency_conflict",
        message: "private idempotency detail",
      }),
      "idempotency_conflict",
    ],
  ] as const

  for (const [error, status] of cases) {
    const state = commandStateFromError(error)
    assert.equal(state.status, status)
    assert.equal(state.message.includes("private"), false)
  }
})

test("backend field errors are allowlisted and sanitized", () => {
  const state = commandStateFromError(
    new CanonicalClientError({
      kind: "validation",
      code: "invalid",
      message: "raw backend validation detail",
      details: {
        customer_id: ["Customer 11 is inactive"],
        password: ["must never surface"],
      },
    }),
  )

  assert.equal(state.status, "field_validation")
  assert.deepEqual(state.fieldErrors, {
    customer_id: "Giá trị không được máy chủ chấp nhận.",
  })
})

test("retry retention is limited to ambiguous transport and server outcomes", () => {
  assert.equal(
    shouldRetainCreateAttempt(
      new CanonicalClientError({
        kind: "timeout",
        code: "request_timeout",
        message: "x",
      }),
    ),
    true,
  )
  assert.equal(
    shouldRetainCreateAttempt(
      new CanonicalClientError({
        kind: "network",
        code: "network_error",
        message: "x",
      }),
    ),
    true,
  )
  assert.equal(
    shouldRetainCreateAttempt(
      new CanonicalClientError({
        kind: "validation",
        code: "invalid",
        message: "x",
      }),
    ),
    false,
  )
})

test("command gate prevents duplicate submissions while a command is pending", () => {
  const gate = createCommandGate()
  assert.equal(gate.tryStart(), true)
  assert.equal(gate.tryStart(), false)
  assert.equal(gate.isPending(), true)
  gate.finish()
  assert.equal(gate.tryStart(), true)
})

test("latest request guard supports cancellation-safe stale response checks", () => {
  const guard = createLatestRequestGuard()
  const first = guard.next()
  const second = guard.next()
  assert.equal(guard.isLatest(first), false)
  assert.equal(guard.isLatest(second), true)
})

test("selector and workspace requests have independent stale-response generations", () => {
  const guards = createRfqRequestGuards()
  const selectorRequest = guards.selectors.next()
  guards.workspace.next()

  assert.equal(guards.selectors.isLatest(selectorRequest), true)

  const newerSelectorRequest = guards.selectors.next()
  assert.equal(guards.selectors.isLatest(selectorRequest), false)
  assert.equal(guards.selectors.isLatest(newerSelectorRequest), true)
})

test("submitted RFQ lifecycle locks header, line mutations, and submit", () => {
  assert.deepEqual(rfqLifecyclePermissions("SUBMITTED", false), {
    header: false,
    lines: false,
    submit: false,
  })
  assert.deepEqual(rfqLifecyclePermissions("DRAFT", true), {
    header: false,
    lines: false,
    submit: false,
  })
})

test("ambiguous add-line timeout directs reconciliation and never claims safe retry", async () => {
  const api = client(
    async (_input, init) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () =>
          reject(init.signal?.reason),
        )
      }),
  )
  let error: unknown
  try {
    await addRfqLine(
      api,
      rfq.id,
      validateRfqLineCreatePayload({
        description: line.description,
        quantity: line.quantity,
        unit: line.unit,
        required_delivery_date: line.required_delivery_date,
        tolerance: line.tolerance,
        technical_notes: line.technical_notes,
        drawing_required: false,
      }),
    )
  } catch (caught) {
    error = caught
  }
  const state = commandStateFromError(error)
  assert.equal(state.status, "timeout")
  assert.match(state.message, /tải lại trạng thái RFQ trước khi thử lại/)
  assert.doesNotMatch(state.message, /thử lại an toàn/i)
})

test("RFQ workspace source clears session on auth failure and avoids stale reconcile writes", async () => {
  const source = await readFile(
    new URL("../components/RfqWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.match(source, /onAuthenticationFailure\(\)/)
  assert.match(
    source,
    /const \{ selectors: selectorGuard, workspace: workspaceGuard \}/,
  )
  assert.match(
    source,
    /if \(!workspaceGuard\.isLatest\(requestId\)\) return\s+applyReconciledRfq/,
  )
})

test("RFQ workspace disables draft edits outside DRAFT or while pending", async () => {
  const source = await readFile(
    new URL("../components/RfqWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.match(source, /rfqLifecyclePermissions\(/)
  assert.match(source, /disabled=\{!headerEditable\}/)
  assert.match(source, /disabled=\{!editable\}/)
  assert.match(source, /disabled=\{!editable \|\| lines\.length === 0\}/)
})

test("Phase 5C integration replaces the read-only RFQ panel only on sales-quotes", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  const salesQuotesStart = source.indexOf('route === "sales-quotes"')
  const salesAiStart = source.indexOf('route === "sales-ai"')
  const slice = source.slice(salesQuotesStart, salesAiStart)
  assert.match(slice, /<RfqWorkspace/)
  assert.match(slice, /client=\{canonicalClient\}/)
  assert.match(slice, /onAuthenticationFailure=\{onAuthenticationFailure\}/)
  assert.match(
    source,
    /onAuthenticationFailure=\{handleRfqAuthenticationFailure\}/,
  )
  assert.equal(slice.includes("<RfqPanel"), false)
})

test("Phase 5C source adds no token persistence, logging, or unrelated write commands", async () => {
  const files = await Promise.all([
    readFile(new URL("./rfqCommands.ts", import.meta.url), "utf8"),
    readFile(
      new URL("../components/RfqWorkspace.tsx", import.meta.url),
      "utf8",
    ),
  ])
  const source = files.join("\n")
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/console\.(log|warn|error|debug|info)/.test(source), false)
  assert.equal(/password/i.test(source), false)
  assert.equal(
    /quotations\/|orders\/|progress|audit|commands\/approve|commands\/reject/.test(
      source,
    ),
    false,
  )
})
