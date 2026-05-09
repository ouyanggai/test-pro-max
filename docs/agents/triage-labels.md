# Local Task Metadata

本项目不使用 GitHub/GitLab issue 标签。任务推进只依赖本地 Markdown 文件中的 metadata 字段。

## Type

| Skill wording | Local `type` | Meaning |
| --- | --- | --- |
| AFK / ready-for-agent | `AFK` | 描述完整，AI 可直接接手推进 |
| HITL / ready-for-human | `HITL` | 需要人工确认、评审、授权或验收 |

## Status

| Local `status` | Meaning |
| --- | --- |
| `todo` | 尚未开始 |
| `doing` | 正在推进 |
| `blocked` | 被人工决策、环境、账号或外部条件阻塞 |
| `done` | 已完成并通过验收 |

## Rules

- 技能提到“apply label”时，不要操作远程标签，改为更新任务文件 metadata。
- 技能提到 `ready-for-agent` 时，使用 `type: AFK`。
- 技能提到 `ready-for-human` 时，使用 `type: HITL`。
- 任务状态变化只更新 `status` 字段，并在 `Notes` 中补充必要说明。
