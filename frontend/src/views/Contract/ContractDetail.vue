<!-- ContractDetail.vue -->
<template>
  <div class="contract-detail">
    <div class="page-header">
      <!-- 在标题中也加入 key，确保它也能被刷新 -->
      <h2 :key="componentKey">合同详情</h2>
      <div class="header-actions">
        <el-button @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 核心修复：使用 :key 强制重新创建子组件 -->
    <div v-else-if="contractData.名称" class="detail-content" :key="componentKey">
      <FandaoContract 
        v-if="contractType === 'defense'"
        v-model="contractData"
        :is-readonly="true"
        :scenario-id="contractData.details?.scenarioId"
        :scenario-name="getScenarioNameFromData()"
      />
      <XunluoContract 
        v-if="contractType === 'patrol'"
        v-model="contractData"
        :is-readonly="true"
        :scenario-id="contractData.details?.scenarioId"
        :scenario-name="getScenarioNameFromData()"
      />
      <DajiContract 
        v-if="contractType === 'strike'"
        v-model="contractData"
        :is-readonly="true"
        :scenario-id="contractData.details?.scenarioId"
        :scenario-name="getScenarioNameFromData()"
      />
      <ZhenchaContract 
        v-if="contractType === 'reconnaissance'"
        v-model="contractData"
        :is-readonly="true"
        :scenario-id="contractData.details?.scenarioId"
        :scenario-name="getScenarioNameFromData()"
      />
    </div>

    <div v-else class="empty-state">
      <el-empty description="无法加载合同数据或合同不存在" />
    </div>
  </div>
</template>


<script>
// 这个普通的 script 块只用来定义组件名称
export default {
  name: 'ContractDetail',
}
</script>



<script setup>
import { ref, onMounted, computed } from 'vue';
// 确保 onBeforeRouteUpdate 被正确引入
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router';
import api from '@/services/api';
import { ArrowLeft } from '@element-plus/icons-vue';
import FandaoContract from '@/components/contract/FandaoContract.vue';
import XunluoContract from '@/components/contract/XunluoContract.vue';
import DajiContract from '@/components/contract/DajiContract.vue';
import ZhenchaContract from '@/components/contract/ZhenchaContract.vue';

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const contractData = ref({});
// 使用一个 key 来强制刷新DOM
const componentKey = ref(0);

const contractType = computed(() => {
  // *** 核心修复：现在从顶层的 contract_type 字段判断 ***
  const type = contractData.value.作战类型;
  if (!type) return null;
  // 假设 contract_type 的值是 'strike', 'patrol' 等
  return type;
});

// 封装数据获取逻辑
const fetchContractDetails = async (id) => {
    console.log(`[ContractDetail] 准备获取合同 #${id} 的数据...`);
    loading.value = true;
    contractData.value = {}; // 立即清空旧数据
    try {
        // 1. fullContract 现在是一个包含了新顶层字段的对象
        const fullContract = await api.getContractById(id);
        
        // 2. 将顶层字段和 details 字段重新组合成子组件期望的“大杂烩”结构
        const reconstructedData = {
            // --- 从顶层获取 ---
            名称: fullContract.name,
            任务描述: fullContract.description,
            作战类型: fullContract.contract_type,
            scenarioId: fullContract.scenario_id,
            side: fullContract.side,
            作战时间: {
                开始时间: fullContract.start_time,
                结束时间: fullContract.end_time,
            },

            // --- 将 details 对象的内容展开合并进来 ---
            ...fullContract.details 
        };
        
        contractData.value = reconstructedData;

    } catch (error) {
        console.error(`[ContractDetail] 获取合同 #${id} 详情失败:`, error);
    } finally {
        loading.value = false;
    }
};

// 第一次加载时调用
onMounted(() => {
  const contractId = route.params.id;
  console.log('[ContractDetail] 组件已挂载 (onMounted)，初始合同 ID:', contractId);
  if (contractId) {
    fetchContractDetails(contractId);
  } else {
    loading.value = false;
  }
});

// 路由更新时调用
onBeforeRouteUpdate(async (to, from) => {
  console.log(`[ContractDetail] 路由更新 (onBeforeRouteUpdate)，从 ID: ${from.params.id} 到 ID: ${to.params.id}`);
  // 确保只有在 ID 变化时才重新加载
  if (to.params.id !== from.params.id) {
    await fetchContractDetails(to.params.id);
  }
});

// 从 contractData 中提取 scenarioName 的辅助函数
const getScenarioNameFromData = () => {
  // 这个函数可能需要调整，取决于 scenarioName 是否还存在于 details 中
  // 根据新的后端结构，'作战场景' (e.g., '对海打击') 现在在 details 内部
  return contractData.value.作战场景 || ''; 
}
</script>

<style scoped>
.contract-detail { padding: 24px; background: #f9fafb; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { color: #000000; margin: 0; font-size: 24px; font-weight: 600; }
.header-actions { display: flex; gap: 12px; }
.detail-content { background: #ffffff; padding: 24px; border-radius: 8px; }
.loading-container { padding: 24px; background: #ffffff; border-radius: 8px; }
</style>