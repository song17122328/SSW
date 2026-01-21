<template>
  <v-chart class="chart" :option="option" autoresize />
</template>
<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { computed } from 'vue';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent]);

const props = defineProps({ data: Object });

const option = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: props.data.labels, axisTick: { alignWithLabel: true } },
  yAxis: { type: 'value' },
  series: [{
    name: '数量',
    type: 'bar',
    barWidth: '60%',
    data: props.data.values.map((value, index) => ({
        value,
        itemStyle: { color: props.data.colors[index] }
    }))
  }]
}));
</script>
<style scoped>
.chart {
  height: 100%;
  width: 100%;
}
</style>