const backendUrl = (
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.NODE_ENV === 'production'
    ? 'https://jansahayak-ai-qyjd.onrender.com'
    : 'http://localhost:8000')
).replace(/\/+$/, '');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/voice/:path*',
        destination: `${backendUrl}/api/voice/:path*`,
      },
    ];
  },
};

export default nextConfig;
