<template>
  <el-dialog
    :model-value="visible"
    title="地图任务编辑器"
    fullscreen
    :show-close="false"
    append-to-body
    class="map-editor-dialog"
  >
    <template #header="{ titleId, titleClass }">      
      <div class="dialog-header">
        <div class="header-left">
          <h4 :id="titleId" :class="titleClass">地图任务编辑器</h4>
          
          <!-- 工具栏已简化 -->
          <div v-if="isAreaTask" class="header-toolbar">
            <!-- 默认状态 -->
            <template v-if="!isDrawing">
              <el-button :icon="EditPen" @click="startPolygonDraw" type="primary" plain>
                绘制区域
              </el-button>
              <el-button 
                :icon="Delete" 
                @click="clearArea" 
                :disabled="localArea.length === 0"
                type="danger"
                plain
              >
                清除区域
              </el-button>
            </template>
            
            <!-- 绘制状态 -->
            <template v-else>
              <el-button :icon="Close" @click="cancelDrawing" plain>
                取消绘制
              </el-button>
            </template>
          </div>
        </div>

        <div class="header-right">
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="primary" @click="handleConfirm">确认并关闭</el-button>
        </div>
      </div>
    </template>

    <div class="map-editor-content" v-loading="loading" element-loading-text="正在加载想定地图...">
      <div id="fullscreen-map-container" class="map-container"></div>
      <div class="map-sidebar">
        <div class="sidebar-header">
          <h4>任务配置</h4>
        </div>
        <div class="sidebar-content">
          <p><strong>想定:</strong> {{ scenarioName }}</p>
          <p><strong>任务类型:</strong> {{ taskTypeMap[taskType] }}</p>
          <p><strong>己方阵营:</strong> <span :class="side.toLowerCase()">{{ side === 'RED' ? '红方' : '蓝方' }}</span></p>
          <el-divider />
          <div v-if="isAreaTask">
            <h5>任务区域 (四点法)</h5>
            <!-- 侧边栏提示已简化 -->
            <el-alert v-if="!isDrawing" title="请使用顶部工具栏的 '绘制区域' 按钮。" type="info" show-icon :closable="false" />
            <el-alert v-else :title="drawingPrompt" type="success" show-icon :closable="false" />
            <div class="point-list">
              <p><strong>已标记顶点:</strong> {{ drawnVertexCount }} / 4</p>
            </div>
          </div>

          
          <div v-if="isTargetSelectionTask">
            <h5>打击/拦截目标</h5>
            <el-alert title="请在地图上点击敌方单位进行选择。" type="info" show-icon :closable="false" />
            <div class="target-list">
              <p v-if="localTargets.length === 0" class="placeholder">当前已选目标: 0</p>
              <el-scrollbar v-else max-height="200px">
                <!-- *** 核心修改 2.1：动态设置标签颜色，并处理新数据结构 *** -->
                <el-tag 
                  v-for="target in localTargets" 
                  :key="target.id" 
                  closable 
                  @close="removeTarget(target.id)" 
                  style="margin: 2px;"
                  :type="enemySide === 'RED' ? 'danger' : 'primary'"
                >
                  {{ target.name }}
                </el-tag>
              </el-scrollbar>

            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
// 只引入需要的图标
import { EditPen, Delete, Close } from '@element-plus/icons-vue';
import api from '@/services/api';
import L from 'leaflet';
import 'leaflet-draw';
import 'leaflet/dist/leaflet.css';
import { ElMessage } from 'element-plus';

// Leaflet 默认图标设置
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41],
    popupAnchor: [1, -34], shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const props = defineProps({
  visible: Boolean,
  scenarioId: [String, Number],
  taskType: String,
  side: String, // 'RED' or 'BLUE'
  initialArea: Array,
  initialTargets: Array, // 现在期望是 [{ id, name }, ...]
});

const emit = defineEmits(['close', 'confirm']);

