<!-- PlatformForm.vue (修正后版本) -->
<template>
  <el-dialog :model-value="visible" :title="title" width="60%" @close="$emit('close')" :close-on-click-modal="false">
    <el-form v-if="form" :model="form" label-position="top" ref="formRef">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="平台名称" prop="name" :rules="[{ required: true, message: '名称不能为空' }]">
            <el-input v-model="form.name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="平台分类" prop="category">
            <el-input v-model="form.category" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="型号" prop="model_type">
            <el-input v-model="form.model_type" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="国家/地区" prop="country">
            <el-input v-model="form.country" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="服役日期" prop="service_date">
            <el-date-picker v-model="form.service_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-select v-model="form.status" style="width: 100%;">
              <el-option label="可用" value="可用" />
              <el-option label="维护" value="维护" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="挂载装备">
            <el-select
              v-model="form.equipment_ids"
              multiple filterable placeholder="搜索并选择可挂载的装备"
              style="width: 100%;"
              :loading="equipmentsLoading"
            >
              <el-option 
                v-for="item in allEquipments" 
                :key="item.id" 
                :label="`${item.name} (ID: ${item.id})`" 
                :value="item.id" 
              />
            </el-select>
          </el-form-item>
        </el-col>

        <!-- *** 核心修复 1：新增 details 字段的表单项 *** -->
        <el-col :span="24">
            <el-form-item label="详细参数 (Details - JSON格式)" prop="details_text">
                <el-input
                    v-model="form.details_text"
                    type="textarea"
                    :rows="4"
                    placeholder='请输入JSON格式的参数, 例如: {"range": "500km", "payload": "2t"}'
                />
                <div v-if="detailsError" class="details-error-tip">{{ detailsError }}</div>
            </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import api from '@/services/api';
import { ElMessage } from 'element-plus';

const props = defineProps({
  visible: Boolean,
  platform: { type: Object, default: null }
});
const emit = defineEmits(['close', 'success']);

const formRef = ref(null);
const form = ref(null);
const saving = ref(false);
const allEquipments = ref([]);
const equipmentsLoading = ref(false);
const detailsError = ref(''); // 用于显示 JSON 格式错误

const title = computed(() => props.platform ? '编辑平台' : '新增平台');

// *** 核心修复 2：在 createInitialData 中添加 details 和 details_text ***
const createInitialData = () => ({
    name: '',
    category: '',
    model_type: '',
    country: '',
    service_date: '',
    status: '可用',
    equipment_ids: [],
    details: {}, // 存储解析后的 JSON 对象
    details_text: '', // 存储用户输入的文本
});

const initializeForm = () => {
  if (props.platform) {
    form.value = JSON.parse(JSON.stringify(props.platform));
    form.value.equipment_ids = props.platform.equipments?.map(e => e.id) || [];
    // 将 details 对象转换回文本进行编辑
    form.value.details_text = JSON.stringify(form.value.details || {}, null, 2);
  } else {
    form.value = createInitialData();
  }
};


const fetchAllEquipments = async () => {
    equipmentsLoading.value = true;
    try {
        const data = await api.getAllEquipments();
        allEquipments.value = data.items;
    } catch (error) {
        ElMessage.error("加载装备列表失败");
    } finally {
        equipmentsLoading.value = false;
    }
};
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    initializeForm();
    detailsError.value = ''; // 每次打开弹窗时清空错误提示
  }
}, { immediate: true });


const handleSave = async () => {
    try {
        await formRef.value.validate();
    } catch (error) {
        return;
    }

    // *** 核心修复 3：在保存前验证并解析 details_text ***
    detailsError.value = '';
    let parsedDetails = {};
    try {
        // 如果用户输入了内容，则尝试解析
        if (form.value.details_text && form.value.details_text.trim()) {
            parsedDetails = JSON.parse(form.value.details_text);
        }
    } catch (e) {
        detailsError.value = '详细参数的JSON格式不正确，请检查！';
        ElMessage.error(detailsError.value);
        return; // 阻止提交
    }

    saving.value = true;
    try {
        const payload = { ...form.value };
        // 将解析后的对象赋给 details 字段
        payload.details = parsedDetails; 

        // 从 payload 中移除不再需要的字段
        delete payload.equipments;
        delete payload.details_text;

        if (payload.id) {
            await api.updatePlatform(payload.id, payload);
            ElMessage.success("平台更新成功！");
        } else {
            await api.createPlatform(payload);
            ElMessage.success("平台新增成功！");
        }
        emit('success');
    } finally {
        saving.value = false;
    }
};

onMounted(fetchAllEquipments);
</script>

<style scoped>
/* *** 核心修复 4：为错误提示添加样式 *** */
.details-error-tip {
    color: #F56C6C;
    font-size: 12px;
    line-height: 1;
    padding-top: 4px;
}
</style>