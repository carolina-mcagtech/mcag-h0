// apps/web/next.config.mjs
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy via Next.js rewrite so browser requests stay same-origin, avoiding CORS in development.
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ]
  },
}

export default nextConfig
