<template>
  <div class="selected-resources" v-if="resources.length > 0">
    <el-card shadow="never" class="selected-card">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon style="margin-right: 5px"><Check /></el-icon>
            已选择资源 ({{ resources.length }})
          </span>
          <el-button
            type="danger"
            size="small"
            text
            @click="clearAll">
            清空全部
          </el-button>
        </div>
      </template>

      <div class="resources-grid">
        <div
          v-for="(resource, index) in resources"
          :key="`${resource.resource_type}-${resource.resource_id}`"
          class="resource-card">
          <div class="resource-header">
            <div class="resource-title">
              <el-icon :size="18" style="margin-right: 8px">
                <Ship v-if="resource.resource_type === 'platform'" />
                <Tools v-if="resource.resource_type === 'equipment'" />
              </el-icon>
              <span class="resource-name">{{ resource.name }}</span>
            </div>
            <el-button
              type="danger"
              size="small"
              :icon="Close"
              circle
              @click="removeResource(index)" />
          </div>

          <div class="resource-info">
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="类别">
                <el-tag size="small" effect="light">{{ resource.category }}</el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="效能评分">
                <el-progress
                  :percentage="resource.match_effectiveness * 100"
                  :stroke-width="8"
                  :show-text="false"
                  :color="getEffectivenessColor(resource.match_effectiveness)" />
                <span class="effectiveness-text">{{ (resource.match_effectiveness * 100).toFixed(0) }}%</span>
              </el-descriptions-item>

              <el-descriptions-item label="打击范围" v-if="resource.capability.strike_range > 0">
                {{ resource.capability.strike_range }} km
              </el-descriptions-item>

              <el-descriptions-item label="探测范围" v-if="resource.perception.detection_range > 0">
                {{ resource.perception.detection_range }} km
              </el-descriptions-item>

              <el-descriptions-item label="最大速度" v-if="resource.capability.max_speed > 0">
                {{ resource.capability.max_speed }} 节
              </el-descriptions-item>

              <el-descriptions-item label="状态">
                <el-tag
                  :type="getStatusColor(resource.state.availability_status)"
                  size="small"
                  effect="light">
                  {{ translateStatus(resource.state.availability_status) }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="resource-actions">
            <el-button
              type="primary"
              size="small"
              text
              @click="viewDetails(resource)">
              查看详情
            </el-button>
          </div>
        </div>
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
import { Check, Close, Ship, Tools } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PCCSDisplay from './PCCSDisplay.vue'

const props = defineProps({
  resources: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['remove', 'clear'])

const detailDialogVisible = ref(false)
const selectedResource = ref(null)

// 移除单个资源
const removeResource = (index) => {
  ElMessageBox.confirm(
    '确定要移除该资源吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('remove', index)
    ElMessage.success('已移除资源')
  }).catch(() => {
    // 用户取消
  })
}

// 清空所有资源
const clearAll = () => {
  ElMessageBox.confirm(
    `确定要清空所有 ${props.resources.length} 个已选资源吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('clear')
    ElMessage.success('已清空所有资源')
  }).catch(() => {
    // 用户取消
  })
}

// 查看资源详情
const viewDetails = (resource) => {
  selectedResource.value = resource
  detailDialogVisible.value = true
}

// 辅助函数
const getEffectivenessColor = (score) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  if (score >= 0.4) return '#f56c6c'
  return '#909399'
}

const getStatusColor = (status) => {
  const colors = {
    available: 'success',
    busy: 'warning',
    reserved: 'info'
  }
  return colors[status] || 'info'
}

const translateStatus = (status) => {
  const map = {
    available: '可用',
    busy: '忙碌',
    reserved: '预留'
  }
  return map[status] || status
}
</script>

<style scoped>
.selected-resources {
  margin-top: 20px;
}

.selected-card {
  border: 2px solid #67c23a;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 15px;
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.resource-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background-color: #f9fafb;
  transition: all 0.3s;
}

.resource-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.resource-title {
  display: flex;
  align-items: center;
  flex: 1;
}

.resource-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.resource-info {
  margin-bottom: 12px;
}

.effectiveness-text {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.resource-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
}
</style>
