# RSH Cloud API 数据规范

> 本文档是接口编排自动化测试工具的**唯一 API 数据源**。所有层（Session、Flow、Assignment、Execution）的实现必须严格遵循本文档的路由和字段定义。
>
> 规范来源：Apifox MCP 查询 + 流程引擎生命周期文档

---

## 1. 通用约定

### 1.1 请求格式

- 所有接口均为 **POST** + JSON body（`Content-Type: application/json`）
- 鉴权方式：`X-SID` 请求头（登录后由 SessionManager 注入）
- 公共请求头：
  ```
  X-SID: {sid}
  Content-Type: application/json
  ```

### 1.2 响应格式

**标准响应（ApiResponse）**
```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

| code | 含义 |
|------|------|
| `0` | 成功 |
| `-1` | 系统繁忙 |
| `99999` | 通用业务错误 |
| `401` | 未认证 |
| `40029` | 微信 OAuth code 无效 |

**分页响应（PageResponse）**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "records": [...],
    "total": 100,
    "page": 1,
    "size": 10
  }
}
```

---

## 2. 认证接口

### 2.1 用户登录
```
POST /web/user/api/login/user/login
```
**请求体**
```json
{
  "username": "string",       // 账号（ACCOUNT 类型必填）
  "password": "string",       // 密码（ACCOUNT 类型必填）
  "loginType": "ACCOUNT",    // 固定 ACCOUNT
  "platformCode": "string",   // 平台编码（从环境配置获取）
  "customerCode": "string"    // 客户编码（从环境配置获取）
}
```
**响应 data 字段**
```json
{
  "sid": "string"             // Session ID，后续请求的 X-SID 值
}
```

---

## 3. 流程模板接口

### 3.1 流程模板列表
```
POST /web/flowTemplateApi/list
```
**请求体**
```json
{
  "page": 1,
  "size": 50,
  "keyword": "string",         // 模板名称关键字（可选）
  "companyId": "string",       // 公司 ID（可选）
  "flowGroupId": "string",     // 流程分组 ID（可选）
  "status": "enable",          // 固定 enable
  "platformCode": "string"     // 平台编码（可选）
}
```
**响应 data.records 字段**
```json
{
  "flowTemplateId": "string",    // 流程模板 ID
  "flowTemplateCode": "string",  // 流程编码
  "flowTemplateName": "string",  // 流程名称
  "flowGroupId": "string",        // 分组 ID
  "flowGroupName": "string",      // 分组名称
  "flowStatus": "string",          // 状态 enable/disable
  "platformCode": "string"
}
```

### 3.2 模板详情（含节点信息）
```
POST /web/flowTemplateApi/detail
```
**请求体**
```json
{
  "id": "string"               // flowTemplateId
}
```
**响应 data 字段**
```json
{
  "flowTemplateId": "string",
  "flowTemplateName": "string",
  "formConfig": [...],          // 表单字段配置
  "flowNodeList": [...],        // 节点列表（见 3.3）
  "flowBranchList": [...]        // 分支列表（见 3.4）
}
```

### 3.3 节点数据结构（flowNodeList）

```json
{
  "nodeId": "string",             // 节点 ID
  "nodeName": "string",           // 节点名称
  "nodeType": "APPROVAL",        // 节点类型 APPROVAL / START / END / ...
  "auditType": "ASSIGN",         // 审核类型 ASSIGN / POSITION / COMPANY / ROLE / DEPARTMENT / ...
  "auditWay": "SCRAMBLE",        // 审核方式 SCRAMBLE（竞签）/ COUNTERSIGN（会签）
  "countersignNum": 1,           // 会签人数
  "branchId": "string",          // 所属分支 ID
  "flowNodeUserList": [...],     // 节点用户列表（见 3.3.1）
  "flowNodeFieldPowerTemplateList": [...]  // 字段权限
}
```

### 3.3.1 节点用户（flowNodeUserList）

```json
{
  "userId": "string",            // 用户 ID
  "userName": "string",           // 用户名
  "displayName": "string",       // 显示名
  "auditType": "assign"          // 人员类型 assign / company / department / position / role / ...
}
```

### 3.4 分支数据结构（flowBranchList）

```json
{
  "branchId": "string",           // 分支 ID
  "branchName": "string",         // 分支名称
  "parentBranchId": "string",     // 父分支 ID
  "condition": "string"          // 条件表达式（条件分支）
}
```

---

## 4. 流程实例接口

### 4.1 发起/提交流程
```
POST /web/flowInstanceApi/submit
```
**请求体**
```json
{
  "flowProxyId": "string",        // 流程代理 ID（新建时必填）
  "flowTemplateId": "string",     // 流程模板 ID
  "formData": {...},             // 表单数据键值对
  "nextAuditorList": [          // 下一节点审批人列表（run_node_choose 时需要）
    {"bizId": "userId", "nodeProxyId": "nodeProxyId"}
  ],
  "comment": "string",            // 审批意见（可选）
  "bizId": "string",             // 业务关联 ID
  "bizType": "string"            // 业务类型
}
```

### 4.2 审批（通过/拒绝）
```
POST /web/flowInstanceApi/audit
```
**请求体**
```json
{
  "flowInstanceId": "string",    // 流程实例 ID
  "jobTaskLinkId": "string",     // 任务节点关联 ID
  "auditType": "APPROVE",       // APPROVE / REJECT / TRANSFER
  "comment": "string",           // 审批意见
  "formData": {...},             // 表单数据（可选）
  "nextAuditorList": [...]       // 下一节点审批人（APPROVE 时可选）
}
```

