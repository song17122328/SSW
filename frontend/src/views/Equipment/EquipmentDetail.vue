<!-- src/views/Equipment/EquipmentDetail.vue -->
<template>
  <div class="detail-page" v-loading="loading">
    <div v-if="equipment">
      <!-- 页面头部 -->
      <el-page-header @back="goBack" class="page-header">
        <template #content>
          <div class="header-content">
            <span class="header-title">{{ equipment.name }}</span>
            <!-- 视图模式切换 -->
            <el-radio-group v-model="viewMode" size="small" style="margin-left: 20px">
              <el-radio-button label="traditional">传统视图</el-radio-button>
              <el-radio-button label="pccs">PCCS 视图</el-radio-button>
            </el-radio-group>
          </div>
        </template>
      </el-page-header>

      <!-- 传统视图 -->
      <div v-if="viewMode === 'traditional'" class="details-grid">
        <!-- 装备基本信息卡片 -->
        <el-card class="detail-card">
          <template #header>
            <div class="card-header"><span>基本信息</span></div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label-class-name="my-label" label="装备名称">
              {{ equipment.name }}
            </el-descriptions-item>
            <el-descriptions-item label-class-name="my-label" label="分类 (S/C/A)">
              <el-tag v-if="equipment.type_code === 'S'" type="success" effect="light">S (感知)</el-tag>
              <el-tag v-else-if="equipment.type_code === 'C'" type="warning" effect="light">C (控制)</el-tag>
              <el-tag v-else-if="equipment.type_code === 'A'" type="danger" effect="light">A (打击)</el-tag>
              <el-tag v-else type="info" effect="light">其他</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label-class-name="my-label" label="具体类型">
              {{ equipment.category_text }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 搭载平台列表卡片 -->
        <el-card class="detail-card" v-if="equipment.used_by_platforms && equipment.used_by_platforms.length > 0">
          <template #header>
            <div class="card-header"><span>搭载平台</span></div>
          </template>
          <el-table :data="equipment.used_by_platforms" stripe style="width: 100%">
            <el-table-column prop="name" label="平台名称">
              <template #default="{ row }">
                <!-- 点击链接跳转回平台详情页 -->
                <router-link :to="{ name: 'PlatformDetail', params: { id: row.id } }" class="item-link">
                  {{ row.name }}
                </router-link>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="平台分类" width="120" />
            <el-table-column prop="model_type" label="型号/类型" />
          </el-table>
        </el-card>

<!-- *** 核心修复 1：使用 v-for 遍历 details 对象来生成表格，支持两层嵌套 *** -->
        <el-card class="info-card">
          <template #header><div class="card-header">详细参数 (Details)</div></template>
          <div v-if="hasDetails">
            <el-descriptions :column="1" border>
              <el-descriptions-item
                v-for="(value, key) in equipment.details"
                :key="key"
                :label="key"
              >
                <!-- 第一级：如果值是对象，渲染为嵌套的描述列表 -->
                <div v-if="isObject(value) && !Array.isArray(value)">
                  <el-descriptions :column="1" border size="small" class="nested-descriptions">
                    <el-descriptions-item
                      v-for="(nestedValue, nestedKey) in value"
                      :key="nestedKey"
                      :label="nestedKey"
                      label-class-name="nested-label"
                    >
                      <!-- 第二级：如果仍然是对象，则使用 JSON 格式显示 -->
                      <pre v-if="isObject(nestedValue)" class="json-code-block">{{ formatJson(nestedValue) }}</pre>
                      <!-- 否则直接显示 -->
                      <span v-else>{{ nestedValue }}</span>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
                <!-- 第一级：如果值是数组，使用 JSON 格式显示 -->
                <pre v-else-if="Array.isArray(value)" class="json-code-block">{{ formatJson(value) }}</pre>
                <!-- 第一级：如果是普通值，直接显示 -->
                <span v-else>{{ value }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="无详细参数" :image-size="60" />
        </el-card>
      </div>

      <!-- PCCS 视图 -->
      <div v-if="viewMode === 'pccs'">
        <PCCSDisplay resource-type="equipment" :resource-id="props.id" />
      </div>
    </div>

    <!-- 加载失败或无数据时的提示 -->
    <el-empty v-else-if="!loading" description="未能加载装备数据" />
  </div>
</template>

<script setup>
import { ref, watchEffect, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage } from 'element-plus';
import PCCSDisplay from '@/components/pccs/PCCSDisplay.vue';


const props = defineProps({
  id: {
    type: [String, Number],
    required: true
  }
});

const router = useRouter();
const loading = ref(true);
const equipment = ref(null);
const viewMode = ref('traditional'); // 视图模式: traditional / pccs


const hasDetails = computed(() => {
    return equipment.value.details && Object.keys(equipment.value.details).length > 0;
});

// *** 核心修复 2：新增辅助函数用于模板判断和格式化 ***
const isObject = (value) => {
    return typeof value === 'object' && value !== null;
};
const formatJson = (obj) => {
    return JSON.stringify(obj, null, 2);
};

const fetchEquipmentDetails = async (equipmentId) => {
  loading.value = true;
  equipment.value = null;
  try {
    equipment.value = await api.getEquipmentById(equipmentId);
  } catch (error) {
    console.error(`加载装备 ${equipmentId} 详情失败:`, error);
    ElMessage.error("加载装备详情失败");
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  // 尝试返回上一页，如果历史记录为空，则跳转到装备列表页
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'EquipmentList' });
  }
};

// 使用 watchEffect 来处理初始加载和路由参数变化
watchEffect(() => {
  if (props.id) {
    fetchEquipmentDetails(props.id);
  }
});
</script>

<style scoped>
.detail-page { padding: 24px; background-color: #f9fafb; }
.page-header { background-color: #fff; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05); }
.header-content { display: flex; align-items: center; gap: 12px; }
.header-title { font-size: 20px; font-weight: 600; color: #303133; }
.details-grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
.detail-card { border-radius: 8px; border: 1px solid #e4e7ed; }
.card-header span { font-weight: bold; color: #303133; }
.item-link { color: #409eff; text-decoration: none; font-weight: 500; }
.item-link:hover { text-decoration: underline; color: #79bbff; }

:deep(.my-label) {
  width: 120px;
}

/* 嵌套描述列表样式 */
.nested-descriptions {
  margin: 0;
  background-color: #fafafa;
}

:deep(.nested-label) {
  width: 150px;
  background-color: #f5f7fa !important;
  font-size: 13px;
  color: #606266;
}

/* JSON 代码块样式 */
.json-code-block {
  margin: 0;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  overflow-x: auto;
}
</style>