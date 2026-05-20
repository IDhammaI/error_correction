import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  // 让 @ 指向 src，简化前端模块导入路径。
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  plugins: [
    vue(),
    // 开发环境下将前端 history 路由重写到 app.html，避免刷新 /auth 或 /app 页面时 404。
    {
      name: 'spa-html-rewrite',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const url = req.url?.split('?')[0]
          if (url === '/' || url === '/auth' || url === '/auth/login' || url === '/auth/register' || url === '/app' || url?.startsWith('/app/')) {
            req.url = '/app.html'
          }
          next()
        })
      },
    },
  ],
  // Vitest 在 jsdom 中运行，方便测试依赖 window/document 的前端逻辑。
  test: {
    environment: 'jsdom',
  },
  server: {
    host: '127.0.0.1',
    // 开发环境接口代理：前端保持相对路径请求，由 Vite 转发到 Flask API 服务。
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
      '/erased': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
  // 生产资源从站点根路径加载；若部署到子目录，需要同步调整该值。
  base: '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    manifest: false,
    // 项目使用 app.html 作为 Vue SPA 入口，而不是 Vite 默认的 index.html。
    rollupOptions: {
      input: {
        app: resolve(__dirname, 'app.html'),
      },
    },
  },
})
