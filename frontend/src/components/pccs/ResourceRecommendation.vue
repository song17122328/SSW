<template>
  <div class="resource-recommendation">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>智能资源推荐 (基于 PCCS Capability)</span>
          <el-button
            type="primary"
            size="small"
            @click="fetchRecommendations"
            :loading="loading"
            :icon="Refresh">
            刷新推荐
          </el-button>
        </div>
      </template>

      <div class="recommendation-body">
        <!-- 任务类型选择 -->
        <el-form :inline="true" class="filter-form">
          <el-form-item label="任务类型">
            <el-select
              v-model="selectedMissionType"
              placeholder="请选择任务类型"
              @change="fetchRecommendations"
              style="width: 150px">
              <el-option label="巡逻" value="patrol" />
              <el-option label="打击" value="strike" />
              <el-option label="反导" value="air_defense" />
              <el-option label="侦察" value="recon" />
            </el-select>
          </el-form-item>

          <el-form-item label="最小效能">
            <el-slider
              v-model="minEffectiveness"
              :min="0"
              :max="100"
              :step="5"
              :format-tooltip="formatTooltip"
              @change="fetchRecommendations"
              style="width: 200px" />
          </el-form-item>

          <el-form-item>
            <el-tag type="info" effect="plain">
              效能阈值: {{ minEffectiveness }}%
            </el-tag>
          </el-form-item>
        </el-form>

        <!-- 推荐结果 -->
        <div v-if="!loading && recommendations.length > 0" class="recommendations-list">
          <el-alert
            :title="`为「${translateMissionType(selectedMissionType)}」任务找到 ${recommendations.length} 个推荐资源`"
            type="success"
            :closable="false"
            show-icon
            style="margin-bottom: 15px" />

          <el-table
            :data="recommendations"
            stripe
            highlight-current-row
            @row-click="handleRowClick"
            style="width: 100%; cursor: pointer">
            <el-table-column type="index" label="#" width="50" />

            <el-table-column prop="name" label="资源名称" min-width="200">
              <template #default="{ row }">
                <div class="resource-name">
                  <el-icon :size="16" style="margin-right: 5px">
                    <Ship v-if="row.resource_type === 'platform'" />
                    <Tools v-if="row.resource_type === 'equipment'" />
                  </el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="category" label="类别" width="120">
              <template #default="{ row }">
                <el-tag size="small" effect="light">{{ row.category }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="match_effectiveness" label="效能评分" width="150">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.match_effectiveness * 100"
                  :color="getEffectivenessColor(row.match_effectiveness)"
                  :stroke-width="12">
                  <span style="font-size: 12px; font-weight: 600">
                    {{ (row.match_effectiveness * 100).toFixed(0) }}%
                  </span>
                </el-progress>
              </template>
            </el-table-column>

            <el-table-column label="关键能力" min-width="300">
              <template #default="{ row }">
                <div class="capabilities">
                  <el-tag
                    v-if="row.capability.strike_range > 0"
                    size="small"
                    type="danger"
                    effect="plain">
                    打击范围: {{ row.capability.strike_range }} km
                  </el-tag>
                  <el-tag
                    v-if="row.perception.detection_range > 0"
                    size="small"
                    type="success"
                    effect="plain">
                    探测范围: {{ row.perception.detection_range }} km
                  </el-tag>
                  <el-tag
                    v-if="row.capability.max_speed > 0"
                    size="small"
                    type="info"
                    effect="plain">
                    最大速度: {{ row.capability.max_speed }} 节
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="state.availability_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getAvailabilityColor(row.state.availability_status)"
                  size="small"
                  effect="light">
                  {{ translateAvailability(row.state.availability_status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click.stop="selectResource(row)"
                  :disabled="row.state.availability_status !== 'available'">
                  选择
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-empty
          v-if="!loading && recommendations.length === 0 && selectedMissionType"
          description="未找到符合条件的推荐资源"
          :image-size="100" />

        <el-empty
          v-if="!loading && !selectedMissionType"
          description="请选择任务类型以获取资源推荐"
          :image-size="100" />
      </div>
    </el-card>

    <!-- 资源详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedResource?.name"
      width="80%"
      destroy-on-close>
      <PCCSDisplay
        v-if="selectedResource"
        :resource-type="selectedResource.resource_type"
        :resource-id="selectedResource.resource_id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Refresh, Ship, Tools } from '@element-plus/icons-vue'
import api from '@/services/api'
import { ElMessage } from 'element-plus'
import PCCSDisplay from './PCCSDisplay.vue'

const props = defineProps({
  missionType: {
    type: String,
    default: ''
  },
  autoLoad: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['select'])

const loading = ref(false)
const recommendations = ref([])
const selectedMissionType = ref(props.missionType || 'patrol')
const minEffectiveness = ref(50) // 百分比

const detailDialogVisible = ref(false)
const selectedResource = ref(null)

// 获取推荐资源
const fetchRecommendations = async () => {
  if (!selectedMissionType.value) {
    ElMessage.warning('请先选择任务类型')
    return
  }

  loading.value = true
  try {
    const response = await api.searchPCCSByCapability(
      selectedMissionType.value,
      minEffectiveness.value / 100
    )

    if (response.success) {
      recommendations.value = response.resources
      ElMessage.success(`找到 ${response.count} 个推荐资源`)
    } else {
      ElMessage.error('获取推荐失败')
    }
  } catch (error) {
    console.error('获取资源推荐失败:', error)
    ElMessage.error('获取资源推荐失败')
  } finally {
    loading.value = false
  }
}

// 选择资源
const selectResource = (resource) => {
  emit('select', resource)
  ElMessage.success(`已选择资源: ${resource.name}`)
}

// 查看资源详情
const handleRowClick = (row) => {
  selectedResource.value = row
  detailDialogVisible.value = true
}

// 辅助函数
const getEffectivenessColor = (score) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  if (score >= 0.4) return '#f56c6c'
  return '#909399'
}

const getAvailabilityColor = (status) => {
  const colors = {
    available: 'success',
    busy: 'warning',
    reserved: 'info'
  }
  return colors[status] || 'info'
}

const translateMissionType = (type) => {
  const map = {
    patrol: '巡逻',
    strike: '打击',
    air_defense: '反导',
    recon: '侦察'
  }
  return map[type] || type
}

const translateAvailability = (status) => {
  const map = {
    available: '可用',
    busy: '忙碌',
    reserved: '预留'
  }
  return map[status] || status
}

const formatTooltip = (value) => {
  return `${value}%`
}

// 自动加载
if (props.autoLoad && selectedMissionType.value) {
  fetchRecommendations()
}

// 暴露方法给父组件
defineExpose({
  fetchRecommendations,
  getRecommendations: () => recommendations.value
})
</script>

<style scoped>
.resource-recommendation {
  margin: 20px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.recommendation-body {
  min-height: 200px;
}

.filter-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.recommendations-list {
  margin-top: 15px;
}

.resource-name {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.el-table {
  border-radius: 8px;
}

.el-table__row {
  cursor: pointer;
}

.el-table__row:hover {
  background-color: #f5f7fa;
}
</style>
