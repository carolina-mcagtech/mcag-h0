// apps/web/next.config.mjs
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy via Next.js rewrite so browser requests stay same-origin, avoiding CORS.
  // fallback: only fires when no app/api/** route handler matches — handlers take precedence.
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      fallback: [
        {
          source: '/api/:path*',
          destination: `${apiUrl}/:path*`,
        },
      ],
    }
  },
}

export default nextConfig