// --- 状态变量 ---
const loading = ref(false);
const scenario = ref(null);
let map = null;
let drawnItems = null;
let drawControlOptions = null;
let currentDrawer = null;
const markers = {};

const localArea = ref([]);
// *** 核心修改 2.2：localTargets 现在存储对象数组 ***
const localTargets = ref([]); // 格式将是: [{ id, name, lat, lon }, ...]

const isDrawing = ref(false);
const drawnVertexCount = ref(0);
const drawingPrompt = ref('请在地图上点击，标记第一个点。');

// --- 计算属性 ---
const taskTypeMap = { 
    patrol: '巡逻', 
    reconnaissance: '侦察', 
    strike: '打击',
    defense: '反导' // 添加反导的中文名
};
const isAreaTask = computed(() => ['patrol', 'reconnaissance'].includes(props.taskType));
// *** 核心修复 2：新增一个计算属性，用于判断是否是“目标选择”类型的任务 ***
const isTargetSelectionTask = computed(() => {
    // 在计算属性中也加入日志
    console.log(`[MapEditor] Computing isTargetSelectionTask with taskType: "${props.taskType}". Result:`, ['strike', 'defense'].includes(props.taskType));
    return ['strike', 'defense'].includes(props.taskType);
});

// *** 核心修改 2.3：计算敌方阵营 ***
const enemySide = computed(() => props.side === 'RED' ? 'BLUE' : 'RED');
const scenarioName = computed(() => scenario.value?.name || '加载中...');

// --- 事件处理 ---
const handleCancel = () => emit('close');
const handleConfirm = () => {
  // *** 核心修改 2.4：确认时传递完整的对象数组 ***
  emit('confirm', { area: localArea.value, targets: localTargets.value });
};

// const getTargetName = (targetId) => {
//   const target = scenario.value?.platforms?.find(p => p.id === targetId);
//   return target ? target.name : `目标ID: ${targetId}`;
// };

// --- 地图核心逻辑 ---
const initMap = () => {
  const mapContainer = document.getElementById('fullscreen-map-container');
  if (!mapContainer || map) return;

  map = L.map(mapContainer, { preferCanvas: true }).setView([30, 120], 5);
  L.tileLayer('https://{s}.tile.jawg.io/jawg-dark/{z}/{x}/{y}{r}.png?access-token={accessToken}', {
    attribution: '© JawgMaps © OpenStreetMap contributors',
    accessToken: 'gFKzkAWSmdodZoYLoSI7VmC4EbpNWaQiPh1Sxd4B4Oxz45J2WfQQMRZYi0HNfvuu'
  }).addTo(map);

  drawnItems = new L.FeatureGroup().addTo(map);
  
  if (localArea.value?.length > 0) {
    try {
      const polygon = L.polygon(localArea.value).addTo(drawnItems);
      map.fitBounds(polygon.getBounds());
    } catch (e) { console.error("恢复已有区域时出错:", e); }
  }

  // 移除 edit 配置
  drawControlOptions = {
    draw: {
      polygon: { 
        shapeOptions: { color: '#f39c12' }, 
        allowIntersection: false, 
        showArea: true,
      },
      polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false
    },
    edit: false // 彻底禁用编辑
  };
  
  // -- 事件监听 --
  map.on(L.Draw.Event.DRAWSTART, () => {
    isDrawing.value = true;
    drawnVertexCount.value = 0;
    drawingPrompt.value = '请在地图上点击，标记第 1 个点。';
  });

  map.on(L.Draw.Event.DRAWVERTEX, (e) => {
    const vertexCount = e.layers.getLayers().length;
    drawnVertexCount.value = vertexCount;
    
    if (vertexCount > 0) {
      drawingPrompt.value = `请继续点击，标记第 ${vertexCount + 1} 个点。`;
    }

    // 自动完成逻辑
    if (vertexCount >= 4) {
      if (currentDrawer) {
        setTimeout(() => {
          // 加一个判断，防止在快速操作下重复调用
          if (currentDrawer) currentDrawer.completeShape();
        }, 50);
      }
    }
  });

  map.on(L.Draw.Event.CREATED, (e) => {
    const layer = e.layer;
    const latlngs = layer.getLatLngs()[0].slice(0, 4);
    layer.setLatLngs(latlngs);
    drawnItems.addLayer(layer);
    
    localArea.value = latlngs.map(p => ({ lat: p.lat, lng: p.lng }));
    drawnVertexCount.value = latlngs.length;

    isDrawing.value = false;
    currentDrawer = null;
    ElMessage.success('区域绘制完成！');
  });
};

