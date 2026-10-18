// Project Author: Samarth Saini
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    PYTHON_SERVICE_URL: process.env.PYTHON_SERVICE_URL || "http://localhost:8000"
  }
};

export default nextConfig;
