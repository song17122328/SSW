// src/services/api.js - 完整修正版
import axios from 'axios';
import { ElMessage } from 'element-plus';


const apiClient = axios.create({
  // baseURL 直接指向我们的代理路径！
  baseURL: '/api',

  // 因为现在在浏览器看来是同源请求，withCredentials 保留即可。
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});
// 全局错误处理拦截器
apiClient.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.error || error.message || '网络请求失败';
    ElMessage.error(message);
    return Promise.reject(error);
  }
);

export default {
  // ==========================================================
  // ===                平台资源管理 (Platforms)                ===
  // ==========================================================

  // --- GET (读取) ---
  getPlatforms(page = 1, pageSize = 10, searchKeyword = '') {
    console.log("接收到的参数是", searchKeyword)
    const params = { page, pageSize };
    if (searchKeyword) {
      params.search = searchKeyword;
    }
    return apiClient.get('/platforms', { params }).then(res => res.data);
  },
  getAllPlatforms() {
    return apiClient.get('/platforms', { params: { page: 1, pageSize: 9999 } }).then(res => res.data);
  },
  getPlatformById(id) {
    return apiClient.get(`/platforms/${id}`).then(res => res.data);
  },

  // --- POST (创建) ---
  // *** 新增：创建平台函数 ***
  createPlatform(platformData) {
    // platformData 是一个包含 name, category, equipment_ids 等字段的对象
    return apiClient.post('/platforms', platformData).then(res => res.data);
  },

  // --- PUT (更新) ---
  // *** 新增：更新平台函数 ***
  updatePlatform(id, platformData) {
    return apiClient.put(`/platforms/${id}`, platformData).then(res => res.data);
  },
  updatePlatformStatus(id, status) {
    return apiClient.put(`/platforms/${id}/status`, { status }).then(res => res.data);
  },

  // --- DELETE (删除) ---
  // *** 新增：删除平台函数 ***
  deletePlatform(id) {
    return apiClient.delete(`/platforms/${id}`).then(res => res.data);
  },


  // ==========================================================
  // ===                装备资源管理 (Equipments)               ===
  // ==========================================================

  // --- GET (读取) ---
  getEquipments(page = 1, pageSize = 10, searchKeyword = '') {
    const params = { page, pageSize };
    if (searchKeyword) {
      params.search = searchKeyword;
    }
    return apiClient.get('/equipments', { params }).then(res => res.data);
  },
  getAllEquipments() {
    return apiClient.get('/equipments', { params: { page: 1, pageSize: 9999 } }).then(res => res.data);
  },
  getEquipmentById(id) {
    return apiClient.get(`/equipments/${id}`).then(res => res.data);
  },

  // --- POST (创建) ---
  // *** 新增：创建装备函数 ***
  createEquipment(equipmentData) {
    return apiClient.post('/equipments', equipmentData).then(res => res.data);
  },

  // --- PUT (更新) ---
  // *** 新增：更新装备函数 ***
  updateEquipment(id, equipmentData) {
    return apiClient.put(`/equipments/${id}`, equipmentData).then(res => res.data);
  },
  updateEquipmentStatus(id, status) {
    return apiClient.put(`/equipments/${id}/status`, { status }).then(res => res.data);
  },

  // --- DELETE (删除) ---
  // *** 新增：删除装备函数 ***
  deleteEquipment(id) {
    return apiClient.delete(`/equipments/${id}`).then(res => res.data);
  },


  // --- 合同 API (保持不变) ---
  getContracts(options = {}) { // 接收一个 options 对象
    // 使用 URLSearchParams 来轻松构建查询字符串
    const params = new URLSearchParams();
    if (options.status) {
      params.append('status', options.status);
    }
    if (options.creater) {
      params.append('creater', options.creater);
    }

    const queryString = params.toString();
    const url = `/contracts${queryString ? `?${queryString}` : ''}`;

    return apiClient.get(url).then(res => res.data);
  },

  getContractById(id) {
    return apiClient.get(`/contracts/${id}`).then(res => res.data);
  },
  // 合同模板API
  getContractTemplates() {
    return apiClient.get('/contract-templates').then(res => res.data);
  },
  getContractTemplateById(id) { // 新增，用于获取模板完整数据
    return apiClient.get(`/contract-templates/${id}`).then(res => res.data);
  },
  createContract(contractData, creater) {
    // 发送一个 POST 请求到 /api/contracts
    // 请求体 (body) 就是 contractData 对象
    const payload = {
      contract_data: contractData,
      creater: creater
    };
    // 调试日志：确认发送的最终 payload 结构
    console.log("最终发送到后端的 Payload:", payload);
    return apiClient.post('/contracts', payload).then(res => res.data);
  },
  updateContractStatus(id, status) {
    // 这个函数会发送一个 PUT 请求到 /api/contracts/<id>/status
    // 请求体是一个包含新状态的对象, e.g., { "status": "approved" }
    return apiClient.put(`/contracts/${id}/status`, { status });
  },
  deleteContract(id) {
    // 这个函数会发送一个 DELETE 请求到 /api/contracts/<id>
    return apiClient.delete(`/contracts/${id}`).then(res => res.data);
  },
  // --- 用户认证 API ---
  register(username, password, role, inviteCode) {
    // ** 核心修改：增加 inviteCode 参数 **
    return apiClient.post('/register', { username, password, role, inviteCode });
  },
  login(username, password) {
    return apiClient.post('/login', { username, password }).then(res => res.data);
  },
  logout() {
    return apiClient.post('/logout');
  },
  checkSession() {
    return apiClient.get('/user/session').then(res => res.data);
  },

  // --- 作战想定仿真 API ---
  getSimScenarios() {
    return apiClient.get('/sim/scenarios').then(res => res.data);
  },

  getSimScenarioDetails(scenarioId) {
    return apiClient.get(`/sim/scenarios/${scenarioId}`).then(res => res.data);
  },

  getSimPlatformEquipments(platformDbId) {
    return apiClient.get(`/sim/platforms/${platformDbId}/equipments`).then(res => res.data);
  },
  uploadSimScenario(file) {
    // ** 关键：使用 FormData 来包装文件 **
    const formData = new FormData();
    formData.append('file', file); // 'file' 必须与后端 request.files['file'] 的键名一致

    return apiClient.post('/sim/scenarios/upload', formData, {
      // ** 关键：设置正确的 Content-Type **
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data);
  },
  // ** 新增：删除想定 API 调用 **
  deleteSimScenario(scenarioId) {
    return apiClient.delete(`/sim/scenarios/${scenarioId}`).then(res => res.data);
  },

  // ==========================================================
  // ===                PCCS 资源虚拟化 API                     ===
  // ==========================================================

  // 获取所有 PCCS 资源
  getPCCSResources(params = {}) {
    // params 可包含: type, category, mission_type, availability
    return apiClient.get('/pccs/resources', { params }).then(res => res.data);
  },

  // 获取单个 PCCS 资源详情
  getPCCSResource(resourceType, resourceId) {
    return apiClient.get(`/pccs/resource/${resourceType}/${resourceId}`).then(res => res.data);
  },

  // 更新 PCCS 资源状态
  updatePCCSResourceState(resourceType, resourceId, stateData) {
    return apiClient.put(`/pccs/resource/${resourceType}/${resourceId}/state`, stateData).then(res => res.data);
  },

  // 根据能力搜索资源 (用于任务匹配)
  searchPCCSByCapability(missionType, minEffectiveness = 0.5) {
    return apiClient.get('/pccs/search', {
      params: {
        mission_type: missionType,
        min_effectiveness: minEffectiveness
      }
    }).then(res => res.data);
  },

  // 获取 PCCS 资源池统计信息
  getPCCSStatistics() {
    return apiClient.get('/pccs/statistics').then(res => res.data);
  },

  // 重新加载 PCCS 资源池
  reloadPCCSResources() {
    return apiClient.post('/pccs/reload').then(res => res.data);
  },

};