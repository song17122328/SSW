<template>
  <div class="list-page">
    <div class="page-header">
      <h2>我的申请</h2>
      <div class="header-actions">
        <el-button type="primary" size="large" @click="goToCreate">
          <el-icon>
            <Plus />
          </el-icon>
          新建合同申请
        </el-button>
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon>
            <Refresh />
          </el-icon>
          刷新
        </el-button>
      </div>
    </div>

   <div class="table-container">
      <!-- *** 核心修改 1：更新表格列以显示新字段 *** -->
      <el-table :data="myContracts" v-loading="loading" stripe border height="calc(100vh - 220px)">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewContractDetail(row.id)">{{ row.name }}</el-link>
          </template>
        </el-table-column>

        <!-- 新增：合同类型列 -->
        <el-table-column prop="contract_type" label="合同类型" width="120">
            <template #default="{ row }">
                <el-tag effect="dark" :color="getContractTypeColor(row.contract_type)" style="border-color: transparent;">
                    {{ formatContractType(row.contract_type) }}
                </el-tag>
            </template>
        </el-table-column>
        
        <!-- 新增：想定ID列 -->
        <el-table-column prop="scenario_id" label="想定ID" width="100" align="center" />

        <el-table-column prop="status" label="审批状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ formatStatus(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="200" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewContractDetail(row.id)">查看</el-button>
            <!-- 只有待审批的合同才允许撤回/删除 -->
            <el-button v-if="row.status === 'pending'" size="small" type="danger" plain @click="handleDelete(row)">
              撤回
            </el-button>

            <el-button v-if="row.status === 'rejected'" size="small" type="danger" plain @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import api from '@/services/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh } from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const myContracts = ref([]);

const fetchMyContracts = async () => {
  loading.value = true;
  try {
    const currentUser = userStore.userInfo.name;
    // 调用 API，按当前用户名过滤
    myContracts.value = await api.getContracts({ creater: currentUser });
  } catch (error) {
    console.error("加载我的申请列表失败:", error);
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  ElMessage.success('正在刷新列表...');
  fetchMyContracts();
};

const goToCreate = () => {
  router.push({ name: 'ContractCreate' });
};

const viewContractDetail = (id) => {
  router.push({ name: 'ContractDetail', params: { id } });
};

const handleDelete = async (row) => {
  // 根据合同状态，动态生成提示信息
  const isWithdraw = row.status === 'pending';
  const actionText = isWithdraw ? '撤回' : '删除';
  const confirmMessage = `确定要${actionText}申请 "${row.name}" 吗？此操作不可逆。`;
  const successMessage = `申请已${actionText}！`;

  try {
    await ElMessageBox.confirm(confirmMessage, `确认${actionText}`, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    // 无论是撤回还是删除，都调用同一个 deleteContract API
    await api.deleteContract(row.id);
    ElMessage.success(successMessage);
    fetchMyContracts(); // 成功后刷新列表

  } catch (action) {
    if (action === 'cancel') {
      ElMessage.info(`已取消${actionText}操作`);
    } else {
      console.error(`${actionText}失败:`, action);
    }
  }
};

// *** 核心修改 2：新增辅助函数用于格式化合同类型 ***
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

// 辅助函数 (可以提取到公共文件中)
const formatStatus = (status) => {
  const map = { pending: '待审批', approved: '已通过', rejected: '已驳回' };
  return map[status] || '未知';
};
const getStatusTag = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' };
  return map[status] || 'info';
};

onMounted(fetchMyContracts);
</script>

<style scoped>
.list-page { padding: 24px; background-color: #f9fafb; }


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

.header-actions { display: flex; gap: 16px; }

.table-container { background: #ffffff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); }


/* 表格样式增强 */
:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-table__header-wrapper th),
:deep(.el-table__fixed-right .el-table__header-wrapper th) {
  background-color: #f4f6f8 !important; /* 使用 !important 确保最高优先级 */
  color: #2c3e50;
  font-weight: 600;
}

:deep(.el-table__row:hover td) {
  background-color: #f8f9fa;
}
/* 状态标签样式 */
:deep(.el-tag) {
  font-weight: 500;
  margin: 0;
}

:deep(.el-tag--warning) {
  background-color: #fdf6ec;
  color: #e6a23c;
  border-color: #f5dab1;
}

:deep(.el-tag--success) {
  background-color: #f0f9ff;
  color: #67c23a;
  border-color: #d1f2eb;
}

:deep(.el-tag--danger) {
  background-color: #fef0f0;
  color: #f56c6c;
  border-color: #fbc4c4;
}

/* 按钮样式 */
:deep(.el-button) {
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-2px);
}

/* 链接样式 */
:deep(.el-link) {
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s ease;
}

:deep(.el-link:hover) {
  color: #3498db;
}

/* 高亮行 */
:deep(.el-table .highlight-row) {
  background-color: #d9ecff !important;
  transition: background-color 0.5s ease;
}

/* 图标与文本间距 */
:deep(.el-button .el-icon + span) {
  margin-left: 8px;
}

/* 操作列按钮组 */
:deep(.el-table .cell .el-button + .el-button) {
  margin-left: 8px;
}

/* 表格边框和悬停效果 */
:deep(.el-table--border) {
  border-color: #e4e7ed;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #f9fafb;
}

/* 危险按钮特殊样式 */
:deep(.el-button--danger.is-plain) {
  background-color: #fef0f0;
  border-color: #fbc4c4;
  color: #f56c6c;
}

:deep(.el-button--danger.is-plain:hover) {
  background-color: #f56c6c;
  border-color: #f56c6c;
  color: #ffffff;
}

/* 操作列按钮对齐 */
:deep(.el-table__fixed-right) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}

/* 加载状态 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #2c3e50;
}
</style>
