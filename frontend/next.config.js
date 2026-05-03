/** @type {import('next').NextConfig} */
const backendUrl = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

const nextConfig = {
  output: "standalone",
  experimental: {
    proxyTimeout: 300_000, // 5 min for long ML requests.
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
