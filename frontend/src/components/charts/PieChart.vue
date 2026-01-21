<!-- src/components/charts/PieChart.vue - 最终简化版 -->
<template>
  <div class="pie-chart-wrapper">
    <!-- 1. ECharts 图表容器 -->
    <v-chart class="chart-container" :option="option" autoresize />
    
    <!-- 2. 下方的自定义图例条 -->
    <div class="custom-legend-bar">
      <div v-for="item in data" :key="item.name" class="legend-item">
        <span class="legend-color-box" :style="{ backgroundColor: item.itemStyle.color }"></span>
        <span class="legend-name">{{ item.name }}:</span>
        <span class="legend-value">{{ formatNumber(item.value) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { PieChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { computed } from 'vue';

use([CanvasRenderer, PieChart, TitleComponent, TooltipComponent, LegendComponent]);

const props = defineProps({ data: Array });

// ECharts 配置 - 恢复到最简单的状态
const option = computed(() => ({
  tooltip: { 
    trigger: 'item', 
    formatter: '{a} <br/>{b} : {c} ({d}%)' 
  },
  
  // 使用 ECharts 默认的图例，它会自动处理位置和交互
  legend: {
    orient: 'vertical',
    left: 'left',
    top: 'top',
  },

  series: [{
    name: '数量统计',
    type: 'pie',
    radius: ['50%', '70%'],
    // 不再手动设置 center，让 ECharts 根据图例位置自动计算
    // center: ['50%', '50%'], 
    avoidLabelOverlap: false,
    label: { show: false, position: 'center' },
    emphasis: {
      label: {
        show: true,
        fontSize: '20',
        fontWeight: 'bold'
      }
    },
    labelLine: { show: false },
    data: props.data,
  }],
}));

function formatNumber(num) {
  return num ? num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : '0';
}
</script>

<style scoped>
/* 整体容器，使用 Flexbox 垂直布局 */
.pie-chart-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

/* 图表容器占据所有可用空间 */
.chart-container {
  flex-grow: 1;
  min-height: 0; /* 防止 flex item 溢出 */
  width: 100%;
}

/* 下方图例条的样式 */
.custom-legend-bar {
  display: flex;
  justify-content: space-around; /* 让各项均匀分布 */
  align-items: center;
  width: 100%;
  padding: 10px 0;
  border-top: 1px solid #f0f2f5; /* 加上一条细微的分割线 */
  margin-top: 10px; /* 与图表之间的间距 */
  flex-shrink: 0; /* 防止被压缩 */
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.legend-color-box {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-right: 8px;
  flex-shrink: 0;
}

.legend-name {
  color: #606266;
  margin-right: 6px;
}

.legend-value {
  color: #303133;
  font-weight: 600;
}
</style>