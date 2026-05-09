# Matt Pocock Skills 使用指南

本项目安装了来自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 12 个 Claude Code 技能。这些技能用于增强软件开发工作流程。

## 技能列表

### 1. setup-matt-pocock-skills
**用途**: 初始化项目配置，为其他工程技能提供上下文  
**触发**: 首次使用其他工程技能前  
**功能**: 
- 配置本地 Markdown 任务推进
- 设置 AFK/HITL 和任务状态 metadata 规则
- 定义领域文档布局

### 2. write-a-skill
**用途**: 创建新的 Claude Code 技能  
**触发**: 用户说"创建技能"、"写技能"、"build a new skill"  
**流程**:
1. 收集需求（技能领域、用例、脚本需求）
2. 起草 SKILL.md 和辅助文件
3. 与用户评审确认

### 3. diagnose
**用途**: 调试复杂 Bug 和性能回退  
**触发**: 用户说"diagnose this"、"debug this"，或报告 Bug  
**流程**:
1. 建立反馈循环（测试/脚本/重放）
2. 复现问题
3. 生成 3-5 个可证伪假设
4. 插桩验证
5. 修复 + 回归测试
6. 清理 + 事后分析

### 4. tdd
**用途**: 测试驱动开发（红-绿-重构循环）  
**触发**: 用户想用 TDD 构建功能或修复 Bug  
**核心原则**:
- 测试行为，不测试实现
- 垂直切片（一个测试 → 一个实现）
- 通过公共接口测试
- 反模式：水平切片（先写所有测试）

### 5. improve-codebase-architecture
**用途**: 发现代码库的深化机会，提升可测试性和 AI 可导航性  
**触发**: 用户想改善架构、找重构机会  
**术语**:
- **Module**: 任何有接口和实现的东西
- **Interface**: 调用者必须知道的一切
- **Depth**: 接口上的杠杆（小接口 + 大实现）
- **Seam**: 可改变行为的位置

### 6. prototype
**用途**: 构建一次性原型，在承诺前验证设计  
**触发**: 用户说"prototype this"、"让我试试"、"尝试几种设计"  
**两个分支**:
- **逻辑原型**: 状态机/数据模型验证 → 终端交互应用
- **UI 原型**: 多种 UI 变体 → 单一路由切换展示

### 7. triage
**用途**: 本地任务分类和状态流转  
**触发**: 用户想创建、分类或审查本地任务  
**状态机**:
- `todo` → 尚未开始
- `doing` → 正在推进
- `blocked` → 被人工决策、环境、账号或外部条件阻塞
- `done` → 已完成并通过验收
- `type: AFK` → AI 可直接接手推进
- `type: HITL` → 需要人工确认、授权、评审或验收

### 8. grill-with-docs
**用途**: 压力测试计划，对照领域模型挑战  
**触发**: 用户想用项目语言和文档决策验证计划  
**功能**:
- 挑战术语一致性
- 锐化模糊语言
- 讨论具体场景
- 更新 CONTEXT.md
- 建议 ADR

### 9. grill-me
**用途**: 无情面试用户的计划或设计  
**触发**: 用户说"grill me"  
**流程**: 一次问一个问题，逐步解析决策树

### 10. to-issues
**用途**: 将计划/PRD 拆分为本地 Markdown 任务  
**触发**: 用户想把计划转为可推进任务  
**垂直切片规则**:
- 每个任务是端到端的薄切片
- 完成后可独立演示/验证
- 偏好多而薄的切片

### 11. to-prd
**用途**: 从当前上下文生成 PRD  
**触发**: 用户想从上下文创建 PRD  
**模板包含**:
- 问题陈述
- 解决方案
- 用户故事
- 实现决策
- 测试决策
- 范围外内容

### 12. zoom-out
**用途**: 提供更高层次视角  
**触发**: 用户不熟悉代码区域，需要理解大局  
**输出**: 所有相关模块和调用者的地图

## 使用流程

### 首次使用
```bash
# 1. 运行 setup 初始化配置
/setup-matt-pocock-skills

# 2. 本项目固定使用 docs/开发文档/issues/ 作为本地 Markdown 任务推进目录
```

### 日常工作流
```
/grill-me          # 压力测试计划
/prototype         # 快速验证设计
/tdd               # 测试驱动开发
/diagnose          # 调试问题
/to-issues         # 拆分成本地 Markdown 任务
/to-prd            # 生成 PRD
/triage            # 分类本地任务
```

## 领域文档

### CONTEXT.md
定义项目领域术语和关系：

```markdown
# 项目名称

一两句话描述

## Language

**Order**:
订单，客户发起的购买请求
_Avoid_: Purchase, transaction

## Relationships

- **Order** 产生 **Invoice**
```

### ADR (Architecture Decision Records)
存储在 `docs/adr/`，记录架构决策：

```markdown
# 使用 Postgres 作为写模型

我们选择 Postgres 而非 MongoDB，因为...
```

## 注意事项

1. **先运行 setup**: 其他技能依赖 setup 生成的配置
2. **术语一致性**: 使用 CONTEXT.md 中定义的术语
3. **ADRs 冲突**: 如果建议与现有 ADR 冲突，需要明确指出
4. **原型是一次性的**: 完成后删除或验证决策
5. **Agent Briefs**: 给 AFK Agent 的说明要描述行为，不描述实现
