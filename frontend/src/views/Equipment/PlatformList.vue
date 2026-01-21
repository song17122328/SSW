<!-- PlatformList.vue -->
<template>
  <div class="list-page">
    <div class="page-header">
      <h2>平台资料库</h2>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="输入平台名称..."
          clearable
          size="large"
          class="search-input"
          @keyup.enter="handleSearch" 
        />
        <!-- *** 核心修复 1：新增查询按钮 *** -->
        <el-button type="info" size="large" @click="handleSearch" :icon="Search">
          查询
        </el-button>


        <el-button type="primary" size="large" @click="openForm(null)">
          <el-icon><Plus /></el-icon> 新增平台
        </el-button>
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div class="table-container card-style">
      <el-table 
        v-loading="loading" 
        :data="platforms" 
        row-key="id" 
        :row-style="tableRowStyle"
        stripe 
        height="calc(100vh - 280px)" 
        style="width: 100%" 
        ref="tableRef"
      >
        <el-table-column prop="name" label="平台名称" min-width="220" sortable>
          <template #default="{ row }">
            <div class="platform-name-cell">
              <el-icon class="platform-icon" :size="20">
                <Ship v-if="row.category === '舰艇'" />
                <MostlyCloudy v-else />
              </el-icon>
              <span class="name-text">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="平台分类" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.category === '舰艇' ? 'primary' : 'success'" effect="light" round>
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_type" label="型号/类型" min-width="150" />
        <el-table-column prop="country" label="国别" min-width="150" />
        <el-table-column prop="service_date" label="服役时间" min-width="180" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)" effect="dark" round>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small"  plain @click="viewDetails(row)">查看</el-button>
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
          layout="total, prev, pager, next, jumper"
          :total="totalItems"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </div>


        <!-- *** 核心修复 1：确保 PlatformForm 组件被正确地包含在模板中 *** -->
    <PlatformForm 
      v-if="formVisible"
      :visible="formVisible" 
      :platform="selectedPlatform" 
      @close="formVisible = false" 
      @success="onSaveSuccess" 
    />


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
import { useDebounceFn } from '@vueuse/core'; // 引入防抖函数库
import { useUserStore } from '@/stores/user';
import { ref, onMounted, watch, nextTick, computed } from 'vue'; 
import { useRouter, useRoute } from 'vue-router';
import api from '@/services/api';
import { ElMessage,ElMessageBox } from 'element-plus';
import { Refresh, Ship, MostlyCloudy, Search,Plus } from '@element-plus/icons-vue'; // <-- 添加 Search
import StatusEditorDialog from '@/components/StatusEditorDialog.vue'; // 引入新组件
import PlatformForm from '@/components/equipment/PlatformForm.vue';


const userStore = useUserStore();
const router = useRouter();
const route = useRoute();

const loading = ref(true);
const platforms = ref([]);  // <-- 这个现在是我们的“原始数据源”
const pagination = ref({ page: 1, pageSize: 10, total: 0 });
const formVisible = ref(false);
const selectedPlatform = ref(null);

const openForm = async (platform) => {
    if (platform) {
        // 编辑时需要获取完整详情，因为列表可能不包含所有字段
        const fullDetail = await api.getPlatformById(platform.id);
        selectedPlatform.value = fullDetail;
    } else {
        selectedPlatform.value = null; // 新增
    }
    formVisible.value = true;
};

const onSaveSuccess = () => {
    formVisible.value = false;
    fetchPlatforms(); // 成功后刷新列表
};


const handleDelete = async (platform) => {
    await ElMessageBox.confirm(`确定删除平台 "${platform.name}" 吗？`, '警告', { type: 'warning' });
    await api.deletePlatform(platform.id);
    ElMessage.success("删除成功！");
    fetchPlatforms();
};

// *** 2. 新增搜索关键字的状态 ***
const searchKeyword = ref('');

// *** 3. 创建计算属性来过滤数据 ***
const filteredPlatforms = computed(() => {
  // 如果搜索关键字为空，直接返回所有平台
  if (!searchKeyword.value) {
    return platforms.value;
  }
  // 如果有关键字，则进行过滤
  const keyword = searchKeyword.value.toLowerCase();
  return platforms.value.filter(platform => 
    // 我们将根据平台名称进行不区分大小写的搜索
    platform.name.toLowerCase().includes(keyword)
  );
});

// *** 新增：弹窗状态管理 ***
const dialogVisible = ref(false);
const updateLoading = ref(false);
const currentItem = ref({});

const openStatusDialog = (item) => {
  currentItem.value = { ...item }; // 复制一份，避免直接修改
  dialogVisible.value = true;
};

