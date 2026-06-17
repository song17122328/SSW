// index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', layout: 'clean' } // <--- 添加 layout 标志
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', layout: 'clean' } // <--- 添加 layout 标志
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘', icon: 'Dashboard', roles: ['user', 'admin'] }
  },
  // --- 资源管理路由 (保持不变) ---
  {
    path: '/equipment',
    name: 'EquipmentParent',
    meta: { title: '资源管理', icon: 'Box', roles: ['user', 'admin'] },
    children: [
      {
        path: 'platforms',
        name: 'PlatformList',
        component: () => import('@/views/Equipment/PlatformList.vue'),
        meta: { title: '平台列表', roles: ['user', 'admin'] }
      },
      // *** 新增平台详情路由 ***
      {
        // 关键：使用正则表达式 \\d+ 确保 id 是数字
        path: 'platforms/:id(\\d+)',
        name: 'PlatformDetail',
        component: () => import('@/views/Equipment/PlatformDetail.vue'),
        meta: {
          title: '平台详情',
          roles: ['user', 'admin'],
          hidden: true // 在侧边栏菜单中隐藏此项
        },
        // 将路由参数 :id 作为 props 传递给组件，这是最佳实践
        props: true
      },
      {
        path: 'list',
        name: 'EquipmentList',
        component: () => import('@/views/Equipment/EquipmentList.vue'),
        meta: { title: '装备列表', roles: ['user', 'admin'] }
      },
      {
        // 新的装备详情
        path: 'items/:id(\\d+)',
        name: 'EquipmentDetail',
        component: () => import('@/views/Equipment/EquipmentDetail.vue'), // 指向新的详情组件
        meta: { title: '装备详情', roles: ['user', 'admin'], hidden: true },
        props: true
      }
    ]
  },
  // --- 合同管理路由 (*** 在这里修改 ***) ---
  {
    path: '/contracts',
    name: 'ContractParent',
    meta: { title: '合同管理', icon: 'Document', roles: ['user', 'admin'] },
    children: [
      {
        path: 'create',
        name: 'ContractCreate',
        component: () => import('@/views/Contract/ContractCreate.vue'),
        // ** a) 普通用户可见，管理员不可见 **
        meta: { title: '合同创建', roles: ['user'] }
      },
      {
        path: 'list',
        name: 'ContractList',
        component: () => import('@/views/Contract/ContractList.vue'),
        // ** a) 管理员可见，普通用户不可见 **
        meta: { title: '合同列表', roles: ['admin'] }
      },
      {
        path: 'my-applications',
        name: 'MyApplications',
        component: () => import('@/views/Contract/MyApplications.vue'),
        // ** a) 普通用户可见，管理员不可见 **
        // 将其重命名为“我的申请”以符合您的要求
        meta: { title: '我的申请', roles: ['user'] }
      },
      {
        path: 'pending',
        name: 'PendingContracts',
        component: () => import('@/views/Contract/PendingContracts.vue'),
        // ** a) 管理员可见，普通用户不可见 **
        meta: { title: '待审批合同', roles: ['admin'] }
      },
      {
        path: 'detail/:id',
        name: 'ContractDetail',
        component: () => import('@/views/Contract/ContractDetail.vue'),
        // ** 详情页对两者都可见，但通常在菜单中隐藏 **
        meta: { title: '合同详情', roles: ['user', 'admin'], hidden: true },
        props: true
      },
      {
        path: 'rl-monitor',
        name: 'RLJobMonitor',
        component: () => import('@/views/Contract/RLJobMonitor.vue'),
        // ** 假设 RL 监控对两者都可见 **
        meta: { title: 'RL任务监控', roles: ['user', 'admin'] }
      }
      // 移除 contract-templates 路由，因为它似乎没有被使用
    ]
  },
  // --- 作战仿真路由 (保持不变) ---
  {
    path: '/combat',
    name: 'Combat',
    redirect: '/combat/simulation',
    meta: { title: '作战仿真', icon: 'Aim', roles: [] },
    children: [
      {
        path: 'simulation',
        name: 'CombatSimulation',
        component: () => import('@/views/Combat/CombatSimulation.vue'),
        meta: { title: '作战仿真', roles: ['user', 'admin'] }
      },
      {
        path: 'history',
        name: 'CombatHistory',
        component: () => import('@/views/Combat/CombatHistory.vue'),
        meta: { title: '作战历史', roles: ['user', 'admin'] }
      }
    ]
  },
  // ** 新增：作战想定管理路由 **
  {
    path: '/simulation',
    name: 'SimulationParent',
    meta: { title: '作战想定', icon: 'Opportunity', roles: ['user', 'admin'] },
    children: [
      {
        path: 'list',
        name: 'ScenarioList',
        component: () => import('@/views/Simulation/ScenarioList.vue'),
        meta: { title: '想定列表', roles: ['user', 'admin'] }
      },
      {
        path: 'detail/:id',
        name: 'ScenarioDetail',
        component: () => import('@/views/Simulation/ScenarioDetail.vue'),
        meta: { title: '想定详情', roles: ['user', 'admin'], hidden: true }, // 在菜单中隐藏
        props: true
      }
    ]
  },



  // --- 系统管理路由 (保持不变) ---
  {
    path: '/system',
    name: 'System',
    redirect: '/system/settings',
    meta: { title: '系统管理', icon: 'Setting', roles: [] },
    children: [
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/System/Settings.vue'),
        meta: { title: '系统设置', roles: ['admin'] }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/System/Logs.vue'),
        meta: { title: '系统日志', roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
// --- 全局路由守卫 (增加防环检查) ---



// --- 全局路由守卫 (最终修复版) ---
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  userStore.initialize()

  const isLoggedIn = userStore.isLoggedIn
  const isPublicPage = ['Login', 'Register'].includes(to.name)

  // 场景 1: 用户已登录 (isLoggedIn is true)
  if (isLoggedIn) {
    // 关键点: 如果是从登录页跳转过来的，我们信任这次登录，直接放行，不进行会话验证。
    // 这避免了登录成功后立即验证而可能失败的问题。
    if (from.name === 'Login') {
      return next()
    }

    // 对于其他情况（如刷新页面），需要验证会话
    const isSessionValid = await userStore.validateStoredSession();
    if (!isSessionValid) {
      console.log('🛡️ 本地会话已失效，强制登出并重定向到 /login');
      userStore.reset(); // 使用我们自己实现的 reset 方法
      clearStorage(); // 调用你 store 里的 clearStorage 更好
      return next({ name: 'Login', query: { redirect: to.fullPath } });
    }

    if (isPublicPage) {
      // 已登录用户还想去登录页，送回首页
      next({ name: 'Dashboard' })
    } else {
      // 检查权限
      const userRole = userStore.currentRole
      if (to.meta.roles && !to.meta.roles.includes(userRole)) {
        console.warn(`❌ 用户权限不足，重定向到 Dashboard`)
        next({ name: 'Dashboard' })
      } else {
        next() // 权限足够，放行
      }
    }
  }
  // 场景 2: 用户未登录 (isLoggedIn is false)
  else {
    if (isPublicPage) {
      next() // 未登录访问公共页面，放行
    } else {
      console.log(`🛡️ 用户未登录，访问受限页面 ${to.fullPath}。重定向到 /login`)
      next({ name: 'Login', query: { redirect: to.fullPath } })
    }
  }
})

// 在你的 userStore 中，确保有一个 clearStorage 的导出
// 如果没有，可以简单地用 localStorage.clear() 替代
function clearStorage() {
  localStorage.removeItem('military-sim-authenticated-users');
  localStorage.removeItem('military-sim-current-role');
}


export default router
