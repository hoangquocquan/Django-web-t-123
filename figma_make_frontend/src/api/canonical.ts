export const DEFAULT_CANONICAL_API_BASE_URL = "/api/v1/canonical/"
export const DEFAULT_REQUEST_TIMEOUT_MS = 10_000
export const MAX_REQUEST_TIMEOUT_MS = 30_000

export type CanonicalSuccessEnvelope<T,> = {
  success: true
  data: T
}

export type CanonicalErrorEnvelope = {
  success: false
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export type CanonicalErrorKind = "authentication" | "permission" | "validation" | "conflict" | "not_found" | "timeout" | "cancelled" | "network" | "server" | "protocol"

export class CanonicalClientError extends Error {
  readonly kind: CanonicalErrorKind
  readonly code: string
  readonly status: number | null
  readonly details?: unknown

  constructor(options: {
    kind: CanonicalErrorKind
    code: string
    message: string
    status?: number | null
    details?: unknown
  }) {
    super(options.message)
    this.name = "CanonicalClientError"
    this.kind = options.kind
    this.code = options.code
    this.status = options.status ?? null
    this.details = options.details
  }
}

export interface AuthSession {
  getAccessToken(): string | null
}

export class InMemoryAuthSession implements AuthSession {
  #accessToken: string | null = null

  setAccessToken(accessToken: string): void {
    this.#accessToken = validateAccessToken(accessToken)
  }

  clear(): void {
    this.#accessToken = null
  }

  getAccessToken(): string | null {
    return this.#accessToken
  }
}

export function canonicalApiBaseUrl(
  configured = import.meta.env.VITE_CANONICAL_API_BASE_URL,
): string {
  const value = configured?.trim() || DEFAULT_CANONICAL_API_BASE_URL
  if (/[\s\\]/.test(value) || value.startsWith("//") || /[?#]/.test(value)) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_canonical_base_url",
      message: "The API base URL must target the canonical API namespace.",
    })
  }

  if (/^https?:\/\//i.test(value)) {
    let url: URL
    try {
      url = new URL(value)
    } catch {
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_canonical_base_url",
        message: "The API base URL must target the canonical API namespace.",
      })
    }

    const pathname = url.pathname.replace(/\/+$/, "")
    if (url.username || url.password || pathname !== "/api/v1/canonical") {
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_canonical_base_url",
        message: "The API base URL must target the canonical API namespace.",
      })
    }
    url.pathname = "/api/v1/canonical/"
    return url.toString()
  }

  const normalized = value.replace(/\/+$/, "")
  if (normalized !== "/api/v1/canonical") {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_canonical_base_url",
      message: "The API base URL must target the canonical API namespace.",
    })
  }
  return `${normalized}/`
}

export type CanonicalRequestOptions = Omit<RequestInit, "signal"> & {
  signal?: AbortSignal
  timeoutMs?: number
}

export type CanonicalClientOptions = {
  baseUrl: string
  auth: AuthSession
  fetch?: typeof fetch
  defaultTimeoutMs?: number
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isSuccessEnvelope<T>(
  value: unknown,
): value is CanonicalSuccessEnvelope<T> {
  return isRecord(value) && value.success === true && "data" in value
}

function isErrorEnvelope(value: unknown): value is CanonicalErrorEnvelope {
  if (!isRecord(value) || value.success !== false || !isRecord(value.error)) {
    return false
  }
  return (
    typeof value.error.code === "string" &&
    value.error.code.trim().length > 0 &&
    typeof value.error.message === "string" &&
    value.error.message.trim().length > 0
  )
}

function errorKind(status: number): CanonicalErrorKind {
  if (status === 401) return "authentication"
  if (status === 403) return "permission"
  if (status === 404) return "not_found"
  if (status === 409) return "conflict"
  if (status === 400) return "validation"
  return "server"
}

function requestUrl(baseUrl: string, path: string): string {
  const normalizedPath = path.trim()
  const pathOnly = normalizedPath.split("?", 1)[0]
  if (
    !normalizedPath ||
    normalizedPath.startsWith("/") ||
    normalizedPath.includes("\\") ||
    normalizedPath.includes("#") ||
    /[\u0000-\u001f\u007f]/.test(normalizedPath) ||
    /^[a-z][a-z\d+.-]*:/i.test(normalizedPath) ||
    hasUnsafePathSegment(pathOnly)
  ) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_canonical_path",
      message: "A relative canonical API path is required.",
    })
  }
  return `${baseUrl.replace(/\/+$/, "")}/${normalizedPath}`
}

