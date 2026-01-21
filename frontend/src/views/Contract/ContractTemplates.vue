<template>
  <div class="list-page">
    <div class="page-header">
      <h2>合同模板</h2>
      <div class="header-actions">
        <el-button type="default" size="large" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    <div class="table-container">
      <el-table :data="templates" v-loading="loading" stripe border height="calc(100vh - 220px)" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="name" label="模板名称" min-width="200" sortable show-overflow-tooltip>
           <template #default="{ row }">
            <span style="font-weight: 500;">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="scenario" label="适用场景" width="180" sortable />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="createFromTemplate(row.id)">
              <el-icon><DocumentAdd /></el-icon>
              <span>基于此模板创建</span>
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
import { ElMessage } from 'element-plus';
import { Refresh, DocumentAdd } from '@element-plus/icons-vue';

const router = useRouter();
const loading = ref(false);
const templates = ref([]);

const fetchTemplates = async () => {
  loading.value = true;
  try {
    templates.value = await api.getContractTemplates();
  } catch (error) {
    console.error("加载合同模板失败:", error);
  } finally {
    loading.value = false;
  }
};

const handleRefresh = () => {
  ElMessage.success("正在刷新模板列表...");
  fetchTemplates();
};

const createFromTemplate = async (templateId) => {
  try {
    // 1. 先通过ID获取模板的完整数据 (包括 details)
    const template = await api.getContractTemplateById(templateId);
    
    // 2. 将独立字段和 details 字段重新组合成一个完整的 contract_data 结构
    const templateData = {
      名称: template.name,
      任务描述: template.description,
      作战场景: template.scenario,
      作战时间: {
        开始时间: template.start_time,
        结束时间: template.end_time,
      },
      ...template.details // 展开剩余的 details JSON
    };
    
    // 3. 将这个完整的对象字符串化后，通过查询参数传递给创建页
    router.push({ 
      name: 'ContractCreate', 
      query: { template: JSON.stringify(templateData) } 
    });
  } catch (error) {
    ElMessage.error("加载模板数据失败");
  }
};

onMounted(fetchTemplates);
</script>

<style scoped>
.list-page { padding: 24px; background-color: #f9fafb; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding: 16px 24px; background-color: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.page-header h2 { font-size: 24px; font-weight: 600; color: #1f2937; margin: 0; }
.header-actions { display: flex; gap: 16px; }
.table-container { background: #ffffff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); }
.el-button .el-icon + span { margin-left: 8px; }
</style>