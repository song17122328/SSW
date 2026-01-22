<!-- DajiContract.vue -->
<template>
    <el-card>
        <template #header>
            <!-- 确认标题能正确显示想定名称 -->
            <h3>
                打击任务配置 
                <small v-if="scenarioName" class="header-subtitle">
                    (基于想定: {{ scenarioName }})
                </small>
            </h3>
        </template>

        <div class="form-section">
            <h4>基本信息</h4>
            <el-form :model="formData" label-width="120px">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="合同名称" required>
                            <el-input v-model="formData.name" placeholder="请输入合同名称" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>

                    <!-- *** 核心修复 2.1：彻底移除“关联想定”的 el-col *** -->
                    
                    <el-col :span="12">
                        <el-form-item label="作战场景">
                            <el-select v-model="formData.scenario" style="width: 100%" @change="onScenarioChange" :disabled="isReadonly">
                                <el-option label="对海打击" value="对海打击" />
                                <el-option label="对空打击" value="对空打击" />
                                <el-option label="全面打击" value="全面打击" />
                            </el-select>
                        </el-form-item>
                    </el-col>

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
                    <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请描述打击任务的具体要求和目标" :disabled="isReadonly" />
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

        <!-- 感知装备要求 -->
        <div class="form-section">
            <h4>感知(Sense)作战装备要求</h4>
            <el-form label-width="150px">
                <el-form-item label="装备类型">
                    <el-select v-model="formData.senseRequirement.equipmentTypes" multiple placeholder="请选择装备类型"
                        style="width: 100%" :disabled="isReadonly">
                        <el-option label="飞行器" value="飞行器" />
                        <el-option label="舰艇" value="舰艇" />
                        <el-option label="航母" value="航母" />
                    </el-select>
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="感知范围">
                            <el-input v-model="formData.senseRequirement.capabilities.sensingRange"
                                placeholder="例如：100" :disabled="isReadonly">
                                <template #append>km</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="精度">
                            <el-input v-model="formData.senseRequirement.capabilities.accuracy" placeholder="例如：1" :disabled="isReadonly">
                                <template #append>m</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="速度">
                            <el-input v-model="formData.senseRequirement.capabilities.speed" placeholder="例如：120" :disabled="isReadonly">
                                <template #append>m/s</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="通信链路带宽">
                            <el-input v-model="formData.senseRequirement.capabilities.communicationBandwidth"
                                placeholder="例如：2" :disabled="isReadonly">
                                <template #append>MB/s</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="出航航线">
                            <el-input v-model="formData.senseRequirement.capabilities.departureRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="返航航线">
                            <el-input v-model="formData.senseRequirement.capabilities.returnRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </el-form>
        </div>

        <!-- 控制装备要求 -->
        <div class="form-section">
            <h4>控制(Command)作战装备要求</h4>
            <el-form label-width="180px">
                <el-form-item label="装备类型">
                    <el-select v-model="formData.commandRequirement.equipmentTypes" multiple placeholder="请选择装备类型"
                        style="width: 100%" :disabled="isReadonly">
                        <el-option label="飞行器" value="飞行器" />
                        <el-option label="舰艇" value="舰艇" />
                        <el-option label="航母" value="航母" />
                    </el-select>
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="与Act装备距离要求">
                            <el-input v-model="formData.commandRequirement.capabilities.distanceToAct"
                                placeholder="例如：200" :disabled="isReadonly">
                                <template #append>km</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="计算能力">
                            <el-input v-model="formData.commandRequirement.capabilities.computingPower"
                                placeholder="例如：1.6" :disabled="isReadonly">
                                <template #append>GHz</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="控制范围">
                            <el-input v-model="formData.commandRequirement.capabilities.controlRange"
                                placeholder="例如：300" :disabled="isReadonly">
                                <template #append>km</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="指挥精度">
                            <el-input v-model="formData.commandRequirement.capabilities.commandAccuracy"
                                placeholder="例如：100" :disabled="isReadonly">
                                <template #append>m</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="出航航线">
                            <el-input v-model="formData.commandRequirement.capabilities.departureRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="返航航线">
                            <el-input v-model="formData.commandRequirement.capabilities.returnRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </el-form>
        </div>

        <!-- 执行装备要求 -->
        <div class="form-section">
            <h4>执行(Act)作战装备要求</h4>
            <el-form label-width="180px">
                <el-form-item label="装备类型">
                    <el-select v-model="formData.actRequirement.equipmentTypes" multiple placeholder="请选择装备类型"
                        style="width: 100%" :disabled="isReadonly">
                        <el-option label="飞行器" value="飞行器" />
                        <el-option label="舰艇" value="舰艇" />
                        <el-option label="航母" value="航母" />
                    </el-select>
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="弹药最低数量">
                            <el-input v-model="formData.actRequirement.capabilities.minAmmunition" placeholder="例如：1" :disabled="isReadonly">
                                <template #append>枚</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="同时发送弹药数量">
                            <el-input v-model="formData.actRequirement.capabilities.simultaneousAmmunition"
                                placeholder="例如：1" :disabled="isReadonly">
                                <template #append>枚</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-form-item label="弹药类型">
                    <el-select v-model="formData.actRequirement.capabilities.ammunitionType" style="width: 100%" :disabled="isReadonly">
                        <el-option label="所有对海打击导弹" value="所有对海打击导弹" v-if="formData.scenario === '对海打击'" />
                        <el-option label="所有对空打击导弹" value="所有对空打击导弹" v-if="formData.scenario === '对空打击'" />
                        <el-option label="所有导弹" value="所有导弹" v-if="formData.scenario === '全面打击'" />
                    </el-select>
                </el-form-item>

                <el-form-item label="弹药攻击方式">
                    <el-input v-model="formData.actRequirement.capabilities.attackMode"
                        placeholder="在最远距离上投掷/抛弃弹药以满足最大打击半径" :disabled="isReadonly" />
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-form-item label="最小打击半径">
                            <el-input v-model="formData.actRequirement.capabilities.minStrikeRange" placeholder="例如：2" :disabled="isReadonly">
                                <template #append>km</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="最大打击半径">
                            <el-input v-model="formData.actRequirement.capabilities.maxStrikeRange" placeholder="例如：6" :disabled="isReadonly">
                                <template #append>km</template>
                            </el-input>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-form-item label="速度">
                    <el-input v-model="formData.actRequirement.capabilities.speed" placeholder="例如：120"
                        style="width: 200px" :disabled="isReadonly">
                        <template #append>m/s</template>
                    </el-input>
                </el-form-item>

                <el-row :gutter="20">
                    <el-col :span="8">
                        <el-form-item label="出航航线">
                            <el-input v-model="formData.actRequirement.capabilities.departureRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="返航航线">
                            <el-input v-model="formData.actRequirement.capabilities.returnRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="武器航线">
                            <el-input v-model="formData.actRequirement.capabilities.weaponRoute" :disabled="isReadonly" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </el-form>
        </div>

        <!-- 杀伤网要求 (仅对海打击显示) -->
        <div class="form-section" v-if="formData.scenario === '对海打击'">
            <h4>杀伤网要求</h4>
            <el-form label-width="120px">
                <el-row :gutter="20">
                    <el-col :span="8">
                        <el-form-item label="冗余性指标">
                            <el-select v-model="formData.killNetRequirement.redundancy" style="width: 100%" :disabled="isReadonly">
                                <el-option label="低" value="低" />
                                <el-option label="中" value="中" />
                                <el-option label="高" value="高" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="风险性指标">
                            <el-select v-model="formData.killNetRequirement.risk" style="width: 100%" :disabled="isReadonly">
                                <el-option label="低" value="低" />
                                <el-option label="中" value="中" />
                                <el-option label="高" value="高" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="敏捷性指标">
                            <el-select v-model="formData.killNetRequirement.agility" style="width: 100%" :disabled="isReadonly">
                                <el-option label="低" value="低" />
                                <el-option label="中" value="中" />
                                <el-option label="高" value="高" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                </el-row>
            </el-form>
        </div>


        <div class="form-section">
            <h4>敌方目标</h4>
            <!-- *** 核心修复：确保 :is-readonly="isReadonly" 存在 *** -->
            <MapSelection 
                v-model="formData.mapSelectedTargets"
                mode="target"
                :scenario-id="scenarioId" 
                task-type="strike" 
                :side="formData.side"
                :is-readonly="isReadonly"  
            />
        </div>



        <!-- 期望毁伤率 -->
        <div class="form-section">
            <h4>期望毁伤率</h4>
            <el-form label-width="120px">
                <el-form-item label="毁伤要求">
                    <el-select v-model="formData.expectedDamageRate" style="width: 200px" :disabled="isReadonly">
                        <el-option label="仅攻击一次" value="仅攻击一次" />
                        <el-option label="完全摧毁" value="完全摧毁" />
                        <el-option label="重度损伤" value="重度损伤" />
                        <el-option label="轻度损伤" value="轻度损伤" />
                    </el-select>
                </el-form-item>
            </el-form>
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
                    系统将根据打击任务需求，从资源池中推荐最适合的平台和装备
                </el-text>
            </div>
            <ResourceRecommendation
                mission-type="strike"
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

        <!-- 在只读模式下隐藏这些按钮 -->
        <div class="step-actions" v-if="!isReadonly">
            <el-button @click="$emit('back')">上一步</el-button>
            <el-button type="primary" @click="handleNext">下一步</el-button>
        </div>
    </el-card>
