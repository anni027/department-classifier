/** @type {import('next').NextConfig} */
const nextConfig = {
  // Emits .next/standalone with a self-contained server.js and only the
  // node_modules actually reached at runtime. Keeps the runtime image small
  // and means the production stage never installs dependencies.
  output: "standalone",
};

export default nextConfig;
