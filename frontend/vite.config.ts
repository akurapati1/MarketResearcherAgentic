import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { "/api": { target: process.env.API_URL ?? "http://localhost:8000", changeOrigin: true } } },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes("node_modules")) {
            if (/recharts|d3-|victory/.test(id)) return "charts";
            if (/react-markdown|remark|micromark|mdast|unified|hast|vfile/.test(id)) return "markdown";
            if (/react|scheduler|tanstack/.test(id)) return "vendor";
          }
        },
      },
    },
  },
});
