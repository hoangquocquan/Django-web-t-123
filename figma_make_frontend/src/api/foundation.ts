import {
  CanonicalClientError,
  InMemoryAuthSession,
  MAX_REQUEST_TIMEOUT_MS,
  canonicalApiBaseUrl,
} from "./canonical.ts"

const FOUNDATION_AUTH_BASE_URL = "/api/v1/foundation/auth/"
const DEFAULT_FOUNDATION_TIMEOUT_MS = 10_000

function viteEnvValue(name: string): string | undefined {
  return (import.meta as { env?: Record<string, string | undefined> }).env?.[
    name
  ]
}

export type FoundationUser = {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
}

export type FoundationLoginResult = {
  expires_at: string
  user: FoundationUser
}

type FoundationSuccessEnvelope<T,> = {
  success: true
  data: T
}

type FoundationErrorEnvelope = {
  success: false
  error: {
    code: string
    message: string
    details?: unknown
  }
}

type FoundationLoginEnvelope = FoundationSuccessEnvelope<FoundationLoginResult & {
  token: string
}>

export type FoundationAuthClientOptions = {
  auth: InMemoryAuthSession
  baseUrl?: string
  fetch?: typeof fetch
  defaultTimeoutMs?: number
}

export type FoundationLoginCredentials = {
  email: string
  password: string
}

export type FoundationRequestOptions = {
  signal?: AbortSignal
  timeoutMs?: number
}

function boundedTimeout(timeoutMs: number): number {
  if (
    !Number.isFinite(timeoutMs) ||
    timeoutMs <= 0 ||
    timeoutMs > MAX_REQUEST_TIMEOUT_MS
  ) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_timeout",
      message: `Request timeout must be between 1 and ${MAX_REQUEST_TIMEOUT_MS} milliseconds.`,
    })
  }
  return timeoutMs
}

function validateApiNamespaceBaseUrl(
  value: string,
  namespacePath: string,
  errorCode: string,
): string {
  const trimmed = value.trim()
  if (
    /[\s\\]/.test(trimmed) ||
    trimmed.startsWith("//") ||
    /[?#]/.test(trimmed)
  ) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: errorCode,
      message: "The API base URL must target the expected API namespace.",
    })
  }

  const normalizedNamespace = namespacePath.replace(/\/+$/, "")

  if (/^https?:\/\//i.test(trimmed)) {
    let url: URL
    try {
      url = new URL(trimmed)
    } catch {
      throw new CanonicalClientError({
        kind: "protocol",
        code: errorCode,
        message: "The API base URL must target the expected API namespace.",
      })
    }

    const pathname = url.pathname.replace(/\/+$/, "")
    if (url.username || url.password || pathname !== normalizedNamespace) {
      throw new CanonicalClientError({
        kind: "protocol",
        code: errorCode,
        message: "The API base URL must target the expected API namespace.",
      })
    }
    url.pathname = `${normalizedNamespace}/`
    return url.toString()
  }

  const normalized = trimmed.replace(/\/+$/, "")
  if (normalized !== normalizedNamespace) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: errorCode,
      message: "The API base URL must target the expected API namespace.",
    })
  }
  return `${normalized}/`
}

function baseUrlFromApiRoot(
  apiRoot: string | undefined,
  namespacePath: string,
  errorCode: string,
): string | null {
  const trimmed = apiRoot?.trim()
  if (!trimmed) return null
  if (
    /[\s\\]/.test(trimmed) ||
    trimmed.startsWith("//") ||
    /[?#]/.test(trimmed)
  ) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: errorCode,
      message:
        "The API root URL must be an origin with an optional path prefix.",
    })
  }
  if (/^https?:\/\//i.test(trimmed)) {
    let url: URL
    try {
      url = new URL(trimmed)
    } catch {
      throw new CanonicalClientError({
        kind: "protocol",
        code: errorCode,
        message:
          "The API root URL must be an origin with an optional path prefix.",
      })
    }
    if (url.username || url.password) {
      throw new CanonicalClientError({
        kind: "protocol",
        code: errorCode,
        message:
          "The API root URL must be an origin with an optional path prefix.",
      })
    }
    url.pathname = `${url.pathname.replace(/\/+$/, "")}${namespacePath}/`
    return url.toString()
  }
  return validateApiNamespaceBaseUrl(
    `${trimmed.replace(/\/+$/, "")}${namespacePath}/`,
    namespacePath,
    errorCode,
  )
}

export function foundationAuthBaseUrl(
  configured = viteEnvValue("VITE_FOUNDATION_AUTH_BASE_URL"),
  apiRoot = viteEnvValue("VITE_API_BASE_URL"),
): string {
  return (
    (configured?.trim()
      ? validateApiNamespaceBaseUrl(
          configured,
          "/api/v1/foundation/auth",
          "invalid_foundation_auth_base_url",
        )
      : baseUrlFromApiRoot(
          apiRoot,
          "/api/v1/foundation/auth",
          "invalid_foundation_auth_base_url",
        )) ?? FOUNDATION_AUTH_BASE_URL
  )
}

