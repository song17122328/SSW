<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>仪表盘总览</h2>
      <el-button type="default" size="large" @click="refreshData" :icon="Refresh">
        刷新数据
      </el-button>
    </div>

    <!-- 第一行：核心数据统计卡片 -->
    <div class="stats-grid">
      <StatCard icon="Ship" title="平台总数" :value="dashboardStore.platformCount" color="#3498db" />
      <StatCard icon="Box" title="装备总数" :value="dashboardStore.equipmentCount" color="#2ecc71" />
      <StatCard icon="Document" title="合同总数" :value="dashboardStore.contractCount" color="#e67e22" />
      <StatCard icon="Opportunity" title="想定总数" :value="dashboardStore.scenarioCount" color="#9b59b6" />
    </div>

       <!-- 第二行：图表和快速操作 -->
    <div class="dashboard-content">
      <!-- 左侧内容区 -->
      <div class="content-left">
        <!-- 第一行：平台状态 / 装备状态 -->
        <div class="charts-row">
          <!-- 平台状态 -->
          <el-card class="dashboard-card" shadow="hover">
            <template #header><div class="card-header">平台状态</div></template>
            <div class="chart-container" v-loading="dashboardStore.loading">
              <pie-chart
                v-if="!dashboardStore.loading && dashboardStore.platformCount > 0"
                :data="platformStatusChartData"
              />
              <el-empty v-else description="暂无平台数据" :image-size="80" />
            </div>
          </el-card>

          <!-- 装备状态 -->
          <el-card class="dashboard-card" shadow="hover">
            <template #header><div class="card-header">装备状态</div></template>
            <div class="chart-container" v-loading="dashboardStore.loading">
              <pie-chart
                v-if="!dashboardStore.loading && dashboardStore.equipmentCount > 0"
                :data="equipmentStatusChartData"
              />
              <el-empty v-else description="暂无装备数据" :image-size="80" />
            </div>
          </el-card>
        </div>

        <!-- 第二行：平台分类 / 装备分类 -->
        <div class="charts-row">
          <!-- 平台分类 -->
          <el-card class="dashboard-card" shadow="hover">
            <template #header><div class="card-header">平台分类</div></template>
            <div class="chart-container" v-loading="dashboardStore.loading">
              <pie-chart
                v-if="!dashboardStore.loading && dashboardStore.platformCount > 0"
                :data="platformChartData"
              />
              <el-empty v-else description="暂无平台数据" :image-size="80" />
            </div>
          </el-card>

          <!-- 装备分类 -->
          <el-card class="dashboard-card" shadow="hover">
            <template #header><div class="card-header">装备分类</div></template>
            <div class="chart-container" v-loading="dashboardStore.loading">
              <pie-chart
                v-if="!dashboardStore.loading && dashboardStore.equipmentCount > 0"
                :data="equipmentTypeChartData"
              />
              <el-empty v-else description="暂无装备数据" :image-size="80" />
            </div>
          </el-card>
        </div>

        <!-- 第三行：合同状态（单独占一行）-->
        <el-card class="dashboard-card" shadow="hover">
          <template #header><div class="card-header">合同状态</div></template>
          <div class="chart-container" v-loading="dashboardStore.loading">
            <bar-chart
              v-if="!dashboardStore.loading && dashboardStore.contractCount > 0"
              :data="contractChartData"
            />
            <el-empty v-else description="合同数量为 0" :image-size="80" />
          </div>
        </el-card>
      </div>


      



      <!-- 右侧内容区 -->
      <div class="content-right">
        <!-- 快速操作 -->
        <!-- *** 核心修改: 添加 class="dashboard-card" *** -->
        <!-- Dashboard.vue -> <template> -> 快速操作 el-card -->
        <el-card class="dashboard-card" shadow="hover">
          <template #header><div class="card-header">快速操作</div></template>
          
          <!-- *** 核心修改区: 清理多余的按钮 *** -->
          <div class="actions-grid">
            
            <el-button class="action-btn" @click="$router.push({ name: 'PlatformList' })">
              <div class="action-btn-content">
                <el-icon><Ship /></el-icon>
                <span>平台列表</span>
              </div>
            </el-button>

            <el-button class="action-btn" @click="$router.push({ name: 'EquipmentList' })">
              <div class="action-btn-content">
                <el-icon><Box /></el-icon>
                <span>装备列表</span>
              </div>
            </el-button>

            <el-button class="action-btn" @click="$router.push({ name: 'ContractList' })">
              <div class="action-btn-content">
                <el-icon><Document /></el-icon>
                <span>合同列表</span>
              </div>
            </el-button>

            <el-button class="action-btn" @click="$router.push({ name: 'ScenarioList' })">
              <div class="action-btn-content">
                <el-icon><Opportunity /></el-icon>
                <span>想定列表</span>
              </div>
            </el-button>

          </div>
        </el-card>
        

        <!-- ========================================================== -->
        <!-- *** 新增：恢复系统信息卡片 *** -->
        <!-- ========================================================== -->
        <el-card class="dashboard-card" shadow="hover">
          <template #header><div class="card-header">系统信息</div></template>
          <div class="system-info">
            <div class="info-row">
              <span class="label">系统名称:</span>
              <span class="value">{{ systemStore.systemInfo.name }}</span>
            </div>
            <div class="info-row">
              <span class="label">版本:</span>
              <span class="value">{{ systemStore.systemInfo.version }}</span>
            </div>
            <div class="info-row">
              <span class="label">运行时长:</span>
              <span class="value">{{ systemStore.uptime }}</span>
            </div>
            <div class="info-row">
              <span class="label">当前角色:</span>
              <span class="value">{{ userStore.userInfo?.role === 'admin' ? '管理员' : '用户' }}</span>
            </div>
            <div class="info-row">
              <span class="label">系统状态:</span>
              <span class="value status-running">
                <span class="status-dot"></span>
                正常运行
              </span>
            </div>
          </div>
        </el-card>

        <!-- 最近活动 -->
        <!-- *** 核心修改: 添加 class="dashboard-card" *** -->
        <el-card class="dashboard-card" shadow="hover">
          <template #header><div class="card-header">最近活动</div></template>
          <div class="activity-list" v-loading="dashboardStore.loading">
            <div v-if="!dashboardStore.loading && dashboardStore.recentActivities.length === 0" class="empty-state">
              暂无活动
            </div>
            <div v-for="log in dashboardStore.recentActivities" :key="log.id" class="activity-item">
              <div class="activity-icon" :class="log.level">
                <el-icon v-if="log.level === 'info'"><InfoFilled /></el-icon>
                <el-icon v-else-if="log.level === 'success'"><SuccessFilled /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-message">{{ log.message }}</div>
                <div class="activity-time">{{ formatDateTime(log.timestamp) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>

import { computed, onMounted, onActivated } from 'vue'; 
import { useDashboardStore } from '@/stores/dashboard';
// ==========================================================
// *** 新增：导入 system 和 user store ***
// ==========================================================
import { useSystemStore } from '@/stores/system';
import { useUserStore } from '@/stores/user';
// ==========================================================
import { formatDateTime } from '@/utils/format';
import StatCard from '@/components/dashboard/StatCard.vue';
import PieChart from '@/components/charts/PieChart.vue';
import BarChart from '@/components/charts/BarChart.vue';
import { Refresh, Ship, Box, Document, Opportunity, InfoFilled, SuccessFilled } from '@element-plus/icons-vue';

const dashboardStore = useDashboardStore();

// ==========================================================
// *** 新增：创建 store 实例 ***
// ==========================================================
const systemStore = useSystemStore();
const userStore = useUserStore();
// ==========================================================

// 为图表准备数据
const platformChartData = computed(() => [
  { value: dashboardStore.platformStats.ship, name: '舰艇平台', itemStyle: { color: '#3498db' } },
  { value: dashboardStore.platformStats.aircraft, name: '航空平台', itemStyle: { color: '#2ecc71' } }
]);

// 平台状态图表数据
const platformStatusChartData = computed(() => [
  { value: dashboardStore.platformStatusStats.active, name: '可用', itemStyle: { color: '#27ae60' } },
  { value: dashboardStore.platformStatusStats.maintenance, name: '维护中', itemStyle: { color: '#f39c12' } },
  { value: dashboardStore.platformStatusStats.inactive, name: '已停用', itemStyle: { color: '#95a5a6' } },
]);

const contractChartData = computed(() => ({
  labels: ['待审批', '已批准', '已驳回'],
  values: [
    dashboardStore.contractStats.pending,
    dashboardStore.contractStats.approved,
    dashboardStore.contractStats.rejected
  ],
  colors: ['#f39c12', '#27ae60', '#e74c3c']
}));
// ==========================================================
// *** 新增：为装备状态饼图准备数据 ***
// ==========================================================
const equipmentStatusChartData = computed(() => [
  { value: dashboardStore.equipmentStatusStats.active, name: '可用', itemStyle: { color: '#27ae60' } },
  { value: dashboardStore.equipmentStatusStats.maintenance, name: '维护中', itemStyle: { color: '#f39c12' } },
  { value: dashboardStore.equipmentStatusStats.inactive, name: '已停用', itemStyle: { color: '#95a5a6' } },
]);
// ==========================================================

// ==========================================================
// *** 新增：为装备类型饼图准备数据 ***
// ==========================================================
const equipmentTypeChartData = computed(() => [
  { value: dashboardStore.equipmentTypeStats.sense, name: '感知类 (S)', itemStyle: { color: '#3498db' } },
  { value: dashboardStore.equipmentTypeStats.control, name: '控制类 (C)', itemStyle: { color: '#9b59b6' } },
  { value: dashboardStore.equipmentTypeStats.action, name: '执行类 (A)', itemStyle: { color: '#e74c3c' } },
]);
// ==========================================================

const refreshData = async () => {
  // 我们将异步请求逻辑统一放在这个函数里
  await dashboardStore.fetchDashboardData();
  // 可以在这里添加一些只有在手动刷新时才执行的逻辑
};

// onMounted: 只在组件第一次创建时调用
onMounted(() => {
  console.log('Dashboard component mounted for the first time.');
  dashboardStore.fetchDashboardData();
  dashboardStore.addActivity('info', '用户访问仪表盘');
});

// ==========================================================
// *** 核心修改：添加 onActivated 钩子 ***
// ==========================================================
// onActivated: 每次进入这个被缓存的组件时都会调用
onActivated(() => {
  console.log('Dashboard component has been activated.');
  // 在这里也调用数据刷新，确保每次进入页面数据都是最新的
  dashboardStore.fetchDashboardData();
});
</script>

<style scoped>
/* ========================================================== */
/* *** 核心修改区: 统一卡片样式 *** */
/* ========================================================== */

/* 1. 页面整体背景 */
.dashboard {
  /*
    为整个页面设置一个统一的内边距。
    这将成为所有内部元素对齐的基准线。
  */
  padding: 24px;
  background-color: #f4f6f8;
  min-height: calc(100vh - 60px);
}

.dashboard-header,
.stats-grid,
.dashboard-content {
  /*
    确保所有主布局块之间的垂直间距是一致的。
  */
  margin-bottom: 24px;
}
/* 最后一个块不需要下边距 */
.dashboard-content {
  margin-bottom: 0;
}

/* ========================================================== */
/* *** 2. 网格布局和卡片间距 (核心修正区) *** */
/* ========================================================== */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px; /* 统一使用 24px 间距 */
}

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px; /* 确保左右两栏之间的间距也是 24px */
  
  /* 关键：移除可能存在的 align-items，让 grid 自己处理对齐 */
  align-items: start; /* 顶部对齐 */
}

