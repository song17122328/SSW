    <template>
        <el-card>
        <template #header>
            <!-- 1. 在标题处显示想定名称 -->
            <h3>
                侦察任务配置
                <small v-if="scenarioName" class="header-subtitle">
                    (基于想定: {{ scenarioName }})
                </small>
            </h3>
        </template>

            <!-- 基本信息 -->
            <div class="form-section">
                <h4>基本信息</h4>
                <el-form :model="formData" label-width="120px">
                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-form-item label="合同名称" required>
                                <el-input v-model="formData.name" placeholder="请输入合同名称" :disabled="isReadonly" />
                            </el-form-item>
                        </el-col>

                        <el-col :span="12">
                            <el-form-item label="作战场景">
                                <el-select v-model="formData.scenario" style="width: 100%" @change="onScenarioChange" :disabled="isReadonly">
                                    <el-option label="对海侦察" value="对海侦察" />
                                    <el-option label="对空侦察" value="对空侦察" />
                                </el-select>
                            </el-form-item>
                        </el-col>

                                            <!-- *** 核心修改 2：添加己方阵营选择 *** -->
                        <el-col :span="12">
                            <el-form-item label="己方阵营" required>
                                <el-radio-group v-model="formData.side" :disabled="isReadonly">
                                    <el-radio-button value="RED">红方</el-radio-button>
                                    <el-radio-button value="BLUE">蓝方</el-radio-button>
                                </el-radio-group>
                            </el-form-item>
                        </el-col>

                    </el-row>
                    <el-form-item label="任务描述" required>
                        <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请描述侦察任务的具体要求和目标" :disabled="isReadonly" />
                    </el-form-item>
                </el-form>
            </div>

            <!-- 作战时间 -->
            <div class="form-section">
                <h4>作战时间</h4>
                <el-form :model="formData.operationTime" label-width="120px">
                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-form-item label="开始时间" required>
                                <el-date-picker v-model="formData.operationTime.startTime" type="datetime"
                                    placeholder="选择开始时间" format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                    style="width: 100%" :disabled="isReadonly" />
                            </el-form-item>
                        </el-col>
                        <el-col :span="12">
                            <el-form-item label="结束时间" required>
                                <el-date-picker v-model="formData.operationTime.endTime" type="datetime"
                                    placeholder="选择结束时间" format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss"
                                    style="width: 100%" :disabled="isReadonly" />
                            </el-form-item>
                        </el-col>
                    </el-row>
                </el-form>
            </div>

            <!-- 侦察作战装备要求 -->
            <div class="form-section">
                <h4>侦察作战装备要求</h4>
                <el-form label-width="180px">
                    <el-form-item label="装备类型要求">
                        <el-select v-model="formData.reconnaissanceRequirement.equipmentTypes" multiple
                            placeholder="请选择装备类型" style="width: 100%" :disabled="isReadonly">
                            <el-option label="潜艇" value="潜艇" v-if="formData.scenario === '对海侦察'" />
                            <el-option label="驱逐舰" value="驱逐舰" v-if="formData.scenario === '对海侦察'" />
                            <el-option label="巡逻舰" value="巡逻舰" v-if="formData.scenario === '对海侦察'" />
                            <el-option label="战斗机" value="战斗机" v-if="formData.scenario === '对空侦察'" />
                            <el-option label="预警机" value="预警机" v-if="formData.scenario === '对空侦察'" />
                            <el-option label="无人机" value="无人机" v-if="formData.scenario === '对空侦察'" />
                        </el-select>
                    </el-form-item>

                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-form-item label="雷达能力">
                                <el-input v-model="formData.reconnaissanceRequirement.capabilities.radarCapability"
                                    placeholder="例如：100" :disabled="isReadonly">
                                    <template #append>km</template>
                                </el-input>
                            </el-form-item>
                        </el-col>
                        <el-col :span="12">
                            <el-form-item label="行驶速度">
                                <el-input v-model="formData.reconnaissanceRequirement.capabilities.travelSpeed"
                                    placeholder="例如：60" :disabled="isReadonly">
                                    <template #append>km/h</template>
                                </el-input>
                            </el-form-item>
                        </el-col>
                    </el-row>

                    <el-row :gutter="20">
                        <el-col :span="8">
                            <el-form-item label="出航航线">
                                <el-input v-model="formData.reconnaissanceRequirement.capabilities.departureRoute" :disabled="isReadonly" />
                            </el-form-item>
                        </el-col>
                        <el-col :span="8">
                            <el-form-item label="巡航路线">
                                <el-select v-model="formData.reconnaissanceRequirement.capabilities.cruiseRoute"
                                    style="width: 100%" :disabled="isReadonly">
                                    <el-option label="沿边界往返" value="沿边界往返" />
                                    <el-option label="沿边界循环" value="沿边界循环" />
                                </el-select>
                            </el-form-item>
                        </el-col>
                        <el-col :span="8">
                            <el-form-item label="返航航线">
                                <el-input v-model="formData.reconnaissanceRequirement.capabilities.returnRoute" :disabled="isReadonly" />
                            </el-form-item>
                        </el-col>
                    </el-row>

                    <el-form-item label="装备最低数量要求">
                        <el-select v-model="formData.reconnaissanceRequirement.capabilities.minEquipmentCount"
                            style="width: 300px" :disabled="isReadonly">
                            <el-option label="无偏好" value="无偏好" />
                            <el-option label="所有装备出动" value="所有装备出动" />
                            <el-option label="1编队" value="1编队" />
                            <el-option label="2编队" value="2编队" />
                            <el-option label="3编队" value="3编队" />
                            <el-option label="4编队" value="4编队" />
                            <el-option label="6编队" value="6编队" />
                            <el-option label="8编队" value="8编队" />
                            <el-option label="12编队" value="12编队" />
                        </el-select>
                    </el-form-item>

                    <el-row :gutter="20">
                        <el-col :span="12">
                            <el-form-item label="出航油门">
                                <el-select v-model="formData.reconnaissanceRequirement.capabilities.departureThrottle"
                                    style="width: 100%" :disabled="isReadonly">
                                    <el-option label="低速" value="低速" />
                                    <el-option label="巡航" value="巡航" />
                                    <el-option label="全速" value="全速" />
                                </el-select>
                            </el-form-item>
                        </el-col>
                        <el-col :span="12">
                            <el-form-item label="出航速度">
                                <el-input v-model="formData.reconnaissanceRequirement.capabilities.departureSpeed"
                                    placeholder="例如：50" :disabled="isReadonly">
                                    <template #append>km/h</template>
                                </el-input>
                            </el-form-item>
                        </el-col>
                    </el-row>
                </el-form>
            </div>

        <div class="form-section">
            <h4>侦察区域</h4>
            <!-- 3. 确保 isReadonly 和 scenarioId 正确绑定 -->
            <MapSelection 
                v-model="formData.mapSelectedArea"
                mode="area"
                :scenario-id="scenarioId"
                task-type="reconnaissance"
                :side="formData.side"
                :is-readonly="isReadonly"
            />
        </div>

        <!-- PCCS 智能资源推荐 -->
        <div class="form-section" v-if="!isReadonly">
            <div class="section-header-with-badge">
                <h4>
                    智能资源推荐
                    <el-tag type="success" effect="light" size="small" style="margin-left: 10px">
                        基于 PCCS Capability 维度
                    </el-tag>
                </h4>
                <el-text type="info" size="small">
                    系统将根据侦察任务需求，从资源池中推荐最适合的平台和装备
                </el-text>
            </div>
            <ResourceRecommendation
                mission-type="recon"
                :auto-load="true"
                :hide-task-type-selector="true"
                @select="handleResourceSelect"
            />

            <!-- 已选资源列表 -->
            <SelectedResourcesList
                :resources="selectedResources"
                @remove="removeResource"
                @clear="clearResources"
            />
        </div>

            <div class="step-actions" v-if="!isReadonly">
                <el-button @click="$emit('back')">上一步</el-button>
                <el-button type="primary" @click="handleNext">下一步</el-button>
            </div>
        </el-card>
    </template>

