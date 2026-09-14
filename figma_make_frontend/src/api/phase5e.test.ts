import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  createCanonicalClient,
} from "./canonical.ts"
import {
  canConvertQuotation,
  canViewGlobalAudit,
  classifyProgressReconciliation,
  convertQuotationToOrder,
  createOrderCommandGate,
  createOrderConversionAttemptManager,
  createOrderRequestGuards,
  executeOrderConversionAttempt,
  fetchAcceptedQuotations,
  fetchGlobalAudit,
  fetchOrderIndex,
  fetchOrderWorkspace,
  globalAuditPath,
  orderCommandStateFromError,
  orderIndexPaths,
  orderLifecyclePermissions,
  orderReadPaths,
  postOrderProgressCommand,
  settleOrderCommandOnDeactivate,
  validateOrderConversionPayload,
  validateOrderProgressPayload,
  wouldDuplicateInProgressEvent,
  type CanonicalAuditEvent,
  type CanonicalOrder,
  type CanonicalOrderLine,
  type CanonicalOrderProgress,
  type OrderProgressAction,
  type OrderProgressPayload,
  type OrderWorkspaceData,
} from "./orderCommands.ts"
import type { CanonicalQuotationSummary } from "./quotationCommands.ts"
import type { CanonicalPage } from "./rfq.ts"

type ConversionRequest = {
  path: string
  method?: string
  body: string
}

type ConversionCall = {
  key: string | null
  body: string
}

type CommandCasePayload = OrderProgressPayload & {
  reason?: string
}

const token = "phase5e-test-token"

const order: CanonicalOrder = {
  id: 501,
  data_contract: "MVP_V1",
  order_number: "SO-2026-0001",
  source_quotation_id: 101,
  source_rfq_id: 41,
  customer_id: 11,
  workflow_status: "CONFIRMED",
  currency: "USD",
  subtotal: "100.0000",
  discount_total: "5.0000",
  tax_amount: "10.0000",
  total_amount: "105.0000",
  ordered_at: "2026-09-14T10:00:00+09:00",
  expected_delivery_date: "2026-10-15",
  progress_percent: 0,
  hold_reason: "",
  cancel_reason: "",
  source_quotation_sent_at: "2026-09-14T08:00:00+09:00",
  completed_at: null,
  created_by_id: 7,
  updated_by_id: 7,
  created_at: "2026-09-14T10:00:00+09:00",
  updated_at: "2026-09-14T10:00:00+09:00",
  compatibility: null,
}

const orderLine: CanonicalOrderLine = {
  id: 601,
  order_id: order.id,
  data_contract: "MVP_V1",
  line_number: 1,
  source_quotation_line_id: 201,
  part_id: 21,
  description_snapshot: "Machined bracket",
  part_code_snapshot: "PART-001",
  material_snapshot: "SUS304",
  quantity: "10.0000",
  unit: "PCS",
  unit_price: "10.0000",
  line_total: "100.0000",
  compatibility: null,
}

const initialProgress: CanonicalOrderProgress = {
  id: 701,
  order_id: order.id,
  from_status: null,
  to_status: "CONFIRMED",
  progress_percent: 0,
  milestone_note: "Converted",
  reason: "",
  actor_id: 7,
  created_at: "2026-09-14T10:00:00+09:00",
}

const audit: CanonicalAuditEvent = {
  id: 801,
  actor_ref: "user:7",
  actor_display: "Sales User",
  action: "order.converted",
  entity_type: "order",
  entity_id: String(order.id),
  old_status: null,
  new_status: "CONFIRMED",
  reason: "",
  metadata: { progress_percent: 0 },
  correlation_id: "00000000-0000-4000-8000-000000000001",
  created_at: "2026-09-14T10:00:00+09:00",
}

