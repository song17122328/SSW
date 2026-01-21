/**
 * 📦 装备状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'


export const useEquipmentStore = defineStore('equipment', () => {
  const equipmentList = ref([])
  const loading = ref(false)
  const currentEquipment = ref(null)
  const total = ref(0)

  const filters = ref({
    category: 'all',
    type: 'all',
    status: 'all',
    search: ''
  })

  const pagination = ref({
    page: 1,
    pageSize: 20
  })

  const filteredEquipment = computed(() => {
    let result = equipmentList.value

    if (filters.value.category !== 'all') {
      result = result.filter(item => item.category === filters.value.category)
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(item =>
        item.name.toLowerCase().includes(search)
      )
    }

    return result
  })

  const equipmentStats = computed(() => ({
    total: equipmentList.value.length,
    active: equipmentList.value.filter(item => item.status === 'active').length,
    inactive: equipmentList.value.filter(item => item.status === 'inactive').length
  }))

  async function fetchEquipment() {
    try {
      loading.value = true
      // 使用 api.js 中已有的 getPlatforms 函数
      const responseData = await api.getPlatforms()
      equipmentList.value = responseData || []
      total.value = responseData ? responseData.length : 0
      console.log(`✅ 加载装备数据: ${equipmentList.value.length} 项`)
    } catch (error) {
      console.error('❌ 获取装备列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // --- 处理缺失的 API 函数 ---
  // 这些函数直接在 store 内部实现模拟行为，因为 api.js 中没有它们
  async function createNewEquipment(equipmentData) {
    console.warn("Action: createNewEquipment 未连接后端API，使用模拟数据");
    const newEquipment = { id: Date.now(), ...equipmentData };
    equipmentList.value.unshift(newEquipment);
    return Promise.resolve(newEquipment);
  }

  async function updateExistingEquipment(id, equipmentData) {
    console.warn("Action: updateExistingEquipment 未连接后端API，使用模拟数据");
    const index = equipmentList.value.findIndex(item => item.id === id);
    if (index !== -1) {
      equipmentList.value[index] = { ...equipmentList.value[index], ...equipmentData };
      return Promise.resolve(equipmentList.value[index]);
    }
    return Promise.reject(new Error("Equipment not found"));
  }

  async function removeEquipment(id) {
    console.warn("Action: removeEquipment 未连接后端API，使用模拟数据");
    equipmentList.value = equipmentList.value.filter(item => item.id !== id);
    return Promise.resolve();
  }

  function setFilter(key, value) {
    filters.value[key] = value
    pagination.value.page = 1
  }

  function setPage(page) {
    pagination.value.page = page
  }

  return {
    equipmentList,
    loading,
    currentEquipment,
    total,
    filters,
    pagination,
    filteredEquipment,
    equipmentStats,
    fetchEquipment,
    createNewEquipment,
    updateExistingEquipment,
    removeEquipment,
    setFilter,
    setPage
  }
})
