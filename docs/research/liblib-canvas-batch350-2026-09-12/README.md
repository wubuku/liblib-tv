# Batch 350 — 剩余 8 项归档失败批量分诊（`TRIAGE_RECORDED`）

> 状态：8 项归档失败（6/44/48/49/57/61/64/89）全部复跑并逐项分诊
> 入账（台账 §5.z3 注记更新）；batch 64 分诊为
> `MODERNIZATION_DEFERRED`（专项批次处理），半迁移状态已回滚。
> 无产品代码变更。源站恢复探测：`RECOVERY: still-broken`。

## 复跑结果（2026-09-12，逐项）

| 验证器 | 失败点 | 分诊 |
|---|---|---|
| 6 | selection rectangle did not appear | 维持（marquee 历史化） |
| 44 | line 334 keyframe time 序列 | 维持（同点同形，非时序） |
| 48 | line 224 bare assert | 维持（同点同形，非时序） |
| 49 | viewport gizmo wait 30s 超时 | 维持（同点同形） |
| 57 | text-id 连接元组断言 | 维持（LIBTV-VR-009 local slice） |
| 61 | synthetic corpus 断言 | 维持（LIBTV-VR-016 focused pass 之外） |
| 64 | 级联（toolbar→mobile→stale-guard） | **MODERNIZATION_DEFERRED**：六子流程 × 320px 面板架构重推需专项批次；桌面段 -120→-160 已单点验证，整体半迁移已回滚 |
| 89 | 移动面板关闭按钮（自动关闭生命周期取代） | 维持（batch 339 深查在档） |

## 方法论结论（39/40/41/46/64 五项深查的归纳）

sweep 失败分四类：①时序抖动（39→轮询）；②环境伪影（40→Chrome 147
duration hack）；③验证器读错层/命名漂移（41→authored 层、46→现版
命名）；④真实架构级联（64→面板 flex 化贯穿六子流程，需专项）。
①②③类可低风险修复，④类需专项。

## 验收

- 台账 §5.z3 注记更新；docs check 通过（909 Markdown）；
- 无产品代码变更；维护集态势不变（46 项全绿）。

## 后续候选

- batch 64 专项现代化批次（六子流程 × 320px 架构重推）；
- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
