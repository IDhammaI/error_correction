import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/download': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
  // 开发模式用 /，构建时才加 /static/vue/ 前缀给 Flask 托管
  base: command === 'build' ? '/static/vue/' : '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    manifest: false,
    // 新增多页面入口配置
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'), // 你的酷炫落地页
        app: resolve(__dirname, 'app.html')     // 真正的 Vue 工作台
      }
    }
  },
}))