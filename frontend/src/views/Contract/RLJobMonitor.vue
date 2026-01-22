<!-- RLJobMonitor.vue -->
<template>
  <div class="page dashboard light">
    <header class="header">
      <h1 class="brand">
        <span class="glow">训练 / 评估 监控</span>
        <span class="sub">Mission RL Console</span>
      </h1>
      <div class="conn" :class="{on: connected}">
        <span class="dot"></span>{{ connected ? '已连接' : '未连接' }}
      </div>
    </header>

    <!-- 1. 合同选择 -->
    <section class="card glass">
      <div class="section-title">
        <span class="badge">1</span>
        <h2>选择并加载任务合同</h2>
      </div>

      <div class="row">
        <el-select 
          v-model="selectedTaskContractId" 
          placeholder="请选择一个任务合同" 
          class="grow"
          filterable
          :loading="contractsLoading"
          size="large"
          @change="confirmContractSelection"
        >
          <el-option 
            v-for="c in contracts" 
            :key="c.id" 
            :label="`${c.name} (ID: ${c.id})`" 
            :value="c.id" 
          />
        </el-select>
        <el-button class="ml" @click="loadContracts" :loading="contractsLoading" size="large">
          刷新列表
        </el-button>
      </div>

      <div v-if="contractDetailLoading" class="contract-preview">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="loadedContracts.length > 0" class="contract-preview">
        <div class="preview-header">
          <h4>
            <el-icon><Compass /></el-icon>
            基于想定: 
            <span v-if="scenarioNameLoading" class="scenario-name-loading">加载中...</span>
            <strong v-else>{{ associatedScenarioName }}</strong> 
            (ID: {{ firstLoadedContract.scenario_id }})
          </h4>
          <span>已加载 {{ loadedContracts.length }} 个合同</span>
        </div>
        <div class="loaded-contracts-list">
          <div v-for="contract in loadedContracts" :key="contract.id" class="contract-item">
            <div class="item-main">
              <span class="item-id">#{{ contract.id }}</span>
              <span class="item-name">{{ contract.name }}</span>
            </div>
            <div class="item-tags">
              <el-tag effect="dark" :color="getContractTypeColor(contract.contract_type)" class="type-tag">
                {{ formatContractType(contract.contract_type) }}
              </el-tag>
              <el-tag :type="contract.side === 'RED' ? 'danger' : 'primary'" size="small">
                {{ contract.side === 'RED' ? '红方' : '蓝方' }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- PCCS 资源展示 -->
        <div v-if="hasPCCSResources" class="pccs-section">
          <div class="pccs-header">
            <el-icon><DataBoard /></el-icon>
            <h4>PCCS 智能资源分配</h4>
            <el-tag type="success" effect="light" size="small">
              {{ totalPCCSResources }} 项资源
            </el-tag>
          </div>
          <div class="pccs-info-text">
            <el-icon><InfoFilled /></el-icon>
            强化学习算法将基于以下 PCCS 资源的 <strong>Capability</strong> (能力) 和 <strong>State</strong> (状态) 维度进行智能分配
          </div>
          <div class="pccs-resources-grid">
            <div v-for="(resource, index) in allPCCSResources" :key="index" class="pccs-resource-item">
              <div class="resource-badge">
                <el-tag :type="resource.resource_type === 'platform' ? 'primary' : 'success'" size="small">
                  {{ resource.resource_type === 'platform' ? '平台' : '装备' }}
                </el-tag>
              </div>
              <div class="resource-name">{{ resource.name }}</div>
              <div class="resource-metrics">
                <div class="metric">
                  <span class="metric-label">效能:</span>
                  <el-progress
                    :percentage="(resource.match_effectiveness * 100)"
                    :color="getEffectivenessColor(resource.match_effectiveness)"
                    :stroke-width="4"
                    :show-text="false"
                  />
                  <span class="metric-value">{{ (resource.match_effectiveness * 100).toFixed(0) }}%</span>
                </div>
                <div class="metric">
                  <span class="metric-label">状态:</span>
                  <el-tag
                    :type="resource.state.operational_status === '可用' ? 'success' : 'warning'"
                    size="small"
                  >
                    {{ resource.state.operational_status }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p class="note" v-else>请从上方列表选择一个任务合同，或从"待审批"页面批量进入。</p>
    </section>

    <!-- 2. 发起任务 -->
    <section class="card glass">
       <div class="section-title">
        <span class="badge">2</span>
        <h2>发起任务</h2>
      </div>
      <el-form :model="form" label-position="top" class="form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="Job ID">
              <el-input v-model.trim="form.jobId" placeholder="例如 01" size="large" required />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Trace Mode">
              <el-select v-model="form.traceMode" size="large" style="width: 100%;">
                <el-option value="episode" />
                <el-option value="step" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="自动评估 (Auto Eval)">
              <el-switch v-model="autoEval" size="large" style="height: 40px;"/>
            </el-form-item>
          </el-col>
        </el-row>
        
        <div class="grid" style="grid-template-columns: repeat(4, 1fr);">
            <el-form-item label="Episodes"><el-input v-model.number="form.episodes" type="number" min="1" size="large" /></el-form-item>
            <el-form-item label="Steps/Ep"><el-input v-model.number="form.stepsPerEp" type="number" min="1" size="large" /></el-form-item>
            <el-form-item label="Epsilon"><el-input v-model.number="form.epsilon" type="number" step="0.01" min="0" max="1" size="large" /></el-form-item>
            <el-form-item label="Epsilon Decay"><el-input v-model.number="form.epsilonDecay" type="number" step="0.001" min="0" max="1" size="large" /></el-form-item>
        </div>
        
        <div class="actions">
          <el-button type="primary" size="large" @click="startTrain" :disabled="!connected || loadedContracts.length === 0">开始训练</el-button>
          <el-button size="large" @click="startEval()" :disabled="!connected || loadedContracts.length === 0">仅评估</el-button>
        </div>
        <p class="note warn" v-if="loadedContracts.length === 0">请先加载任务合同再发起任务。</p>
      </el-form>
    </section>

    <!-- 3. 查看历史 -->
    <section class="card glass">
      <div class="section-title">
        <span class="badge">3</span>
        <h2>查看历史</h2>
      </div>
      <div class="row">
        <input v-model.trim="queryId" class="input" placeholder="输入 Job ID 查看历史训练与评估结果">
        <button class="btn ghost" @click="viewHistory">查看</button>
        <span class="muted" v-if="queryNotFound">无</span>
      </div>
      <p class="note">说明：优先从本页已缓存的数据中查找；若没有则请求后端
        <code>/api/rl/jobs/{jobId}/train_trace</code> 与
        <code>/api/rl/jobs/{jobId}/eval_result</code>。若未实现接口或不存在该 Job，会显示“无”。</p>
    </section>

    <!-- 4. 训练进度 -->
    <section v-if="currentTrain" class="card glass">
      <div class="section-title">
        <span class="badge">4</span>
        <h2>训练进度 <small>Job {{ currentTrain }}</small></h2>
      </div>

      <div class="metrics">
        <div class="metric">
          <div class="k">回合数</div><div class="v">{{ episodes[currentTrain]?.length || 0 }}</div>
        </div>
        <div class="metric">
          <div class="k">最近奖励</div><div class="v">{{ lastReward(currentTrain) }}</div>
        </div>
        <div class="metric">
          <div class="k">最后 ε</div><div class="v">{{ (doneMap[currentTrain]?.last_epsilon ?? '-') }}</div>
        </div>
        <div class="metric trend" v-if="rewardSeries(currentTrain).length >= 2">
          <div class="k">趋势</div>
          <svg class="spark" viewBox="0 0 260 64" preserveAspectRatio="none">
            <path class="spark-fill" :d="sparkFillPath(rewardSeries(currentTrain), 260, 64)"/>
            <path class="spark-line" :d="sparkPath(rewardSeries(currentTrain), 260, 64)"/>
          </svg>
        </div>
      </div>

      <div class="table-wrap">
        <table class="table glass-table">
          <thead>
            <tr>
              <th>#Episode</th><th>Steps</th><th>Total Reward</th><th>Cover</th><th>Scarcity</th><th>Cost</th><th>Timeliness</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rec in episodes[currentTrain]" :key="`ep-${rec.episode}`">
              <td>{{ rec.episode }}</td>
              <td>{{ rec.steps }}</td>
              <td>{{ fmt(rec.reward?.total) }}</td>
              <td>{{ fmt(rec.reward?.components?.cover) }}</td>
              <td>{{ fmt(rec.reward?.components?.scarcity) }}</td>
              <td>{{ fmt(rec.reward?.components?.cost) }}</td>
              <td>{{ fmt(rec.reward?.components?.timeliness) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 评估结果 -->
    <section v-if="lastEval" class="card glass">
      <div class="section-title">
        <span class="badge">5</span>
        <h2>评估结果 <small>Job {{ lastEval.job_id }}</small></h2>
      </div>

      <div class="metrics">
        <div class="metric">
          <div class="k">总分</div><div class="v">{{ fmt(lastEval.reward?.total) }}</div>
        </div>
        <div class="metric">
          <div class="k">覆盖</div><div class="v">{{ fmt(lastEval.reward?.components?.cover) }}</div>
        </div>
        <div class="metric">
          <div class="k">稀缺</div><div class="v">{{ fmt(lastEval.reward?.components?.scarcity) }}</div>
        </div>
        <div class="metric">
          <div class="k">成本</div><div class="v">{{ fmt(lastEval.reward?.components?.cost) }}</div>
        </div>
      </div>

      <!-- PCCS 资源使用分析 -->
      <div v-if="hasPCCSResources" class="pccs-eval-section">
        <div class="pccs-eval-header">
          <el-icon><DataAnalysis /></el-icon>
          <h4>PCCS 智能分配分析</h4>
        </div>
        <div class="pccs-eval-info">
          <div class="eval-stat">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <div class="stat-label">PCCS 资源池</div>
              <div class="stat-value">{{ allPCCSResources.length }} 项资源</div>
            </div>
          </div>
          <div class="eval-stat">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
              <div class="stat-label">Capability 匹配</div>
              <div class="stat-value">
                <el-tag type="success" size="small">基于任务能力维度</el-tag>
              </div>
            </div>
          </div>
          <div class="eval-stat">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
              <div class="stat-label">State 优先级</div>
              <div class="stat-value">
                <el-tag type="success" size="small">优先可用状态</el-tag>
              </div>
            </div>
          </div>
        </div>
        <div class="pccs-eval-description">
          <el-icon><InfoFilled /></el-icon>
          <span>
            强化学习算法已根据 PCCS 资源的 <strong>Capability</strong> (能力) 维度自动匹配任务需求，
            并基于 <strong>State</strong> (状态) 维度优先分配可用资源，
            实现了 <strong>Perception</strong>-<strong>Control</strong>-<strong>Capability</strong>-<strong>State</strong> 四维度的智能决策。
          </span>
        </div>
      </div>

      <details class="details agg">
        <summary>按任务聚合的分配</summary>

        <div class="agg-wrap">
          <div
            v-for="(group, taskName) in aggPerTask"
            :key="taskName"
            class="task-card"
          >
            <header class="task-card__header">
              <h4 class="task-title">{{ taskName }}</h4>
              <div class="capsum">
                <span class="cap-chip cap-sense" v-if="group.sense.length">sense {{ group.sense.length }}</span>
                <span class="cap-chip cap-comm"  v-if="group.comm.length">comm {{ group.comm.length }}</span>
                <span class="cap-chip cap-act"   v-if="group.act.length">act {{ group.act.length }}</span>
                <span class="cap-chip cap-other" v-if="group.other.length">other {{ group.other.length }}</span>
              </div>
            </header>

            <div class="task-card__body">
              <div class="col" v-if="group.sense.length">
                <div class="col-title">感知</div>
                <ul class="res-list">
                  <li v-for="(x, idx) in group.sense" :key="'se'+idx" class="res-item">
                    <span class="dot dot-sense"></span>{{ x.resource_name }}
                  </li>
                </ul>
              </div>

              <div class="col" v-if="group.comm.length">
                <div class="col-title">通信</div>
                <ul class="res-list">
                  <li v-for="(x, idx) in group.comm" :key="'co'+idx" class="res-item">
                    <span class="dot dot-comm"></span>{{ x.resource_name }}
                  </li>
                </ul>
              </div>

              <div class="col" v-if="group.act.length">
                <div class="col-title">执行</div>
                <ul class="res-list">
                  <li v-for="(x, idx) in group.act" :key="'ac'+idx" class="res-item">
                    <span class="dot dot-act"></span>{{ x.resource_name }}
                  </li>
                </ul>
              </div>

              <div class="col" v-if="group.other.length">
                <div class="col-title">其它</div>
                <ul class="res-list">
                  <li v-for="(x, idx) in group.other" :key="'ot'+idx" class="res-item">
                    <span class="dot dot-other"></span>{{ x.resource_name }} <em class="cap-small">({{ x.capability }})</em>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </details>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox, ElSkeleton, ElDescriptions, ElDescriptionsItem, ElTag, ElIcon, ElSelect, ElOption, ElButton, ElForm, ElFormItem, ElInput, ElRow, ElCol, ElSwitch, ElProgress } from 'element-plus';
import { io } from 'socket.io-client';
import { Compass, DataBoard, InfoFilled, DataAnalysis } from '@element-plus/icons-vue';
import api from '@/services/api';

// --- State ---
const route = useRoute();
let socket = null;

// 记录已加入的房间，便于重连后自动恢复
const joinedRooms = new Set();

const connected = ref(false);
const autoEval = ref(true);

const contracts = ref([]);
const contractsLoading = ref(false);
const selectedTaskContractId = ref('');
const loadedContracts = ref([]); // 存储一个或多个加载的合同对象
const contractDetailLoading = ref(false);

const associatedScenarioName = ref('');
const scenarioNameLoading = ref(false);

const queryId = ref('');
const queryNotFound = ref(false);

const form = reactive({
  jobId: `job_${Date.now().toString().slice(-6)}`,
  episodes: 20,
  stepsPerEp: 64,
  epsilon: 0.2,
  epsilonDecay: 0.99,
  traceMode: 'episode',
});

const episodes = reactive({});
const doneMap = reactive({});
const evalMap = reactive({});
const trainToEval = reactive({});

const currentTrain = ref(null);
const lastEval = ref(null);

// --- Computed ---
const firstLoadedContract = computed(() => {
  return loadedContracts.value.length > 0 ? loadedContracts.value[0] : null;
});
const aggPerTask = computed(() => {
  if (!lastEval.value?.per_task_named) return {};
  const groups = {};
  Object.entries(lastEval.value.per_task_named).forEach(([taskName, list]) => {
    groups[taskName] = { sense: [], comm: [], act: [], other: [] };
    list.forEach(x => {
      const cap = (x.capability || '').toLowerCase();
      if (cap.includes('sense')) groups[taskName].sense.push(x);
      else if (cap.includes('comm')) groups[taskName].comm.push(x);
      else if (cap.includes('act')) groups[taskName].act.push(x);
      else groups[taskName].other.push(x);
    });
  });
  return groups;
});

// PCCS 资源相关 computed
const allPCCSResources = computed(() => {
  const resources = [];
  loadedContracts.value.forEach(contract => {
    if (contract.details && contract.details.PCCS资源 && Array.isArray(contract.details.PCCS资源)) {
      resources.push(...contract.details.PCCS资源);
    }
  });
  return resources;
});

const hasPCCSResources = computed(() => allPCCSResources.value.length > 0);

const totalPCCSResources = computed(() => allPCCSResources.value.length);

// --- Helpers ---
const pushLog = (s) => console.log(`[RL LOG | ${new Date().toLocaleTimeString()}] ${s}`);

const fmt = (v) => (v === undefined || v === null || isNaN(v) ? '-' : Number(v).toFixed(3));

const lastReward = (jid) => {
  const arr = episodes[jid] || [];
  return arr.length ? fmt(arr[arr.length - 1]?.reward?.total) : '-';
};

const resolveEvalKey = (jid) => {
  if (evalMap[jid]) return jid;
  const evalId = `${jid}_eval`;
  if (evalMap[evalId]) return evalId;
  const mapped = trainToEval[jid];
  if (mapped && evalMap[mapped]) return mapped;
  return null;
};

// spark helpers
const rewardSeries = (jid) => (episodes[jid] || []).map(r => (isNaN(Number(r?.reward?.total)) ? 0 : Number(r?.reward?.total)));
const sparkPath = (series, W, H) => {
  if (!series || series.length < 2) return '';
  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const step = W / (series.length - 1);
  let d = `M 0 ${H - ((series[0] - min) / span) * H}`;
  series.forEach((v, i) => {
    if (i > 0) {
      const x = i * step;
      const y = H - ((v - min) / span) * H;
      d += ` L ${x} ${y}`;
    }
  });
  return d;
};
const sparkFillPath = (series, W, H) => (!series || series.length < 2 ? '' : `${sparkPath(series, W, H)} L ${W} ${H} L 0 ${H} Z`);

// 加入房间（并记入 joinedRooms，便于重连恢复）
const joinJobRoom = (jobId) => {
  if (!socket || !jobId) return;
  socket.emit('join_job', { job_id: jobId });
  joinedRooms.add(jobId);
  pushLog(`已加入房间: ${jobId}`);
};

const loadContracts = async () => {
  contractsLoading.value = true;
  try {
    contracts.value = await api.getContracts();
    pushLog('[contracts] 合同列表加载成功');
  } catch (e) {
    ElMessage.error(`加载合同列表失败: ${e.message}`);
  } finally {
    contractsLoading.value = false;
  }
};

const fetchAssociatedScenarioName = async (scenarioId) => {
  if (!scenarioId) {
    associatedScenarioName.value = '未指定';
    return;
  }
  scenarioNameLoading.value = true;
  try {
    const scenarioDetails = await api.getSimScenarioDetails(scenarioId);
    associatedScenarioName.value = scenarioDetails.name;
  } catch (error) {
    associatedScenarioName.value = '获取失败';
    pushLog(`获取想定 #${scenarioId} 名称失败: ${error.message}`);
  } finally {
    scenarioNameLoading.value = false;
  }
};

const loadContractsByIds = async (ids, scenarioId) => {
  if (!ids || ids.length === 0) return;
  contractDetailLoading.value = true;
  loadedContracts.value = [];
  try {
    const detailPromises = ids.map(id => api.getContractById(id));
    const contractsDetails = await Promise.all(detailPromises);
    loadedContracts.value = contractsDetails;

    await fetchAssociatedScenarioName(scenarioId);

    if (loadedContracts.value.length > 0) {
      const firstName = loadedContracts.value[0].name.replace(/[\s()]/g, '_');
      form.jobId = `${firstName}_${Date.now().toString().slice(-4)}`;
      pushLog(`已自动填充 Job ID 为: ${form.jobId}`);
    }
  } catch (e) {
    ElMessage.error(`加载合同详情失败: ${e.message}`);
  } finally {
    contractDetailLoading.value = false;
  }
};

const confirmContractSelection = async () => {
  if (!selectedTaskContractId.value) return;
  const selectedContract = contracts.value.find(c => c.id === selectedTaskContractId.value);
  await loadContractsByIds([selectedTaskContractId.value], selectedContract?.scenario_id);
};

const connectSocket = () => {
  socket = io('http://localhost:5000', { transports: ['websocket'], withCredentials: true });

  socket.on('connect', () => {
    connected.value = true;
    pushLog('Socket.IO 已连接');
    // 断线重连后，把之前加入过的房间全部重新加入
    joinedRooms.forEach(jid => joinJobRoom(jid));
  });

  socket.on('disconnect', () => {
    connected.value = false;
    pushLog('Socket.IO 已断开');
  });
  
  socket.on('job/accepted', d => {
    pushLog(`任务已接受: ${JSON.stringify(d)}`);
    if (d.resolved_task_dir || d.resolved_resource_dir) {
      pushLog(`后端解析路径: task_dir=${d.resolved_task_dir || '-'}, resource_dir=${d.resolved_resource_dir || '-'}`);
    }
  });

  socket.on('job/error', d => {
    ElMessage.error(`任务错误: ${d.error || JSON.stringify(d)}`);
    pushLog(`任务错误: ${d.error || JSON.stringify(d)}`);
  });

  socket.on('train/episode', rec => {
    const jid = rec.job_id;
    if (!episodes[jid]) episodes[jid] = [];
    episodes[jid].push(rec);
    currentTrain.value = jid;
  });

  socket.on('train/done', d => {
    pushLog(`训练完成: ${JSON.stringify(d)}`);
    const jid = d.job_id;
    doneMap[jid] = {
      last_epsilon: d.last_epsilon ?? d.lastEpsilon,
      checkpoint: d.checkpoint
    };
    if (autoEval.value) {
      const evalId = `${jid}_eval`;
      trainToEval[jid] = evalId;
      startEval(doneMap[jid].checkpoint, evalId);
    }
  });

  socket.on('eval/result', d => {
    pushLog(`收到评估结果 (Job: ${d.job_id}), 总分: ${fmt(d?.reward?.total)}`);
    const ejid = d.job_id;
    evalMap[ejid] = d;
    if (d.meta && d.meta.from_train_job) {
      trainToEval[d.meta.from_train_job] = ejid;
    }
    // 直接展示最新一次评估（支持“仅评估”场景）
    lastEval.value = d;
  });
};

const createJobPayload = (jobType, extraParams = {}) => {
  const firstContract = loadedContracts.value[0];
  return {
    job_id: form.jobId,
    job_type: jobType,
    meta: {
      task_contract_ids: loadedContracts.value.map(c => c.id),
      scenario_id: firstContract.scenario_id,
    },
    ...extraParams
  };
};

const startTrain = async () => {
  if (!connected.value || loadedContracts.value.length === 0) return;

  // 如果有PCCS资源，显示确认对话框
  if (hasPCCSResources.value) {
    const platformCount = allPCCSResources.value.filter(r => r.resource_type === 'platform').length;
    const equipmentCount = allPCCSResources.value.filter(r => r.resource_type === 'equipment').length;
    const availableCount = allPCCSResources.value.filter(r => r.state.operational_status === '可用').length;

    const message = `
      <div style="text-align: left;">
        <p style="margin-bottom: 12px;"><strong>强化学习算法将基于以下 PCCS 资源进行智能分配：</strong></p>
        <ul style="line-height: 1.8; margin: 8px 0;">
          <li>📦 总资源数量：<strong>${allPCCSResources.value.length}</strong> 项</li>
          <li>🚢 平台资源：<strong>${platformCount}</strong> 个</li>
          <li>⚙️ 装备资源：<strong>${equipmentCount}</strong> 个</li>
          <li>✅ 可用状态：<strong>${availableCount}</strong> 项</li>
        </ul>
        <p style="margin-top: 16px; padding: 12px; background: #ecfdf5; border-left: 4px solid #10b981; border-radius: 4px; font-size: 13px; color: #065f46;">
          <strong>💡 智能分配机制：</strong><br/>
          算法将根据资源的 <strong>Capability</strong> (能力维度) 匹配任务需求，
          并考虑 <strong>State</strong> (状态维度) 优先选择可用资源。
        </p>
      </div>
    `;

    try {
      await ElMessageBox.confirm(message, '确认训练任务', {
        confirmButtonText: '开始训练',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: true,
        center: false,
      });
    } catch {
      return; // 用户取消了
    }
  }

  // ✅ 先加入训练房间
  joinJobRoom(form.jobId);

  const payload = createJobPayload('train', {
    train_params: {
      episodes: form.episodes,
      steps_per_ep: form.stepsPerEp,
      epsilon: form.epsilon,
      epsilon_decay: form.epsilonDecay,
      trace_mode: form.traceMode,
    }
  });
  socket.emit('submit_job', payload);
  pushLog(`发起训练任务: ${JSON.stringify(payload)}`);
  currentTrain.value = form.jobId;
  if (!episodes[form.jobId]) episodes[form.jobId] = [];
};

const startEval = (checkpoint = 'outputs/dqn.pt', jobId) => {
  if (!connected.value || loadedContracts.value.length === 0) return;
  const firstContract = loadedContracts.value[0];
  const jid = jobId || `${form.jobId}_eval`;

  // ✅ 先加入评估房间（关键修复）
  joinJobRoom(jid);

  const payload = {
    job_id: jid,
    job_type: 'eval',
    meta: {
      task_contract_ids: loadedContracts.value.map(c => c.id),
      scenario_id: firstContract.scenario_id,
      from_train_job: form.jobId,
    },
    // 兼容后端两种读取方式：eval_params 内的 policy；顶层 checkpoint
    eval_params: { policy: 'dqn' },
    checkpoint: checkpoint,
  };

  socket.emit('submit_job', payload);
  pushLog(`发起评估任务: ${JSON.stringify(payload)}`);
};

const viewHistory = async () => {
  const jid = queryId.value.trim();
  queryNotFound.value = false;
  if (!jid) return;

  const hasLocalTrain = Array.isArray(episodes[jid]) && episodes[jid].length > 0;
  const evalKeyLocal = resolveEvalKey(jid);

  if (hasLocalTrain || evalKeyLocal) {
    currentTrain.value = hasLocalTrain ? jid : null;
    lastEval.value = evalKeyLocal ? evalMap[evalKeyLocal] : null;
    pushLog(`从本地缓存加载历史 Job: ${jid}`);
    return;
  }

  pushLog(`本地无缓存，正在从后端拉取历史 Job: ${jid}`);
  let anyFetched = false;

  try {
    const trainTrace = await api.getTrainTrace(jid);
    if (Array.isArray(trainTrace) && trainTrace.length > 0) {
      episodes[jid] = trainTrace;
      currentTrain.value = jid;
      anyFetched = true;
    }
  } catch (e) {
    pushLog(`拉取训练历史(train_trace)失败: ${e.message}`);
  }

  const tryFetchEval = async (key) => {
    try {
      const evalResult = await api.getEvalResult(key);
      if (evalResult && typeof evalResult === 'object') {
        const k = evalResult.job_id || key;
        evalMap[k] = evalResult;
        if (evalResult.meta?.from_train_job) {
          trainToEval[evalResult.meta.from_train_job] = k;
        }
        lastEval.value = evalResult;
        return true;
      }
    } catch (e) {
      pushLog(`拉取评估结果(eval_result for ${key})失败: ${e.message}`);
    }
    return false;
  };

  const evalFetched = await tryFetchEval(jid) || await tryFetchEval(`${jid}_eval`);
  anyFetched = evalFetched || anyFetched;

  if (!anyFetched) {
    queryNotFound.value = true;
    currentTrain.value = null;
    lastEval.value = null;
    ElMessage.info(`未找到 Job ID 为 "${jid}" 的历史记录`);
  }
};

// 合同类型展示
const contractTypeMap = { defense: '反导', patrol: '巡逻', strike: '打击', reconnaissance: '侦察' };
const contractTypeColorMap = { defense: '#4caf50', patrol: '#2ecc71', strike: '#3498db', reconnaissance: '#f1c40f' };
const formatContractType = (type) => contractTypeMap[type] || type || '未知';
const getContractTypeColor = (type) => contractTypeColorMap[type] || '#909399';

// PCCS 效能颜色
const getEffectivenessColor = (effectiveness) => {
  if (effectiveness >= 0.8) return '#67c23a'; // 绿色
  if (effectiveness >= 0.6) return '#e6a23c'; // 橙色
  return '#909399'; // 灰色
};

// --- Lifecycle ---
onMounted(async () => {
  connectSocket();
  await loadContracts();
  const contractIdsStr = route.query.contract_ids;
  const scenarioId = route.query.scenario_id;
  if (contractIdsStr && scenarioId) {
    const contractIds = contractIdsStr.split(',').map(id => parseInt(id.trim(), 10));
    await loadContractsByIds(contractIds, scenarioId);
    if (loadedContracts.value.length > 0) {
      selectedTaskContractId.value = loadedContracts.value[0].id;
    }
  }
});

onBeforeUnmount(() => {
  if (socket) socket.disconnect();
});
</script>

<style scoped>
/* ---------- FLAT THEME (no gradients) ---------- */
.dashboard {
  --bg: #ffffff;
  --panel: #ffffff;
  --panel-border: #e5e7eb;

  --text-strong: #0f172a;
  --text: #111827;
  --text-muted: #64748b;
  --text-soft: #94a3b8;

  --primary: #2563eb;
  --success: #16a34a;
  --danger:  #dc2626;

  color: var(--text);
  background: var(--bg);
  min-height: 100vh;
}

.dashboard.light { color: var(--text); background: var(--bg); }

.glass {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  box-shadow: 0 4px 12px rgba(0,0,0,.05);
  backdrop-filter: none;
}

.page { max-width: 1200px; margin: 24px auto; padding: 0 24px; }

.header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.brand { display:flex; flex-direction:column; gap:6px; margin:0; }
.brand .glow { font-size: 28px; font-weight: 800; letter-spacing: .2px; color: var(--text-strong); }
.brand .sub { font-size: 12px; color: var(--text-muted); }

.conn {
  font-size: 12px; padding: 6px 12px; border-radius: 999px; background: #f1f5f9;
  color: var(--text-strong); border: 1px solid var(--panel-border);
  display: flex; align-items: center; gap: 8px;
}
.conn .dot { width:8px; height:8px; border-radius:50%; background:#9ca3af; }
.conn.on  { background:#dcfce7; color:#166534; border-color:#bbf7d0; }
.conn.on .dot { background:#22c55e; }

.card { border-radius: 16px; padding: 24px; margin: 16px 0; }
.section-title { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
.section-title h2 { margin:0; font-size:20px; font-weight:700; color: var(--text-strong); }

.badge {
  display:inline-flex; align-items:center; justify-content:center;
  width:28px; height:28px; font-size:14px; border-radius:50%;
  background:#eff6ff; color:#1e40af; font-weight:700;
  border:1px solid #bfdbfe;
}

.row { display:flex; align-items:center; gap:16px; margin:16px 0; }
.row .grow { flex-grow: 1; }
.row .ml { margin-left: 8px; }

.form .grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:20px; }
.actions { display:flex; gap:12px; margin-top:24px; }

:deep(.el-form-item) { margin-bottom: 20px; }
:deep(.el-form-item__label) {
  color: var(--text-muted);
  font-weight: 600;
  line-height: 1.5 !important;
  margin-bottom: 4px !important;
}

.metrics {
  display:grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap:16px; margin:16px 0 24px;
}
.metric { background:#f9fafb; border:1px solid #e5e7eb; border-radius:14px; padding:12px 16px; }
.metric .k { font-size:13px; font-weight:500; color: var(--text-muted); margin-bottom:4px; }
.metric .v { font-size:22px; font-weight:800; color: var(--text-strong); }

.table-wrap { overflow:auto; border-radius:14px; border:1px solid var(--panel-border); }
table { width:100%; border-collapse:separate; border-spacing:0; font-size:14px; }
thead th {
  position: sticky; top:0;
  background:#f8fafc;
  text-align:left; padding:12px 16px;
  font-weight:700; color: var(--text-muted);
  border-bottom:1px solid var(--panel-border);
}
tbody td {
  padding:12px 16px; border-bottom:1px dashed #e5e7eb; white-space:nowrap;
  color: var(--text-strong);
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background:#f8fafc; }

.contract-preview { margin-top:24px; background:#fff; border:1px solid var(--panel-border); border-radius:12px; padding:16px; }
.preview-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:16px; border-bottom:1px solid var(--panel-border); }
.preview-header h4 { margin:0; font-size:16px; font-weight:600; color:var(--text-strong); }
.preview-header span { font-size:14px; color: var(--text-muted); }
.scenario-name-loading { font-style: italic; color: var(--text-muted); }

.loaded-contracts-list { display:flex; flex-direction:column; gap:12px; }
.contract-item { display:flex; justify-content:space-between; align-items:center; padding:12px; background:#f8fafc; border-radius:8px; }
.item-main { display:flex; align-items:center; gap:12px; }
.item-id { font-size:13px; font-weight:500; color: var(--text-muted); background:#eef2f7; padding:4px 8px; border-radius:6px; }
.item-name { font-size:15px; font-weight:700; color: var(--text-strong); }
.item-tags { display:flex; align-items:center; gap:10px; }
.type-tag { color:#fff !important; font-weight:600; }

.note { font-size:13px; color: var(--text-muted); margin-top:16px; }
.note.warn { color: var(--danger); font-weight:600; }
.muted { color: var(--text-muted); margin-left:8px; }

.details summary { cursor:pointer; font-weight:700; color: var(--primary); }

.agg-wrap{ display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 10px; }
.task-card{ background:#ffffff; border:1px solid #eef2f7; border-radius:12px; }
.task-card__header{ display:flex; justify-content:space-between; align-items:center; padding:10px 12px; border-bottom:1px solid #eef2f7; background:#f8fafc; }
.task-title{ margin:0; font-size:14px; color: var(--text-strong); }
.capsum{ display:flex; gap:6px; flex-wrap:wrap; }
.cap-chip{ display:inline-flex; align-items:center; gap:4px; height:22px; padding:0 8px; border-radius:999px; font-size:12px; font-weight:700; color:#0f172a; }
.cap-sense{ background:#e6f4ff; }
.cap-comm { background:#efeaff; }
.cap-act  { background:#ffe7ea; }
.cap-other{ background:#e9fbeF; }

.task-card__body{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; padding:10px 12px; }
@media (max-width: 720px){ .task-card__body{ grid-template-columns: 1fr; } }
.col-title{ font-size:12px; font-weight:700; color:#64748b; margin-bottom:6px; }
.res-list{ list-style:none; padding:0; margin:0; }
.res-item{ display:flex; align-items:center; gap:8px; padding:6px 8px; margin:4px 0; border:1px dashed #e5e7eb; border-radius:10px; color: var(--text-strong); background:#ffffff; }
.res-item:hover{ background:#f8fafc; }
.dot{ width:8px; height:8px; border-radius:999px; display:inline-block; }
.dot-sense{ background:#38bdf8; }
.dot-comm { background:#a78bfa; }
.dot-act  { background:#fb7185; }
.dot-other{ background:#34d399; }
.cap-small{ font-style: normal; font-size: 12px; color: #64748b; margin-left: 4px; }

/* PCCS 资源展示样式 */
.pccs-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 2px dashed #e5e7eb;
}

.pccs-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pccs-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-strong);
}

.pccs-info-text {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-left: 4px solid #10b981;
  border-radius: 8px;
  font-size: 13px;
  color: #065f46;
  margin-bottom: 16px;
}

.pccs-info-text strong {
  color: #047857;
  font-weight: 700;
}

.pccs-resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.pccs-resource-item {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.pccs-resource-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.pccs-resource-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #3b82f6;
}

.pccs-resource-item:hover::before {
  opacity: 1;
}

.resource-badge {
  position: absolute;
  top: 10px;
  right: 10px;
}

.resource-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-strong);
  margin-bottom: 12px;
  padding-right: 60px;
}

.resource-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  min-width: 40px;
}

.metric-value {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-strong);
  margin-left: 8px;
}

.metric :deep(.el-progress) {
  flex: 1;
}

/* PCCS 评估结果展示样式 */
.pccs-eval-section {
  margin: 24px 0;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 2px solid #0ea5e9;
  border-radius: 12px;
}

.pccs-eval-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.pccs-eval-header h4 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #0c4a6e;
}

.pccs-eval-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.eval-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.eval-stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  font-size: 32px;
  line-height: 1;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-strong);
}

.pccs-eval-description {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 16px;
  background: white;
  border-left: 4px solid #0ea5e9;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}

.pccs-eval-description strong {
  color: #0c4a6e;
  font-weight: 700;
}
</style>
