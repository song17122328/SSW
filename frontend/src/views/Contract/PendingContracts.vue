<template>
  <div class="list-page">
    <div class="page-header">
      <h2>待审批合同 (按想定分类)</h2>
      <div class="header-actions">
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <div v-loading="loading">
      <!-- 遍历分组后的合同 -->
      <div v-for="(group, scenarioId) in groupedContracts" :key="scenarioId" class="scenario-group-card">
        <el-card>
          <template #header>
            <div class="card-header">
              <!-- 处理未知想定的标题 -->
              <h3 v-if="scenarioId !== 'undefined' && scenarioId !== 'unknown'">
                想定 ID: {{ scenarioId }} 
                <span v-if="scenarioNames[scenarioId]" class="scenario-name">({{ scenarioNames[scenarioId] }})</span>
              </h3>
              <h3 v-else class="unknown-scenario-header">
                <el-icon><Warning /></el-icon>
                未关联有效想定
              </h3>
              
              <!-- 批量审批按钮，增加 loading 状态，并对未知想定的分组禁用 -->
              <el-button 
                v-if="scenarioId !== 'undefined' && scenarioId !== 'unknown'"
                type="primary"
                :loading="bulkApprovalLoading[scenarioId]"
                :disabled="!selections[scenarioId] || selections[scenarioId].length === 0"
                @click="handleBulkApproval(scenarioId)"
              >
                <el-icon><Promotion /></el-icon>
                批量审批通过并分配 ({{ selections[scenarioId] ? selections[scenarioId].length : 0 }})
              </el-button>
            </div>
          </template>
          
          <el-table 
            :data="group" 
            stripe 
            border 
            style="width: 100%"
            @selection-change="(selectedRows) => handleSelectionChange(scenarioId, selectedRows)"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="id" label="ID" width="80" sortable />
            <el-table-column prop="name" label="任务名称" min-width="200" sortable show-overflow-tooltip>
               <template #default="{ row }">
                <el-link type="primary" @click="viewContractDetail(row.id)">{{ row.name }}</el-link>
              </template>
            </el-table-column>
            <!-- 使用“合同类型”替代“作战场景” -->
            <el-table-column prop="contract_type" label="合同类型" width="150" sortable>
              <template #default="{ row }">
                  <el-tag effect="dark" :color="getContractTypeColor(row.contract_type)" style="border-color: transparent;">
                      {{ formatContractType(row.contract_type) }}
                  </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="creater" label="创建人" width="150" sortable />
            <el-table-column prop="start_time" label="开始时间" width="200" sortable />
            <el-table-column label="单项操作" width="150" fixed="right">
              <template #default="{ row }">
                 <el-button size="small" @click="viewContractDetail(row.id)">查看</el-button>
                <el-button size="small" type="danger" plain @click="handleApproval(row, 'rejected')">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div v-if="!loading && Object.keys(groupedContracts).length === 0" class="empty-state">
        <el-empty description="当前没有待审批的合同" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, shallowReactive } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Promotion, Warning } from '@element-plus/icons-vue';
import { groupBy } from 'lodash-es';

const router = useRouter();
const loading = ref(false);
const pendingContracts = ref([]);

// 使用 shallowReactive 提高性能，因为我们只关心对象顶层属性的变化
const selections = shallowReactive({});
const scenarioNames = shallowReactive({});
const bulkApprovalLoading = shallowReactive({});

const groupedContracts = computed(() => {
  // 确保 scenario_id 为 null 或 undefined 的合同被归为 'unknown' 组
  return groupBy(pendingContracts.value, contract => contract.scenario_id || 'unknown');
});

const fetchPending = async () => {
  loading.value = true;
  Object.keys(selections).forEach(key => delete selections[key]);
  try {
    const [contractsResult, scenariosResult] = await Promise.allSettled([
      api.getContracts({ status: 'pending' }),
      api.getSimScenarios()
    ]);

    if (scenariosResult.status === 'fulfilled') {
      scenariosResult.value.forEach(sc => scenarioNames[sc.id] = sc.name);
    } else {
      console.error("加载想定列表失败:", scenariosResult.reason);
      ElMessage.error("加载想定列表失败");
    }

    if (contractsResult.status === 'fulfilled') {
      pendingContracts.value = contractsResult.value;
    } else {
      console.error("加载待审批合同失败:", contractsResult.reason);
      throw new Error("加载待审批合同失败");
    }
  } catch(error) {
    ElMessage.error(error.message || "数据加载时发生错误");
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
    ElMessage.success('正在刷新数据...');
    fetchPending();
};
const viewContractDetail = (id) => {
  router.push({ name: 'ContractDetail', params: { id } });
};

const handleSelectionChange = (scenarioId, selectedRows) => {
  selections[scenarioId] = selectedRows;
};

const handleBulkApproval = async (scenarioId) => {
  const selectedContracts = selections[scenarioId];
  if (!selectedContracts || selectedContracts.length === 0) {
    ElMessage.warning('请至少选择一个合同进行审批');
    return;
  }
  const contractIds = selectedContracts.map(c => c.id);
  const contractNames = selectedContracts.map(c => `"${c.name}"`).join(', ');

  bulkApprovalLoading[scenarioId] = true;
  try {
    await ElMessageBox.confirm(`确定要批量通过以下 ${contractIds.length} 个合同吗？<br><strong>${contractNames}</strong>`, '确认批量审批', {
        confirmButtonText: '确定并通过',
        cancelButtonText: '取消',
        type: 'success',
        dangerouslyUseHTMLString: true,
    });

    const approvalPromises = contractIds.map(id => api.updateContractStatus(id, 'approved'));
    await Promise.all(approvalPromises);
    
    ElMessage.success(`${contractIds.length} 个合同已成功审批！正在跳转到资源分配页面...`);
    
    router.push({
        name: 'RLJobMonitor',
        query: {
            scenario_id: scenarioId,
            contract_ids: contractIds.join(',')
        }
    });

  } catch (action) {
    if (action === 'cancel') {
        ElMessage.info('已取消批量审批操作');
    } else {
        console.error("批量审批操作失败:", action);
        ElMessage.error('批量审批时发生错误');
    }
  } finally {
    bulkApprovalLoading[scenarioId] = false;
  }
};

const handleApproval = async (row, status) => {
  const actionText = status === 'approved' ? '通过' : '驳回';
  try {
     await ElMessageBox.confirm(`确定要${actionText}合同 "${row.name}" 吗？`, `确认${actionText}`, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: status === 'approved' ? 'success' : 'warning',
    });

    await api.updateContractStatus(row.id, status);
    ElMessage.success(`操作成功，合同已${actionText}`);
    fetchPending();
  } catch (action) {
    if (action === 'cancel') {
      ElMessage.info(`已取消${actionText}操作`);
    } else {
      console.error("审批操作失败:", action);
    }
  }
};

// --- 辅助函数 ---
const contractTypeMap = {
  defense: '反导',
  patrol: '巡逻',
  strike: '打击',
  reconnaissance: '侦察'
};
const contractTypeColorMap = {
  defense: '#4caf50',
  patrol: '#2ecc71',
  strike: '#3498db',
  reconnaissance: '#f1c40f'
};

const formatContractType = (type) => {
  return contractTypeMap[type] || type || '未知';
};
const getContractTypeColor = (type) => {
  return contractTypeColorMap[type] || '#909399';
};

onMounted(fetchPending);
</script>

<style scoped>
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