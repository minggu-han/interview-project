// 前端入口：创建 Vue 应用，挂载 Pinia(状态管理) 与 Vue Router(路由)，渲染到 index.html 的 #app
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(createPinia()).use(router).mount('#app')
