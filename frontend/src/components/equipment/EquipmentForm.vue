<!-- src/components/equipment/EquipmentForm.vue (最终版) -->
<template>
  <el-dialog :model-value="visible" :title="title" width="50%" @close="$emit('close')" :close-on-click-modal="false">
    <el-form v-if="form" :model="form" label-position="top" ref="formRef">
      <el-form-item label="装备名称" prop="name" :rules="[{ required: true, message: '名称不能为空' }]">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="型号代码" prop="type_code">
        <el-input v-model="form.type_code" />
      </el-form-item>
      <el-form-item label="分类文本" prop="category_text">
        <el-input v-model="form.category_text" placeholder="例如：武器/反舰导弹" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" style="width: 100%;">
          <el-option label="可用" value="可用" />
          <el-option label="维护" value="维护" />
          <el-option label="停用" value="停用" />
        </el-select>
      </el-form-item>
       <el-form-item label="详细参数 (Details - JSON格式)" prop="details_text">
            <el-input
                v-model="form.details_text"
                type="textarea"
                :rows="4"
                placeholder='请输入JSON格式的参数'
            />
            <div v-if="detailsError" class="details-error-tip">{{ detailsError }}</div>
        </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import api from '@/services/api';
import { ElMessage } from 'element-plus';

const props = defineProps({
  visible: Boolean,
  equipment: { type: Object, default: null }
});
const emit = defineEmits(['close', 'success']);

const formRef = ref(null);
const form = ref(null);
const saving = ref(false);
const detailsError = ref('');

const title = computed(() => props.equipment ? '编辑装备' : '新增装备');

const initializeForm = () => {
  if (props.equipment) {
    // 1. 深拷贝数据，确保隔离
    form.value = JSON.parse(JSON.stringify(props.equipment));
    // 2. 核心修复：将 details 对象转换回文本，用于在 textarea 中显示
    form.value.details_text = JSON.stringify(form.value.details || {}, null, 2);
  } else {
    // 3. 新增时提供完整的初始结构
    form.value = { 
      name: '', 
      type_code: '', 
      category_text: '', 
      status: '可用',
      details: {},
      details_text: '{}', // 默认为一个空的JSON对象字符串
    };
  }
};

watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    initializeForm();
    detailsError.value = '';
  }
}, { immediate: true });

const handleSave = async () => {
    try {
        await formRef.value.validate();
    } catch (e) { return; }

    detailsError.value = '';
    let parsedDetails = {};
    try {
        if(form.value.details_text && form.value.details_text.trim()) {
            parsedDetails = JSON.parse(form.value.details_text);
        }
    } catch (e) {
        detailsError.value = '详细参数的JSON格式不正确！';
        ElMessage.error(detailsError.value);
        return;
    }
    
    saving.value = true;
    try {
        // 4. 构建一个干净的 payload
        const payload = {
            id: form.value.id,
            name: form.value.name,
            type_code: form.value.type_code,
            category_text: form.value.category_text,
            status: form.value.status,
            details: parsedDetails, // 使用解析后的 details 对象
        };

        if (payload.id) {
            await api.updateEquipment(payload.id, payload);
            ElMessage.success("装备更新成功！");
        } else {
            // 新增时不需要 id
            delete payload.id;
            await api.createEquipment(payload);
            ElMessage.success("装备新增成功！");
        }
        emit('success');
    } finally {
        saving.value = false;
    }
};
</script>

<style scoped>
.details-error-tip {
    color: #F56C6C;
    font-size: 12px;
    line-height: 1;
    padding-top: 4px;
}
</style>