<script setup>
import { reactive, watch, defineEmits, defineProps, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { get } from 'lodash-es';
import MapSelection from './MapSelection.vue';
import ResourceRecommendation from '@/components/pccs/ResourceRecommendation.vue';
import SelectedResourcesList from '@/components/pccs/SelectedResourcesList.vue';

// 4. 定义 props，接收来自父组件的数据
const props = defineProps({
    modelValue: { type: Object, default: () => ({}) },
    isReadonly: { type: Boolean, default: false },
    scenarioId: { type: [String, Number], required: true },
    scenarioName: { type: String, default: '' },
    contractType: { type: String, required: true },

});
const emit = defineEmits(['update:modelValue', 'next', 'back']);


// 5. 封装初始数据和更新函数
const createInitialData = () => ({
    name: '',
    description: '',
    scenario: '对海侦察',
    operationTime: { startTime: '', endTime: '' },
    reconnaissanceRequirement: {
        equipmentTypes: [],
        capabilities: {
            radarCapability: '', travelSpeed: '', departureRoute: '默认',
            cruiseRoute: '沿边界往返', returnRoute: '默认', minEquipmentCount: '无偏好',
            departureThrottle: '巡航', departureSpeed: ''
        }
    },
    side: 'RED',
    mapSelectedArea: [],
});

const formData = reactive(createInitialData());

// PCCS 资源选择跟踪
const selectedResources = ref([]);

const parseUnitValue = (str) => {
    if (!str || typeof str !== 'string') return '';
    const match = str.match(/^(-?\d+\.?\d*)/);
    return match ? match[0] : '';
};

const updateFormDataFromModel = (newVal) => {
    if (!newVal || Object.keys(newVal).length === 0) {
        Object.assign(formData, createInitialData());
        onScenarioChange(formData.scenario); 
        return;
    }
    
    formData.name = get(newVal, '名称', '');
    formData.description = get(newVal, '任务描述', '');
    formData.scenario = get(newVal, '作战场景', '对海侦察');
    formData.operationTime.startTime = get(newVal, '作战时间.开始时间', '');
    formData.operationTime.endTime = get(newVal, '作战时间.结束时间', '');
    
    const reconReq = get(newVal, '侦察作战装备要求', {});
    const reconReqCapa = get(reconReq, '能力要求', {});
    formData.reconnaissanceRequirement.equipmentTypes = get(reconReq, '类型要求', []);
    formData.reconnaissanceRequirement.capabilities.radarCapability = parseUnitValue(get(reconReqCapa, '雷达能力'));
    formData.reconnaissanceRequirement.capabilities.travelSpeed = parseUnitValue(get(reconReqCapa, '行驶速度'));
    formData.reconnaissanceRequirement.capabilities.departureRoute = get(reconReqCapa, '出航航线', '默认');
    formData.reconnaissanceRequirement.capabilities.cruiseRoute = get(reconReqCapa, '巡航路线', '沿边界往返');
    formData.reconnaissanceRequirement.capabilities.returnRoute = get(reconReqCapa, '返航航线', '默认');
    formData.reconnaissanceRequirement.capabilities.minEquipmentCount = get(reconReqCapa, '启用任务所需的装备最低数量[0]', '无偏好');
    formData.reconnaissanceRequirement.capabilities.departureThrottle = get(reconReqCapa, '出航油门[0]', '巡航');
    formData.reconnaissanceRequirement.capabilities.departureSpeed = parseUnitValue(get(reconReqCapa, '出航速度'));

    const details = get(newVal, 'details', {});
    formData.side = get(details, 'side', 'RED');

    const areaFromJSON = get(newVal, '侦察区域', {});
    formData.reconnaissanceArea = areaFromJSON;

    const tl = get(areaFromJSON, 'topLeft', []);
    const tr = get(areaFromJSON, 'topRight', []);
    const br = get(areaFromJSON, 'bottomRight', []);
    const bl = get(areaFromJSON, 'bottomLeft', []);
    if (tl[0] && tr[0] && br[0] && bl[0]) {
        formData.mapSelectedArea = [
            { lng: parseFloat(tl[0]), lat: parseFloat(tl[1]) },
            { lng: parseFloat(tr[0]), lat: parseFloat(tr[1]) },
            { lng: parseFloat(br[0]), lat: parseFloat(br[1]) },
            { lng: parseFloat(bl[0]), lat: parseFloat(bl[1]) },
        ];
    } else {
        formData.mapSelectedArea = [];
    }
};

const onScenarioChange = (scenario) => {
    if (props.isReadonly) return;
    formData.reconnaissanceRequirement.equipmentTypes = [];
    if (scenario === '对海侦察') {
        formData.reconnaissanceRequirement.equipmentTypes = ['潜艇', '驱逐舰', '巡逻舰'];
    } else if (scenario === '对空侦察') {
        formData.reconnaissanceRequirement.equipmentTypes = ['战斗机', '预警机', '无人机'];
    }
};

// --- Watcher 1: 数据输入 (Props -> 本地状态) ---
watch(() => props.modelValue, (newVal) => {
    updateFormDataFromModel(newVal);
}, { immediate: true, deep: true });


// --- Watcher 3: 数据输出 (本地状态 -> Props) ---
watch(formData, (newValue) => {
    if (props.isReadonly) return;
    // *** 核心修复 3：在输出时动态计算 reconnaissanceArea ***
    
    let reconnaissanceAreaForEmit = {};
    if (newValue.mapSelectedArea && newValue.mapSelectedArea.length === 4) {
        const area = newValue.mapSelectedArea;
        // [修复点 C] 输出时使用驼峰式键名，保持对称
        reconnaissanceAreaForEmit = {
            topLeft: [area[0].lng.toFixed(6), area[0].lat.toFixed(6)],
            topRight: [area[1].lng.toFixed(6), area[1].lat.toFixed(6)],
            bottomRight: [area[2].lng.toFixed(6), area[2].lat.toFixed(6)],
            bottomLeft: [area[3].lng.toFixed(6), area[3].lat.toFixed(6)],
        };
    }
    const contractPartialData = {
        合同名称: newValue.name,
        任务描述: newValue.description,
        作战场景: newValue.scenario,
        作战类型: props.contractType,
        作战时间: {
            开始时间: newValue.operationTime.startTime,
            结束时间: newValue.operationTime.endTime
        },
        侦察作战装备要求: {
            类型要求: newValue.reconnaissanceRequirement.equipmentTypes,
            能力要求: {
                雷达能力: newValue.reconnaissanceRequirement.capabilities.radarCapability ? `${newValue.reconnaissanceRequirement.capabilities.radarCapability} km` : '',
                行驶速度: newValue.reconnaissanceRequirement.capabilities.travelSpeed ? `${newValue.reconnaissanceRequirement.capabilities.travelSpeed} km/h` : '',
                出航航线: newValue.reconnaissanceRequirement.capabilities.departureRoute,
                巡航路线: newValue.reconnaissanceRequirement.capabilities.cruiseRoute,
                返航航线: newValue.reconnaissanceRequirement.capabilities.returnRoute,
                启用任务所需的装备最低数量: [newValue.reconnaissanceRequirement.capabilities.minEquipmentCount],
                出航油门: [newValue.reconnaissanceRequirement.capabilities.departureThrottle],
                出航速度: newValue.reconnaissanceRequirement.capabilities.departureSpeed ? `${newValue.reconnaissanceRequirement.capabilities.departureSpeed} km/h` : ''
            }
        },
        侦察区域: reconnaissanceAreaForEmit,
        scenarioId: props.scenarioId,
        side: newValue.side,
    };
    emit('update:modelValue', contractPartialData);
}, { deep: true });

// PCCS 资源推荐选择处理
function handleResourceSelect(resource) {
    // 检查是否已经选择过该资源
    const exists = selectedResources.value.some(
        r => r.resource_type === resource.resource_type && r.resource_id === resource.resource_id
    );

    if (exists) {
        ElMessage.warning('该资源已经被选择');
        return;
    }

    // 添加到已选资源列表
    selectedResources.value.push(resource);
    ElMessage.success({
        message: `已选择资源: ${resource.name}`,
        duration: 2000
    });

    // 可以在这里添加将选中资源应用到合同配置的逻辑
    console.log('选中的资源 PCCS 信息:', resource);
    console.log('效能评分:', resource.match_effectiveness);
    console.log('能力信息:', resource.capability);
}

// 移除单个资源
function removeResource(index) {
    selectedResources.value.splice(index, 1);
}

// 清空所有已选资源
function clearResources() {
    selectedResources.value = [];
}

function handleNext() {
    if (!formData.name) { ElMessage.warning('请输入合同名称'); return; }
    if (!formData.description) { ElMessage.warning('请输入任务描述'); return }

    if (!formData.operationTime.startTime || !formData.operationTime.endTime) { ElMessage.warning('请选择作战时间'); return }
    if (!formData.mapSelectedArea || formData.mapSelectedArea.length < 4) {
        ElMessage.warning('请使用地图编辑器划定完整的侦察区域');
        return;
    }
    emit('next');
}

onMounted(() => {
    if (!props.isReadonly && (!props.modelValue || Object.keys(props.modelValue).length === 0)) {
       onScenarioChange(formData.scenario);
    }
});
</script>

    <style scoped>
    /* 样式与 ZhenchaContract.vue 保持一致或自定义 */
    .form-section { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #f3f4f6; }
    .form-section:last-of-type { border-bottom: none; margin-bottom: 0; }
    .form-section h4 { color: #000000; margin: 0 0 20px 0; font-size: 16px; font-weight: 600; padding-left: 8px; border-left: 3px solid #e4e716; }
    .area-config { background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
    .coordinates-grid { margin-bottom: 24px; }
    .coordinate-row { display: flex; gap: 24px; margin-bottom: 16px; }
    .coordinate-row .el-form-item { flex: 1; margin-bottom: 0; }
    .area-preview { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; }
    .area-preview h5 { margin: 0 0 16px 0; font-size: 14px; font-weight: 600; color: #374151; }
    .preview-box { position: relative; width: 100%; height: 200px; border: 2px dashed #94a3b8; border-radius: 8px; background: #ffffff; }
    .corner { position: absolute; padding: 8px; background: #3b82f6; color: white; border-radius: 4px; font-size: 12px; line-height: 1.2; min-width: 80px; }
    .corner span { display: block; font-weight: 600; margin-bottom: 2px; }
    .corner small { display: block; opacity: 0.9; font-size: 10px; }
    .top-left { top: 8px; left: 8px; }
    .top-right { top: 8px; right: 8px; }
    .bottom-left { bottom: 8px; left: 8px; }
    .bottom-right { bottom: 8px; right: 8px; }
    .step-actions { display: flex; justify-content: center; gap: 16px; margin-top: 32px; padding-top: 24px; border-top: 1px solid #f3f4f6; }
    .section-header-with-badge { margin-bottom: 16px; }
    .section-header-with-badge h4 { display: inline-flex; align-items: center; }
    .header-subtitle { color: #6b7280; font-size: 13px; font-weight: normal; margin-left: 8px; }
    </style>