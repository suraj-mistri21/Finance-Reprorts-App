import { reactRouter } from "@react-router/dev/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 3000,
    strictPort: true,
    cors: true,

    watch: {
      ignored: [
        "**/backend/*.csv",
        "**/backend/page_*.json",
        "**/backend/*.json",
      ],
    },
  },

  resolve: {
    // IMPORTANT:
    // Force Vite/SSR to use the same React instance everywhere.
    dedupe: [
      "react",
      "react-dom",
      "react-router",
    ],
  },

  plugins: [
    reactRouter(),
    tsconfigPaths(),
    tailwindcss(),
  ],

  optimizeDeps: {
    force: true,
  },

  build: {
    assetsInlineLimit: 0,
  },
});