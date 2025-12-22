/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // Backend is running on port 8001 in this environment.
        destination: 'http://localhost:8001/:path*',
      },
    ];
  },
};

export default nextConfig;
