<template>
  <div class="detail-page" v-loading.fullscreen.lock="loading" element-loading-text="正在加载想定数据...">
    <div class="page-header">
      <h2>想定详情: {{ scenario.name }}</h2>
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </div>
    <div class="content-area">
      <div id="map-container" class="map-container"></div>
      <div class="sidebar">
        <h3>兵力部署</h3>
        <el-scrollbar height="calc(100vh - 200px)">
          <div v-for="team in ['RED', 'BLUE']" :key="team" class="team-section">
            <h4 :class="team.toLowerCase()">{{ team === 'RED' ? '红方' : '蓝方' }}兵力 ({{ getPlatformsByTeam(team).length }})</h4>
            <div 
              v-for="platform in getPlatformsByTeam(team)" 
              :key="platform.id" 
              class="platform-item"
              @click="focusOnPlatform(platform)"
              :class="{ active: activePlatform?.id === platform.id }"
            >
              <span class="platform-name">{{ platform.name }}</span>
              <span class="platform-type">{{ platform.type_name }}</span>
            </div>
          </div>
        </el-scrollbar>
      </div>
    </div>

   <el-dialog v-model="equipmentDialogVisible" :title="activeEquipment?.name || '装备详情'" width="60%">
      <div v-if="activeEquipment">
        <!-- 1. 基本信息部分 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="装备ID">{{ activeEquipment.equipment_id }}</el-descriptions-item>
          <el-descriptions-item label="装备类别">{{ activeEquipment.category }}</el-descriptions-item>
          
          <template v-for="(value, key) in activeEquipment.details" :key="key">
            <el-descriptions-item v-if="!['inputInfo', 'parameterList'].includes(key)" :label="key">
              {{ value }}
            </el-descriptions-item>
          </template>

        </el-descriptions>
        
        <!-- 2. inputInfo 折叠面板 -->
        <el-collapse v-if="parsedInputInfo(activeEquipment.details.inputInfo)" style="margin-top: 20px;">
          <el-collapse-item name="inputInfo">
            <template #title>
              <h4><el-icon><Grid /></el-icon> 详细技术参数 (InputInfo) - 点击展开/收起</h4>
            </template>
            <el-table :data="parsedInputInfo(activeEquipment.details.inputInfo)" size="small" border stripe max-height="400px">
              <el-table-column prop="name" label="参数名" width="220" fixed></el-table-column>
              <el-table-column prop="value" label="参数值"></el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>

        <!-- 3. parameterList 折叠面板 -->
        <el-collapse v-if="activeEquipment.details.parameterList && activeEquipment.details.parameterList.length > 0" style="margin-top: 10px;">
          <el-collapse-item name="parameterList">
            <template #title>
              <h4><el-icon><Paperclip /></el-icon> 挂载组件列表 (ParameterList) - 点击展开/收起</h4>
            </template>
            <div v-for="(item, index) in activeEquipment.details.parameterList" :key="item.id || index" class="sub-component">
              <h5>{{ item.name || `组件 ${index + 1}` }}</h5>
              <el-descriptions :column="1" border size="small">
                <!-- ** 核心修改：遍历子组件的属性 ** -->
                <template v-for="(value, key) in item" :key="key">
                  <el-descriptions-item :label="key">
                    <!-- ** 如果是 inputInfo，则格式化为 pre 标签 ** -->
                    <template v-if="key === 'inputInfo' && parsedInputInfo(value)">
                      <pre class="json-code-block">{{ formatJson(value) }}</pre>
                    </template>
                    <!-- 其他属性正常显示 -->
                    <template v-else>
                       {{ value }}
                    </template>
                  </el-descriptions-item>
                </template>
              </el-descriptions>
            </div>
          </el-collapse-item>
        </el-collapse>

      </div>
      <template #footer>
        <el-button @click="equipmentDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/services/api';
import L from 'leaflet';
import 'leaflet-rotatedmarker';
import 'leaflet/dist/leaflet.css';
import { ArrowLeft } from '@element-plus/icons-vue';
import { Grid, Paperclip } from '@element-plus/icons-vue'; // 引入新图标

// 解决 Leaflet 默认图标加载问题
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41],
    popupAnchor: [1, -34], shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const route = useRoute();
const router = useRouter();
const scenario = ref({});
const loading = ref(true);
const activePlatform = ref(null);

let map = null;
const markers = {};


// ** 2. 新增：对话框相关状态 **
const equipmentDialogVisible = ref(false);
const activeEquipment = ref(null);

// ** 新增：用于在 Popup 中点击装备时触发的函数 **
//    注意：我们需要在全局作用域暴露这个函数，以便 Popup 的 HTML 可以调用它
window.showEquipmentDetails = (platformId, equipmentId) => {
  const platform = scenario.value.platforms?.find(p => p.id === platformId);
  const equipment = platform?.equipments?.find(e => e.id === equipmentId);
  if (equipment) {
    activeEquipment.value = equipment;
    equipmentDialogVisible.value = true;
  }
};

// ** 新增：解析 inputInfo 字符串的辅助函数 **
const parsedInputInfo = (jsonString) => {
  try {
    const data = JSON.parse(jsonString);
    if (Array.isArray(data)) return data;
  } catch (e) {
    //
  }
  return null; // 如果不是合法的JSON数组，则不进行特殊渲染
};


const getPlatformsByTeam = (team) => {
  return scenario.value.platforms?.filter(p => p.team === team) || [];
};

