<!-- AppSidebar.vue -->
<template>
    <aside class="app-sidebar">
        <el-menu :default-active="$route.name" class="sidebar-menu" background-color="#ffffff" text-color="#374151"
            active-text-color="#2563eb" :collapse="false" router>
            <!-- 遍历的是父路由 -->
            <template v-for="route in filteredRoutes" :key="route.name">
                <!-- 无子菜单或只有一个可显示子菜单的，直接显示为一级菜单 -->
                <el-menu-item 
                    v-if="!route.children || getVisibleChildren(route.children).length <= 1" 
                    :index="getSingleChildRoute(route).name"
                    :route="{ name: getSingleChildRoute(route).name }"
                >
                    <el-icon v-if="route.meta.icon"><component :is="route.meta.icon" /></el-icon>
                    <span>{{ getSingleChildRoute(route).meta.title }}</span>
                </el-menu-item>

                <!-- 有多个可显示子菜单的，显示为下拉菜单 -->
                <el-sub-menu v-else :index="route.name">
                    <template #title>
                        <el-icon v-if="route.meta.icon"><component :is="route.meta.icon" /></el-icon>
                        <span>{{ route.meta.title }}</span>
                    </template>
                    <!-- 遍历的是过滤后的子路由 -->
                    <template v-for="child in getVisibleChildren(route.children)" :key="child.name">
                        <el-menu-item :index="child.name" :route="{ name: child.name }" class="sub-menu-item">
                            <span class="sub-menu-dot"></span>
                            <span>{{ child.meta.title }}</span>
                        </el-menu-item>
                    </template>
                </el-sub-menu>
            </template>
        </el-menu>

        <div class="sidebar-footer">
            <!-- ... footer 不变 ... -->
        </div>
    </aside>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useSystemStore } from '@/stores/system';

const router = useRouter();
const userStore = useUserStore();
const systemStore = useSystemStore();

// ** 核心辅助函数：过滤出可显示的子路由 **
const getVisibleChildren = (children = []) => {
    return children.filter(child => {
        return child.meta && !child.meta.hidden && child.meta.roles.includes(userStore.currentRole);
    });
};

// ** 核心辅助函数：处理只有一个子菜单的情况 **
const getSingleChildRoute = (parentRoute) => {
    const visibleChildren = getVisibleChildren(parentRoute.children);
    if (visibleChildren.length === 1) {
        return visibleChildren[0];
    }
    // 如果没有可显示的子菜单，返回父菜单自身的信息（这种情况较少）
    return parentRoute;
};

// 根据用户角色筛选可访问的父路由
const filteredRoutes = computed(() => {
    return router.options.routes.filter(route => {
        // 过滤登录和注册
        if (route.name === 'Login' || route.name === 'Register') return false;

        // 过滤掉没有 meta 或被隐藏的顶层路由
        if (!route.meta || route.meta.hidden) return false;

        // 检查顶层路由权限
        if (route.meta.roles && !route.meta.roles.includes(userStore.currentRole)) {
            return false;
        }

        // 检查是否有任何一个可显示的子路由
        if (route.children && getVisibleChildren(route.children).length === 0) {
            return false;
        }

        return true;
    });
});
</script>


<style scoped>
/* 样式部分不需要做任何修改 */
/* ... */
.app-sidebar {
    width: 250px;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    height: 100%;
    border-right: 1px solid #e5e7eb;
}

.sidebar-menu {
    flex: 1;
    border: none;
    font-weight: 600;
}

.sidebar-footer {
    padding: 16px;
    border-top: 1px solid #e5e7eb;
    background: #f9fafb;
}

.system-info {
    color: #6b7280;
    font-size: 12px;
    font-weight: 500;
}

.info-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.info-item:last-child {
    margin-bottom: 0;
}

.label {
    opacity: 0.8;
}

.value {
    font-weight: 600;
    color: #374151;
}

/* 子菜单小圆点样式 */
.sub-menu-dot {
    display: inline-block;
    width: 4px;
    height: 4px;
    background-color: #9ca3af;
    border-radius: 50%;
    margin-right: 8px;
    transition: all 0.3s ease;
    vertical-align: middle;
}

</style>