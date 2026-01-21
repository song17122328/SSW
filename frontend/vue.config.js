// vue.config.js
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,

  devServer: {
    // 代理配置保持不变
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        ws: true
      }
    },

    // *** 核心修复：在这里添加 client 配置 ***
    client: {
      // 关闭浏览器中的错误浮层
      overlay: {
        errors: true, // 默认显示错误
        warnings: false, // 默认不显示警告

        // ** 关键：定义一个运行时错误的过滤器函数 **
        runtimeErrors: (error) => {
          // 如果错误是 ResizeObserver 相关的，返回 false 来忽略它
          if (
            error.message.includes('ResizeObserver loop completed with undelivered notifications') ||
            error.message.includes('ResizeObserver loop limit exceeded')
          ) {
            return false; // 不显示这个错误的浮层
          }
          // 对于所有其他错误，返回 true 来显示浮层
          return true;
        },
      },
    },
  }
});