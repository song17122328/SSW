# 前端

### 一、启动说明

#### 1、安装npm

```
npm install
```

安装相关的npm包

```
npm install echarts vue-echarts 
npm install socket.io-client
npm install lodash-es
npm install leaflet-draw
```
#### 2、运行服务
```
npm run serve
```

(可选)

#### 3、编译用于生产

```
npm run build
```

#### 4、Lints 和修复文件
```
npm run lint
```

自定义配置：

Vue参考文档:  [Configuration Reference](https://cli.vuejs.org/config/).



### 二、开发说明

v1.0.0 : 完成了合同和装备相关的程序。增加了许多页面如下所示：

* 合同功能

新增 `view/Login.vue` ,`view/Register.vue` 用户登录和注册，可参考后端

新增 `views/Contract/ContractDetail.vue` 展示合同详情；

新增 `views/Contract/ContractList.vue`  展示审核通过的合同列表(已通过)；

新增 `views/Contract/ContractTemplates.vue`  创建合同时可选通过模板创建；

新增 `views/Contract/MyApplications.vue`  查看当前用户提交的合同申请状态(待审核/已通过/已驳回)；

新增 `views/Contract/PendingContracts` 仅管理员可见，用来审核所有用户提交的合同，批准或驳回。

完成`views/Contract/ContractCreate.vue` 现在有完整的合同创建逻辑

* 装备功能

完成`views/Equipment/EquipmentList.vue` 现在有完整的装备列表展示

完成`views/Equipment/PlatformList.vue` 现在有完整的平台列表展示

* 路由相关

修改`router/index.js` 把所有相关路由添加

新建 `services/api.js` 负责所有与后端通信的同步异步请求发送



其他：

修改了合同相关的四个组件，使其同时应用于合同详情展示 、合同创建。 

```
src/components/contract
├── DajiContract.vue        #打击对应的组件
├── FandaoContract.vue      #反导对应的组件
├—— XunluoContract.vue      #巡逻对应的组件
├── ZhenchaContract.vue     #侦查对于组件        
```

为系统整体完善，修改了`src/components/common`下面的组件。
