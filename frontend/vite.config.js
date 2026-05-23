import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? "/DB_project/" : "/",
  plugins: [vue()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
