/** @type {import('next').NextConfig} */
const nextConfig = {
  // Emits .next/standalone with a self-contained server.js and only the
  // node_modules actually reached at runtime. Keeps the runtime image small
  // and means the production stage never installs dependencies.
  //
  // Vercel ignores this (it builds its own output); it is kept because the
  // self-hosted stack in DEPLOY.md builds the image from this same config.
  output: "standalone",

  // On Lightsail, Caddy sets the security headers (see Caddyfile). Vercel has
  // no Caddy, so the ones that can be set from the app are set here.
  //
  // The Caddyfile's Content-Security-Policy is deliberately NOT reproduced:
  // it pins `connect-src 'self'`, which was correct only while the frontend
  // and the API shared one origin. In the split deployment the browser calls
  // the API on a different origin, so a copied CSP would block the quiz at
  // runtime. Reproducing it correctly means interpolating
  // NEXT_PUBLIC_API_BASE_URL into the directive — a worthwhile follow-up, but
  // not something to guess at. See DEPLOY-RAILWAY-VERCEL.md.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          // Matches the Caddyfile: 30 days, no includeSubDomains, no preload.
          { key: "Strict-Transport-Security", value: "max-age=2592000" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "geolocation=(), microphone=(), camera=(), payment=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
