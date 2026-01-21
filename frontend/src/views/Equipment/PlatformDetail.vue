<template>
  <div class="detail-page" v-loading="loading">
    <div v-if="platform">
      <!-- 1. 页面头部和面包屑导航 -->
      <el-page-header @back="goBack" class="page-header">
        <template #content>
          <div class="header-content">
            <span class="header-title">{{ platform.name }}</span>
            <el-tag :type="platform.category === '舰艇' ? 'primary' : 'success'" effect="light" round>
              {{ platform.category }}
            </el-tag>
          </div>
        </template>
        <template #extra>
          <div class="header-breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>{{ platform.country || '未知国别' }}</el-breadcrumb-item>
              <el-breadcrumb-item>{{ platform.model_type || '未知型号' }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </template>
      </el-page-header>

      <div class="details-grid">
        <!-- 渲染平台自身详情的卡片 (例如概况, 技术数据) -->
        <template v-for="(section, title) in platform.details" :key="title">
          <el-card class="detail-card" v-if="Object.keys(section).length > 0">
            <template #header>
              <div class="card-header"><span>{{ title }}</span></div>
            </template>
            <el-descriptions :column="2" border>
              <template v-for="(value, key) in section" :key="key">
                <el-descriptions-item>
                  <template #label>{{ key }}</template>
                  <pre class="preserve-format">{{ value || 'N/A' }}</pre>
                </el-descriptions-item>
              </template>
            </el-descriptions>
          </el-card>
        </template>
        
        <!-- *** 新增：独立的、可点击的装备列表卡片 *** -->
        <el-card class="detail-card" v-if="platform.equipments && platform.equipments.length > 0">
          <template #header>
            <div class="card-header"><span>搭载装备</span></div>
          </template>
          <el-table :data="platform.equipments" stripe style="width: 100%">
            <el-table-column prop="name" label="装备名称">
              <template #default="{ row }">
                <router-link :to="{ name: 'EquipmentDetail', params: { id: row.id } }" class="item-link">
                  {{ row.name }}
                </router-link>
              </template>
            </el-table-column>
            <el-table-column prop="type_code" label="分类 (S/C/A)" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.type_code === 'S'" type="success" effect="light">S (感知)</el-tag>
                <el-tag v-if="row.type_code === 'C'" type="warning" effect="light">C (控制)</el-tag>
                <el-tag v-if="row.type_code === 'A'" type="danger" effect="light">A (打击)</el-tag>
                <el-tag v-if="row.type_code === 'U'" type="info" effect="light">其他</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category_text" label="具体类型" />
          </el-table>
        </el-card>

      </div>
    </div>
    <el-empty v-if="!loading && !platform" description="未能加载平台数据" />
  </div>
</template>

<script setup>
// *** 核心修改：引入 watchEffect ***
import { ref, watchEffect } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage } from 'element-plus';
// (您可能还需要从 element-plus 导入其他组件，这里省略)

const props = defineProps({
  id: {
    // ID 既可以是 URL 传来的 string，也可以是数字
    type: [String, Number],
    required: true,
  },
});

const router = useRouter();
const loading = ref(true);
const platform = ref(null);

const fetchPlatformDetails = async (platformId) => {
  loading.value = true;
  platform.value = null;
  try {
    platform.value = await api.getPlatformById(platformId);
  } catch (error) {
    console.error(`加载平台 ${platformId} 详情失败:`, error);
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.push({ name: 'PlatformList', query: { highlight: props.id } });
};

watchEffect(() => {
  if (props.id) {
    fetchPlatformDetails(props.id);
  }
});
</script>

<style scoped>
.detail-page {
  padding: 24px;
  background-color: #f9fafb;
}

.page-header {
  background-color: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-breadcrumb {
  display: flex;
  align-items: center;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr; /* 默认单列布局 */
  gap: 24px;
}

.detail-card {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: box-shadow 0.3s;
}

.detail-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header span {
  font-weight: bold;
  color: #303133;
}

/* 保持长文本格式 */
.preserve-format {
  white-space: pre-wrap; /* 自动换行 */
  word-break: break-all; /* 在任意字符间断行 */
  margin: 0;
  font-family: inherit; /* 使用与页面相同的字体 */
  font-size: 14px;
}
.equipment-link {
  color: #409eff;
  text-decoration: none;
}
.equipment-link:hover {
  text-decoration: underline;
}

.item-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
}
.item-link:hover {
  text-decoration: underline;
  color: #79bbff;
}
.preserve-format {
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: inherit;
  font-size: 14px;
}
</style>