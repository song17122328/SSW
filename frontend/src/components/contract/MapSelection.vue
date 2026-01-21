<!-- src/components/contract/MapSelection.vue -->
<template>
  <div class="map-selection-container">
    <!-- 按钮只在非只读模式下显示 -->
    <div class="map-interaction-row" v-if="!isReadonly">
      <el-button @click="openMapEditor" :icon="FullScreen">打开地图编辑器</el-button>
    </div>

    <!-- 结果展示区 -->
    <!-- 1. 目标选择的标签列表 -->
    <div v-if="modelValue && modelValue.length > 0" class="selection-result-tags">
      <template v-if="isTargetSelectionMode"> 
          <el-tag 
            v-for="target in modelValue"
            :key="target.id"
            class="result-tag"
            :type="enemySide === 'RED' ? 'danger' : 'primary'"
          >
          {{ target.name }} (ID: {{ target.id }})
          </el-tag>
        </template>
    </div>

    <!-- *** 核心修改 1：为区域选择添加详细的预览卡片 *** -->
    <!-- 2. 区域选择的预览卡片 -->
    <div v-if="mode === 'area' && areaCorners.topLeft" class="area-preview-card">
      <div class="preview-box">
        <div class="corner top-left">
          <span>左上角</span>
          <small>{{ areaCorners.topLeft[0] }}, {{ areaCorners.topLeft[1] }}</small>
        </div>
        <div class="corner top-right">
          <span>右上角</span>
          <small>{{ areaCorners.topRight[0] }}, {{ areaCorners.topRight[1] }}</small>
        </div>
        <div class="corner bottom-left">
          <span>左下角</span>
          <small>{{ areaCorners.bottomLeft[0] }}, {{ areaCorners.bottomLeft[1] }}</small>
        </div>
        <div class="corner bottom-right">
          <span>右下角</span>
          <small>{{ areaCorners.bottomRight[0] }}, {{ areaCorners.bottomRight[1] }}</small>
        </div>
      </div>
    </div>

    <!-- 如果没有任何选择，显示提示信息 -->
    <div v-if="!modelValue || modelValue.length === 0" class="placeholder-info">
        <!-- *** 核心修复 2：更新这里的 v-if 条件 *** -->
        <el-tag type="info" v-if="isReadonly && isTargetSelectionMode">
            该合同未指定任何打击/拦截目标。
        </el-tag>
      <el-tag type="info" v-if="isReadonly && mode === 'area'">该合同未划定任何任务区域。</el-tag>
      <span v-if="!isReadonly" class="muted-text">
          <!-- *** 核心修复 3：更新这里的 v-if 条件 *** -->
          <template v-if="isTargetSelectionMode">请点击上方按钮选择打击/拦截目标。</template>
          <template v-if="mode === 'area'">请点击上方按钮划定任务区域。</template>
      </span>
    </div>

    <!-- 地图编辑器弹窗 -->
    <MapEditor
      v-if="mapEditorVisible"
      :visible="mapEditorVisible"
      :scenario-id="scenarioId"
      :task-type="taskType"
      :side="side"
      :initial-area="mode === 'area' ? modelValue : []"
      :initial-targets="mode === 'target' ? modelValue : []"
      @close="mapEditorVisible = false"
      @confirm="handleMapConfirm"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { FullScreen } from '@element-plus/icons-vue';
import MapEditor from './MapEditor.vue';

const props = defineProps({
  modelValue: Object, 
  mode: { type: String, required: true },
  scenarioId: { type: [String, Number] },
  taskType: { type: String, required: true },
  side: { type: String, required: true },
  isReadonly: { type: Boolean, default: false },
});
console.log("MapSelection.vue获取到的组件是:",props.modelValue)
const emit = defineEmits(['update:modelValue']);

const mapEditorVisible = ref(false);
const enemySide = computed(() => props.side === 'RED' ? 'BLUE' : 'RED');

// *** 核心修复 4：新增计算属性，用于判断是否是目标选择模式 ***
//    这个逻辑应该放在使用它的组件内部，而不是只放在 MapEditor 中
const isTargetSelectionMode = computed(() => props.mode === 'target');

// *** 核心修改 2：新增计算属性，将坐标点数组转换为四个角的对象 ***
const areaCorners = computed(() => {
    if (props.mode !== 'area' || !props.modelValue || props.modelValue.length !== 4) {
        return {}; // 如果不是区域模式或数据不合法，返回空对象
    }
    const area = props.modelValue;
    // 假设 MapEditor 返回的坐标点顺序是固定的（例如：左上, 右上, 右下, 左下）
    return {
        topLeft: [area[0].lng.toFixed(6), area[0].lat.toFixed(6)],
        topRight: [area[1].lng.toFixed(6), area[1].lat.toFixed(6)],
        bottomRight: [area[2].lng.toFixed(6), area[2].lat.toFixed(6)],
        bottomLeft: [area[3].lng.toFixed(6), area[3].lat.toFixed(6)],
    };
});

const openMapEditor = () => {
  if (!props.scenarioId) {
    ElMessage.error("错误：必须先选择一个想定才能打开地图编辑器！");
    return;
  }
  mapEditorVisible.value = true;
};

const handleMapConfirm = (data) => {
  if (props.mode === 'area') {
    emit('update:modelValue', data.area);
  } else if (props.mode === 'target') {
    emit('update:modelValue', data.targets);
  }
  mapEditorVisible.value = false;
};

// *** 核心修改 4：移除不再需要的 removeTarget 方法 ***
</script>

<style scoped>
.map-selection-container {
    width: 100%;
}
.map-interaction-row { 
    margin-bottom: 12px; 
}

/* *** 核心修改 5：为新UI添加样式 *** */
.selection-result-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}
.result-tag {
    transition: all 0.2s ease;
}
.result-tag:hover {
    transform: scale(1.05);
}

.placeholder-info {
    margin-top: 12px;
}
.muted-text {
  color: #909399;
  font-size: 14px;
}
/* *** 核心修改 3：为区域预览卡片添加样式，复用之前的风格 *** */
.area-preview-card {
  margin-top: 16px;
}
.preview-box {
  position: relative;
  width: 100%;
  height: 150px; /* 可以适当减小高度 */
  border: 2px dashed #94a3b8;
  border-radius: 8px;
  background: #fdfdfe;
}
.corner {
  position: absolute;
  padding: 8px;
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.2;
  min-width: 140px; /* 增加宽度以容纳坐标 */
  text-align: left;
}
.corner span {
  display: block;
  font-weight: 600;
  margin-bottom: 2px;
}
.corner small {
  display: block;
  opacity: 0.9;
  font-size: 10px;
  font-family: 'Courier New', Courier, monospace;
}
.top-left { top: 8px; left: 8px; }
.top-right { top: 8px; right: 8px; }
.bottom-left { bottom: 8px; left: 8px; }
.bottom-right { bottom: 8px; right: 8px; }
</style>