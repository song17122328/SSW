<!-- ScenarioList.vue -->
<template>
  <div class="list-page">
    <div class="page-header">
      <h2>作战想定列表</h2>
      <div class="header-actions">
        <!-- *** 核心修改 1：使用 v-if="userStore.isAdmin" 控制上传按钮 *** -->
        <el-upload 
          v-if="userStore.isAdmin"
          :show-file-list="false" 
          :http-request="handleUpload" 
          accept=".json"
        >
          <el-button type="primary" size="large">
            <el-icon><Upload /></el-icon>
            添加作战想定
          </el-button>
        </el-upload>
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    <div class="table-container">
      <el-table :data="scenarios" v-loading="loading" stripe border height="calc(100vh - 220px)">
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="name" label="想定名称" min-width="250" sortable show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetails(row.id)">
              <span style="font-weight: 500;">{{ row.name }}</span>
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="150" sortable />
        <el-table-column prop="force_count" label="兵力数" width="100" align="center" sortable />
        <el-table-column prop="creator" label="创建者" width="120" sortable />
        <el-table-column prop="create_time" label="创建时间" width="180" sortable />



        <!-- *** 核心修改 2：使用 v-if="userStore.isAdmin" 控制操作列的删除按钮 *** -->
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDetails(row.id)">
              <el-icon><View /></el-icon>
              <span>进入想定</span>
            </el-button>
            <el-button 
              v-if="userStore.isAdmin"
              size="small" 
              type="danger" 
              plain 
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>
              <span>删除</span>
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
import api from '@/services/api';
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus';
import { Refresh, View, Upload, Delete } from '@element-plus/icons-vue'; // 引入 Delete
// *** 核心修改 3：引入 userStore ***
import { useUserStore } from '@/stores/user';

const router = useRouter();
const loading = ref(false);
const scenarios = ref([]);
// *** 核心修改 4：获取 userStore 实例 ***
const userStore = useUserStore();

// ** 新增：删除处理函数 **
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除想定 "${row.name}" 吗？此操作将同时删除其下所有兵力数据，且不可逆。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
      }
    );

    const response = await api.deleteSimScenario(row.id);
    ElMessage.success(response.message || '删除成功！');
    fetchScenarios(); // 删除成功后刷新列表

  } catch (action) {
    if (action === 'cancel') {
      ElMessage.info('已取消删除操作');
    } else {
      console.error("删除失败:", action);
    }
  }
};


// ** 2. 新增的上传处理函数 **
const handleUpload = async (options) => {
  const file = options.file;
  if (!file) {
    ElMessage.error("未选择文件");
    return;
  }

  // 1. 打开加载服务并获取实例
  const loadingInstance = ElLoading.service({
    lock: true,
    text: '正在上传并解析想定文件...',
    background: 'rgba(0, 0, 0, 0.7)',
  });

  try {
    // 2. 执行异步上传
    const response = await api.uploadSimScenario(file);
    ElMessage.success(response.message || "上传成功！");
    fetchScenarios(); // 上传成功后刷新列表
  } catch (error) {
    // API 拦截器通常会处理错误消息，这里可以留空或记录日志
    console.error("上传失败:", error);
  } finally {
    // 3. 确保在 finally 块中关闭加载实例
    loadingInstance.close();
  }
};


const fetchScenarios = async () => {
  loading.value = true;
  try {
    scenarios.value = await api.getSimScenarios();
  } catch (error) {
    console.error("加载想定列表失败:", error);
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  ElMessage.success("正在刷新想定列表...");
  fetchScenarios();
};

const viewDetails = (id) => {
  router.push({ name: 'ScenarioDetail', params: { id } });
};

onMounted(fetchScenarios);
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

/* 上传组件样式 */
:deep(.el-upload) {
  display: inline-block;
}

:deep(.el-upload .el-button) {
  transition: all 0.3s ease;
}

:deep(.el-upload .el-button:hover) {
  transform: translateY(-2px);
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

/* 危险按钮样式 */
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

/* 主要按钮样式 */
:deep(.el-button--primary) {
  background-color: #3498db;
  border-color: #3498db;
}

:deep(.el-button--primary:hover) {
  background-color: #2980b9;
  border-color: #2980b9;
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

/* 操作列按钮组 - 确保按钮横向排列 */
:deep(.el-table .cell) {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
}

:deep(.el-table .el-table__cell:last-child .cell) {
  justify-content: flex-start;
}

:deep(.el-table .cell .el-button + .el-button) {
  margin-left: 0;
}

/* 表格边框和悬停效果 */
:deep(.el-table--border) {
  border-color: #e4e7ed;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #f9fafb;
}

/* 加载状态 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #2c3e50;
}

/* 固定列阴影 */
:deep(.el-table__fixed-right) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
}

/* 表格单元格对齐 */
:deep(.el-table .el-table__cell) {
  padding: 8px 12px;
}

/* 想定名称链接特殊样式 */
:deep(.el-link--primary span) {
  font-weight: 500;
  color: #3498db;
}

:deep(.el-link--primary:hover span) {
  color: #2980b9;
}

/* 兵力数居中对齐 */
:deep(.el-table .cell[align="center"]) {
  text-align: center;
}

/* 溢出文本提示 */
:deep(.el-table .cell.el-table__cell) {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
