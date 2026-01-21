<template>
  <el-card class="step-card">
    <template #header>
      <div class="card-header-title">
        <el-icon><Opportunity /></el-icon>
        <h3>第一步：选择战场态势 (作战想定)</h3>
      </div>
    </template>
    <div v-loading="loading" class="scenario-grid">
      <div 
        v-for="scenario in scenarios" 
        :key="scenario.id"
        class="scenario-card"
        :class="{ active: selectedScenarioId === scenario.id }"
        @click="selectScenario(scenario)"
      >
        <div class="card-header">
          <el-icon><Compass /></el-icon>
          <h4>{{ scenario.name }}</h4>
        </div>
        <p class="description">{{ scenario.description || '暂无描述' }}</p>
        <div class="card-footer">
          <div class="info-tag">
            <el-icon><User /></el-icon>
            <span>兵力: {{ scenario.force_count }}</span>
          </div>
          <div class="info-tag">
            <el-icon><Clock /></el-icon>
            <span>{{ scenario.type || '未知类型' }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="scenarios.length === 0 && !loading" class="empty-state">
      <el-empty description="暂无可用的作战想定" />
    </div>
    <div class="step-actions">
      <el-button 
        type="primary" 
        size="large"
        :disabled="!selectedScenarioId" 
        @click="$emit('next', selectedScenario)"
      >
        下一步，配置任务参数
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import { ElMessage } from 'element-plus';
import { Opportunity, User, Clock, Compass } from '@element-plus/icons-vue';

// 定义组件可以触发的事件
const emit = defineEmits(['next']);

const loading = ref(true);
const scenarios = ref([]);
const selectedScenarioId = ref(null);
const selectedScenario = ref(null);

const fetchScenarios = async () => {
  loading.value = true;
  try {
    // 调用 API 获取所有想定列表
    scenarios.value = await api.getSimScenarios();
  } catch (error) {
    ElMessage.error("加载想定列表失败");
  } finally {
    loading.value = false;
  }
};

const selectScenario = (scenario) => {
  selectedScenarioId.value = scenario.id;
  selectedScenario.value = scenario;
};

// 组件挂载时获取数据
onMounted(fetchScenarios);
</script>

<style scoped>
.step-card { border-radius: 12px; }
.card-header-title { display: flex; align-items: center; gap: 10px; font-size: 18px; }
.scenario-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
  gap: 20px; 
  margin: 24px 0; 
}
.scenario-card { 
  border: 1px solid #e4e7ed; 
  border-radius: 8px; 
  padding: 20px; 
  cursor: pointer; 
  transition: all 0.3s ease; 
  background-color: #fff;
}
.scenario-card:hover { 
  transform: translateY(-5px); 
  box-shadow: 0 8px 16px rgba(0,0,0,0.1); 
}
.scenario-card.active { 
  border-color: #409eff; 
  background: #ecf5ff; 
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(64, 158, 255, 0.2);
}
.card-header { 
  display: flex; 
  align-items: center; 
  gap: 10px; 
  margin-bottom: 12px; 
}
.card-header .el-icon { font-size: 20px; color: #409eff; }
.card-header h4 { margin: 0; font-size: 16px; font-weight: 600; color: #303133; }
.description { 
  font-size: 14px; 
  color: #606266; 
  margin-bottom: 16px; 
  min-height: 42px; /* 保持卡片高度基本一致 */
  line-height: 1.5;
}
.card-footer { 
  display: flex; 
  justify-content: space-between; 
  font-size: 12px; 
  color: #909399; 
  padding-top: 12px;
  border-top: 1px solid #f0f2f5;
}
.info-tag { display: flex; align-items: center; gap: 4px; }
.step-actions { 
  display: flex; 
  justify-content: center; 
  margin-top: 24px; 
  padding-top: 24px; 
  border-top: 1px solid #e4e7ed; 
}
.empty-state {
  padding: 40px 0;
}
</style>