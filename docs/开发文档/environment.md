# RSH Cloud 测试环境信息

> 基于 `workflow-test-desktop/config/` 目录配置文件整理，覆盖所有服务地址、数据库连接、中间件、Nginx 路由、租户编码和测试账号。

---

## 目录

1. [环境总览](#1-环境总览)
2. [服务器与网络](#2-服务器与网络)
3. [Nginx 路由](#3-nginx-路由)
4. [数据库连接](#4-数据库连接)
5. [MongoDB 连接](#5-mongodb-连接)
6. [Redis 连接](#6-redis-连接)
7. [Nacos 配置中心](#7-nacos-配置中心)
8. [API 网关](#8-api-网关)
9. [租户与平台编码](#9-租户与平台编码)
---

## 1. 环境总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        测试环境拓扑                              │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │ 220 服务器│    │ 203 服务器│    │ 244 服务器               │  │
│  │ (前端+Nginx)│  │ (后端+DB) │    │ (MongoDB)                │  │
│  │          │    │          │    │                          │  │
│  │ :38080   │───>│ :8077    │    │ :27017                   │  │
│  │ (前端静态)│    │ (API网关) │    │ (MongoDB)                │  │
│  │          │    │          │    │                          │  │
│  │ :38081   │───>│ :3306    │    └──────────────────────────┘  │
│  │ (API代理) │    │ (MySQL)  │                                  │
│  │          │    │          │                                  │
│  │          │    │ :6379    │                                  │
│  │          │    │ (Redis)  │                                  │
│  └──────────┘    └──────────┘                                  │
│                                                                 │
│  ┌──────────────────────────┐                                  │
│  │ Nacos 配置中心            │                                  │
│  │ 192.168.1.203:28888      │                                  │
│  │ 命名空间: quanguocheng_test│                                 │
│  └──────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 服务器与网络

| 服务器 | IP | 用途 | SSH |
|--------|-----|------|-----|
| 220 | `192.168.1.220` | 前端静态资源 + Nginx 反向代理 | root@22:22 (机器名: service2) |
| 203 | `192.168.1.203` | 后端微服务 + MySQL + Redis + Nacos | -- |
| 244 | `192.168.1.244` | MongoDB | -- |

**Nginx 版本**: `nginx/1.20.1`（运行在 220 服务器）

---

## 3. Nginx 路由

> 来源：`server-access-notes.md`，通过 `nginx -T` 复核

### 3.1 前端静态入口（端口 38080）

| URL | 用途 | 后端静态目录 |
|-----|------|-------------|
| `http://192.168.1.220:38080/invest/rsh/` | 流程运行前端入口 | `/opt/uat_test/invest/dist` |
| `http://192.168.1.220:38080/management/rsh/` | 实施平台前端入口 | `/opt/uat_test/management/dist` |
| `http://192.168.1.220:38080/cloud/rsh/` | Cloud 平台前端入口 | `/opt/uat_test/cloud/dist` |
| `http://192.168.1.220:38080/files/` | 前端文件访问代理 | `http://192.168.1.203:8880/files/` |

### 3.2 API 反向代理（端口 38081）

| URL | 用途 | 后端真实地址 |
|-----|------|-------------|
| `http://192.168.1.220:38081/api` | **Runner/API 网关入口** | `http://192.168.1.203:8077/api` |
| `http://192.168.1.220:38081/api/web/file/...` | 文件上传特例 | `http://192.168.1.203:9999/web/file/...` |

### 3.3 路由裁决

- `38080` = 前端静态资源入口，**不是** Runner 直接调用的 API 网关
- `38081/api` = Runner 和前端共用的 API 入口，后端实际落到 `203:8077`
- `9999` 端口仅用于文件上传特例，不作为主流程接口网关
- 旧的 `192.168.1.127:9999` 已弃用

---

## 4. 数据库连接

### 4.1 MySQL

| 项目 | 值 |
|------|-----|
| 主机 | `192.168.1.203` |
| 端口 | `3306` |
| 用户名 | `root` |
| 密码 | 仅保存在本机 `.env`（不提交） |

#### 库表清单

| 数据库 | 用途 | 来源 |
|--------|------|------|
| `rsh_cloud_workflow_center` | 流程引擎主库 | Nacos: `rsh-cloud-workflow-center-test.properties` |
| `rsh_cloud_user_center` | 用户中心库 | Nacos: `rsh-cloud-user-center-api-test.properties` |

#### 关键表

| 表名 | 库 | 用途 |
|------|-----|------|
| `t_user` | `rsh_cloud_user_center` | 用户表 |
| `t_flow_template` | `rsh_cloud_workflow_center` | 流程模板 |
| `t_flow_proxy` | `rsh_cloud_workflow_center` | 运行时流程代理 |
| `t_flow_node_template` | `rsh_cloud_workflow_center` | 节点模板 |
| `t_flow_node_proxy` | `rsh_cloud_workflow_center` | 运行时节点代理 |
| `t_flow_job_task_link` | `rsh_cloud_workflow_center` | 任务节点关联 |
| `t_flow_instance` | `rsh_cloud_workflow_center` | 流程实例 |
| `t_flow_audit_record` | `rsh_cloud_workflow_center` | 审批记录 |
| `t_flow_group` | `rsh_cloud_workflow_center` | 流程分组 |
| `t_flow_role` | `rsh_cloud_workflow_center` | 流程角色 |


## 5. MongoDB 连接

| 项目 | 值 |
|------|-----|
| 连接 URI | `mongodb://192.168.1.244:27017/rsh?waitQueueTimeoutMS=15000` |
| 数据库 | `rsh` |
| 来源 | Nacos: `mongodb-workflow.properties` |

**用途**：存储流程表单数据（FormData），通过 FormDataService 读写。

---

## 6. Redis 连接

| 项目 | 值 |
|------|-----|
| 主机 | `192.168.1.203` |
| 端口 | `6379` |
| 数据库 | `1` |
| 密码 | 仅保存在本机 `.env`（不提交） |
| 来源 | Nacos: `redis-commons.properties` |

**注意**：Redis 库号为 `1`（非默认 `0`），避免误用默认库导致 sid/缓存语义错误。

### Redis 缓存用途

| 缓存类型 (ReidsDataType) | Key 模式 | 用途 |
|--------------------------|----------|------|
| `UserCache` | `sid` (Session ID) | 用户会话缓存 |
| `VERIFICATION` | 验证码 key | 短信/图形验证码 |
| `MACHINE_CODE` | 机器码 | License 校验 |
| `SYSTEMTASK` | 系统任务 | 定时任务 |
| `USER_PLATFORM_RESOURCES` | 用户平台资源 | 平台资源缓存 |
| `REQ_URL_AUTH` | 请求 URL | 鉴权缓存 |
| `third_party_user_token` | 第三方 Token | 联动登录 Token |
| `FLOW_AUDIT_LOCK` | `userId_jobTaskId` (TTL=3s) | 审核并发锁 |
| `flowCallBackMap` (Hash) | field=auditWay.name() | 流程回调映射 |
| `FLOW_TEMPLATE_DATA_{id}` | 模板 ID (TTL=120h) | 流程模板数据缓存 |

---

## 7. Nacos 配置中心

| 项目 | 值 |
|------|-----|
| 地址 | `http://192.168.1.203:28888/nacos` |
| 命名空间 | `quanguocheng_test` |
| 配置分组 | `DEFAULT_GROUP` |
| 账号密码 | 仅保存在本机环境变量（不提交） |

### 7.1 重点配置文件

| 目标 | dataId | 需要提取的字段 |
|------|--------|---------------|
| Workflow MySQL | `rsh-cloud-workflow-center-test.properties`、`rsh-cloud-workflow-center-api-test.properties` | `spring.datasource.druid.url`、`spring.datasource.druid.username` |
| MongoDB | `mongodb-workflow.properties`、`mongodb-commons.properties` | `spring.data.mongodb.uri` |
| Redis | `redis-commons.properties`、`rsh-cloud-web-api-test.properties` | `spring.redis.host`、`spring.redis.port`、`spring.redis.database` |
| 租户编码 | `rsh-cloud-user-center-api-test.properties` | `casdoor.applications.*.platform-code`、`customer-code` |
| 网关 | `rsh-cloud-gateway-test.properties`、`rsh-cloud-web-api-test.properties` | 网关直连地址 |

### 7.2 常用 API

```bash
# 登录 Nacos
curl -sS -X POST 'http://192.168.1.203:28888/nacos/v1/auth/users/login' \
  -H 'content-type: application/x-www-form-urlencoded' \
  --data-urlencode "username=${NACOS_USER}" \
  --data-urlencode "password=${NACOS_PASSWORD}"

# 列出配置
curl -sS 'http://192.168.1.203:28888/nacos/v1/cs/configs' \
  --get \
  --data-urlencode "tenant=quanguocheng_test" \
  --data-urlencode "group=DEFAULT_GROUP" \
  --data-urlencode "pageNo=1" \
  --data-urlencode "pageSize=100" \
  --data-urlencode "accessToken=${NACOS_TOKEN}"

# 读取单个配置
curl -sS 'http://192.168.1.203:28888/nacos/v1/cs/configs' \
  --get \
  --data-urlencode "tenant=quanguocheng_test" \
  --data-urlencode "group=DEFAULT_GROUP" \
  --data-urlencode "dataId=rsh-cloud-workflow-center-test.properties" \
  --data-urlencode "accessToken=${NACOS_TOKEN}"
```

---

## 8. API 网关

| 项目 | 值 |
|------|-----|
| Runner 使用的网关 | `http://192.168.1.220:38081/api` |
| 网关后端真实地址 | `http://192.168.1.203:8077/api` |
| 前端 API 代理 | `http://192.168.1.220:38081/api`

### 8.1 登录端点

所有用户的密码都是1 验证码也写1 就可以登录测试环境

### 8.2 AES 加密 Key

```
LOGIN_AES_KEY=fff65019-27a2-49
```

密码在传输时使用此 Key 进行 AES 加密。

---

## 9. 租户与平台编码

| 项目 | 值 | 来源 |
|------|-----|------|
| 平台编码 (platform_code) | `200001` | Nacos: `rsh-cloud-user-center-api-test.properties` |
| 客户编码 (customer_code) | `d4036cc6581141a8b13cf39387c8d6f2` | Nacos: `rsh-cloud-user-center-api-test.properties` |
| 客户名称 | 润世华新能源集团 | Nacos 配置 |
| Management 平台码 | `999999` | 前端登录页配置 |



