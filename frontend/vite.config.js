import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the React app (port 5173) forwards /api and /media to Django (port 8000),
// so the browser sees one origin and there are no CORS problems.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
    },
  },
});
