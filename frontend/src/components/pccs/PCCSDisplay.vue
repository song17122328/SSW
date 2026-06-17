<template>
  <div class="pccs-display" v-loading="loading">
    <div v-if="pccsData">
      <!-- PCCS 四维度标签页 -->
      <el-tabs v-model="activeTab" type="border-card" class="pccs-tabs">
        <!-- 1. Perception 感知 -->
        <el-tab-pane label="感知 (Perception)" name="perception">
          <div class="pccs-section">
            <el-descriptions :column="2" border>
              <!-- 环境感知 -->
              <el-descriptions-item label="探测范围" label-class-name="desc-label">
                <el-tag type="success" effect="light">{{ pccsData.perception.detection_range }} km</el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="探测类型" label-class-name="desc-label">
                <el-tag
                  v-for="type in pccsData.perception.detection_types"
                  :key="type"
                  :type="getDetectionTypeColor(type)"
                  effect="light"
                  size="small"
                  style="margin-right: 5px">
                  {{ translateDetectionType(type) }}
                </el-tag>
                <span v-if="pccsData.perception.detection_types.length === 0" class="text-muted">无</span>
              </el-descriptions-item>

              <el-descriptions-item label="跟踪容量" label-class-name="desc-label">
                {{ pccsData.perception.tracking_capacity }} 个目标
              </el-descriptions-item>

              <el-descriptions-item label="更新频率" label-class-name="desc-label">
                {{ pccsData.perception.update_frequency }} Hz
              </el-descriptions-item>

              <!-- 自身状态感知 -->
              <el-descriptions-item label="位置信息" :span="2" label-class-name="desc-label">
                <div class="position-info">
                  <span>经度: {{ pccsData.perception.position.longitude.toFixed(6) }}°</span>
                  <span>纬度: {{ pccsData.perception.position.latitude.toFixed(6) }}°</span>
                  <span>高度: {{ pccsData.perception.position.altitude }} m</span>
                </div>
              </el-descriptions-item>

              <el-descriptions-item label="航向" label-class-name="desc-label">
                {{ pccsData.perception.heading }}°
              </el-descriptions-item>

              <el-descriptions-item label="速度" label-class-name="desc-label">
                {{ pccsData.perception.speed }} 节
              </el-descriptions-item>

              <!-- 通信感知 -->
              <el-descriptions-item label="数据链状态" label-class-name="desc-label">
                <el-tag
                  :type="getDatalinkStatusColor(pccsData.perception.datalink_status)"
                  effect="light">
                  {{ translateDatalinkStatus(pccsData.perception.datalink_status) }}
                </el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="数据链类型" label-class-name="desc-label">
                <el-tag
                  v-for="type in pccsData.perception.datalink_type"
                  :key="type"
                  type="primary"
                  effect="light"
                  size="small"
                  style="margin-right: 5px">
                  {{ type }}
                </el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="通信范围" label-class-name="desc-label">
                {{ pccsData.perception.communication_range }} km
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 2. Control 控制 -->
        <el-tab-pane label="控制 (Control)" name="control">
          <div class="pccs-section">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="控制权限" label-class-name="desc-label">
                <el-tag :type="getControlAuthorityColor(pccsData.control.control_authority)" effect="light">
                  {{ translateControlAuthority(pccsData.control.control_authority) }}
                </el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="控制者ID" label-class-name="desc-label">
                {{ pccsData.control.controller_id || '未分配' }}
              </el-descriptions-item>

              <el-descriptions-item label="可用指令" :span="2" label-class-name="desc-label">
                <el-tag
                  v-for="cmd in pccsData.control.available_commands"
                  :key="cmd"
                  type="info"
                  effect="plain"
                  size="small"
                  style="margin: 2px">
                  {{ translateCommand(cmd) }}
                </el-tag>
              </el-descriptions-item>

              <el-descriptions-item label="API端点" label-class-name="desc-label">
                <code>{{ pccsData.control.api_endpoint }}</code>
              </el-descriptions-item>

              <el-descriptions-item label="控制协议" label-class-name="desc-label">
                {{ pccsData.control.control_protocol }}
              </el-descriptions-item>

              <el-descriptions-item label="消息格式" label-class-name="desc-label">
                {{ pccsData.control.message_format.toUpperCase() }}
              </el-descriptions-item>

              <el-descriptions-item label="指令延迟" label-class-name="desc-label">
                {{ pccsData.control.command_latency }} 秒
              </el-descriptions-item>

              <el-descriptions-item label="响应超时" label-class-name="desc-label">
                {{ pccsData.control.response_timeout }} 秒
              </el-descriptions-item>

              <el-descriptions-item label="优先级" label-class-name="desc-label">
                <el-rate
                  v-model="pccsData.control.priority_level"
                  :max="10"
                  disabled
                  show-score
                  text-color="#ff9900">
                </el-rate>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 3. Capability 能力 -->
        <el-tab-pane label="能力 (Capability)" name="capability">
          <div class="pccs-section">
            <!-- 感知能力 -->
            <el-card class="capability-card" shadow="never">
              <template #header>
                <div class="card-header-small">传感器能力</div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="传感器类型" :span="2" label-class-name="desc-label">
                  <el-tag
                    v-for="sensor in pccsData.capability.sensor_type"
                    :key="sensor"
                    type="success"
                    size="small"
                    style="margin: 2px">
                    {{ translateSensorType(sensor) }}
                  </el-tag>
                  <span v-if="pccsData.capability.sensor_type.length === 0" class="text-muted">无</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 武器能力 -->
            <el-card class="capability-card" shadow="never">
              <template #header>
                <div class="card-header-small">武器系统能力</div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="武器系统数量" label-class-name="desc-label">
                  {{ pccsData.capability.weapon_systems.length }} 种
                </el-descriptions-item>

                <el-descriptions-item label="打击范围" label-class-name="desc-label">
                  <el-tag type="danger" effect="light">{{ pccsData.capability.strike_range }} km</el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="打击类型" :span="2" label-class-name="desc-label">
                  <el-tag
                    v-for="type in pccsData.capability.strike_types"
                    :key="type"
                    type="danger"
                    size="small"
                    style="margin: 2px">
                    {{ translateStrikeType(type) }}
                  </el-tag>
                  <span v-if="pccsData.capability.strike_types.length === 0" class="text-muted">无</span>
                </el-descriptions-item>

                <el-descriptions-item label="火力值" label-class-name="desc-label">
                  <el-progress
                    :percentage="Math.min(pccsData.capability.firepower, 100)"
                    :color="getFirepowerColor(pccsData.capability.firepower)">
                  </el-progress>
                </el-descriptions-item>
              </el-descriptions>

              <!-- 武器系统详情 -->
              <el-table
                v-if="pccsData.capability.weapon_systems.length > 0"
                :data="pccsData.capability.weapon_systems"
                size="small"
                style="margin-top: 10px">
                <el-table-column prop="name" label="武器名称" />
                <el-table-column prop="type" label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag size="small" effect="plain">{{ row.type }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="range" label="射程 (km)" width="100" />
                <el-table-column prop="firepower" label="火力" width="80" />
              </el-table>
            </el-card>

            <!-- 机动能力 -->
            <el-card class="capability-card" shadow="never">
              <template #header>
                <div class="card-header-small">机动能力</div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="最大速度" label-class-name="desc-label">
                  {{ pccsData.capability.max_speed }} 节
                </el-descriptions-item>

                <el-descriptions-item label="巡航速度" label-class-name="desc-label">
                  {{ pccsData.capability.cruise_speed }} 节
                </el-descriptions-item>

                <el-descriptions-item label="续航力" label-class-name="desc-label">
                  {{ pccsData.capability.endurance }} km
                </el-descriptions-item>

                <el-descriptions-item label="机动性" label-class-name="desc-label">
                  <el-tag :type="getManeuverabilityColor(pccsData.capability.maneuverability)" effect="light">
                    {{ translateManeuverability(pccsData.capability.maneuverability) }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 任务适配性 (最重要) -->
            <el-card class="capability-card" shadow="never">
              <template #header>
                <div class="card-header-small">任务适配性 (用于资源匹配)</div>
              </template>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="适合任务类型" label-class-name="desc-label">
                  <el-tag
                    v-for="mission in pccsData.capability.mission_types"
                    :key="mission"
                    :type="getMissionTypeColor(mission)"
                    size="small"
                    style="margin: 2px">
                    {{ translateMissionType(mission) }}
                  </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="效能评分" :span="1" label-class-name="desc-label">
                  <div class="effectiveness-scores">
                    <div
                      v-for="(score, mission) in pccsData.capability.effectiveness_scores"
                      :key="mission"
                      class="score-item">
                      <span class="score-label">{{ translateMissionType(mission) }}:</span>
                      <el-progress
                        :percentage="score * 100"
                        :color="getEffectivenessColor(score)"
                        :stroke-width="12">
                        <span class="score-text">{{ (score * 100).toFixed(0) }}%</span>
                      </el-progress>
                    </div>
                  </div>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 4. State 状态 -->
        <el-tab-pane label="状态 (State)" name="state">
          <div class="pccs-section">
            <!-- 工作状态 -->
            <el-card class="state-card" shadow="never">
              <template #header>
                <div class="card-header-small">工作状态</div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="在线状态" label-class-name="desc-label">
                  <el-tag :type="getOperationalStatusColor(pccsData.state.operational_status)" effect="light">
                    {{ translateOperationalStatus(pccsData.state.operational_status) }}
                  </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="可用状态" label-class-name="desc-label">
                  <el-tag :type="getAvailabilityStatusColor(pccsData.state.availability_status)" effect="light">
                    {{ translateAvailabilityStatus(pccsData.state.availability_status) }}
                  </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="任务状态" label-class-name="desc-label">
                  <el-tag :type="getMissionStatusColor(pccsData.state.mission_status)" effect="light">
                    {{ translateMissionStatus(pccsData.state.mission_status) }}
                  </el-tag>
                </el-descriptions-item>

                <el-descriptions-item label="健康度" label-class-name="desc-label">
                  <el-progress
                    :percentage="pccsData.state.health_level * 100"
                    :color="getHealthColor(pccsData.state.health_level)">
                  </el-progress>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 能量状态 -->
            <el-card class="state-card" shadow="never">
              <template #header>
                <div class="card-header-small">能量状态</div>
              </template>
              <el-row :gutter="20">
                <el-col :span="8">
                  <div class="resource-gauge">
                    <div class="gauge-label">燃油余量</div>
                    <el-progress
                      type="dashboard"
                      :percentage="pccsData.state.fuel_level * 100"
                      :color="getResourceColor(pccsData.state.fuel_level)">
                      <template #default="{ percentage }">
                        <span class="gauge-value">{{ percentage }}%</span>
                      </template>
                    </el-progress>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="resource-gauge">
                    <div class="gauge-label">电池电量</div>
                    <el-progress
                      type="dashboard"
                      :percentage="pccsData.state.battery_level * 100"
                      :color="getResourceColor(pccsData.state.battery_level)">
                      <template #default="{ percentage }">
                        <span class="gauge-value">{{ percentage }}%</span>
                      </template>
                    </el-progress>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="resource-gauge">
                    <div class="gauge-label">弹药余量</div>
                    <el-progress
                      type="dashboard"
                      :percentage="pccsData.state.ammunition_level * 100"
                      :color="getResourceColor(pccsData.state.ammunition_level)">
                      <template #default="{ percentage }">
                        <span class="gauge-value">{{ percentage }}%</span>
                      </template>
                    </el-progress>
                  </div>
                </el-col>
              </el-row>
            </el-card>

            <!-- 网络状态 -->
            <el-card class="state-card" shadow="never">
              <template #header>
                <div class="card-header-small">网络状态</div>
              </template>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="网络延迟" label-class-name="desc-label">
                  {{ pccsData.state.network_latency }} ms
                </el-descriptions-item>

                <el-descriptions-item label="丢包率" label-class-name="desc-label">
                  {{ (pccsData.state.packet_loss_rate * 100).toFixed(2) }}%
                </el-descriptions-item>

                <el-descriptions-item label="连接强度" label-class-name="desc-label">
                  <el-progress
                    :percentage="pccsData.state.connection_strength * 100"
                    :stroke-width="8"
                    :show-text="false">
                  </el-progress>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 时间信息 -->
            <el-card class="state-card" shadow="never">
              <template #header>
                <div class="card-header-small">时间信息</div>
              </template>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="最后更新时间" label-class-name="desc-label">
                  {{ formatTime(pccsData.state.last_update_time) }}
                </el-descriptions-item>

                <el-descriptions-item label="运行时间" label-class-name="desc-label">
                  {{ pccsData.state.uptime }} 小时
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-empty v-if="!loading && !pccsData" description="暂无 PCCS 数据" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  resourceType: {
    type: String,
    required: true,
    validator: (value) => ['platform', 'equipment'].includes(value)
  },
  resourceId: {
    type: [String, Number],
    required: true
  }
})