const acceptedQuotation: CanonicalQuotationSummary = {
  id: 101,
  data_contract: "MVP_V1",
  quotation_family_number: "QT-2026-0001",
  quotation_number: "QT-2026-0001-R0",
  revision: 0,
  rfq_id: 41,
  customer_id: 11,
  workflow_status: "ACCEPTED",
  currency: "USD",
  valid_from: "2026-09-14",
  valid_until: "2026-09-28",
  subtotal: "100.0000",
  discount_total: "5.0000",
  tax_amount: "10.0000",
  total: "105.0000",
  sent_at: "2026-09-14T08:00:00+09:00",
  created_by_id: 7,
  created_at: "2026-09-14T00:00:00+09:00",
  updated_at: "2026-09-14T09:00:00+09:00",
  compatibility: {},
}

const page = <T>(results: T[]): CanonicalPage<T> => ({
  count: results.length,
  limit: 100,
  offset: 0,
  next_offset: null,
  previous_offset: null,
  results,
})

const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify({ success: true, data }), {
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
    defaultTimeoutMs: 50,
  })
}

const workspace: OrderWorkspaceData = {
  order,
  lines: [orderLine],
  progress: [initialProgress],
  timeline: [audit],
}

function orderWorkspaceFetch(paths: string[], nextOrder = order) {
  return client(async (input) => {
    const path = String(input)
    paths.push(path)
    if (path.endsWith(`/orders/${order.id}/`)) return response(nextOrder)
    if (path.includes("/lines/")) return response(page([orderLine]))
    if (path.includes("/progress/")) return response(page([initialProgress]))
    return response(page([audit]))
  })
}

test("exact canonical Order read paths are bounded", () => {
  assert.deepEqual(orderIndexPaths(), {
    orders: "orders/?data_contract=MVP_V1&limit=20&ordering=-ordered_at",
    acceptedQuotations:
      "quotations/?data_contract=MVP_V1&workflow_status=ACCEPTED&limit=20&ordering=-created_at",
  })
  assert.deepEqual(orderReadPaths(501), {
    detail: "orders/501/",
    lines: "orders/501/lines/?limit=100&ordering=line_number",
    progress: "orders/501/progress/?limit=100&ordering=created_at",
    timeline: "timelines/order/501/?limit=100&ordering=created_at",
  })
})

test("accepted quotation index accepts the backend MVP compatibility null", async () => {
  const result = await fetchAcceptedQuotations(
    client(async () =>
      response(page([{ ...acceptedQuotation, compatibility: null }])),
    ),
  )
  assert.equal(result.results[0]!.workflow_status, "ACCEPTED")
})

test("conversion uses exact endpoint and POST method", async () => {
  let request: ConversionRequest | null = null
  await convertQuotationToOrder(
    client(async (input, init) => {
      request = {
        path: String(input),
        method: init?.method,
        body: String(init?.body),
      }
      return response(order, 201)
    }),
    101,
    {},
    "conversion-key",
  )
  assert.deepEqual(request, {
    path: "/api/v1/canonical/quotations/101/commands/convert-to-order/",
    method: "POST",
    body: "{}",
  })
})

test("conversion payload strictly allows only the empty backend serializer", () => {
  assert.deepEqual(validateOrderConversionPayload({}), {})
  assert.throws(() => validateOrderConversionPayload({ customer_id: 9 }), {
    code: "client_validation_error",
  })
})

test("conversion attempt retains the exact target, payload, and opaque key", async () => {
  const manager = createOrderConversionAttemptManager(() => "retained-key")
  const calls: ConversionCall[] = []
  const api = client(async (_input, init) => {
    calls.push({
      key: new Headers(init?.headers).get("idempotency-key"),
      body: String(init?.body),
    })
    throw new CanonicalClientError({
      kind: "network",
      code: "network_error",
      message: "private",
    })
  })
  await assert.rejects(
    executeOrderConversionAttempt(
      api,
      manager,
      { quotationId: 101, familyNumber: "QT-2026-0001" },
      {},
      async () => workspace,
    ),
  )
  assert.deepEqual(manager.activeTarget(), {
    quotationId: 101,
    familyNumber: "QT-2026-0001",
  })
  assert.deepEqual(manager.activePayload(), {})
  assert.deepEqual(calls, [{ key: "retained-key", body: "{}" }])
})

