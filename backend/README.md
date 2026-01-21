# 海战作战管理平台 (Naval Combat Management Platform)

## 项目简介

## 功能特性
- ⚔️ **装备管理**: 雷达、导弹、火炮等武器装备管理
- 📋 **合同管理**: 反导、巡逻、打击、侦察任务管理

## 技术栈
- **后端框架**: Flask + Flask-RESTful
- **数据库**: SQLite3
- **ORM**: SQLAlchemy
- **认证**: JWT
- **跨域**: Flask-CORS

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python database.py
python 1_populate_from_mapping.py 
python 2_populate_extra_data.py 
```

### 3. 启动服务
```bash
python app.py
```

## API文档
(待补充) 服务启动后访问: http://localhost:5000/

## 项目结构
```
naval_combat_platform/
├── app.py   #程序入口，所有路由
├── database.py           # 初始化数据库, 填入模板数据和装备平台初始数据
├—— military_data.db      # 运行完database.py 后得到的本地sqlite数据库
├── mock_data             # 模拟用数据，database.py从这里获得数据

```



## 开发进度

* 版本: v1.0.0：当前完成了装备展示和平台展示、合同创建(根据类别创建和根据模板创建)、合同查看、合同删除(不同权限)、管理员权限的合同批准与驳回



### 用户身份

数据库默认附带一个普通用户和管理员用户，在登录界面用placeholder展示了 

```json
'普通用户':{
    "username":"user",
    "password":"user123"
},
'管理员':{
    "username":"admin",
    "password":"admin123"
}
```

也可以自己申请用户，普通用户申请无要求；管理员用户申请需要输入邀请码 `9999` 这个邀请码以硬编码的形式编写在 `app.py`中

