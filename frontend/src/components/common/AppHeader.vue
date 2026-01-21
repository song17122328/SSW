<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="app-title">
        <el-icon><Aim /></el-icon>
        对海作战仿真平台
      </h1>
    </div>
    
    <div class="header-center">
      <!-- 可以在此放置全局状态或通知 -->
    </div>
    
    <div class="header-right">
      <!-- 只有在用户登录后才显示这部分内容 -->
      <template v-if="userStore.isLoggedIn">
        <div class="user-info">
          <el-avatar :size="32">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ userStore.userInfo?.name }}</span>
        </div>

        <!-- 分隔线 -->
        <el-divider direction="vertical" class="header-divider" />

        <!-- 退出登录按钮 -->
        <el-button type="danger" :icon="SwitchButton" link @click="handleLogout">
          退出登录
        </el-button>
      </template>

      <!-- v-else 分支被移除，未登录时此区域为空 -->

    </div>
  </header>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
// 引入所需图标
import { Aim, User, SwitchButton } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()

// 退出登录的处理函数
function handleLogout() {
  ElMessageBox.confirm(
    '您确定要退出登录吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 用户点击了“确定”
    userStore.logout()
  }).catch(() => {
    // 用户点击了“取消”或关闭了对话框
    console.log('取消退出')
  })
}
</script>

<style scoped>
.app-header {
  height: 60px;
  background: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.header-left .app-title {
  display: flex;
  align-items: center;
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin: 0;
}

.header-left .app-title .el-icon {
  margin-right: var(--spacing-sm);
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: default; /* 不再是可点击的，改为默认鼠标样式 */
}

.username {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

/* 自定义分隔线样式以适应深色背景 */
.header-divider {
  height: 24px;
  background-color: rgba(255, 255, 255, 0.3);
  border: none;
}

/* Element Plus 的 link button 默认颜色可能不适合深色背景，我们手动覆盖 */
.el-button.is-link {
  color: white;
}
.el-button.is-link:hover,
.el-button.is-link:focus {
  color: #f5c4c4; /* 鼠标悬停时的颜色，可以自定义 */
}
</style>