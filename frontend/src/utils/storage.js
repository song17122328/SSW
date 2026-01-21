/**
 * 💾 本地存储工具
 */

const STORAGE_PREFIX = 'naval_combat_'

export function setStorage(key, value) {
  try {
    const data = JSON.stringify(value)
    localStorage.setItem(STORAGE_PREFIX + key, data)
  } catch (error) {
    console.error('❌ 存储失败:', error)
  }
}

export function getStorage(key, defaultValue = null) {
  try {
    const data = localStorage.getItem(STORAGE_PREFIX + key)
    return data ? JSON.parse(data) : defaultValue
  } catch (error) {
    console.error('❌ 读取存储失败:', error)
    return defaultValue
  }
}

export const userPreferences = {
  get theme() {
    return getStorage('theme', 'military')
  },
  
  set theme(value) {
    setStorage('theme', value)
  },
  
  get role() {
    return getStorage('current_role', 'user')
  },
  
  set role(value) {
    setStorage('current_role', value)
  }
}
