# 009: SessionManager 防顶号与 SID 失效重登闭环

## Metadata

- type: AFK
- status: todo
- blocked_by: 008
- source: PRD v1.0
- owner: unassigned

## What to build

完善 SessionManager，使同一账号并发只登录一次，SID 失效或被顶后自动重登，并在重登后先查询节点状态，避免重复提交有副作用动作。

## User stories covered

- 30
- 31
- 32
- 33
- 34
- 35
- 51

## Acceptance criteria

- [ ] 同一缓存键并发获取会话时只触发一次登录。
- [ ] SID 有效时复用缓存。
- [ ] SID 失效时自动重登并更新 generation。
- [ ] 账号被顶后能恢复执行。
- [ ] 重登后先查询节点是否仍可处理。
- [ ] 会话复用、登录、重登、失效原因写入 session_log。

## Notes

缓存键为 env_id + login_type + username。不得在日志或报告中明文输出 SID。
