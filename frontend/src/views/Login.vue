<template>
  <div class="login-container">
    <div class="login-wrapper">
      <div class="login-background">
        <div class="bg-shape shape-1"></div>
        <div class="bg-shape shape-2"></div>
        <div class="bg-shape shape-3"></div>
      </div>

      <el-card class="login-card" shadow="hover">
        <div class="login-header">
          <div class="logo">
            <el-icon class="logo-icon">
              <User />
            </el-icon>
          </div>
          <h2 class="title">系统登录</h2>
          <p class="subtitle">欢迎回来，请输入您的账户信息</p>
        </div>

        <el-form @submit.prevent="handleLogin" class="login-form">
          <el-form-item>
            <el-input v-model="username" placeholder="请输入用户名" size="large" :prefix-icon="User" class="login-input" />
          </el-form-item>

          <el-form-item>
            <el-input v-model="password" type="password" placeholder="请输入密码" size="large" :prefix-icon="Lock"
              show-password class="login-input" />
          </el-form-item>

          <div class="login-tips">
            <el-text type="info" size="small">
              提示：admin/admin123 或 user/user123
            </el-text>
          </div>

          <el-form-item>
            <el-button type="primary" native-type="submit" :loading="loading" size="large" class="login-button">
              <span v-if="!loading">立即登录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <div class="register-link">
            还没有账户？
            <router-link :to="{ name: 'Register' }" class="link">立即注册</router-link>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!password.value.trim()) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    const success = await userStore.login(username.value, password.value)
    if (success) {
      ElMessage.success("登录成功！")
    }
  } catch (error) {
    // 错误处理由拦截器处理
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 85vh;
  overflow: hidden;
}

.login-wrapper {
  position: relative;
  z-index: 2;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  right: 10%;
  animation-delay: -2s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  bottom: 20%;
  left: 15%;
  animation-delay: -4s;
}

.shape-3 {
  width: 100px;
  height: 100px;
  top: 50%;
  right: 20%;
  animation-delay: -1s;
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }

  50% {
    transform: translateY(-20px) rotate(10deg);
  }
}

.login-card {
  width: 420px;
  padding: 20px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 25px 45px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  margin-bottom: 20px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 10px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: #718096;
  font-size: 14px;
  margin: 0;
  font-weight: 400;
}

.login-form {
  margin-bottom: 30px;
}

.login-input {
  margin-bottom: 20px;
}

.login-tips {
  text-align: center;
  margin: -10px 0 20px 0;
  padding: 10px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.register-link {
  color: #718096;
  font-size: 14px;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}
</style>