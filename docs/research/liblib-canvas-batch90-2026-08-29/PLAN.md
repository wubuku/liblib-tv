# Batch 90 计划：Director project/session authority 与场景命令

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 计划

- [x] 读取 Director 评估、project/session/history 合同和 Batch 89 结果；
- [x] 明确本批只处理 session 可观察性与 scene command 边界；
- [x] 实施 session outcome 与稳定诊断入口；
- [x] 实施 scene semantic command；
- [x] 将 scene name 改为 draft + blur/Enter commit；
- [x] 新增并运行 Batch 90 pure/source verifier；
- [x] 新增并运行 Batch 90 fresh-page Playwright verifier；
- [x] 运行 current-gate 与全量检查；
- [x] 记录结果并 commit/push。

## 2. 不可破坏的约束

- 不把 `sessionOutcome`、selection、playhead、panel 或 R3F runtime ref 写入
  portable project；
- 失效 owner/session 不允许 scene command 改写 registry、persistence 或 history；
- scene name 不能提交为空；
- 连续文本输入不能制造逐字符 Director history；
- 普通 canvas graph history 与 Director project history 保持隔离；
- 不新增截图，除非结构化 DOM/状态无法验证本批合同。

## 3. 验证矩阵

| 场景 | 预期 |
|---|---|
| 初始打开 | owner/project/session/generation/lifecycle 可读 |
| scene name 连续输入 | state draft 可变，history 不逐字符增长 |
| scene name blur/Enter | 成功时一条 history，registry/persistence 更新 |
| 空白 scene name commit | reject/no-op，旧值保留 |
| ground/grid/color command | 成功时一条 history，字段更新 |
| same-value update | `NOOP`，零 history |
| undo/redo | 恢复 scene document |
| mobile inspector | 无水平溢出 |
| diagnostics | console/page/request error 均为 0 |