// --- 绘图控制函数 ---
const startPolygonDraw = () => {
  if (isDrawing.value) return;
  clearArea();
  currentDrawer = new L.Draw.Polygon(map, drawControlOptions.draw.polygon);
  currentDrawer.enable();
};

const cancelDrawing = () => {
  if (currentDrawer) {
    currentDrawer.disable();
    currentDrawer = null;
  }
  isDrawing.value = false;
  drawnVertexCount.value = 0;
  ElMessage.info('绘制已取消');
};

const clearArea = () => {
  if (drawnItems) drawnItems.clearLayers();
  localArea.value = [];
  drawnVertexCount.value = 0;
  if (isDrawing.value) {
    cancelDrawing();
  }
};

const drawPlatforms = () => {
  if (!map || !scenario.value?.platforms) return;
  
  Object.values(markers).forEach(m => m.remove());

  scenario.value.platforms.forEach(p => {
    // *** 核心修改 1.1：判断是否为敌方和我方 ***
    const isEnemy = p.team !== props.side;
    
    // *** 核心修改 2.5：检查目标是否已被选择 ***
    const isSelectedTarget = localTargets.value.some(t => t.id === p.id);

    const color = p.team === 'RED' ? '#F56C6C' : '#409EFF';

    // *** 核心修改 1.2：为不同阵营和状态设置不同的SVG样式 ***
    let svgStyle = 'transform: rotate(180deg); transition: all 0.2s ease;';
    if (isTargetSelectionTask.value) {
      if (isEnemy) {
        // 敌方单位默认高亮
        svgStyle += ' filter: drop-shadow(0 0 4px white); opacity: 1;';
        if (isSelectedTarget) {
          // 被选中的敌方单位，黄色超高亮
          svgStyle += ' filter: drop-shadow(0 0 8px yellow) scale(1.4);';
        }
      } else {
        // 我方单位变暗，不可交互
        svgStyle += ' opacity: 0.4;';
      }
    } else {
        // 非打击任务下，如果目标被选中，也给一点高亮
        if (isSelectedTarget) {
             svgStyle += ' filter: drop-shadow(0 0 6px yellow) scale(1.3);';
        }
    }

    const marker = L.marker([p.lat, p.lon], {
      icon: L.divIcon({
        className: 'arrow-icon',
        html: `<svg style="${svgStyle}" width="20" height="20" viewBox="0 0 1024 1024"><path fill="${color}" d="M512 0L95.8 832h820.4L512 0z"/></svg>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })
    }).addTo(map);

    // 只有在打击任务中，且是敌方单位时，才绑定点击事件
    if (isTargetSelectionTask.value && isEnemy) {
      marker.on('click', () => toggleTarget(p));
      marker.bindTooltip(p.name);
    } else {
      marker.bindPopup(`<b>${p.name}</b><br/>阵营: ${p.team === 'RED' ? '红方' : '蓝方'}`);
    }
    markers[p.id] = marker;
  });
};

const updateMapAfterVisible = () => {
  if (!map) return;
  setTimeout(() => {
    map.invalidateSize();
    const platformMarkers = Object.values(markers);
    if (drawnItems.getLayers().length > 0) {
       map.fitBounds(drawnItems.getBounds().pad(0.2));
    } else if (platformMarkers.length > 0) {
      const group = L.featureGroup(Object.values(markers));
      map.fitBounds(group.getBounds().pad(0.2));
    }
  }, 200);
};
// *** 核心修改 1.2：重构 toggleTarget 函数以保存位置信息 ***
const toggleTarget = (platform) => {
  const index = localTargets.value.findIndex(t => t.id === platform.id);
  if (index > -1) {
    localTargets.value.splice(index, 1);
  } else {
    // 关键：在这里存入 id, name, lat, 和 lon
    localTargets.value.push({ 
      id: platform.id, 
      name: platform.name,
      lat: platform.lat,
      lon: platform.lon,
    });
  }
  drawPlatforms();
};

// removeTarget 也需要用 findIndex
const removeTarget = (targetId) => {
  const index = localTargets.value.findIndex(t => t.id === targetId);
  if (index > -1) {
    localTargets.value.splice(index, 1);
  }
  drawPlatforms();
};

// --- Watcher ---
watch(() => props.visible, async (isVisible) => {
  if (isVisible) {
        console.log('[MapEditor] Props received:', {
        scenarioId: props.scenarioId,
        taskType: props.taskType,
        side: props.side,
    }); 
    loading.value = true;
    localArea.value = props.initialArea ? JSON.parse(JSON.stringify(props.initialArea)) : [];
    localTargets.value = props.initialTargets ? JSON.parse(JSON.stringify(props.initialTargets)) : [];
    
    if (!props.scenarioId) {
      ElMessage.error("错误：未提供想定ID，无法加载地图编辑器。");
      loading.value = false;
      return;
    }
    
    try {
      scenario.value = await api.getSimScenarioDetails(props.scenarioId);
      await nextTick();
      initMap();
      drawPlatforms();
      updateMapAfterVisible();
    } catch (e) {
      console.error("MapEditor 加载流程出错:", e);
      ElMessage.error("加载地图编辑器数据失败！");
    } finally {
      loading.value = false;
    }
  } else {
    if (map) {
      map.remove();
      map = null;
    }
    // 重置所有相关状态
    isDrawing.value = false;
    currentDrawer = null;
  }
}, { immediate: true });
</script>

<style>
/* ... 全局样式无变化 ... */
.map-editor-dialog.is-fullscreen { display: flex; flex-direction: column; }
.map-editor-dialog .el-dialog__header { padding: 0; margin-right: 0; flex-shrink: 0; }
.map-editor-dialog .el-dialog__body { padding: 0; flex-grow: 1; min-height: 0; overflow: hidden; }
.arrow-icon { background: transparent; border: none; }
</style>

<style scoped>
/* ... scoped 样式无变化 ... */
.dialog-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 15px 20px; 
  border-bottom: 1px solid #dcdfe6; 
}
.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}
.dialog-header h4 { margin: 0; font-size: 18px; }
.header-toolbar {
  display: flex;
  gap: 10px;
}
.map-editor-content { display: flex; height: 100%; width: 100%; }
.map-container { flex-grow: 1; height: 100%; }
.map-sidebar { width: 300px; flex-shrink: 0; padding: 15px; border-left: 1px solid #dcdfe6; display: flex; flex-direction: column; background-color: #f9fafb; }
.sidebar-header h4 { margin: 0 0 15px 0; }
.sidebar-content { flex-grow: 1; overflow-y: auto; font-size: 14px; }
.sidebar-content p { margin: 0 0 10px 0; }
.sidebar-content p strong { color: #303133; }
.sidebar-content span.red { color: #F56C6C; font-weight: bold; }
.sidebar-content span.blue { color: #409EFF; font-weight: bold; }
.target-list { margin-top: 10px; }
.target-list .placeholder { color: #909399; }
.point-list { margin-top: 15px; font-size: 14px; color: #606266; }
.point-list p { margin: 5px 0; }
</style>