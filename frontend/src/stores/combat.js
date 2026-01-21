/**
 * ⚔️ 作战状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useCombatStore = defineStore('combat', () => {
  const currentSimulation = ref(null)
  const simulationHistory = ref([])
  const combatResults = ref([])
  const isSimulating = ref(false)
  const simulationProgress = ref(0)

  const combatParams = ref({
    scenario: null,
    blueForce: [],
    redForce: [],
    environment: {
      weather: 'clear',
      seaState: 2,
      visibility: 'good'
    }
  })

  const simulationStats = computed(() => ({
    total: simulationHistory.value.length,
    success: simulationHistory.value.filter(s => s.result === 'success').length,
    failed: simulationHistory.value.filter(s => s.result === 'failed').length
  }))

  const canStartSimulation = computed(() => {
    return combatParams.value.blueForce.length > 0 &&
      combatParams.value.redForce.length > 0 &&
      !isSimulating.value
  })

  async function fetchCombatHistory() {
    try {
      const response = await api.getCombatHistory()
      simulationHistory.value = response.data || []
      console.log(`✅ 加载作战历史: ${simulationHistory.value.length} 项`)
    } catch (error) {
      console.error('❌ 获取作战历史失败:', error)
      throw error
    }
  }

  async function startSimulation(params) {
    try {
      isSimulating.value = true
      simulationProgress.value = 0

      console.log('🚀 开始作战仿真...')

      const simulation = await api.createCombatSimulation(params)
      currentSimulation.value = simulation

      await api.startCombatSimulation(simulation.id)

      // 模拟进度更新
      const progressInterval = setInterval(async () => {
        simulationProgress.value += Math.random() * 10

        if (simulationProgress.value >= 100) {
          clearInterval(progressInterval)
          await completeSimulation()
        }
      }, 500)

    } catch (error) {
      console.error('❌ 仿真启动失败:', error)
      isSimulating.value = false
      throw error
    }
  }

  async function completeSimulation() {
    if (currentSimulation.value) {
      const result = {
        ...currentSimulation.value,
        endTime: new Date().toISOString(),
        result: Math.random() > 0.3 ? 'success' : 'failed',
        status: 'completed',
        casualties: {
          blue: Math.floor(Math.random() * 10),
          red: Math.floor(Math.random() * 15)
        }
      }

      simulationHistory.value.unshift(result)
      console.log('✅ 作战仿真完成:', result.result)
    }

    isSimulating.value = false
    simulationProgress.value = 0
    currentSimulation.value = null
  }

  function setCombatParams(params) {
    combatParams.value = { ...combatParams.value, ...params }
  }

  function addForceUnit(side, unit) {
    if (side === 'blue') {
      combatParams.value.blueForce.push(unit)
    } else if (side === 'red') {
      combatParams.value.redForce.push(unit)
    }
  }

  return {
    currentSimulation,
    simulationHistory,
    isSimulating,
    simulationProgress,
    combatParams,
    simulationStats,
    canStartSimulation,
    fetchCombatHistory,
    startSimulation,
    setCombatParams,
    addForceUnit
  }
})
