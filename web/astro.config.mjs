// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  // Absolute origin for canonical + OpenGraph URLs (production deploy on Vercel).
  // Update here if the site moves to a custom domain.
  site: 'https://tw-cycling-data.vercel.app',
  integrations: [react()],

  vite: {
    plugins: [tailwindcss()],
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes("node_modules/echarts") || id.includes("node_modules/echarts-for-react")) {
              return "echarts";
            }
          },
        },
      },
    },
  }
});