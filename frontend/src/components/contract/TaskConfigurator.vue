<template>
  <el-card class="step-card">
    <template #header>
      <div class="card-header-title">
        <el-icon><Edit /></el-icon>
        <h3>第二步：配置任务参数</h3>
      </div>
      <p v-if="scenarioName" class="header-subtitle">基于想定: <strong>{{ scenarioName }}</strong></p>
    </template>
    
    <el-form :model="taskDetails" label-position="top" ref="formRef">
      <el-form-item label="任务名称" prop="taskName" :rules="[{ required: true, message: '请输入任务名称' }]">
        <el-input v-model="taskDetails.taskName" placeholder="例如：A区域巡逻任务" />
      </el-form-item>
      
      <el-form-item label="任务类型" prop="taskType" :rules="[{ required: true, message: '请选择任务类型' }]">
        <el-select v-model="taskDetails.taskType" @change="onTaskTypeChange" placeholder="请选择" style="width: 100%;">
          <el-option label="巡逻" value="patrol" />
          <el-option label="侦察" value="reconnaissance" />
          <el-option label="打击" value="strike" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="选择己方阵营" prop="side">
        <el-radio-group v-model="taskDetails.side">
          <el-radio-button value="RED">红方</el-radio-button>
          <el-radio-button value="BLUE">蓝方</el-radio-button>
        </el-radio-group>
      </el-form-item>
      
      <div v-if="['patrol', 'reconnaissance'].includes(taskDetails.taskType)">
        <el-form-item label="任务区域">
          <div class="map-interaction-row">
            <el-button @click="openMapEditor" :icon="FullScreen">打开地图编辑器</el-button>
            <span class="result-display" v-if="taskDetails.area && taskDetails.area.length > 0">
              <el-icon color="#67C23A"><Select /></el-icon>
              已划定 1 个区域 ({{ taskDetails.area.length }} 个顶点)
            </span>
            <span class="result-display placeholder" v-else>
               <el-icon><Warning /></el-icon>
              未划定区域
            </span>
          </div>
        </el-form-item>
      </div>
      
      <div v-if="taskDetails.taskType === 'strike'">
        <el-form-item label="打击目标">
          <div class="map-interaction-row">
            <el-button @click="openMapEditor" :icon="FullScreen">打开地图编辑器</el-button>
            <span class="result-display" v-if="taskDetails.targets && taskDetails.targets.length > 0">
               <el-icon color="#67C23A"><Select /></el-icon>
              已选择 {{ taskDetails.targets.length }} 个目标
            </span>
            <span class="result-display placeholder" v-else>
               <el-icon><Warning /></el-icon>
              未选择目标
            </span>
          </div>
        </el-form-item>
      </div>
    </el-form>

    <div class="step-actions">
      <el-button size="large" @click="$emit('back')">返回上一步</el-button>
      <el-button type="primary" size="large" @click="validateAndProceed">下一步，预览合同</el-button>
    </div>

    <!-- 地图编辑器弹窗 -->
    <MapEditor
      v-if="mapEditorVisible"
      :visible="mapEditorVisible"
      
      :scenario-id="scenarioId"
      
      :task-type="taskDetails.taskType"
      :side="taskDetails.side"
      :initial-area="taskDetails.area"
      :initial-targets="taskDetails.targets"
      @close="mapEditorVisible = false"
      @confirm="handleMapConfirm"
    />
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Edit, FullScreen, Select, Warning } from '@element-plus/icons-vue';
import MapEditor from './MapEditor.vue';

// *** 核心：必须正确定义 props 来接收父组件传来的值 ***
const props = defineProps({
  scenarioId: { 
    type: [String, Number], 
    required: true 
  },
  scenarioName: { 
    type: String, 
    default: '' 
  },
  modelValue: { 
    type: Object, 
    required: true 
  },
});
const emit = defineEmits(['update:modelValue', 'back', 'next']);

const formRef = ref(null);
const mapEditorVisible = ref(false);

// 直接在模板中使用 props.modelValue 也是可以的，但 computed 提供了更好的封装
const taskDetails = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const onTaskTypeChange = () => {
  taskDetails.value.area = [];
  taskDetails.value.targets = [];
};

const openMapEditor = () => {
  if (!taskDetails.value.taskType) {
    ElMessage.warning('请先选择任务类型');
    return;
  }
  mapEditorVisible.value = true;
};

const handleMapConfirm = (data) => {
  taskDetails.value.area = data.area;
  taskDetails.value.targets = data.targets;
  mapEditorVisible.value = false;
};

const validateAndProceed = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      if (['patrol', 'reconnaissance'].includes(taskDetails.value.taskType) && (!taskDetails.value.area || taskDetails.value.area.length === 0)) {
        ElMessage.warning('请为任务划定区域');
        return;
      }
      if (taskDetails.value.taskType === 'strike' && (!taskDetails.value.targets || taskDetails.value.targets.length === 0)) {
        ElMessage.warning('请为打击任务选择至少一个目标');
        return;
      }
      emit('next');
    } else {
      ElMessage.error('请填写所有必填项');
    }
  });
};
</script>

<style scoped>
.step-card { border-radius: 12px; }
.card-header-title { display: flex; align-items: center; gap: 10px; font-size: 18px; }
.header-subtitle { font-size: 14px; color: #909399; margin-top: 4px; }
.step-actions { display: flex; justify-content: space-between; margin-top: 24px; padding-top: 24px; border-top: 1px solid #e4e7ed; }
.map-interaction-row { display: flex; align-items: center; gap: 16px; }
.result-display { font-size: 14px; color: #606266; display: flex; align-items: center; gap: 6px; }
.result-display.placeholder { color: #c0c4cc; }
</style>