export function canonicalBaseUrlForPhase5b(
  configured = viteEnvValue("VITE_CANONICAL_API_BASE_URL"),
  apiRoot = viteEnvValue("VITE_API_BASE_URL"),
): string {
  const fromApiRoot = baseUrlFromApiRoot(
    apiRoot,
    "/api/v1/canonical",
    "invalid_canonical_base_url",
  )
  if (configured?.trim()) return canonicalApiBaseUrl(configured)
  if (fromApiRoot) return canonicalApiBaseUrl(fromApiRoot)
  return "/api/v1/canonical/"
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isFoundationErrorEnvelope(
  value: unknown,
): value is FoundationErrorEnvelope {
  return (
    isRecord(value) &&
    value.success === false &&
    isRecord(value.error) &&
    typeof value.error.code === "string" &&
    value.error.code.trim().length > 0 &&
    typeof value.error.message === "string" &&
    value.error.message.trim().length > 0
  )
}

function isFoundationLoginEnvelope(
  value: unknown,
): value is FoundationLoginEnvelope {
  return (
    isRecord(value) &&
    value.success === true &&
    isRecord(value.data) &&
    typeof value.data.token === "string" &&
    typeof value.data.expires_at === "string" &&
    isRecord(value.data.user) &&
    typeof value.data.user.id === "number" &&
    typeof value.data.user.email === "string" &&
    typeof value.data.user.full_name === "string" &&
    typeof value.data.user.role === "string" &&
    typeof value.data.user.is_active === "boolean"
  )
}

function isLogoutEnvelope(
  value: unknown,
): value is FoundationSuccessEnvelope<{ logged_out: true }> {
  return (
    isRecord(value) &&
    value.success === true &&
    isRecord(value.data) &&
    value.data.logged_out === true
  )
}

function errorKind(status: number) {
  if (status === 401) return "authentication"
  if (status === 403) return "permission"
  if (status === 400) return "validation"
  return "server"
}

function loginValidationError() {
  return new CanonicalClientError({
    kind: "validation",
    code: "login_validation_failed",
    message: "Email and password are required.",
  })
}

async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_response_envelope",
      message: "The server returned an invalid response envelope.",
      status: response.status,
    })
  }
}

function lifecycleError(kind: "cancelled" | "timeout") {
  return new CanonicalClientError({
    kind,
    code: kind === "timeout" ? "request_timeout" : "request_cancelled",
    message:
      kind === "timeout"
        ? "The request timed out."
        : "The request was cancelled.",
  })
}

async function boundedFetch(
  fetchImplementation: typeof fetch,
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController()
  let abortKind: "cancelled" | "timeout" | null = null
  const externalSignal = init.signal

  if (externalSignal?.aborted) throw lifecycleError("cancelled")

  const abortWith = (kind: "cancelled" | "timeout") => {
    if (abortKind === null) abortKind = kind
    controller.abort()
  }
  const cancelFromCaller = () => abortWith("cancelled")
  externalSignal?.addEventListener("abort", cancelFromCaller, { once: true })

  let timeout: ReturnType<typeof setTimeout> | null = null
  try {
    const aborted = new Promise<never>((_resolve, reject) => {
      controller.signal.addEventListener(
        "abort",
        () =>
          reject(
            lifecycleError(abortKind === "timeout" ? "timeout" : "cancelled"),
          ),
        { once: true },
      )
    })
    timeout = setTimeout(() => abortWith("timeout"), timeoutMs)
    return await Promise.race([
      fetchImplementation(url, { ...init, signal: controller.signal }),
      aborted,
    ])
  } catch (error) {
    if (error instanceof CanonicalClientError) throw error
    throw new CanonicalClientError({
      kind: "network",
      code: "network_error",
      message: "The server could not be reached.",
    })
  } finally {
    if (timeout !== null) clearTimeout(timeout)
    externalSignal?.removeEventListener("abort", cancelFromCaller)
  }
}

export function createFoundationAuthClient(
  options: FoundationAuthClientOptions,
) {
  const fetchImplementation = options.fetch ?? globalThis.fetch
  const defaultTimeoutMs = boundedTimeout(
    options.defaultTimeoutMs ?? DEFAULT_FOUNDATION_TIMEOUT_MS,
  )
  const baseUrl = foundationAuthBaseUrl(options.baseUrl)

  return {
    async login(
      credentials: FoundationLoginCredentials,
      requestOptions: FoundationRequestOptions = {},
    ): Promise<FoundationLoginResult> {
      const email = credentials.email.trim()
      if (!email || !credentials.password) throw loginValidationError()

      const response = await boundedFetch(
        fetchImplementation,
        `${baseUrl}login/`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ email, password: credentials.password }),
          signal: requestOptions.signal,
        },
        boundedTimeout(requestOptions.timeoutMs ?? defaultTimeoutMs),
      )
      const payload = await parseJson(response)

      if (response.ok && isFoundationLoginEnvelope(payload)) {
        options.auth.setAccessToken(payload.data.token)
        return {
          expires_at: payload.data.expires_at,
          user: payload.data.user,
        }
      }

      if (!response.ok && isFoundationErrorEnvelope(payload)) {
        throw new CanonicalClientError({
          kind: errorKind(response.status),
          code: payload.error.code,
          message:
            response.status === 400
              ? "Login request validation failed."
              : "Login was rejected.",
          status: response.status,
        })
      }

      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_response_envelope",
        message: "The server returned an invalid response envelope.",
        status: response.status,
      })
    },

    async logout(
      accessToken: string,
      requestOptions: FoundationRequestOptions = {},
    ): Promise<void> {
      const response = await boundedFetch(
        fetchImplementation,
        `${baseUrl}logout/`,
        {
          method: "POST",
          headers: { authorization: `Bearer ${accessToken}` },
          signal: requestOptions.signal,
        },
        boundedTimeout(requestOptions.timeoutMs ?? defaultTimeoutMs),
      )
      const payload = await parseJson(response)
      if (response.ok && isLogoutEnvelope(payload)) return
      if (!response.ok && isFoundationErrorEnvelope(payload)) {
        throw new CanonicalClientError({
          kind: errorKind(response.status),
          code: payload.error.code,
          message: "Logout request was rejected.",
          status: response.status,
        })
      }
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_response_envelope",
        message: "The server returned an invalid response envelope.",
        status: response.status,
      })
    },
  }
}
