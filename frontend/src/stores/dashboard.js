// src/stores/dashboard.js

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
    // --- State ---
    const loading = ref(false)
    const platformCount = ref(0)
    const equipmentCount = ref(0)
    const contractCount = ref(0)
    const scenarioCount = ref(0)

    // 模拟最近活动日志
    const recentActivities = ref([
        { id: 1, level: 'info', message: '用户登录系统', timestamp: new Date() },
        { id: 2, level: 'success', message: '成功加载平台数据', timestamp: new Date(Date.now() - 1000 * 60 * 2) },
    ])

    // --- Getters (Computed) ---

    // 按平台类型（舰艇/飞机）分类统计
    const platformStats = ref({ ship: 0, aircraft: 0 })

    // 按平台状态统计
    const platformStatusStats = ref({
        active: 0,    // 可用
        inactive: 0,  // 停用
        maintenance: 0 // 维护
    })

    // 按合同状态统计 (我们可以获取所有合同，然后在前端分类)
    const contractStats = ref({ pending: 0, approved: 0, rejected: 0 })

    // ==========================================================
    // *** 新增：为装备状态统计添加 State ***
    // ==========================================================
    const equipmentStatusStats = ref({
        active: 0,    // 可用
        inactive: 0,  // 停用
        maintenance: 0 // 维护
    })
    // ==========================================================

    // ==========================================================
    // *** 新增：为装备类型统计添加 State ***
    // ==========================================================
    const equipmentTypeStats = ref({
        sense: 0,    // 感知类 (S)
        control: 0,  // 控制类 (C)
        action: 0    // 执行类 (A)
    })
    // ==========================================================

    // --- Actions ---
    async function fetchDashboardData() {
        loading.value = true
        try {
            // 使用 Promise.all 并行发起所有请求
            const [
                platformResponse,
                equipmentResponse,
                allContracts,
                scenarios
            ] = await Promise.all([
                api.getAllPlatforms(),
                api.getAllEquipments(),
                api.getContracts(),
                api.getSimScenarios()
            ]);

            // 1. 更新平台统计
            const allPlatforms = platformResponse.items;
            platformCount.value = platformResponse.total;
            platformStats.value.ship = allPlatforms.filter(p => p.category === '舰艇').length;
            platformStats.value.aircraft = allPlatforms.filter(p => p.category === '飞机').length;

            // 计算平台状态统计
            platformStatusStats.value.active = allPlatforms.filter(p => p.status === '可用').length;
            platformStatusStats.value.inactive = allPlatforms.filter(p => p.status === '停用').length;
            platformStatusStats.value.maintenance = allPlatforms.filter(p => p.status === '维护').length;

            // 2. 更新装备统计
            const allEquipment = equipmentResponse.items;
            equipmentCount.value = equipmentResponse.total;

            // ==========================================================
            // *** 核心修正：计算真实的装备状态统计 ***
            // ==========================================================
            // 不再使用模拟数据，而是遍历全量装备列表进行计数
            equipmentStatusStats.value.active = allEquipment.filter(e => e.status === '可用').length;
            equipmentStatusStats.value.inactive = allEquipment.filter(e => e.status === '停用').length;
            equipmentStatusStats.value.maintenance = allEquipment.filter(e => e.status === '维护').length;
            // ==========================================================

            // ==========================================================
            // *** 新增：计算装备类型统计（基于 type_code）***
            // ==========================================================
            equipmentTypeStats.value.sense = allEquipment.filter(e => e.type_code === 'S').length;
            equipmentTypeStats.value.control = allEquipment.filter(e => e.type_code === 'C').length;
            equipmentTypeStats.value.action = allEquipment.filter(e => e.type_code === 'A').length;
            // ==========================================================

            // 3. 更新合同统计
            contractCount.value = allContracts.length;
            contractStats.value.pending = allContracts.filter(c => c.status === 'pending').length;
            contractStats.value.approved = allContracts.filter(c => c.status === 'approved').length;
            contractStats.value.rejected = allContracts.filter(c => c.status === 'rejected').length;

            // 4. 更新想定统计
            scenarioCount.value = scenarios.length;

            console.log('✅ 仪表盘数据已与真实状态同步');

        } catch (error) {
            console.error('❌ 加载仪表盘数据失败:', error);
        } finally {
            loading.value = false;
        }
    }

    function addActivity(level, message) {
        recentActivities.value.unshift({
            id: Date.now(),
            level,
            message,
            timestamp: new Date()
        });
        if (recentActivities.value.length > 5) {
            recentActivities.value.pop();
        }
    }

    return {
        loading,
        platformCount,
        equipmentCount,
        contractCount,
        scenarioCount,
        platformStats,
        platformStatusStats,
        contractStats,
        recentActivities,
        equipmentStatusStats,
        equipmentTypeStats,
        fetchDashboardData,
        addActivity
    }
})