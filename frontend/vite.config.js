import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 开发服务器配置：前端跑在 5173，把 /api 与 /ws 请求代理到后端 8002，规避跨域
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8002', changeOrigin: true }, // 普通 HTTP 接口
      '/ws': { target: 'ws://localhost:8002', ws: true },              // WebSocket（实时答题，需 ws:true）
    },
  },
})
