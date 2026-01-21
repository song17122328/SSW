<template>
  <div class="status-bar">
    <div class="status-item">
      <el-icon><Connection /></el-icon>
      <span>{{ connectionStatus }}</span>
    </div>
    
    <div class="status-item">
      <el-icon><Clock /></el-icon>
      <span>{{ currentTime }}</span>
    </div>
    
    <!-- 检查 userInfo 是否存在，并显示角色 -->
    <div class="status-item" v-if="userStore.isLoggedIn">
      <el-icon><User /></el-icon>
      <!-- 显示当前用户的角色，例如 '管理员' 或 '普通用户' -->
      <span>当前角色: {{ userStore.userInfo?.role === 'admin' ? '管理员' : '用户' }}</span>
    </div>
    
    <div class="status-item">
      <el-icon><Monitor /></el-icon>
      <span>运行正常</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
// 确保导入了 User 图标
import { Connection, Clock, User, Monitor } from '@element-plus/icons-vue'

const userStore = useUserStore()

const currentTime = ref('')
const connectionStatus = ref('已连接')

let timeInterval = null

function updateTime() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN')
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--background-light);
  border-top: 1px solid var(--border-color);
  font-size: var(--font-size-xs);
  color: var(--text-color-secondary);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.status-item .el-icon {
  font-size: 14px;
}
</style>