const initializeMap = () => {
  // ** 核心修正：将地图初始化逻辑放回 nextTick 中 **
  nextTick(() => {
    if (map) { // 如果地图已存在，只清除标记层
        Object.values(markers).forEach(marker => marker.remove());
    } else { // 如果地图不存在，则创建
        map = L.map('map-container').setView([21.5, 127], 7);
        L.tileLayer('https://{s}.tile.jawg.io/jawg-dark/{z}/{x}/{y}{r}.png?access-token={accessToken}', {
            attribution: '<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank">© <b>Jawg</b>Maps</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            accessToken: 'gFKzkAWSmdodZoYLoSI7VmC4EbpNWaQiPh1Sxd4B4Oxz45J2WfQQMRZYi0HNfvuu'
        }).addTo(map);
    }

    // 绘制兵力
    scenario.value.platforms?.forEach(platform => {
        const color = platform.team === 'RED' ? '#F56C6C' : '#409EFF';
        const marker = L.marker([platform.lat, platform.lon], {
            rotationAngle: platform.heading || 0,
            icon: L.divIcon({
                className: 'arrow-icon',
                html: `<svg style="transform: rotate(180deg);" width="20" height="20" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path fill="${color}" d="M512 0L95.8 832h820.4L512 0z"/></svg>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        }).addTo(map);

        marker.on('click', () => focusOnPlatform(platform));
        markers[platform.id] = marker;
    });
  });
};
// ** 核心修改：focusOnPlatform 函数，构造可点击的 Popup 内容 **
const focusOnPlatform = async (platform) => {
  activePlatform.value = platform;

  if (map && markers[platform.id]) {
    const marker = markers[platform.id];
    map.flyTo(marker.getLatLng(), 12);

    try {
        // 如果已经加载过装备，则不再重复请求
        if (!platform.equipments) {
            platform.equipments = await api.getSimPlatformEquipments(platform.id);
        }
        
        // 构造 Popup 的 HTML 内容
        let content = `<h4>${platform.name}</h4>`;
        content += `<p>类型: ${platform.type_name} | 阵营: ${platform.team}</p>`;
        content += `<p>坐标: ${platform.lat.toFixed(4)}, ${platform.lon.toFixed(4)}</p>`;
        content += `<p>高度(alt): ${platform.alt}米 | 航向(heading): ${platform.heading}°</p>`;
        
        const sensors = platform.equipments.filter(e => e.category === 'sensor');
        const weapons = platform.equipments.filter(e => e.category === 'weapon');

        if (sensors.length > 0) {
            content += '<h5>传感器:</h5><ul>';
            sensors.forEach(s => {
                // ** 关键：为每个装备项添加 onclick 事件 **
                content += `<li><a href="#" onclick="window.showEquipmentDetails(${platform.id}, ${s.id})">${s.name}</a></li>`;
            });
            content += '</ul>';
        }

        if (weapons.length > 0) {
            content += '<h5>武器:</h5><ul>';
            weapons.forEach(w => {
                content += `<li><a href="#" onclick="window.showEquipmentDetails(${platform.id}, ${w.id})">${w.name}</a> (数量: ${w.details?.num || 'N/A'})</li>`;
            });
            content += '</ul>';
        }
        
        marker.bindPopup(content).openPopup();

    } catch (error) {
        marker.bindPopup(`<b>${platform.name}</b><br>装备信息加载失败`).openPopup();
        console.error("加载装备信息失败:", error);
    }
  }
};
// ** 新增：格式化JSON字符串的辅助函数 **
const formatJson = (jsonString) => {
  try {
    const data = JSON.parse(jsonString);
    // JSON.stringify 的第三个参数 '2' 表示使用2个空格进行缩进
    return JSON.stringify(data, null, 2);
  } catch (e) {
    return jsonString; // 如果解析失败，返回原始字符串
  }
};
onMounted(async () => {
  const scenarioId = route.params.id;
  if (scenarioId) {
    try {
      scenario.value = await api.getSimScenarioDetails(scenarioId);
      // ** 关键：直接调用 initializeMap，具体的 nextTick 已在函数内部处理 **
      initializeMap();
    } catch(error) {
      console.error("加载想定详情失败:", error);
    } finally {
      loading.value = false;
    }
  }
});
</script>

<style>
/* ... (全局样式不变) ... */
.arrow-icon {
  background: transparent;
  border: none;
}
</style>

<style scoped>
/* ... (scoped 样式不变) ... */
.detail-page { display: flex; flex-direction: column; height: calc(100vh - 50px); padding: 24px; background-color: #f0f2f5; box-sizing: border-box; }
.page-header { flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 22px; }
.content-area { flex-grow: 1; display: flex; gap: 16px; min-height: 0; }
.map-container { flex-grow: 1; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); }
.sidebar { width: 320px; flex-shrink: 0; background-color: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); }
.sidebar h3 { margin-top: 0; }
.team-section { margin-bottom: 20px; }
.team-section h4 { margin: 0 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid; }
.team-section h4.red { border-color: #F56C6C; }
.team-section h4.blue { border-color: #409EFF; }
.platform-item { display: flex; justify-content: space-between; padding: 10px 8px; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.platform-item:hover { background-color: #f5f7fa; }
.platform-item.active { background-color: #ecf5ff; border-left: 3px solid #409eff; padding-left: 5px; }
.platform-name { font-weight: 500; }
.platform-type { color: #909399; font-size: 12px; }

/* ** 新增：为格式化的 JSON 代码块添加样式 ** */
.json-code-block {
  background-color: #282c34; /* 深色背景 */
  color: #abb2bf; /* 柔和的文字颜色 */
  padding: 10px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  white-space: pre-wrap; /* 自动换行 */
  word-wrap: break-word;
  margin: 0;
}
/* 为折叠面板的标题添加一些样式 */
:deep(.el-collapse-item__header) h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 子组件样式 */
.sub-component {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}
.sub-component h5 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: bold;
}
.sub-component:last-child {
  margin-bottom: 0;
}


</style>