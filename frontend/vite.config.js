
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  // GitHub Pages deployment base path
  base: "/account-statement-generator/",

  // Local development server configuration
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Production build configuration
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
