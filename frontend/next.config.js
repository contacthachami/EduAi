/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    proxyTimeout: 300_000, // 5 min — les embeddings ML sont longs
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