const loading = ref(false)
const pccsData = ref(null)
const activeTab = ref('perception')

// 获取 PCCS 数据
const fetchPCCSData = async () => {
  loading.value = true
  try {
    const response = await api.getPCCSResource(props.resourceType, props.resourceId)
    if (response.success) {
      pccsData.value = response.resource
    } else {
      ElMessage.warning('无法加载 PCCS 数据')
    }
  } catch (error) {
    console.error('获取 PCCS 数据失败:', error)
    ElMessage.error('获取 PCCS 数据失败')
  } finally {
    loading.value = false
  }
}

// 颜色辅助函数
const getDetectionTypeColor = (type) => {
  const colors = { air: 'primary', surface: 'success', subsurface: 'warning' }
  return colors[type] || 'info'
}

const getDatalinkStatusColor = (status) => {
  const colors = { online: 'success', offline: 'danger', degraded: 'warning' }
  return colors[status] || 'info'
}

const getControlAuthorityColor = (authority) => {
  const colors = { manual: 'primary', 'semi-auto': 'warning', auto: 'success' }
  return colors[authority] || 'info'
}

const getFirepowerColor = (value) => {
  if (value >= 80) return '#f56c6c'
  if (value >= 50) return '#e6a23c'
  return '#67c23a'
}

const getManeuverabilityColor = (level) => {
  const colors = { low: 'info', medium: 'warning', high: 'success' }
  return colors[level] || 'info'
}

