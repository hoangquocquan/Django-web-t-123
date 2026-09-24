export const DEFAULT_PHASE6_DJANGO_ORIGIN = "http://127.0.0.1:8000"
export const DEFAULT_PHASE6_VITE_PORT = 8443

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"])

export function phase6DjangoOrigin(
  configured = process.env.VITE_DJANGO_ORIGIN,
): string {
  const value = configured?.trim() || DEFAULT_PHASE6_DJANGO_ORIGIN
  let url: URL
  try {
    url = new URL(value)
  } catch {
    throw new Error("VITE_DJANGO_ORIGIN must be a loopback HTTP origin.")
  }
  if (
    url.protocol !== "http:" ||
    !LOOPBACK_HOSTS.has(url.hostname === "::1" ? "[::1]" : url.hostname) ||
    !url.port ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      "VITE_DJANGO_ORIGIN must be a loopback HTTP origin with an explicit port.",
    )
  }
  return url.origin
}

export function phase6VitePort(
  configured = process.env.PHASE6_VITE_PORT,
): number {
  const value = configured?.trim() || String(DEFAULT_PHASE6_VITE_PORT)
  if (!/^\d+$/.test(value))
    throw new Error("PHASE6_VITE_PORT must be an integer port.")
  const port = Number(value)
  if (!Number.isSafeInteger(port) || port < 1 || port > 65535) {
    throw new Error("PHASE6_VITE_PORT must be between 1 and 65535.")
  }
  return port
}

export function phase6ServerConfig(env = process.env) {
  return {
    host: "127.0.0.1",
    port: phase6VitePort(env.PHASE6_VITE_PORT),
    strictPort: true,
    proxy: {
      "/api": {
        target: phase6DjangoOrigin(env.VITE_DJANGO_ORIGIN),
        changeOrigin: false,
      },
    },
  } as const
}
