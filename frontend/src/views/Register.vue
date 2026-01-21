<template>
  <div class="register-container">
    <div class="register-wrapper">
      <div class="register-background">
        <div class="bg-shape shape-1"></div>
        <div class="bg-shape shape-2"></div>
        <div class="bg-shape shape-3"></div>
      </div>

      <el-card class="register-card" shadow="hover">
        <div class="register-header">
          <div class="logo">
            <el-icon class="logo-icon">
              <UserFilled />
            </el-icon>
          </div>
          <h2 class="title">用户注册</h2>
          <p class="subtitle">创建您的账户，开始使用我们的服务</p>
        </div>

        <el-form @submit.prevent="handleRegister" :model="form" class="register-form">
          <el-form-item>
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" :prefix-icon="User"
              class="register-input" clearable />
          </el-form-item>

          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" :prefix-icon="Lock"
              show-password class="register-input" />
          </el-form-item>

          <el-form-item>
            <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" size="large"
              :prefix-icon="Lock" show-password class="register-input" />
          </el-form-item>

          <el-form-item>
            <div class="role-selection">
              <label class="role-label">注册类型：</label>
              <el-radio-group v-model="form.role" class="role-group">
                <el-radio label="user" class="role-radio">普通用户</el-radio>
                <el-radio label="admin" class="role-radio">管理员</el-radio>
              </el-radio-group>
            </div>
          </el-form-item>

          <!-- 动态显示的邀请码输入框 -->
          <el-form-item v-if="form.role === 'admin'">
            <el-input v-model="form.inviteCode" placeholder="注册管理员需要邀请码" size="large" :prefix-icon="Key"
              class="register-input" />
          </el-form-item>

          <div class="register-tips">
            <el-text type="info" size="small">
              提示：管理员注册需要有效的邀请码
            </el-text>
          </div>

          <el-form-item>
            <el-button type="primary" native-type="submit" :loading="loading" size="large" class="register-button">
              <span v-if="!loading">立即注册</span>
              <span v-else>注册中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <div class="login-link">
            已有账户？
            <router-link :to="{ name: 'Login' }" class="link">立即登录</router-link>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { ElMessage } from 'element-plus';
import { User, Lock, UserFilled, Key } from '@element-plus/icons-vue';

const router = useRouter();
const loading = ref(false);
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'user',
  inviteCode: '',
});

const handleRegister = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('用户名和密码不能为空');
    return;
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.error('两次输入的密码不一致');
    return;
  }

  // 增加邀请码验证
  if (form.role === 'admin' && !form.inviteCode) {
    ElMessage.warning('注册管理员必须填写邀请码');
    return;
  }

  loading.value = true;
  try {
    // 将邀请码传递给 API
    await api.register(form.username, form.password, form.role, form.inviteCode);
    ElMessage.success('注册成功！即将跳转到登录页...');
    setTimeout(() => {
      router.push({ name: 'Login' });
    }, 1500);
  } catch (error) {
    console.error("注册失败:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 85vh;
  overflow: hidden;
}

.register-wrapper {
  position: relative;
  z-index: 2;
}

.register-background {
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

.register-card {
  width: 450px;
  padding: 20px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 25px 45px rgba(0, 0, 0, 0.1);
}

.register-header {
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

.register-form {
  margin-bottom: 30px;
}

.register-input {
  margin-bottom: 20px;
}

.role-selection {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background-color: #fff;
  display: flex;
  align-items: center;
  gap: 15px;
}

.role-label {
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.role-group {
  flex: 1;
}

.role-radio {
  margin-right: 20px;
}

.register-tips {
  text-align: center;
  margin: -10px 0 20px 0;
  padding: 10px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.register-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

.register-button:active {
  transform: translateY(0);
}

.register-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.login-link {
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