</template>

<script setup>

import { reactive, watch, defineEmits, defineProps, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { get } from 'lodash-es';
import MapSelection from './MapSelection.vue';
import ResourceRecommendation from '@/components/pccs/ResourceRecommendation.vue';
import SelectedResourcesList from '@/components/pccs/SelectedResourcesList.vue';
// *** 核心修复 2.2：移除不再需要的 import ***
// import api from '@/services/api';
// import { onMounted } from 'vue';


// *** 核心修复 2.3：确认 props 定义 ***
const props = defineProps({
    modelValue: { type: Object, default: () => ({}) },
    isReadonly: { type: Boolean, default: false },
    scenarioId: { type: [String, Number], required: true },
    scenarioName: { type: String, default: '' },
    contractType: { type: String, required: true }, // 新增
});

const emit = defineEmits(['update:modelValue', 'next', 'back']);


// *** 核心修复 1：将 formData 的创建和重置逻辑封装成一个函数 ***
const createInitialData = () => ({
    name: '',
    description: '',
    scenario: '对海打击',
    operationTime: { startTime: '', endTime: '' },
    senseRequirement: { equipmentTypes: [], capabilities: {} },
    commandRequirement: { equipmentTypes: [], capabilities: {} },
    actRequirement: { equipmentTypes: [], capabilities: {} },
    killNetRequirement: {},
    enemyTargets: [],
    expectedDamageRate: '',
    mapSelectedTargets: [],
    side: 'RED',
});

const formData = reactive(createInitialData());

// PCCS 资源选择跟踪
const selectedResources = ref([]);

const parseUnitValue = (str) => {
    if (!str || typeof str !== 'string') return '';
    const match = str.match(/^(-?\d+\.?\d*)/);
    return match ? match[0] : '';
};

// *** 核心修复 1：使用一个统一的 watch 来处理从 props 到 formData 的所有更新 ***
watch(() => props.modelValue, (newVal) => {
    if (!newVal || Object.keys(newVal).length === 0) {
        Object.assign(formData, createInitialData());
        return;
    }

    // --- 填充所有表单字段 ---
    formData.name = get(newVal, '名称', '');
    formData.description = get(newVal, '任务描述', '');
    formData.scenario = get(newVal, '作战场景', '对海打击');
    formData.operationTime.startTime = get(newVal, '作战时间.开始时间', '');
    formData.operationTime.endTime = get(newVal, '作战时间.结束时间', '');
    
    const senseReq = get(newVal, '感知Sense作战装备要求', {});
    formData.senseRequirement.equipmentTypes = get(senseReq, '类型要求', []);
    formData.senseRequirement.capabilities.sensingRange = parseUnitValue(get(senseReq, '能力要求.感知范围'));
    formData.senseRequirement.capabilities.accuracy = parseUnitValue(get(senseReq, '能力要求.精度'));
    formData.senseRequirement.capabilities.speed = parseUnitValue(get(senseReq, '能力要求.速度'));
    formData.senseRequirement.capabilities.communicationBandwidth = parseUnitValue(get(senseReq, '能力要求.通信链路带宽需求'));
    formData.senseRequirement.capabilities.departureRoute = get(senseReq, '能力要求.出航航线', '默认');
    formData.senseRequirement.capabilities.returnRoute = get(senseReq, '能力要求.返航航线', '默认');

    const commandReq = get(newVal, '控制Command作战装备要求', {});
    formData.commandRequirement.equipmentTypes = get(commandReq, '类型要求', []);
    formData.commandRequirement.capabilities.distanceToAct = parseUnitValue(get(commandReq, '能力要求.与Act作战装备距离要求'));
    formData.commandRequirement.capabilities.computingPower = parseUnitValue(get(commandReq, '能力要求.计算能力'));
    formData.commandRequirement.capabilities.controlRange = parseUnitValue(get(commandReq, '能力要求.控制范围'));
    formData.commandRequirement.capabilities.commandAccuracy = parseUnitValue(get(commandReq, '能力要求.指挥精度'));
    formData.commandRequirement.capabilities.departureRoute = get(commandReq, '能力要求.出航航线', '默认');
    formData.commandRequirement.capabilities.returnRoute = get(commandReq, '能力要求.返航航线', '默认');

    const actReq = get(newVal, '执行Act作战装备要求', {});
    formData.actRequirement.equipmentTypes = get(actReq, '类型要求', []);
    formData.actRequirement.capabilities.minAmmunition = parseUnitValue(get(actReq, '能力要求.弹药最低数量'));
    formData.actRequirement.capabilities.simultaneousAmmunition = parseUnitValue(get(actReq, '能力要求.同时发送的弹药数量'));
    formData.actRequirement.capabilities.ammunitionType = get(actReq, '能力要求.弹药类型', '');
    formData.actRequirement.capabilities.attackMode = get(actReq, '能力要求.弹药攻击方式', '');
    formData.actRequirement.capabilities.minStrikeRange = parseUnitValue(get(actReq, '能力要求.最小打击半径'));
    formData.actRequirement.capabilities.maxStrikeRange = parseUnitValue(get(actReq, '能力要求.最大打击半径'));
    formData.actRequirement.capabilities.speed = parseUnitValue(get(actReq, '能力要求.速度'));
    formData.actRequirement.capabilities.departureRoute = get(actReq, '能力要求.出航航线', '默认');
    formData.actRequirement.capabilities.returnRoute = get(actReq, '能力要求.返航航线', '默认');
    formData.actRequirement.capabilities.weaponRoute = get(actReq, '能力要求.武器航线', '默认');
    
    const killNetReq = get(newVal, '杀伤网要求', {});
    formData.killNetRequirement.redundancy = get(killNetReq, '冗余性指标[0]', '');
    formData.killNetRequirement.risk = get(killNetReq, '风险性指标[0]', '');
    formData.killNetRequirement.agility = get(killNetReq, '敏捷性指标[0]', '');
    

    formData.expectedDamageRate = get(newVal, '期望毁伤率[0]', '');
    const details = get(newVal, 'details', {});
    formData.side = get(details, 'side', 'RED'); 

    // --- 填充 mapSelectedTargets 和 enemyTargets ---
    const targetsFromModel = get(newVal, '敌方目标', []);
    
    // 填充 enemyTargets (这是最终要提交的数据结构)
    formData.enemyTargets = targetsFromModel;

    console.log(newVal)
    console.log('尝试获取敌方目标', JSON.parse(JSON.stringify(targetsFromModel)));

    // 填充 mapSelectedTargets (这是 MapSelection 组件需要的数据结构)
    if (targetsFromModel.every(t => typeof t === 'object' && t.id && t.name)) {
        formData.mapSelectedTargets = targetsFromModel.map(t => ({ 
            id: t.id, 
            name: t.name,
            lon: t.position?.[0] || null,
            lat: t.position?.[1] || null,
        }));
    } else {
        formData.mapSelectedTargets = [];
    }

}, { immediate: true, deep: true });

// *** 核心修复 2：使用一个 watch 来同步用户在 MapSelection 中的选择到最终数据结构 ***
watch(() => formData.mapSelectedTargets, (newTargetObjects) => {
    // 这个 watch 的职责是：当用户通过地图编辑器改变了选择（更新了 mapSelectedTargets），
    // 我们需要将这个变化同步回 formData.enemyTargets，因为 enemyTargets 才是最终要提交的数据。
    if (props.isReadonly) return; // 只读模式下不需要同步

    if (!newTargetObjects) {
        formData.enemyTargets = [];
        return;
    }
    
    formData.enemyTargets = newTargetObjects.map(target => ({
        name: target.name,
        position: [
            target.lon ? target.lon.toFixed(6) : '',
            target.lat ? target.lat.toFixed(6) : ''
        ],
        priority: '中',
        type: '未知',
        id: target.id,
    }));
}, { deep: true });

watch(formData, (newValue) => {
    if (props.isReadonly) return;
    const contractPartialData = {
        合同名称: newValue.name,
        作战类型: props.contractType,
        任务描述: newValue.description,
        作战场景: newValue.scenario,
        作战时间: { 开始时间: newValue.operationTime.startTime, 结束时间: newValue.operationTime.endTime },
        "感知Sense作战装备要求": {
            类型要求: newValue.senseRequirement.equipmentTypes,
            能力要求: {
                感知范围: newValue.senseRequirement.capabilities.sensingRange ? `${newValue.senseRequirement.capabilities.sensingRange} km` : '',
                精度: newValue.senseRequirement.capabilities.accuracy ? `${newValue.senseRequirement.capabilities.accuracy} m` : '',
                速度: newValue.senseRequirement.capabilities.speed ? `${newValue.senseRequirement.capabilities.speed} m/s` : '',
                通信链路带宽需求: newValue.senseRequirement.capabilities.communicationBandwidth ? `${newValue.senseRequirement.capabilities.communicationBandwidth} MB/s` : '',
                出航航线: newValue.senseRequirement.capabilities.departureRoute,
                返航航线: newValue.senseRequirement.capabilities.returnRoute
            }
        },
        "控制Command作战装备要求": {
            类型要求: newValue.commandRequirement.equipmentTypes,
            能力要求: {
                "与Act作战装备距离要求": newValue.commandRequirement.capabilities.distanceToAct ? `${newValue.commandRequirement.capabilities.distanceToAct} km` : '',
                计算能力: newValue.commandRequirement.capabilities.computingPower ? `${newValue.commandRequirement.capabilities.computingPower} GHz` : '',
                控制范围: newValue.commandRequirement.capabilities.controlRange ? `${newValue.commandRequirement.capabilities.controlRange} km` : '',
                指挥精度: newValue.commandRequirement.capabilities.commandAccuracy ? `${newValue.commandRequirement.capabilities.commandAccuracy} m` : '',
                出航航线: newValue.commandRequirement.capabilities.departureRoute,
                返航航线: newValue.commandRequirement.capabilities.returnRoute
            }
        },
        "执行Act作战装备要求": {
            类型要求: newValue.actRequirement.equipmentTypes,
            能力要求: {
                弹药最低数量: newValue.actRequirement.capabilities.minAmmunition ? `${newValue.actRequirement.capabilities.minAmmunition} 枚` : '',
                同时发送的弹药数量: newValue.actRequirement.capabilities.simultaneousAmmunition ? `${newValue.actRequirement.capabilities.simultaneousAmmunition} 枚` : '',
                弹药类型: newValue.actRequirement.capabilities.ammunitionType,
                弹药攻击方式: newValue.actRequirement.capabilities.attackMode,
                最小打击半径: newValue.actRequirement.capabilities.minStrikeRange ? `${newValue.actRequirement.capabilities.minStrikeRange} km` : '',
                最大打击半径: newValue.actRequirement.capabilities.maxStrikeRange ? `${newValue.actRequirement.capabilities.maxStrikeRange} km` : '',
                速度: newValue.actRequirement.capabilities.speed ? `${newValue.actRequirement.capabilities.speed} m/s` : '',
                出航航线: newValue.actRequirement.capabilities.departureRoute,
                返航航线: newValue.actRequirement.capabilities.returnRoute,
                武器航线: newValue.actRequirement.capabilities.weaponRoute
            }
        },
        ...(newValue.scenario === '对海打击' && { "杀伤网要求": { 冗余性指标: [newValue.killNetRequirement.redundancy], 风险性指标: [newValue.killNetRequirement.risk], 敏捷性指标: [newValue.killNetRequirement.agility] } }),
        敌方目标: newValue.enemyTargets,
        期望毁伤率: [newValue.expectedDamageRate],
        // 关键：在提交时，从 props 而不是 formData 中获取 scenarioId
        scenarioId: props.scenarioId, 
        side: newValue.side,
    };
    emit('update:modelValue', contractPartialData);
}, { deep: true });

function onScenarioChange(scenario) {
    if (props.isReadonly) return;
    switch (scenario) {
        case '对海打击': formData.actRequirement.capabilities.ammunitionType = '所有对海打击导弹'; break;
        case '对空打击': formData.actRequirement.capabilities.ammunitionType = '所有对空打击导弹'; break;
        case '全面打击': formData.actRequirement.capabilities.ammunitionType = '所有导弹'; break;
    }
}

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
    // 例如：根据资源的能力自动填充装备要求
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
    if (!formData.name) { ElMessage.warning('请输入合同名称'); return }
    if (!formData.description) { ElMessage.warning('请输入任务描述'); return }

    if (!formData.operationTime.startTime || !formData.operationTime.endTime) { ElMessage.warning('请选择作战时间'); return }
    if (!formData.mapSelectedTargets || formData.mapSelectedTargets.length === 0) {
        ElMessage.warning('请使用地图编辑器选择敌方目标');
        return;
    }
    emit('next');
}
</script>

<style scoped>
.form-section {
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid #f3f4f6;
}

.form-section:last-of-type {
    border-bottom: none;
    margin-bottom: 0;
}

.form-section h4 {
    color: #000000;
    margin: 0 0 20px 0;
    font-size: 16px;
    font-weight: 600;
    padding-left: 8px;
    border-left: 3px solid #ef4444;
}

.target-manager {
    background: #fef2f2;
    padding: 16px;
    border-radius: 6px;
    border: 1px solid #fecaca;
}

.target-list {
    margin-bottom: 12px;
}

.target-item {
    margin-bottom: 12px;
}

.target-item:last-child {
    margin-bottom: 0;
}

.step-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #f3f4f6;
}

.section-header-with-badge {
    margin-bottom: 16px;
}

.section-header-with-badge h4 {
    display: inline-flex;
    align-items: center;
}

.header-subtitle {
    color: #6b7280;
    font-size: 13px;
    font-weight: normal;
    margin-left: 8px;
}

</style>