### 4.3 撤回/撤销
```
POST /web/flowInstanceApi/revocation
```
**请求体**
```json
{
  "flowInstanceId": "string"
}
```

### 4.4 回退上一节点
```
POST /web/flowInstanceApi/rollBackThePreviousLevel
```
**请求体**
```json
{
  "flowInstanceId": "string",
  "jobTaskLinkId": "string",
  "comment": "string"
}
```

### 4.5 追加审批人（移交）
```
POST /web/flowInstanceApi/approverAppend
```

### 4.6 流程实例分页列表
```
POST /web/flowInstanceApi/list
```
**请求体**
```json
{
  "page": 1,
  "size": 10,
  "flowTemplateId": "string",
  "title": "string",
  "status": "run",              // draft / run / end / rejected / withdraw / abandon
  "startDate": "2025-01-01",
  "endDate": "2025-12-31",
  "initiatorId": "string",
  "currentNodeAssigneeId": "string",
  "platformCode": "string"
}
```

### 4.7 获取当前表单数据
```
POST /web/flowInstanceApi/getCurrentFromData
```
**请求体**
```json
{
  "flowInstanceId": "string"
}
```

### 4.8 流程追踪列表
```
POST /web/flowInstanceApi/tracking/list
```
**请求体**
```json
{
  "flowInstanceId": "string"
}
```

### 4.9 审批记录列表
```
POST /flowAuditRecord/list
```
**请求体**
```json
{
  "flowInstanceId": "string",
  "page": 1,
  "size": 10
}
```

---

## 5. 任务节点接口

### 5.1 查询节点用户配置
```
POST /flowJobTaskLink/queryNodeUserConfig
```
**请求体**
```json
{
  "nodeProxyId": "string"        // 节点代理 ID
}
```

### 5.2 查找流程实例待办任务
```
POST /flowJobTaskLink/findPendingByFlowInstanceId
```
**请求体**
```json
{
  "flowInstanceId": "string"
}
```

### 5.3 验证审批权限
```
POST /web/flowProxy/validateAuditPermissions
```
**请求体**
```json
{
  "flowProxyId": "string",
  "userId": "string"
}
```

---

## 6. 用户查询接口

### 6.1 用户分页列表
```
POST /web/user/api/user/list
```
**请求体**
```json
{
  "page": 1,
  "size": 50,
  "keyword": "string",           // 用户名/姓名关键字
  "companyId": "string"
}
```

### 6.2 获取人员架构（组织树）
```
POST /web/user/api/user/getUserStructure
```
**请求体**
```json
{}
```
**响应 data** — 树形结构，节点类型：
- `COMPANY` — 公司
- `DEPARTMENT` — 部门
- `PROJECT_DEPT` — 项目部
- `USER` — 用户

### 6.3 获取下属用户
```
POST /web/user/api/user/getSubordinateUser
```
**请求体**
```json
{
  "userId": "string"
}
```

### 6.4 组织全景视图
```
POST /web/user/api/user/findByOrganizationList
```
**请求体**
```json
{}
```

### 6.5 查找上级领导
```
POST /web/user/api/user/findSuperiorLeader
```

### 6.6 根据用户名或手机号查找
```
POST /web/user/api/user/findByUsernameOrPhone
```

---

## 7. 审核类型枚举（AuditType）

| auditType | 说明 | 对应指派策略 |
|-----------|------|-------------|
| `assign` | 指定人员 | manual（手动选择） |
| `initiator` | 发起人自己 | auto（发起人） |
| `run_node_choose` | 审批人自选 | auto（运行时选） |
| `role` | 按角色 | position_random（角色池随机） |
| `company_id` | 按公司 | range_random（公司范围） |
| `position` | 按岗位 | position_random（岗位池） |
| `level` | 按岗级 | department_random（岗级池） |
| `form_person` | 表单人员 | auto（从表单提取） |

---

## 8. 流程状态枚举

| status | 说明 | 生命周期阶段 |
|--------|------|-------------|
| `draft` | 草稿 | 发起前 |
| `await_sent` | 待发 | 运行时（有未选人节点） |
| `run` | 运行中 | 审批流转中 |
| `rejected` | 驳回 | 被拒绝 |
| `withdraw` | 撤销 | 主动撤回 |
| `termination` | 终止 | 被废弃 |
| `end` | 完结 | 终态 |

---

## 9. 审核操作枚举

| 操作 | auditType | 说明 |
|------|-----------|------|
| 通过 | `APPROVE` | 审批通过，流转下一节点 |
| 拒绝 | `REJECT` | 驳回到发起人 |
| 转办 | `TRANSFER` | 转给其他人 |

---

## 10. 数据字段映射速查

### 流程模板相关
| 后端字段 | 前端/代码字段 |
|---------|-------------|
| `flowTemplateId` | `flow_id` |
| `flowTemplateName` | `flow_name` |
| `flowNodeList` | `nodes` |
| `flowBranchList` | `branches` |
| `flowNodeUserList` | `assignment_targets` |

### 用户相关
| 后端字段 | 说明 |
|---------|------|
| `userId` | 用户 ID |
| `username` | 登录用户名 |
| `displayName` | 显示名 |
| `departmentId` | 部门 ID |
| `positionId` | 岗位 ID |
