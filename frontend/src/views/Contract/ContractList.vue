<template>
  <div class="list-page">
    <div class="page-header">
      <h2>合同列表 (已生效)</h2>
      <div class="header-actions">
        <el-button v-if="!userStore.isAdmin" type="primary" size="large" @click="goToCreate">
          <el-icon><Plus /></el-icon>
          新建合同申请
        </el-button>
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 按想定分组遍历 -->
      <div v-for="(group, scenarioId) in groupedContracts" :key="scenarioId" class="scenario-group-card">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3 v-if="scenarioId !== 'undefined' && scenarioId !== 'unknown'">
                想定 ID: {{ scenarioId }} 
                <span v-if="scenarioNames[scenarioId]" class="scenario-name">({{ scenarioNames[scenarioId] }})</span>
              </h3>
              <h3 v-else class="unknown-scenario-header">
                <el-icon><Warning /></el-icon>
                未关联有效想定
              </h3>
            </div>
          </template>
          
          <el-table :data="group" stripe border style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" sortable />
            <el-table-column prop="name" label="任务名称" min-width="200" sortable show-overflow-tooltip>
              <template #default="{ row }">
                <el-link type="primary" @click="viewContractDetail(row.id)">
                  <span style="font-weight: 500;">{{ row.name || '未命名合同' }}</span>
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="contract_type" label="合同类型" width="150" sortable>
              <template #default="{ row }">
                  <el-tag effect="dark" :color="getContractTypeColor(row.contract_type)" style="border-color: transparent;">
                      {{ formatContractType(row.contract_type) }}
                  </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="creater" label="创建人" width="150" sortable />
            <el-table-column prop="start_time" label="开始时间" width="200" sortable />

            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewContractDetail(row.id)">查看详情</el-button>
                <el-button size="small" v-if="userStore.isAdmin" type="danger" plain @click="handleDelete(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div v-if="!loading && Object.keys(groupedContracts).length === 0" class="empty-state">
        <el-empty description="当前没有已生效的合同" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, shallowReactive } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh, Warning } from '@element-plus/icons-vue';
import { useUserStore } from '@/stores/user';
import { groupBy } from 'lodash-es';

const userStore = useUserStore();
const router = useRouter();
const loading = ref(false);
const contracts = ref([]);

// --- 新增状态 ---
const scenarioNames = shallowReactive({});

// --- 计算属性，用于分组 ---
const groupedContracts = computed(() => {
  return groupBy(contracts.value, contract => contract.scenario_id || 'unknown');
});

const fetchContracts = async () => {
  loading.value = true;
  try {
    // 并行获取合同列表和想定列表
    const [contractsResult, scenariosResult] = await Promise.allSettled([
      api.getContracts({ status: 'approved' }), // 获取已通过的合同
      api.getSimScenarios()
    ]);

    if (scenariosResult.status === 'fulfilled') {
      scenariosResult.value.forEach(sc => scenarioNames[sc.id] = sc.name);
    } else {
      console.error("加载想定列表失败:", scenariosResult.reason);
    }

    if (contractsResult.status === 'fulfilled') {
      contracts.value = contractsResult.value;
    } else {
      throw new Error("加载合同列表失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "数据加载失败");
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  ElMessage.success('正在刷新数据...');
  fetchContracts();
};

const goToCreate = () => {
  router.push({ name: 'ContractCreate' });
};

const viewContractDetail = (id) => {
  router.push({ name: 'ContractDetail', params: { id } });
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除合同 "${row.name}" 吗？此操作不可逆。`, '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error',
    });
    await api.deleteContract(row.id);
    ElMessage.success('合同删除成功！');
    fetchContracts();
  } catch (action) {
    if (action === 'cancel') ElMessage.info('已取消删除');
  }
};

// --- 辅助函数 ---
const contractTypeMap = {
  defense: '反导', patrol: '巡逻', strike: '打击', reconnaissance: '侦察'
};
const contractTypeColorMap = {
  defense: '#4caf50', patrol: '#2ecc71', strike: '#3498db', reconnaissance: '#f1c40f'
};
const formatContractType = (type) => contractTypeMap[type] || type || '未知';
const getContractTypeColor = (type) => contractTypeColorMap[type] || '#909399';

onMounted(fetchContracts);
</script>

<style scoped>
/* 样式与 PendingContracts.vue 保持一致 */
.list-page { 
  padding: 24px; 
  background-color: #f9fafb; 
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 24px;
  color: #2c3e50;
  margin: 0;
}
.header-actions { 
  display: flex; 
  gap: 16px; 
}
.scenario-group-card {
    margin-bottom: 24px;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.card-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}
.scenario-name {
    font-size: 14px;
    color: #909399;
    font-weight: normal;
    margin-left: 8px;
}
.empty-state {
    padding: 40px 0;
    text-align: center;
}
.unknown-scenario-header {
  color: #E6A23C;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-style: italic;
  font-weight: normal;
}
:deep(.el-table .el-button + .el-button) {
  margin-left: 8px;
}
</style>