.content-left,
.content-right {
  display: flex;
  flex-direction: column;
  gap: 24px; /* 确保同一列内卡片之间的垂直间距也是 24px */
  padding: 0;
  margin: 0;
}

/* 
  ==========================================================
  *** 最终修正：强制重置所有子元素的 margin ***
  ==========================================================
  这里的 * 选择器会选中 .content-left 和 .content-right
  内部的所有直接子元素（也就是我们的 .dashboard-card）。
  我们强制将它们的外边距设置为 0，这样布局就完全由父级的
  gap 属性控制，消除了由外部样式引入的 margin 偏移。
*/
.content-left > *,
.content-right > * {
  margin: 0 !important;
}
/* ========================================================== */
/* *** 3. 卡片自身样式 (保持不变) *** */
/* ========================================================== */

.dashboard-card {
  background-color: #ffffff;
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  /* 
    !! 关键 !! 
    确保卡片本身没有设置任何外边距 (margin)，
    因为间距已经由父容器的 gap 属性统一管理了。
  */
    margin: 0 !important;
}


/* 3. 卡片头样式 (可选，但推荐) */
.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #34495e;
}
/* 覆盖 Element Plus 的默认 header padding */
:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}
:deep(.el-card__body) {
  padding: 20px;
}


/* ========================================================== */
/* *** 其他布局和细节样式 (保持或优化) *** */
/* ========================================================== */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h2 {
  font-size: 28px;
  color: #2c3e50;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.content-left,
.content-right {
  display: flex;
  flex-direction: column;
  gap: 24px;

  /* 确保这些容器没有内边距，这很重要 */
  padding: 0;

  /*
    我们也可以在这里加 !important 以防万一，
    但通常问题出在子元素（卡片）上。
  */
  margin: 0 !important;
}

/* ========================================================== */
/* *** 新增：图表并排展示的行布局 *** */
/* ========================================================== */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin: 0 !important;
}