test("same logical conversion retry reuses its key", async () => {
  const manager = createOrderConversionAttemptManager(() => "same-key")
  const keys: Array<string | null> = []
  let calls = 0
  const api = client(async (_input, init) => {
    calls += 1
    keys.push(new Headers(init?.headers).get("idempotency-key"))
    if (calls === 1) {
      throw new CanonicalClientError({
        kind: "timeout",
        code: "request_timeout",
        message: "private",
      })
    }
    return response(order)
  })
  const target = { quotationId: 101, familyNumber: "QT-2026-0001" }
  await assert.rejects(
    executeOrderConversionAttempt(
      api,
      manager,
      target,
      {},
      async () => workspace,
    ),
  )
  await executeOrderConversionAttempt(
    api,
    manager,
    { quotationId: 999, familyNumber: "changed" },
    {},
    async () => workspace,
  )
  assert.deepEqual(keys, ["same-key", "same-key"])
})

test("known Order identity prevents duplicate conversion POST", async () => {
  const manager = createOrderConversionAttemptManager(() => "known-order-key")
  let posts = 0
  let reconciles = 0
  const api = client(async () => {
    posts += 1
    return response(order)
  })
  const reconcile = async () => {
    reconciles += 1
    if (reconciles === 1) {
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_reconcile",
        message: "private",
      })
    }
    return workspace
  }
  const target = { quotationId: 101, familyNumber: "QT-2026-0001" }
  await assert.rejects(
    executeOrderConversionAttempt(api, manager, target, {}, reconcile),
  )
  assert.equal(manager.hasCreatedOrder(), true)
  await executeOrderConversionAttempt(api, manager, target, {}, reconcile)
  assert.equal(posts, 1)
  assert.equal(reconciles, 2)
})

test("conversion reconciliation uses canonical Order reads", async () => {
  const paths: string[] = []
  const result = await fetchOrderWorkspace(orderWorkspaceFetch(paths), order.id)
  assert.equal(result.order.id, order.id)
  assert.equal(paths.length, 4)
  assert.deepEqual(paths.slice(1).sort(), [
    "/api/v1/canonical/orders/501/lines/?limit=100&ordering=line_number",
    "/api/v1/canonical/orders/501/progress/?limit=100&ordering=created_at",
    "/api/v1/canonical/timelines/order/501/?limit=100&ordering=created_at",
  ])
})

test("active conversion attempt locks retained quotation selection", () => {
  const manager = createOrderConversionAttemptManager(() => "active-key")
  manager.begin({ quotationId: 101, familyNumber: "QT-2026-0001" }, {})
  assert.equal(manager.hasActiveAttempt(), true)
  assert.equal(canConvertQuotation("Sales", "ACCEPTED", true), false)
})

test("progress, hold, resume, complete, and cancel use exact endpoints", async () => {
  const paths: string[] = []
  const api = client(async (input) => {
    paths.push(String(input))
    return response(order)
  })
  const cases: Array<[OrderProgressAction, CommandCasePayload]> = [
    ["progress", { progress_percent: 10 }],
    ["hold", { progress_percent: 10, reason: "Wait" }],
    ["resume", { progress_percent: 10 }],
    ["complete", { progress_percent: 100 }],
    ["cancel", { progress_percent: 10, reason: "Stop" }],
  ]
  for (const [action, payload] of cases) {
    await postOrderProgressCommand(api, order.id, action, payload)
  }
  assert.deepEqual(
    paths,
    cases.map(([action]) => `/api/v1/canonical/orders/501/commands/${action}/`),
  )
})

test("removed start-progress alias is never constructed", async () => {
  const source = await readFile(
    new URL("./orderCommands.ts", import.meta.url),
    "utf8",
  )
  assert.equal(source.includes("start-progress"), false)
})

