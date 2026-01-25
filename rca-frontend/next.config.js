/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/rca/:path*',
        destination: 'http://localhost:8000/api/rca/:path*',
      },
    ];
  },
}

module.exports = nextConfig
