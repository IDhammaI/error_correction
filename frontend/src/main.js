import { createApp } from 'vue'
import '@/style.css'
import App from '@/App.vue'
import router from '@/router/index.js'

// 创建 Vue 应用实例，注册全局路由后挂载到 app.html 中的 #app 节点。
createApp(App).use(router).mount('#app')
