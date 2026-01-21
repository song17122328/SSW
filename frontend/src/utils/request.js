/**
 * 🌐 HTTP请求封装
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: 'http://localhost:3001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    console.log(`🚀 API请求: ${config.method?.toUpperCase()} ${config.url}`)
    
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  error => {
    console.error('❌ 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { data, status } = response
    
    if (status >= 200 && status < 300) {
      console.log(`✅ API响应: ${response.config.url}`, data)
      return data
    }
    
    throw new Error(`HTTP ${status}: ${response.statusText}`)
  },
  error => {
    console.error('❌ 响应错误:', error)
    
    let message = '网络请求失败'
    
    if (error.response) {
      const { status, data } = error.response
      message = data?.message || `服务器错误 (${status})`
    } else if (error.request) {
      message = '无法连接到服务器'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
