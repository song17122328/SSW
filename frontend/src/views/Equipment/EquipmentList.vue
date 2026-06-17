<!-- EquipmentList.vue (最终版) -->
<template>
  <div class="list-page">
    <div class="page-header">
      <h2>装备库</h2>
      <div class="header-actions">
<!-- 搜索框 -->
        <el-input
          v-model="searchKeyword"
          placeholder="在后端搜索装备名称..."
          clearable
          size="large"
          class="search-input"
          @keyup.enter="handleSearch"
        />
        <!-- 查询按钮 -->
        <el-button type="info" size="large" @click="handleSearch" :icon="Search">
          查询
        </el-button>
        <!-- 新增按钮 -->
        <el-button v-if="userStore.isAdmin" type="primary" size="large" @click="openForm(null)">
          <el-icon><Plus /></el-icon> 新增装备
        </el-button>
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div class="table-container card-style">
      <el-table 
        v-loading="loading" 
        :data="equipments" 
        row-key="id" 
        stripe 
        height="calc(100vh - 280px)" 
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="name" label="装备名称" min-width="220" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetails(row)">
              <span class="name-text">{{ row.name }}</span>
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type_code" label="型号代码" min-width="150" />
        <el-table-column prop="category_text" label="分类" min-width="180" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" effect="dark" round>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" @click="viewDetails(row)">查看</el-button>
              <el-button v-if="userStore.isAdmin" size="small" type="primary" plain @click="openForm(row)">编辑</el-button>
              <el-button v-if="userStore.isAdmin" size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
              <el-button v-if="userStore.isAdmin" size="small" type="warning" plain @click="openStatusDialog(row)">
                修改状态
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalItems"
          v-model:page-size="pageSize"
          v-model:current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
        />
      </div>
    </div>

    <!-- 表单弹窗 -->
    <EquipmentForm 
      v-if="formVisible"
      :visible="formVisible" 
      :equipment="selectedEquipment" 
      @close="formVisible = false" 
      @success="onSaveSuccess" 
    />

    <!-- 状态编辑弹窗 -->
    <StatusEditorDialog
      v-if="dialogVisible"
      :visible="dialogVisible"
      :item-name="currentItem.name || ''"
      :current-status="currentItem.status || '可用'"
      :loading="updateLoading"
      @close="dialogVisible = false"
      @confirm="handleUpdateStatus"
    />
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user';
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Search, Plus } from '@element-plus/icons-vue';
import StatusEditorDialog from '@/components/StatusEditorDialog.vue';
import EquipmentForm from '@/components/equipment/EquipmentForm.vue'; // 引入装备表单

const userStore = useUserStore();
const router = useRouter();

const loading = ref(true);
const equipments = ref([]);
const searchKeyword = ref('');

const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);

const formVisible = ref(false);
const selectedEquipment = ref(null);

const dialogVisible = ref(false);
const updateLoading = ref(false);
const currentItem = ref({});


// *** 核心修复 2：更新 fetchEquipments 以包含搜索参数 ***
const fetchEquipments = async () => {
  loading.value = true;
  try {
    const response = await api.getEquipments(currentPage.value, pageSize.value, searchKeyword.value);
    equipments.value = response.items;
    totalItems.value = response.total;
  } catch (error) {
    console.error("加载装备列表失败:", error);
  } finally {
    loading.value = false;
  }
};

// *** 核心修复 3：监听分页变化 ***
watch([currentPage, pageSize], fetchEquipments);

// *** 核心修复 4：新增查询处理函数 ***
const handleSearch = () => {
  currentPage.value = 1; // 搜索时重置到第一页
  fetchEquipments();
};

// *** 核心修复 5：优化刷新逻辑 ***
const handleRefresh = () => {
  searchKeyword.value = ''; // 清空搜索词
  currentPage.value = 1;    // 回到第一页
  ElMessage.success('正在刷新数据...');
  fetchEquipments();
};

// *** 核心修复：修改 openForm 函数，使其调用详情接口 ***
const openForm = async (equipment) => {
    if (equipment) {
        // 编辑模式：总是通过 API 获取最新的、最完整的数据
        try {
            const fullDetail = await api.getEquipmentById(equipment.id);
            selectedEquipment.value = fullDetail;
        } catch (error) {
            ElMessage.error("获取装备详情失败，无法编辑");
            return; // 获取失败则不打开弹窗
        }
    } else {
        // 新增模式
        selectedEquipment.value = null;
    }
    formVisible.value = true;
};

const onSaveSuccess = () => {
    formVisible.value = false;
    fetchEquipments();
};

const handleDelete = async (equipment) => {
  try {
    await ElMessageBox.confirm(`确定删除装备 "${equipment.name}" 吗？`, '警告', { type: 'warning' });
    await api.deleteEquipment(equipment.id);
    ElMessage.success("删除成功！");
    if (equipments.value.length === 1 && currentPage.value > 1) {
        currentPage.value--;
    }
    fetchEquipments();
  } catch (error) {
    if (error !== 'cancel') {
        console.error("删除失败:", error);
    }
  }
};

const viewDetails = (equipment) => {
  router.push({ name: 'EquipmentDetail', params: { id: equipment.id } });
};

const openStatusDialog = (item) => {
  currentItem.value = { ...item };
  dialogVisible.value = true;
};

const handleUpdateStatus = async (newStatus) => {
  if (newStatus === currentItem.value.status) {
    dialogVisible.value = false;
    return;
  }
  updateLoading.value = true;
  try {
    await api.updateEquipmentStatus(currentItem.value.id, newStatus);
    const index = equipments.value.findIndex(p => p.id === currentItem.value.id);
    if (index !== -1) {
      equipments.value[index].status = newStatus;
    }

    // 重载 PCCS 资源池以同步最新状态
    try {
      await api.reloadPCCSResources();
      console.log('PCCS 资源池已更新');
    } catch (pccsError) {
      console.warn('PCCS 资源池更新失败，但装备状态已更新', pccsError);
    }

    ElMessage.success('状态更新成功');
    dialogVisible.value = false;
  } finally {
    updateLoading.value = false;
  }
};

const statusColor = (status) => {
  return { '可用': 'success', '停用': 'info', '维护': 'warning' }[status] || '';
};

onMounted(fetchEquipments);
</script>

<style scoped>
/* 样式与 PlatformList.vue 完全一致 */
.list-page {
  padding: 24px;
  background-color: #f0f2f5;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}
.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2d3d;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.search-input {
  width: 240px;
}
.table-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
:deep(.el-table) {
  flex-grow: 1;
  border-radius: 8px;
  overflow: hidden;
}
:deep(.el-table__header-wrapper th) {
  background-color: #f7f8fa !important;
  color: #606266;
  font-weight: 600;
}
.name-text {
  font-weight: 500;
  color: #303133;
}
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
  flex-shrink: 0;
}
</style>