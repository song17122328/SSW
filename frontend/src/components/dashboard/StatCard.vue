<!-- src/components/dashboard/StatCard.vue -->
<template>
  <div class="stat-card" :style="{ '--card-color': color }">
    <div class="stat-icon"><el-icon><component :is="icon" /></el-icon></div>
    <div class="stat-content">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ title }}</div>
    </div>
  </div>
</template>
<script setup>
defineProps({
  icon: String,
  title: String,
  value: [Number, String],
  color: String
})
</script>
<style scoped>
.stat-card { background: #fff; border-radius: 12px; padding: 24px; display: flex; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stat-icon { font-size: 32px; color: #fff; background-color: var(--card-color); width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 16px; }
.stat-value { font-size: 28px; font-weight: bold; color: #2c3e50; }
.stat-label { font-size: 14px; color: #7f8c8d; }
</style>