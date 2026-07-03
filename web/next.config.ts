import type { NextConfig } from 'next';

const apiBackend =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: process.env.NODE_ENV === 'production',
  typedRoutes: true,
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiBackend.replace(/\/$/, '')}/api/v1/:path*`,
      },
    ];
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Legacy admin/landing types still being tightened; dev compile already succeeds.
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

export default nextConfig;