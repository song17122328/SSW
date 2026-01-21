// src/stores/system.js - 支持持久化运行时长

import { defineStore } from 'pinia'
import { ref } from 'vue'

// 将 sessionStorage 的 key 定义为常量，便于管理
const UPTIME_START_KEY = 'system_uptime_start';

export const useSystemStore = defineStore('system', () => {
  // --- State ---
  const systemInfo = ref({
    name: '对海作战仿真平台',
    version: '1.0.0',
  })

  const uptime = ref('...') // 初始显示...
  let uptimeInterval = null

  // --- Actions ---

  function formatUptime(totalSeconds) {
    // ... (这个函数保持不变)
    totalSeconds = Math.floor(totalSeconds);
    const days = Math.floor(totalSeconds / (3600 * 24));
    totalSeconds %= (3600 * 24);
    const hours = Math.floor(totalSeconds / 3600);
    totalSeconds %= 3600;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const pad = (num) => String(num).padStart(2, '0');
    let result = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    if (days > 0) {
      result = `${days}天 ${result}`;
    }
    return result;
  }

  // 更新计时器的核心函数
  function updateTimer() {
    // 从 sessionStorage 读取启动时间
    const startTime = parseInt(sessionStorage.getItem(UPTIME_START_KEY), 10);
    if (!startTime) return; // 如果没有启动时间，则不执行

    const now = Date.now();
    const elapsedSeconds = (now - startTime) / 1000;
    uptime.value = formatUptime(elapsedSeconds);
  }


  // 初始化函数
  function initialize() {
    if (uptimeInterval) {
      clearInterval(uptimeInterval);
    }

    // 1. 检查 sessionStorage 中是否已有启动时间
    let startTime = sessionStorage.getItem(UPTIME_START_KEY);

    if (!startTime) {
      // 2. 如果没有，说明是新的会话，记录当前时间
      startTime = Date.now();
      sessionStorage.setItem(UPTIME_START_KEY, startTime);
      console.log('New session started. Uptime timer initialized.');
    } else {
      console.log('Existing session found. Resuming uptime timer.');
    }

    // 3. 立即执行一次，并启动每秒的定时器
    updateTimer();
    uptimeInterval = setInterval(updateTimer, 1000);
  }

  // 这个函数应该在用户登出时被调用
  function resetUptime() {
    sessionStorage.removeItem(UPTIME_START_KEY);
    if (uptimeInterval) {
      clearInterval(uptimeInterval);
      uptimeInterval = null;
    }
    uptime.value = '00:00:00';
    console.log('Uptime timer has been reset.');
  }

  return {
    systemInfo,
    uptime,
    initialize,
    resetUptime // 导出重置函数
  }
})