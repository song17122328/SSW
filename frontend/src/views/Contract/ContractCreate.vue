<!-- ContractCreate.vue -->
<template>
  <div class="list-page">
    <div class="page-header">
      <h2>合同创建</h2>
      <div class="header-actions">
        <!-- <el-button type="primary" plain @click="openTemplateDialog">
          <el-icon><Files /></el-icon>
          从模板选择
        </el-button> -->
        <el-button @click="handleResetAndAlert">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </div>
    <div class="steps-container">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="选择想定与类型" />
        <el-step title="配置合同参数" />
        <el-step title="确认发布" />
      </el-steps>
    </div>

    <div v-if="currentStep === 0" class="step-content">
      <el-card>
        <!-- 阶段一：选择作战想定 -->
        <div class="selection-phase" v-loading="scenariosLoading">
          <h3>第一步：请选择作战想定</h3>
          <div class="type-selection">
            <div 
              class="type-card" 
              :class="{ active: selectedScenario?.id === scenario.id }" 
              v-for="scenario in scenarios"
              :key="scenario.id" 
              @click="selectScenario(scenario)"
            >
              <!-- *** 核心修复 3：更换图标 *** -->
              <div class="type-icon" :class="getScenarioIconClass(scenario)">
                <el-icon>
                  <component :is="getScenarioIcon(scenario)" />
                </el-icon>
              </div>
              <h4>{{ scenario.name }}</h4>
              <p>{{ scenario.description || '暂无描述' }}</p>
            </div>
            <div v-if="scenarios.length === 0 && !scenariosLoading" class="empty-state">
              <el-empty description="暂无可用的作战想定" />
            </div>
          </div>
        </div>

        <el-divider />

        <!-- 阶段二：选择作战类型 -->
        <div class="selection-phase">
           <h3>第二步：请选择作战类型</h3>
          <div class="type-selection">
            <div 
              class="type-card" 
              :class="{ active: selectedCombatType === type.value }" 
              v-for="type in combatTypes"
              :key="type.value" 
              @click="selectCombatType(type.value)"
            >
              <div class="type-icon" :class="type.iconClass">
                <el-icon><component :is="type.icon" /></el-icon>
              </div>
              <h4>{{ type.label }}</h4>
              <p>{{ type.description }}</p>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <el-button 
            type="primary" 
            :disabled="!selectedScenario || !selectedCombatType" 
            @click="nextStep"
          >
            下一步
          </el-button>
        </div>
      </el-card>
    </div>

    <div v-if="currentStep === 1" class="step-content">
 <FandaoContract 
        v-if="selectedCombatType === 'defense'" 
        v-model="contractData" 
        :scenario-id="selectedScenario.id"
        :scenario-name="selectedScenario.name"
        :contract-type="selectedCombatType"  
        @next="nextStep" @back="prevStep" 
      />
      <XunluoContract 
        v-if="selectedCombatType === 'patrol'" 
        v-model="contractData" 
        :scenario-id="selectedScenario.id"
        :scenario-name="selectedScenario.name"
        :contract-type="selectedCombatType" 
        @next="nextStep" @back="prevStep" 
      />
      <DajiContract 
        v-if="selectedCombatType === 'strike'" 
        v-model="contractData" 
        :scenario-id="selectedScenario.id"
        :scenario-name="selectedScenario.name"
        :contract-type="selectedCombatType" 
        @next="nextStep" @back="prevStep" 
      />
      <ZhenchaContract 
        v-if="selectedCombatType === 'reconnaissance'" 
        v-model="contractData" 
        :scenario-id="selectedScenario.id"
        :scenario-name="selectedScenario.name"
        :contract-type="selectedCombatType"
        @next="nextStep" @back="prevStep" 
      />
    </div>


    <!-- 第三步：确认发布 -->
    <div v-if="currentStep === 2" class="step-content">
      <el-card>
        <template #header>
          <h3>合同预览</h3>
        </template>
        <div class="contract-preview">
          <div class="preview-section">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">合同名称：</span>
                <span class="value">{{ contractData.名称 }}</span>
              </div>
              <div class="info-item">
                <span class="label">作战类型：</span>
                <!-- *** 核心修复 2：使用正确的变量和函数 *** -->
                <span class="value">{{ getTypeLabel(selectedCombatType) }}</span>
              </div>
              <div class="info-item">
                <span class="label">作战场景：</span>
                <span class="value">{{ contractData.作战场景 }}</span>
              </div>
              <div class="info-item">
                <span class="label">任务描述：</span>
                <span class="value">{{ contractData.任务描述 }}</span>
              </div>
            </div>
          </div>


          <div class="preview-section">
            <h4>作战时间</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">开始时间：</span>
                <span class="value">{{ contractData.作战时间?.开始时间 || '未设置' }}</span>
              </div>
              <div class="info-item">
                <span class="label">结束时间：</span>
                <span class="value">{{ contractData.作战时间?.结束时间 || '未设置' }}</span>
              </div>
            </div>
          </div>

          <!-- PCCS 选中资源展示 -->
          <div class="preview-section" v-if="contractData.PCCS资源 && contractData.PCCS资源.length > 0">
            <h4>
              选中的 PCCS 资源
              <el-tag type="success" effect="light" size="small" style="margin-left: 10px">
                共 {{ contractData.PCCS资源.length }} 项
              </el-tag>
            </h4>
            <div class="pccs-resources-grid">
              <div v-for="(resource, index) in contractData.PCCS资源" :key="index" class="pccs-resource-card">
                <div class="resource-header">
                  <span class="resource-name">{{ resource.name }}</span>
                  <el-tag :type="getResourceTypeTag(resource.resource_type)" size="small">
                    {{ resource.resource_type === 'platform' ? '平台' : '装备' }}
                  </el-tag>
                </div>
                <div class="resource-info">
                  <div class="info-row">
                    <span class="label">类别：</span>
                    <span class="value">{{ resource.category }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">效能评分：</span>
                    <el-tag
                      :type="resource.match_effectiveness >= 0.8 ? 'success' : resource.match_effectiveness >= 0.6 ? 'warning' : 'info'"
                      size="small"
                    >
                      {{ (resource.match_effectiveness * 100).toFixed(0) }}%
                    </el-tag>
                  </div>
                  <div class="info-row" v-if="resource.capability && resource.capability.mission_types">
                    <span class="label">任务类型：</span>
                    <span class="value">{{ resource.capability.mission_types.join(', ') }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">状态：</span>
                    <el-tag
                      :type="resource.state.operational_status === '可用' ? 'success' : resource.state.operational_status === '维护' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ resource.state.operational_status }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="preview-section">
            <h4>详细配置</h4>
            <el-collapse>
              <el-collapse-item title="完整合同数据" name="1">
                <pre class="json-preview">{{ JSON.stringify(contractData, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" :loading="publishing" @click="publishContract">
            发布合同
          </el-button>
        </div>
      </el-card>
    </div>


    <!-- <el-dialog v-model="templateDialogVisible" title="选择合同模板" width="70%">
      <el-table :data="templates" v-loading="templatesLoading" stripe border height="400px">
        <el-table-column prop="name" label="模板名称" />
        <el-table-column prop="scenario" label="适用场景" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="selectTemplate(row.id)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
      </template>
    </el-dialog> -->
  </div>
</template>

<script setup>
import { ref, reactive, toRaw, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'; 
import api from '@/services/api';
import { useUserStore } from '@/stores/user';
// *** 核心修复 3.1：引入新图标 ***
import { Refresh, Files, Compass, Aim, Search, HelpFilled, Ship, Opportunity, TakeawayBox, Ship as ShipIcon, Opportunity as PlaneIcon } from '@element-plus/icons-vue' 
import FandaoContract from '@/components/contract/FandaoContract.vue'
import XunluoContract from '@/components/contract/XunluoContract.vue'
import DajiContract from '@/components/contract/DajiContract.vue'
import ZhenchaContract from '@/components/contract/ZhenchaContract.vue'



const currentStep = ref(0);
const publishing = ref(false);
let contractData = reactive({});

const scenarios = ref([]);
const scenariosLoading = ref(false);
const selectedScenario = ref(null);
const selectedCombatType = ref('');

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// --- 模板对话框状态 ---
const templateDialogVisible = ref(false);
const templatesLoading = ref(false);
const templates = ref([]);

// ** 新增：打开模板对话框并加载数据 **
// const openTemplateDialog = async () => {
//   templateDialogVisible.value = true;
//   if (templates.value.length === 0) { // 避免重复加载
//     templatesLoading.value = true;
//     try {
//       templates.value = await api.getContractTemplates();
//     } catch (error) {
//       ElMessage.error("加载模板列表失败");
//     } finally {
//       templatesLoading.value = false;
//     }
//   }
// };

// ** 新增：选择一个模板后的处理逻辑 **
// const selectTemplate = async (templateId) => {
//   try {
//     const template = await api.getContractTemplateById(templateId);

//     // 构造完整的 contract_data
//     const templateData = {
//       名称: template.name,
//       任务描述: template.description,
//       作战场景: template.scenario,
//       作战时间: {
//         开始时间: template.start_time,
//         结束时间: template.end_time,
//       },
//       ...template.details
//     };

//     // ** 直接填充 contractData **
//     Object.assign(contractData, templateData);

//     ElMessage.success("已从模板加载数据！");
//     templateDialogVisible.value = false; // 关闭对话框

//     // 自动跳转到第二步
//     const scenario = templateData.作战场景;
//     if (scenario) {
//       if (scenario.includes('反导')) selectedCombatType.value = 'defense';
//       else if (scenario.includes('巡逻')) selectedCombatType.value = 'patrol';
//       else if (scenario.includes('打击')) selectedCombatType.value = 'strike';
//       else if (scenario.includes('侦察')) selectedCombatType.value = 'reconnaissance';

//       if (selectedCombatType.value) {
//         currentStep.value = 1;
//       }
//     }

//   } catch (error) {
//     ElMessage.error("应用模板失败");
//   }
// };

// 作战类型配置
const combatTypes = [
  {
    value: 'defense',
    label: '反导',
    description: '对空反导防御任务',
    icon: HelpFilled,
    iconClass: 'defense'
  },
  {
    value: 'patrol',
    label: '巡逻',
    description: '对海、对空区域巡逻任务',
    icon: Compass,
    iconClass: 'patrol'
  },
  {
    value: 'strike',
    label: '打击',
    description: '对空、对海、全面打击任务',
    icon: Aim,
    iconClass: 'strike'
  },
  {
    value: 'reconnaissance',
    label: '侦察',
    description: '对海、对空侦察任务',
    icon: Search,
    iconClass: 'reconnaissance'
  }
]
// *** 核心修复 1.2：更新图标判断逻辑 ***
const getScenarioIcon = (scenario) => {
  const nameLower = scenario.name?.toLowerCase() || '';
  if (nameLower.includes('海')) 
    return ShipIcon;      // 使用 ShipIcon
  if (nameLower.includes('空')) return PlaneIcon;     // 使用 PlaneIcon
  return TakeawayBox; // 默认图标
};

const getScenarioIconClass = (scenario) => {
  const nameLower = scenario.name?.toLowerCase() || '';
  if (nameLower.includes('海')) return 'scenario-sea';   // 使用新的 class
  if (nameLower.includes('空')) return 'scenario-air';   // 使用新的 class
  return 'scenario-default';
};

// *** 核心修改 4：获取想定列表的逻辑 ***
const fetchScenarios = async () => {
    scenariosLoading.value = true;
    try {
        scenarios.value = await api.getSimScenarios();
        // console.log(scenarios.value)
    } catch (error) {
        ElMessage.error("加载想定列表失败");
    } finally {
        scenariosLoading.value = false;
    }
};
// 在组件挂载时获取想定列表
onMounted(fetchScenarios);
// --- 方法 ---
function selectScenario(scenario) {
  selectedScenario.value = scenario;
}

function selectCombatType(type) {
  selectedCombatType.value = type;
}

function nextStep() {
  if (currentStep.value < 2) {
    if (currentStep.value === 0) {
      contractData.scenarioId = selectedScenario.value.id;
      contractData.scenarioName = selectedScenario.value.name;
      contractData.作战类型 = selectedCombatType.value;
    }
    currentStep.value++;
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

// *** 核心修复 1：重置函数中移除对不存在变量的引用 ***
function handleReset() {
  currentStep.value = 0;
  selectedScenario.value = null; // 正确
  selectedCombatType.value = ''; // 正确
  Object.keys(contractData).forEach(key => delete contractData[key]);
}

function handleResetAndAlert() {
  handleReset();
  ElMessage.success('表单已重置');
}


async function publishContract() {
  // 1. 基础验证
  if (Object.keys(contractData).length === 0) {
    ElMessage.warning('合同数据为空，无法发布！');
    return;
  }

  publishing.value = true;

  try {

    const payload = toRaw(contractData);
    
    const creater = userStore.userInfo.name;
    
    console.log("即将发送给后端的扁平化 payload:", JSON.stringify(payload, null, 2));

    // 3. 调用 API
    await api.createContract(payload, creater);

    ElMessage.success('合同已成功提交审批！');

    setTimeout(() => {
      router.push({ name: 'MyApplications' });
    }, 1500);

  } catch (error) {
    console.error('发布合同失败:', error);
    ElMessage.error('发布合同失败，请检查控制台获取详情。');
  } finally {
    publishing.value = false;
  }
}

onBeforeRouteLeave((to, from, next) => {
  handleReset();
  next();
});

// ** 确保 onMounted 逻辑存在，用于处理从模板创建 **
onMounted(() => {
  const templateQuery = route.query.template;
  if (templateQuery) {
    try {
      const templateData = JSON.parse(templateQuery);
      Object.assign(contractData, templateData);
      ElMessage.success("已从模板加载数据！");

      const scenario = templateData.作战场景;
      if (scenario) {
        if (scenario.includes('反导')) selectedCombatType.value = 'defense';
        else if (scenario.includes('巡逻')) selectedCombatType.value = 'patrol';
        else if (scenario.includes('打击')) selectedCombatType.value = 'strike';
        else if (scenario.includes('侦察')) selectedCombatType.value = 'reconnaissance';

        if (selectedCombatType.value) {
          currentStep.value = 1;
        }
      }
    } catch (error) {
      console.error("解析模板数据失败:", error);
      ElMessage.error("加载模板数据失败。");
    }
  }
});

// *** 核心修复 2.1：为预览页提供正确的辅助函数 ***
function getTypeLabel(type) {
  const typeObj = combatTypes.find(t => t.value === type);
  return typeObj ? typeObj.label : '';
}

// PCCS 资源类型标签颜色
function getResourceTypeTag(resourceType) {
  return resourceType === 'platform' ? 'primary' : 'success';
}

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



.steps-container {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.step-content { margin-bottom: 24px; }

/* *** 核心修改 5：为新的UI元素添加样式 *** */
.selection-phase {
  margin-bottom: 24px;
}
.selection-phase h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.type-selection {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 24px; /* 与标题保持间距 */
}


.type-card {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.type-card:hover {
  transform: translateY(-4px);
  border-color: #2563eb;
  box-shadow: 0 8px 25px rgba(37, 99, 235, 0.15);
}

.type-card.active {
  border-color: #2563eb;
  background: #eff6ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(37, 99, 235, 0.15);
}

.type-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #ffffff;
  margin: 0 auto 16px auto;
}


.type-icon.defense {
  background-color: #4caf50;
}

.type-icon.patrol {
  background-color: #2ecc71;
}

.type-icon.strike {
  background-color: #3498db;
}

.type-icon.reconnaissance {
  background-color: #f1c40f;
}

.type-card h4 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.type-card p {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
  line-height: 1.5;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.contract-preview {
  max-height: 600px;
  overflow-y: auto;
}

.preview-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.preview-section:last-child {
  border-bottom: none;
}

.preview-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 16px 0;
  padding-left: 8px;
  border-left: 3px solid #3498db;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid #e4e7ed;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  min-width: 100px;
  font-size: 14px;
  font-weight: bold;
  color: #2c3e50;
}

.value {
  font-size: 14px;
  color: #7f8c8d;
  word-break: break-word;
}

.json-preview {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #2c3e50;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* Element Plus 卡片样式覆盖 */
:deep(.el-card) {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

:deep(.el-card__header) {
  background: #f8fafc;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-card__header h3) {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

:deep(.el-steps) {
  margin: 0;
}

/* 按钮样式保持一致 */
:deep(.el-button) {
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-2px);
}
/* *** 核心修复 3.3：为默认想定图标添加样式 *** */
/* *** 核心修复 1.3：为新图标类名指定颜色 *** */
.type-icon.scenario-sea { background-color: #3498db; } /* 蓝色 */
.type-icon.scenario-air { background-color: #8e44ad; } /* 紫色 */
.type-icon.scenario-default { background-color: #7f8c8d; } /* 灰色 */

/* PCCS 资源展示样式 */
.pccs-resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.pccs-resource-card {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.pccs-resource-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
}

.resource-name {
  font-weight: 600;
  font-size: 15px;
  color: #2c3e50;
}

.resource-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.info-row .label {
  color: #909399;
  min-width: 80px;
}

.info-row .value {
  color: #606266;
  flex: 1;
}
</style>