test("progress payload rejects unknown and protected fields", () => {
  assert.throws(
    () =>
      validateOrderProgressPayload(
        { progress_percent: 10, workflow_status: "COMPLETED" },
        "progress",
      ),
    { code: "client_validation_error" },
  )
})

test("progress percentage must be an integer from zero through 100", () => {
  for (const value of [-1, 101, 1.5, true, "10"]) {
    assert.throws(
      () =>
        validateOrderProgressPayload({ progress_percent: value }, "progress"),
      { code: "client_validation_error" },
    )
  }
  assert.deepEqual(
    validateOrderProgressPayload({ progress_percent: 0 }, "progress"),
    { progress_percent: 0 },
  )
})

test("complete accepts exactly 100 percent", () => {
  assert.deepEqual(validateOrderProgressPayload({}, "complete"), {
    progress_percent: 100,
  })
  assert.throws(
    () => validateOrderProgressPayload({ progress_percent: 99 }, "complete"),
    { code: "client_validation_error" },
  )
})

test("hold and cancel require a non-empty reason", () => {
  for (const action of ["hold", "cancel"] as const) {
    assert.throws(
      () => validateOrderProgressPayload({ progress_percent: 10 }, action),
      { code: "client_validation_error" },
    )
  }
})

test("progress commands never send an idempotency key", async () => {
  let key: string | null = "unexpected"
  await postOrderProgressCommand(
    client(async (_input, init) => {
      key = new Headers(init?.headers).get("idempotency-key")
      return response(order)
    }),
    order.id,
    "progress",
    { progress_percent: 10 },
  )
  assert.equal(key, null)
})

test("ambiguous progress failure is not blindly retried", async () => {
  let posts = 0
  await assert.rejects(
    postOrderProgressCommand(
      client(async () => {
        posts += 1
        throw new TypeError("network")
      }),
      order.id,
      "progress",
      { progress_percent: 10 },
    ),
  )
  assert.equal(posts, 1)
})

test("ambiguous progress reconciliation proves an applied transition", () => {
  const payload = { progress_percent: 25, milestone_note: "First cut" }
  const event: CanonicalOrderProgress = {
    ...initialProgress,
    id: 702,
    from_status: "CONFIRMED",
    to_status: "IN_PROGRESS",
    progress_percent: 25,
    milestone_note: "First cut",
  }
  const after: OrderWorkspaceData = {
    ...workspace,
    order: {
      ...order,
      workflow_status: "IN_PROGRESS",
      progress_percent: 25,
    },
    progress: [initialProgress, event],
  }
  assert.equal(
    classifyProgressReconciliation(workspace, after, "progress", payload),
    "applied",
  )
})

test("progress reconciliation rejects coincident but non-matching evidence", () => {
  const authoritativeOrder = {
    ...order,
    workflow_status: "ON_HOLD" as const,
    progress_percent: 20,
  }
  const expectedPayload = {
    progress_percent: 20,
    milestone_note: "Awaiting material",
    reason: "Supplier delay",
  }
  const matchingShape: CanonicalOrderProgress = {
    ...initialProgress,
    id: 702,
    order_id: order.id,
    from_status: "CONFIRMED",
    to_status: "ON_HOLD",
    progress_percent: 20,
    milestone_note: expectedPayload.milestone_note,
    reason: expectedPayload.reason,
  }

  for (const coincidentEvent of [
    { ...matchingShape, order_id: 999 },
    { ...matchingShape, from_status: "IN_PROGRESS" as const },
    { ...matchingShape, milestone_note: "Different evidence" },
    { ...matchingShape, reason: "Different reason" },
  ]) {
    assert.equal(
      classifyProgressReconciliation(
        workspace,
        {
          ...workspace,
          order: authoritativeOrder,
          progress: [initialProgress, coincidentEvent],
        },
        "hold",
        expectedPayload,
      ),
      "ambiguous",
    )
  }
})

