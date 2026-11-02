import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: {
    // 本機 5173–5180 已被其他專案占用；strictPort 讓衝突時直接報錯，而不是默默換 port
    port: 5290,
    strictPort: true,
    // 透過 proxy 轉給後端，前後端同源，後端就不需要設定 CORS
    proxy: {
      '/api': 'http://127.0.0.1:8010',
    },
  },
})
