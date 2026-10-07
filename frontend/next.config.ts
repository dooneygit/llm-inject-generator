import type { NextConfig } from "next";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Generation can take well over the default 30s proxy timeout (LLM timeout + retries).
  experimental: {
    proxyTimeout: 120_000,
  },
  // Proxy to the FastAPI backend so the browser stays same-origin (no CORS needed).
  rewrites: async () => [
    { source: "/api/:path*", destination: `${API_URL}/:path*` },
  ],
};

export default nextConfig;
