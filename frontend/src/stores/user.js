// user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import router from '@/router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSystemStore } from './system' // <--- 导入 system store
export const useUserStore = defineStore('user', () => {
  // --- State ---
  // authenticatedUsers 将存储所有已通过验证的用户信息
  const authenticatedUsers = ref({}); // e.g., { user: {..}, admin: {..} }
  const currentRole = ref(null); // 'user' or 'admin'

  // --- 持久化相关的常量 ---
  const STORAGE_KEYS = {
    AUTHENTICATED_USERS: 'military-sim-authenticated-users',
    CURRENT_ROLE: 'military-sim-current-role'
  };

  // --- 持久化工具函数 ---
  const saveToStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEYS.AUTHENTICATED_USERS, JSON.stringify(authenticatedUsers.value));
      localStorage.setItem(STORAGE_KEYS.CURRENT_ROLE, currentRole.value || '');
    } catch (error) {
      console.error('保存到 localStorage 失败:', error);
    }
  };

  const loadFromStorage = () => {
    try {
      const savedUsers = localStorage.getItem(STORAGE_KEYS.AUTHENTICATED_USERS);
      const savedRole = localStorage.getItem(STORAGE_KEYS.CURRENT_ROLE);

      if (savedUsers) {
        authenticatedUsers.value = JSON.parse(savedUsers);
      }

      if (savedRole && savedRole !== '') {
        currentRole.value = savedRole;
      }
    } catch (error) {
      console.error('从 localStorage 加载失败:', error);
      clearStorage(); // 如果数据损坏，清理存储
    }
  };

  const clearStorage = () => {
    try {
      localStorage.removeItem(STORAGE_KEYS.AUTHENTICATED_USERS);
      localStorage.removeItem(STORAGE_KEYS.CURRENT_ROLE);
    } catch (error) {
      console.error('清理 localStorage 失败:', error);
    }
  };

  // --- Getters ---
  const isLoggedIn = computed(() => currentRole.value !== null);
  const isAdmin = computed(() => currentRole.value === 'admin');

  // ** 核心 Getter: 返回当前激活的用户信息 **
  const userInfo = computed(() => {
    return isLoggedIn.value ? authenticatedUsers.value[currentRole.value] : null;
  });

  // --- Actions ---

  // 初始化函数 - 从 localStorage 加载数据
  const initialize = () => {
    loadFromStorage();
  };

  // 原始登录
  async function login(username, password) {
    try {
      const userData = await api.login(username, password);
      const userProfile = {
        id: userData.id,
        name: userData.username,
        role: userData.role
      };
      // 登录后，清空之前的身份，只保留当前登录的
      authenticatedUsers.value = { [userData.role]: userProfile };
      currentRole.value = userData.role;

      // 保存到 localStorage
      saveToStorage();

      await router.push({ name: 'Dashboard' });
      return true;
    } catch (error) {
      console.error("登录失败:", error);
      return false;
    }
  }



  // 登出
  async function logout() {
    const systemStore = useSystemStore() // <--- 获取 system store 实例

    try {
      await api.logout();
    } finally {
      authenticatedUsers.value = {};
      currentRole.value = null;

      // 清理 localStorage
      clearStorage();

      // *** 新增：调用 system store 的重置函数 ***
      systemStore.resetUptime();

      await router.push({ name: 'Login' });
    }
  }

  // 检查会话状态
  async function checkLoginStatus() {
    try {
      const sessionData = await api.checkSession();
      if (sessionData.isLoggedIn) {
        const user = sessionData.userInfo;
        authenticatedUsers.value = { [user.role]: user };
        currentRole.value = user.role;

        // 保存到 localStorage
        saveToStorage();
      } else {
        // 如果服务端会话失效，清理本地存储
        authenticatedUsers.value = {};
        currentRole.value = null;
        clearStorage();
      }
    } catch (error) {
      console.error("检查会话状态失败:", error);
      // 网络错误时，可以考虑保留本地存储的用户信息
      // 或者根据业务需求决定是否清理
    }
  }

  // 验证本地存储的用户信息是否仍然有效
  async function validateStoredSession() {
    if (!isLoggedIn.value) return false;

    try {
      const sessionData = await api.checkSession();
      if (!sessionData.isLoggedIn) {
        // 服务端会话失效，清理本地存储
        authenticatedUsers.value = {};
        currentRole.value = null;
        clearStorage();
        return false;
      }
      return true;
    } catch (error) {
      console.error("验证存储会话失败:", error);
      return false;
    }
  }
  // 新增一个手动重置状态的函数
  function reset() {
    authenticatedUsers.value = {};
    currentRole.value = null;
  }

  return {
    userInfo,
    isLoggedIn,
    currentRole,
    isAdmin,
    initialize,
    login,
    logout,
    checkLoginStatus,
    validateStoredSession,
    reset, // <--- 导出这个新函数
  }
})
