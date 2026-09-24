import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

const componentUrls = [
  new URL("../components/RfqWorkspace.tsx", import.meta.url),
  new URL("../components/QuotationWorkspace.tsx", import.meta.url),
  new URL("../components/OrderWorkspace.tsx", import.meta.url),
]

async function readCanonicalSources() {
  const [app, rfq, quotation, order, browserRunner] = await Promise.all([
    readFile(new URL("../App.tsx", import.meta.url), "utf8"),
    readFile(componentUrls[0], "utf8"),
    readFile(componentUrls[1], "utf8"),
    readFile(componentUrls[2], "utf8"),
    readFile(
      new URL("../../../tests/e2e/phase6c_owner_uat.py", import.meta.url),
      "utf8",
    ),
  ])
  return { app, rfq, quotation, order, browserRunner }
}

test("canonical async feedback is announced without exposing raw errors", async () => {
  const { app, rfq, quotation, order } = await readCanonicalSources()
  assert.match(app, /aria-live="assertive"[\s\S]*role="alert"/)
  for (const source of [rfq, quotation, order]) {
    assert.match(source, /aria-live="polite"[\s\S]*role="status"/)
    assert.match(source, /role="alert"/)
    assert.doesNotMatch(source, /console\.(?:log|error)|raw.*exception/i)
  }
})

test("quotation and order form controls have stable accessible names", async () => {
  const { quotation, order } = await readCanonicalSources()
  for (const [name, source] of [
    ["quotation", quotation],
    ["order", order],
  ] as const) {
    const controls =
      source.match(/<(?:input|select|textarea)\b[\s\S]*?>/g) ?? []
    assert.ok(controls.length > 0, `${name} controls were not found`)
    for (const control of controls) {
      assert.match(
        control,
        /aria-label=/,
        `${name} control lacks an accessible name`,
      )
    }
  }
})

test("canonical controls expose visible keyboard focus and RFQ selection is a button", async () => {
  const { app, rfq, quotation, order } = await readCanonicalSources()
  for (const source of [app, rfq, quotation, order]) {
    assert.match(source, /focus-visible:ring-2/)
  }
  assert.match(rfq, /<button[\s\S]{0,300}onClick=\{\(\) => openRfq\(rfq\)\}/)
  assert.doesNotMatch(rfq, /<tr[\s\S]{0,220}onClick=\{\(\) => openRfq/)
  assert.match(app, /aria-pressed=\{quoteWorkspace === "rfq"\}/)
  assert.match(app, /aria-pressed=\{quoteWorkspace === "quotation"\}/)
  assert.match(app, /aria-pressed=\{quoteWorkspace === "order"\}/)
})

test("Phase 6C browser UAT covers accessibility, session, role, and responsive boundaries", async () => {
  const { browserRunner } = await readCanonicalSources()
  assert.match(browserRunner, /audit_accessible_names/)
  assert.match(browserRunner, /assert_keyboard_focus_visible/)
  assert.match(browserRunner, /assert_responsive_layout/)
  assert.match(browserRunner, /driver\.refresh\(\)/)
  assert.match(browserRunner, /driver\.back\(\)/)
  assert.match(browserRunner, /driver\.forward\(\)/)
  assert.match(browserRunner, /Sales-only authoring control/)
  assert.match(browserRunner, /Manager-only review control/)
})

test("Phase 6C retains memory-only auth and canonical write boundaries", async () => {
  const { app, rfq, quotation, order, browserRunner } =
    await readCanonicalSources()
  const source = [app, rfq, quotation, order, browserRunner].join("\n")
  assert.doesNotMatch(
    source,
    /localStorage|sessionStorage|indexedDB|document\.cookie/,
  )
  assert.doesNotMatch(source, /\/api\/v1\/(?!canonical\/|foundation\/)/)
})
