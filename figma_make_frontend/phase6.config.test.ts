import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import {
  DEFAULT_PHASE6_DJANGO_ORIGIN,
  phase6DjangoOrigin,
  phase6ServerConfig,
  phase6VitePort,
} from "./phase6.config.ts"

test("Phase 6A proxies only /api to the default loopback Django origin", () => {
  const config = phase6ServerConfig({})
  assert.equal(config.host, "127.0.0.1")
  assert.equal(config.port, 8443)
  assert.equal(config.strictPort, true)
  assert.deepEqual(Object.keys(config.proxy), ["/api"])
  assert.equal(config.proxy["/api"].target, DEFAULT_PHASE6_DJANGO_ORIGIN)
})

test("Phase 6A accepts explicit alternate local ports consistently", () => {
  assert.equal(
    phase6DjangoOrigin("http://localhost:18000"),
    "http://localhost:18000",
  )
  assert.equal(phase6VitePort("18443"), 18443)
  const config = phase6ServerConfig({
    VITE_DJANGO_ORIGIN: "http://127.0.0.1:18000",
    PHASE6_VITE_PORT: "18443",
  })
  assert.equal(config.proxy["/api"].target, "http://127.0.0.1:18000")
  assert.equal(config.port, 18443)
})

test("Phase 6A rejects malformed, remote, credentialed, and path targets", () => {
  for (const value of [
    "not-a-url",
    "https://127.0.0.1:8000",
    "http://example.com:8000",
    "http://user:password@127.0.0.1:8000",
    "http://127.0.0.1:8000/api",
    "http://127.0.0.1",
    "ftp://127.0.0.1:8000",
  ]) {
    assert.throws(() => phase6DjangoOrigin(value), /loopback HTTP origin/)
  }
  for (const value of ["0", "65536", "12x", "-1"]) {
    assert.throws(() => phase6VitePort(value), /PHASE6_VITE_PORT/)
  }
})

test("browser clients remain root-relative with no mock, legacy, or persistent-token fallback", async () => {
  const canonical = await readFile(
    new URL("./src/api/canonical.ts", import.meta.url),
    "utf8",
  )
  const foundation = await readFile(
    new URL("./src/api/foundation.ts", import.meta.url),
    "utf8",
  )
  assert.match(
    canonical,
    /DEFAULT_CANONICAL_API_BASE_URL = ["']\/api\/v1\/canonical\//,
  )
  assert.match(
    foundation,
    /FOUNDATION_AUTH_BASE_URL = ["']\/api\/v1\/foundation\/auth\//,
  )
  const source = `${canonical}\n${foundation}`
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(
    /mock.*fallback|\/api\/v1\/(?:sales|business|orders)\//i.test(source),
    false,
  )
})

test("Phase 6 launcher builds the current Django source before migrations", async () => {
  const source = await readFile(
    new URL("../scripts/phase6/Start-Phase6.ps1", import.meta.url),
    "utf8",
  )
  const build = source.indexOf(
    '($compose + @("build", "django")) $StartupTimeoutSeconds "django-build"',
  )
  const migrate = source.indexOf(
    '($compose + @("run", "--rm", "django", "python", "manage.py", "migrate", "--noinput"))',
  )
  assert.notEqual(build, -1)
  assert.notEqual(migrate, -1)
  assert.ok(build < migrate)
})