.charts-row > * {
  margin: 0 !important;
}
/* ========================================================== */

.chart-container {
  height: 280px;
  /* 新增以下三行 */
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ========================================================== */
/* *** 快速操作卡片样式 - 深色主题 & 精确对齐 *** */
/* ========================================================== */

.quick-actions .actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

/* 1. el-button 作为容器，我们需要重置它的一些默认样式 */
.action-btn {
  margin-left: 0px;

  padding: 0; 
  width: 100%;
  height: 90px;
  border-radius: 8px;
  
  /* 2. 深色背景主题 */
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 80%); /* 深蓝灰色渐变 */
  border: 1px solid transparent; /* 初始无边框 */
  
  transition: all 0.2s ease-in-out;
}

/* 3. 我们自定义的内容容器，使用 Flexbox 实现完美对齐 */
.action-btn-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

/* 4. 图标和文字的颜色和样式 */
.action-btn-content .el-icon,
.action-btn-content span {
  color: #ffffff; /* 统一白色字体 */
  transition: all 0.2s ease-in-out;
}

.action-btn-content .el-icon {
  font-size: 26px; /* 稍微增大图标 */
  margin-bottom: 8px;
}

.action-btn-content span {
  font-size: 14px;
  font-weight: 500;
}


/* 5. 悬停效果 (Hover State) - 更有活力的效果 */
.action-btn:hover {
  transform: translateY(-5px) scale(1.02); /* 向上浮动并轻微放大 */
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  border-color: #4e6e8e; /* 悬停时显示一个亮一点的边框 */
  background: linear-gradient(135deg, #34495e 0%, #46627f 100%); /* 渐变色变亮 */
}

/* 鼠标悬停时，可以让图标和文字稍微变亮或改变颜色 */
.action-btn:hover .action-btn-content .el-icon,
.action-btn:hover .action-btn-content span {
  color: #ecf0f1; /* 悬停时变为更亮的白色 */
}

/* 覆盖 Element Plus 按钮点击时的默认边框颜色 */
.action-btn:focus,
.action-btn:active {
  border-color: #4e6e8e !important; 
  outline: none;
}

/* 最近活动样式 */
.activity-list {
  max-height: 280px; /* 调整高度以适应新的 padding */
  overflow-y: auto;
  padding-right: 10px; /* 为滚动条留出空间 */
}
.activity-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}
.activity-item:last-child {
  border-bottom: none;
}
.activity-icon {
  font-size: 18px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-right: 12px;
  flex-shrink: 0;
}
.activity-icon.info {
  background-color: #3498db;
}
.activity-icon.success {
  background-color: #2ecc71;
}
.activity-content .activity-message {
  font-size: 14px;
  color: #34495e;
  margin-bottom: 4px;
}
.activity-content .activity-time {
  font-size: 12px;
  color: #95a5a6;
}
.empty-state {
  color: #95a5a6;
  text-align: center;
  padding: 40px 0;
}

/* ========================================================== */
/* *** 新增：为带操作按钮的卡片头添加样式 *** */
/* ========================================================== */
.card-header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header-with-action span {
  font-size: 16px;
  font-weight: 600;
  color: #34495e;
}

/* ========================================================== */
/* *** 新增：系统信息卡片的样式 *** */
/* ========================================================== */
.system-info .info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 0; /* 调整 padding 使其与其他卡片内容高度更协调 */
  border-bottom: 1px solid #f0f2f5;
}
.system-info .info-row:last-child {
  border-bottom: none;
}

.system-info .label {
  font-size: 14px;
  color: #606266;
}

.system-info .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.status-running {
  color: #27ae60;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #27ae60;
  border-radius: 50%;
}
</style>