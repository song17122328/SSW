<!-- App.vue -->
<template>
  <div id="app" class="military-theme">
    <!-- 干净布局，用于登录/注册页 -->
    <router-view v-if="route.meta.layout === 'clean'" />

    <!-- 默认的主应用布局 -->
    <template v-else>
      <AppHeader />
      <div class="app-container">
        <AppSidebar v-if="userStore.isLoggedIn" />
        <main class="main-content" :class="{ 'full-width': !userStore.isLoggedIn }">
          
          <!-- *** 核心修复：为 keep-alive 添加 exclude，并为 component 添加 key *** -->
          <router-view v-slot="{ Component, route }">
            <!-- 
              核心修复：将注释移到 keep-alive 外部。
              使用 route.fullPath 作为 key，可以确保当 URL 变化时
              (即使是同一个组件，如 /contracts/detail/5 -> /contracts/detail/6)，
              Vue 也会将其视为不同的实例，从而强制重新渲染。
              这对于详情页至关重要。
            -->
            <keep-alive :exclude="['ContractDetail', 'PlatformDetail', 'EquipmentDetail', 'ScenarioDetail']">
              <component :is="Component" :key="route.fullPath" />
            </keep-alive>
          </router-view>

        </main>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import { onMounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const systemStore = useSystemStore()
const userStore = useUserStore()

onMounted(() => {
  systemStore.initialize() 
  userStore.initialize()
  console.log('⚔️ 对海作战仿真平台启动成功!')
})
</script>


<style>
/* 你的样式保持不变 */
.app-container {
  display: flex;
  height: calc(100vh - 60px);
}

</style>