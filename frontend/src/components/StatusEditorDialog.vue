<template>
  <el-dialog
    :model-value="visible"
    :title="`修改 '${itemName}' 的状态`"
    width="400px"
    @close="$emit('close')"
    append-to-body
  >
    <el-form>
      <el-form-item label="当前状态">
        <el-tag :type="statusColor(currentStatus)">{{ currentStatus }}</el-tag>
      </el-form-item>
      <el-form-item label="新状态">
        <el-select v-model="newStatus" placeholder="请选择新状态">
          <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('close')">取 消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="loading">
        确 认
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  visible: Boolean,
  itemName: String,
  currentStatus: String,
  loading: Boolean,
});

const emit = defineEmits(['close', 'confirm']);

const newStatus = ref('');
const statusOptions = ['可用', '停用', '维护'];

// 监听 currentStatus 的变化，同步到 newStatus 的初始值
watch(() => props.currentStatus, (val) => {
  newStatus.value = val;
});

const handleConfirm = () => {
  emit('confirm', newStatus.value);
};

// 辅助函数，用于状态颜色
const statusColor = (status) => {
  if (status === '可用') return 'success';
  if (status === '停用') return 'info';
  if (status === '维护') return 'warning';
  return '';
};
</script>