test("ambiguous progress reconciliation distinguishes non-applied and unknown", () => {
  assert.equal(
    classifyProgressReconciliation(workspace, workspace, "progress", {
      progress_percent: 20,
    }),
    "not_applied",
  )
  const changed = {
    ...workspace,
    order: { ...order, progress_percent: 5 },
  }
  assert.equal(
    classifyProgressReconciliation(workspace, changed, "progress", {
      progress_percent: 20,
    }),
    "ambiguous",
  )
})

test("duplicate IN_PROGRESS evidence is prevented", () => {
  const inProgress = {
    ...order,
    workflow_status: "IN_PROGRESS" as const,
    progress_percent: 25,
  }
  assert.equal(
    wouldDuplicateInProgressEvent(inProgress, "progress", {
      progress_percent: 25,
    }),
    true,
  )
  assert.equal(
    wouldDuplicateInProgressEvent(inProgress, "resume", {
      progress_percent: 25,
    }),
    false,
  )
})

test("lifecycle visibility matches every backend-supported state", () => {
  assert.deepEqual(orderLifecyclePermissions("Manager", "CONFIRMED", false), {
    progress: true,
    hold: true,
    resume: false,
    complete: false,
    cancel: true,
  })
  assert.deepEqual(orderLifecyclePermissions("Admin", "IN_PROGRESS", false), {
    progress: true,
    hold: true,
    resume: false,
    complete: true,
    cancel: true,
  })
  assert.equal(
    orderLifecyclePermissions("Manager", "ON_HOLD", false).resume,
    true,
  )
  assert.equal(
    orderLifecyclePermissions("Manager", "COMPLETED", false).cancel,
    false,
  )
  assert.equal(
    orderLifecyclePermissions("Manager", "CANCELLED", false).progress,
    false,
  )
})

test("Admin and Manager controls exclude Sales and unrelated roles", () => {
  assert.equal(
    orderLifecyclePermissions("Admin", "CONFIRMED", false).progress,
    true,
  )
  assert.equal(
    orderLifecyclePermissions("Manager", "CONFIRMED", false).progress,
    true,
  )
  assert.equal(
    orderLifecyclePermissions("Sales", "CONFIRMED", false).progress,
    false,
  )
  assert.equal(
    orderLifecyclePermissions("Reviewer", "CONFIRMED", false).progress,
    false,
  )
})

test("entity-scoped Order timeline is read through its canonical path", async () => {
  const paths: string[] = []
  await fetchOrderWorkspace(orderWorkspaceFetch(paths), order.id)
  assert.equal(
    paths.includes(
      "/api/v1/canonical/timelines/order/501/?limit=100&ordering=created_at",
    ),
    true,
  )
})

test("global audit read is role-gated to Admin and Manager", () => {
  assert.equal(canViewGlobalAudit("Admin"), true)
  assert.equal(canViewGlobalAudit("Manager"), true)
  assert.equal(canViewGlobalAudit("Sales"), false)
})