function hasUnsafePathSegment(path: string): boolean {
  if (!path || path.includes("//") || /%(2f|5c)/i.test(path)) return true

  const decodedPaths = [path]
  let decoded = path
  for (let index = 0; index < 3; index += 1) {
    try {
      const next = decodeURIComponent(decoded)
      if (next === decoded) break
      decoded = next
      decodedPaths.push(decoded)
    } catch {
      return true
    }
  }

  return decodedPaths.some(
    (candidate) =>
      candidate.includes("\\") ||
      candidate
        .split("/")
        .some((segment) => segment === "." || segment === ".."),
  )
}

function validateAccessToken(accessToken: unknown): string {
  if (
    typeof accessToken !== "string" ||
    accessToken.length === 0 ||
    accessToken.trim() !== accessToken ||
    !/^[A-Za-z0-9\-._~+/]+=*$/.test(accessToken)
  ) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_access_token",
      message: "The access token is invalid.",
    })
  }
  return accessToken
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

async function responsePayload(response: Response): Promise<unknown> {
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

export function createCanonicalClient(options: CanonicalClientOptions) {
  const fetchImplementation = options.fetch ?? globalThis.fetch
  const defaultTimeoutMs = boundedTimeout(
    options.defaultTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
  )
  const baseUrl = canonicalApiBaseUrl(options.baseUrl)

  return {
    async request<T,>(
      path: string,
      requestOptions: CanonicalRequestOptions = {},
    ): Promise<T> {
      const timeoutMs = boundedTimeout(
        requestOptions.timeoutMs ?? defaultTimeoutMs,
      )
      const url = requestUrl(baseUrl, path)
      const {
        signal: externalSignal,
        timeoutMs: _timeoutMs,
        headers: requestHeaders,
        ...fetchOptions
      } = requestOptions
      let headers: Headers
      try {
        headers = new Headers(requestHeaders)
        headers.delete("authorization")
        const accessToken = options.auth.getAccessToken()
        if (accessToken !== null) {
          headers.set(
            "authorization",
            `Bearer ${validateAccessToken(accessToken)}`,
          )
        }
      } catch (error) {
        if (error instanceof CanonicalClientError) throw error
        throw new CanonicalClientError({
          kind: "protocol",
          code: "invalid_request_headers",
          message: "The request headers are invalid.",
        })
      }

      if (externalSignal?.aborted) {
        throw new CanonicalClientError({
          kind: "cancelled",
          code: "request_cancelled",
          message: "The request was cancelled.",
        })
      }

      const controller = new AbortController()
      let abortKind: "cancelled" | "timeout" | null = null
      let timeout: ReturnType<typeof setTimeout> | null = null
      const abortWith = (kind: "cancelled" | "timeout") => {
        if (abortKind === null) abortKind = kind
        controller.abort()
      }
      const cancelFromCaller = () => abortWith("cancelled")

      externalSignal?.addEventListener("abort", cancelFromCaller, {
        once: true,
      })

      try {
        const aborted = new Promise<never>((_resolve, reject) => {
          controller.signal.addEventListener(
            "abort",
            () =>
              reject(
                new CanonicalClientError({
                  kind: abortKind === "timeout" ? "timeout" : "cancelled",
                  code:
                    abortKind === "timeout"
                      ? "request_timeout"
                      : "request_cancelled",
                  message:
                    abortKind === "timeout"
                      ? "The request timed out."
                      : "The request was cancelled.",
                }),
              ),
            { once: true },
          )
        })
        timeout = setTimeout(() => abortWith("timeout"), timeoutMs)
        const response = await Promise.race([
          fetchImplementation(url, {
            ...fetchOptions,
            headers,
            signal: controller.signal,
          }),
          aborted,
        ])
        const payload = await responsePayload(response)

        if (response.ok && isSuccessEnvelope<T>(payload)) return payload.data

        if (!response.ok && isErrorEnvelope(payload)) {
          throw new CanonicalClientError({
            kind: errorKind(response.status),
            code: payload.error.code,
            message: payload.error.message,
            status: response.status,
            details: payload.error.details,
          })
        }

        throw new CanonicalClientError({
          kind: "protocol",
          code: "invalid_response_envelope",
          message: "The server returned an invalid response envelope.",
          status: response.status,
        })
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
    },
  }
}
