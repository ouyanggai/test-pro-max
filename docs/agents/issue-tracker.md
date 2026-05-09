# Issue tracker: Local Markdown

本项目使用本地 Markdown 文件推进任务，不使用 GitHub Issues、`gh` CLI 或远程 issue 标签。

## 存放位置

- PRD 文档：`docs/开发文档/`
- 任务拆分总览：`docs/开发文档/issues/README.md`
- 单个任务文件：`docs/开发文档/issues/NNN-短标题.md`

如果 `docs/开发文档/issues/` 不存在，创建该目录。

## 文件命名

单个任务文件使用三位序号和短标题：

```text
001-搭建桌面工作台与环境连接状态闭环.md
002-默认欧阳改登录并查询可发起流程.md
```

序号按依赖顺序递增。后续新增任务不得重排已有编号。

## 任务文件模板

```markdown
# 001: 任务标题

## Metadata

- type: AFK | HITL
- status: todo | doing | blocked | done
- blocked_by: None | 001, 002
- source: PRD v1.0
- owner: unassigned

## What to build

描述这个纵向切片要交付的端到端行为。

## User stories covered

- 1
- 2

## Acceptance criteria

- [ ] 验收标准 1
- [ ] 验收标准 2
- [ ] 验收标准 3

## Notes

实现注意事项、风险、参考文档。
```

## 推进规则

- 新任务默认 `status: todo`。
- 开始处理时改为 `status: doing`。
- 被外部决策、账号、环境或人工验收阻塞时改为 `status: blocked`，并在 `Notes` 说明原因。
- 完成并通过验收后改为 `status: done`。
- `type: AFK` 表示 AI 可按文档直接推进。
- `type: HITL` 表示需要人工确认、设计评审、账号授权、环境许可或业务验收。

## 当技能要求 publish to issue tracker

不要创建 GitHub issue。改为在 `docs/开发文档/issues/` 创建或更新本地 Markdown 任务文件，并维护 `README.md` 总览。

## 当技能要求 fetch the relevant ticket

读取对应的本地任务 Markdown 文件。如果用户给的是编号，按 `docs/开发文档/issues/NNN-*.md` 查找。

## 当技能要求 apply triage label

不要使用远程标签。改写任务文件中的 `type` 或 `status` 字段。