const getMissionTypeColor = (type) => {
  const colors = {
    patrol: 'primary',
    strike: 'danger',
    air_defense: 'warning',
    recon: 'success'
  }
  return colors[type] || 'info'
}

const getEffectivenessColor = (score) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  if (score >= 0.4) return '#f56c6c'
  return '#909399'
}

const getOperationalStatusColor = (status) => {
  const colors = { online: 'success', offline: 'danger', maintenance: 'warning', failure: 'danger' }
  return colors[status] || 'info'
}

const getAvailabilityStatusColor = (status) => {
  const colors = { available: 'success', busy: 'warning', reserved: 'info' }
  return colors[status] || 'info'
}

const getMissionStatusColor = (status) => {
  const colors = { idle: 'info', executing: 'warning', completed: 'success' }
  return colors[status] || 'info'
}

const getHealthColor = (level) => {
  if (level >= 0.8) return '#67c23a'
  if (level >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

const getResourceColor = (level) => {
  if (level >= 0.7) return '#67c23a'
  if (level >= 0.3) return '#e6a23c'
  return '#f56c6c'
}

// 翻译函数
const translateDetectionType = (type) => {
  const map = { air: '空中', surface: '水面', subsurface: '水下' }
  return map[type] || type
}

const translateDatalinkStatus = (status) => {
  const map = { online: '在线', offline: '离线', degraded: '降级' }
  return map[status] || status
}

const translateControlAuthority = (authority) => {
  const map = { manual: '手动', 'semi-auto': '半自动', auto: '自动' }
  return map[authority] || authority
}

const translateCommand = (cmd) => {
  const map = {
    navigate: '导航',
    detect: '探测',
    communicate: '通信',
    fire: '开火',
    defend: '防御',
    power_on: '开机',
    power_off: '关机',
    operate: '操作'
  }
  return map[cmd] || cmd
}

const translateSensorType = (type) => {
  const map = { radar: '雷达', sonar: '声呐', 'eo/ir': '光电/红外' }
  return map[type] || type
}

const translateStrikeType = (type) => {
  const map = {
    'anti-air': '防空',
    'anti-surface': '反舰',
    'anti-submarine': '反潜'
  }
  return map[type] || type
}

const translateManeuverability = (level) => {
  const map = { low: '低', medium: '中', high: '高' }
  return map[level] || level
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

const translateOperationalStatus = (status) => {
  const map = { online: '在线', offline: '离线', maintenance: '维护', failure: '故障' }
  return map[status] || status
}

const translateAvailabilityStatus = (status) => {
  const map = { available: '可用', busy: '忙碌', reserved: '预留' }
  return map[status] || status
}

const translateMissionStatus = (status) => {
  const map = { idle: '空闲', executing: '执行中', completed: '已完成' }
  return map[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return 'N/A'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 监听 props 变化
watch(() => [props.resourceType, props.resourceId], () => {
  fetchPCCSData()
}, { immediate: false })

onMounted(() => {
  fetchPCCSData()
})
</script>

<style scoped>
.pccs-display {
  padding: 20px;
}

.pccs-tabs {
  margin-top: 20px;
}

.pccs-section {
  padding: 10px;
}

.capability-card,
.state-card {
  margin-bottom: 15px;
}

.card-header-small {
  font-weight: 600;
  font-size: 14px;
  color: #409eff;
}

.position-info {
  display: flex;
  gap: 15px;
}

.position-info span {
  font-size: 13px;
}

.effectiveness-scores {
  width: 100%;
}

.score-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.score-label {
  width: 80px;
  font-size: 13px;
  font-weight: 500;
}

.score-item .el-progress {
  flex: 1;
}

.score-text {
  font-size: 12px;
  font-weight: 600;
}

.resource-gauge {
  text-align: center;
  padding: 10px;
}

.gauge-label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 10px;
  color: #606266;
}

.gauge-value {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.text-muted {
  color: #909399;
  font-style: italic;
}

.desc-label {
  font-weight: 500 !important;
}

code {
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 3px;
  font-size: 12px;
  color: #e6a23c;
}

pre.preserve-format {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  margin: 0;
}
</style>
