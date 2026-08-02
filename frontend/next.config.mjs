/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls to the FastAPI backend during development so the browser
  // talks to one origin (no CORS surprises). Override with NEXT_PUBLIC_API_BASE.
  async rewrites() {
    const base = process.env.API_PROXY_TARGET || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${base}/:path*` }];
  },
};

export default nextConfig;
