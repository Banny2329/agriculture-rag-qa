import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发环境代理：/api 与 /health 转发到 FastAPI 后端
// timeout: 0 = 不设代理超时。上传+OCR 建档耗时较长，若走默认超时会被代理层掐断，前端误报 Network Error
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, timeout: 0 },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true, timeout: 0 },
    },
  },
})
