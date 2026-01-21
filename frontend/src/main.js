// main.js

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import '@/assets/styles/index.css'
import { useUserStore } from './stores/user'

async function startApp() {
  console.log('🚀 对海作战仿真平台正在启动...');

  const app = createApp(App);

  // --- 全局错误处理 ---
  const IGNORED_ERRORS = [
    'ResizeObserver loop completed with undelivered notifications',
    'ResizeObserver loop limit exceeded' // *** 核心修复：在这里添加新的错误信息 ***
  ];

  app.config.errorHandler = (err, instance, info) => {
    // 检查错误信息是否在我们想要忽略的列表中
    if (IGNORED_ERRORS.some(msg => err.message.includes(msg))) {
      return false; // 忽略错误，不打印到控制台
    }
    console.error('Vue an error:', err, instance, info);
  };

  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && event.reason.message && IGNORED_ERRORS.some(msg => event.reason.message.includes(msg))) {
      event.preventDefault(); // 阻止默认的控制台错误输出
    }
  });
  // --- 错误处理结束 ---

  // 注册图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }

  // 安装 Pinia
  const pinia = createPinia();
  app.use(pinia);

  // 获取 userStore
  const userStore = useUserStore();

  // 使用 await 等待会话检查完成
  try {
    await userStore.checkLoginStatus();
  } catch (error) {
    console.error("会话检查失败，将以未登录状态启动:", error);
  }

  // 在所有异步操作完成后，再安装路由和 Element Plus
  app.use(router);
  app.use(ElementPlus);

  // 等待路由准备就绪
  await router.isReady();

  // 最后挂载应用
  app.mount('#app');

  console.log('⚔️ 前端应用启动完成!');
}

startApp();