test("Sales receives a global-audit denial presentation without a request", async () => {
  const source = await readFile(
    new URL("../components/OrderWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.match(source, /if \(!globalAuditAllowed\)/)
  assert.match(source, /Global audit chỉ dành cho Admin hoặc Manager/)
})

test("audit UI is append-only and exposes no mutation transport", async () => {
  const source = await readFile(
    new URL("../components/OrderWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.equal(/createAudit|updateAudit|deleteAudit/.test(source), false)
  assert.equal(/event\.metadata|correlation_id/.test(source), false)
})

test("global audit pagination remains bounded", async () => {
  assert.equal(
    globalAuditPath(20),
    "audit-events/?limit=20&offset=20&ordering=-created_at",
  )
  let path = ""
  await fetchGlobalAudit(
    client(async (input) => {
      path = String(input)
      return response(page([audit]))
    }),
    20,
  )
  assert.match(path, /limit=20&offset=20/)
})

test("independent request guards suppress stale responses", () => {
  const guards = createOrderRequestGuards()
  const index = guards.index.next()
  const conversion = guards.conversion.next()
  const workspaceRequest = guards.workspace.next()
  const auditRequest = guards.audit.next()
  guards.workspace.next()
  assert.equal(guards.index.isLatest(index), true)
  assert.equal(guards.conversion.isLatest(conversion), true)
  assert.equal(guards.workspace.isLatest(workspaceRequest), false)
  assert.equal(guards.audit.isLatest(auditRequest), true)
})

test("Order navigation requests honor cancellation", async () => {
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(
    fetchOrderIndex(
      client(async () => response(page([]))),
      controller.signal,
    ),
    { code: "request_cancelled" },
  )
})

test("command gate prevents overlapping progress commands", () => {
  const gate = createOrderCommandGate()
  assert.equal(gate.tryStart(), true)
  assert.equal(gate.tryStart(), false)
  gate.finish()
  assert.equal(gate.tryStart(), true)
})

test("permission, lifecycle, network, and server errors are sanitized", () => {
  const cases = [
    new CanonicalClientError({
      kind: "permission",
      code: "denied",
      message: "secret",
    }),
    new CanonicalClientError({
      kind: "conflict",
      code: "invalid_state",
      message: "secret",
    }),
    new CanonicalClientError({
      kind: "network",
      code: "network",
      message: "secret",
    }),
    new CanonicalClientError({
      kind: "server",
      code: "server",
      message: "secret",
    }),
  ]
  for (const error of cases) {
    assert.equal(
      orderCommandStateFromError(error).message.includes("secret"),
      false,
    )
  }
})

test("Phase 5E source uses no legacy Order or workflow API", async () => {
  const source = await readFile(
    new URL("./orderCommands.ts", import.meta.url),
    "utf8",
  )
  assert.equal(/\/api\/v1\/(?:orders|admin\/orders)/.test(source), false)
  assert.equal(source.includes("start-progress"), false)
})

test("Phase 5E contains no mock Order, progress, or audit business data", async () => {
  const source = await readFile(
    new URL("../components/OrderWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.equal(/SO-DEMO|mockOrder|mockProgress|mockAudit/.test(source), false)
})

test("Phase 5E persists, renders, and logs no token or idempotency key", async () => {
  const sources = await Promise.all([
    readFile(new URL("./orderCommands.ts", import.meta.url), "utf8"),
    readFile(
      new URL("../components/OrderWorkspace.tsx", import.meta.url),
      "utf8",
    ),
  ])
  const source = sources.join("\n")
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/console\.(log|warn|error|debug|info)/.test(source), false)
  assert.equal(
    /attempt\.key|active.*key|idempotencyKey\}/.test(sources[1]),
    false,
  )
})

test("Phase 5A through 5D regression scripts remain in the full suite", async () => {
  const packageSource = JSON.parse(
    await readFile(new URL("../../package.json", import.meta.url), "utf8"),
  ) as { scripts: Record<string, string> }
  for (const name of [
    "canonical.test.ts",
    "phase5b.test.ts",
    "phase5c.test.ts",
    "phase5d.test.ts",
    "phase5e.test.ts",
  ]) {
    assert.match(
      packageSource.scripts.test,
      new RegExp(name.replace(".", "\\.")),
    )
  }
})

test("RFQ, quotation, and Order workspaces stay mounted across tab navigation", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  const start = source.indexOf('route === "sales-quotes"')
  const end = source.indexOf('route === "sales-ai"')
  const slice = source.slice(start, end)
  assert.match(slice, /<RfqWorkspace/)
  assert.match(slice, /<QuotationWorkspace/)
  assert.match(slice, /<OrderWorkspace/)
  assert.match(slice, /active=\{quoteWorkspace === "order"\}/)
})

test("tab deactivation releases pending presentation without changing settled state", () => {
  const pending = { status: "pending" as const, message: "pending" }
  assert.equal(settleOrderCommandOnDeactivate(pending).status, "cancelled")
  assert.equal(
    settleOrderCommandOnDeactivate(pending, true).status,
    "ambiguous",
  )
  const ready = { status: "ready" as const, message: "ready" }
  assert.equal(settleOrderCommandOnDeactivate(ready), ready)
})