const handleUpdateStatus = async (newStatus) => {
  if (newStatus === currentItem.value.status) {
    dialogVisible.value = false;
    return;
  }
  updateLoading.value = true;
  try {
    await api.updatePlatformStatus(currentItem.value.id, newStatus);
    // 更新成功后，在前端列表中直接修改状态，避免重新请求
    const index = platforms.value.findIndex(p => p.id === currentItem.value.id);
    if (index !== -1) {
      platforms.value[index].status = newStatus;
    }
    ElMessage.success('状态更新成功');
    dialogVisible.value = false;
  } catch (error) {
    ElMessage.error('状态更新失败');
  } finally {
    updateLoading.value = false;
  }
};

// 辅助函数，用于状态颜色
const statusColor = (status) => {
  if (status === '可用') return 'success';
  if (status === '停用') return 'info';
  if (status === '维护') return 'warning';
  return '';
};


const tableRef = ref(null);

// *** 新增：分页状态 ***
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);

// *** 核心修复 7：移除 computed 过滤，修改 fetchPlatforms ***
const fetchPlatforms = async () => {
  loading.value = true;
  try {
    const response = await api.getPlatforms(currentPage.value, pageSize.value, searchKeyword.value);
    console.log(searchKeyword.value)
    platforms.value = response.items;
    totalItems.value = response.total;
  } catch (error) {
    console.error("加载平台列表失败:", error);
  } finally {
    loading.value = false;
  }
};

// *** 核心修复 2：修改 watch 逻辑 ***
// 现在只有在分页变化时才自动获取数据
watch([currentPage, pageSize], fetchPlatforms);

// *** 核心修复 3：创建 handleSearch 函数 ***
const handleSearch = () => {
  // 当用户点击查询或按回车时，重置到第一页并获取数据
  currentPage.value = 1;
  fetchPlatforms();
};

// *** 新增：页码改变事件处理函数 ***
const handlePageChange = (newPage) => {
  currentPage.value = newPage;
  fetchPlatforms();
};

const handleRefresh = () => {
  // 刷新时应该清空搜索条件并回到第一页
  searchKeyword.value = '';
  currentPage.value = 1;
  ElMessage.success('正在刷新数据...');
  fetchPlatforms();
};


const highlightState = ref({ id: null });



const viewDetails = (platform) => {
  // platform.id 现在是数字，这没有问题
  router.push({
    name: 'PlatformDetail',
    params: { id: platform.id }
  });
};

const tableRowStyle = ({ row }) => {
  // 关键：比较时确保类型一致
  if (row.id === highlightState.value.id) {
    return { 'font-weight': 'bold', 'background-color': '#e9f5ff' };
  }
  return null;
};
const scrollToRow = () => {
  const { id } = highlightState.value;
  if (id && tableRef.value) {
    nextTick(() => {
      const targetRow = platforms.value.find(p => p.id === id);
      if (targetRow) {
        const rowIndex = platforms.value.indexOf(targetRow);
        if (rowIndex > -1) {
          const rowHeight = 50; 
          const scrollTop = rowIndex * rowHeight;
          tableRef.value.setScrollTop(scrollTop);
        }
      }
    });
  }
}

watch(() => route.query, (newQuery) => {
  // 关键：从 URL query 获取的 highlight 是字符串，需要转换为数字
  const id = newQuery.highlight ? parseInt(newQuery.highlight, 10) : null;
  highlightState.value = { id };
  scrollToRow();
}, { deep: true, immediate: true });

onMounted(() => {
  fetchPlatforms();
  scrollToRow();
});
</script>

<style scoped>
/* 1. 页面整体布局 */
.list-page {
  padding: 24px;
  background-color: #f0f2f5; /* 更柔和的背景色 */
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 2. 页面头部 */
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

/* 3. 表格容器 (卡片化) */
.table-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 4. Element Plus 表格深度定制 */
:deep(.el-table) {
  flex-grow: 1; /* 让表格填充剩余空间 */
  border-radius: 8px;
  overflow: hidden; /* 配合圆角 */
}

/* 表头样式 */
:deep(.el-table__header-wrapper th) {
  background-color: #f7f8fa !important;
  color: #606266;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed !important;
}

/* 移除表头右侧的白边 */
:deep(.el-table__header th.is-leaf) {
  border-bottom: 1px solid #e4e7ed;
}
:deep(th.el-table__cell) {
  background-color: #f7f8fa !important;
}

/* 行样式 */
:deep(.el-table__row) {
  transition: background-color 0.2s ease;
}
:deep(.el-table__row:hover > td) {
  background-color: #f5f7fa !important;
}

/* 斑马纹样式 */
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: #fafbfe;
}

/* 移除表格底部边框 */
.el-table::before {
  height: 0px;
}

/* 5. 单元格内容样式 */
.platform-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.platform-name-cell .name-text {
  font-weight: 500;
  color: #303133;
}
.platform-icon {
  color: #409eff;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}
:deep(.el-button) {
  border-radius: 6px;
}

/* 6. 分页容器 */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
  flex-shrink: 0;
}
</style>