# Batch 335 — 全量验证器清扫与回归归因（`SWEEP_RECORDED`）

> 状态：batch 223 以来首次全量清扫。189 个 Python 验证器：
> 首轮 169 绿 / 20 红；**7 个过期断言修复后全绿**，其余 13 个全部
> 为已归档 AGED_GATE / 历史合同 / ownership-managed，无近期批次回归。
> 维护集（42 项 + 332/334）全绿。
>
> 证据：`evidence-sweep-results.txt`（逐脚本结果）。

## 修复的过期断言（7 项，均系 UI 重建后的验证器迁移）

| 验证器 | 过期原因 | 修复 |
|---|---|---|
| 14 / 97 | batch 201 将 Agent「换一批」目录替换为源站真采四批，`character`（角色三视图）已不在任何批次 | 断言改为第二批首张 `gameplay-pv` |
| 101 | HistoryPanel 评级芯片已成对（本画布/全部画布），单元素定位触发 strict 违规 | `.first` + 按 `="canvas"` 取选中芯片 |
| 107 | 抽屉标题轮换模数从 4 变 5（batch 273 第五条标题） | HEADLINES 补第五条 + 批次错位断言（5%4=第二批） |
| 17 | 筛选菜单属性已迁移（batch 298：`filter-option` → `type-option`，中文值） | 属性名迁移（图片/全部） |
| 19 | batch 298 后资产面板由浮层改为 320px flex 兄弟：工具栏位移 240 不变，`.liblib-minimap` 随画布 pane 位移 320 | 小地图位移断言 240→320 + 差值扩大 80 断言 |
| 202 | 资产面板宽度 280→320 | 宽度断言更新 |

## 残余 13 项失败（全部为已归档历史合同，非回归）

- **AGED_GATE 在档**（batch 108/184 归因，REPLACEMENT_MAP §4.z）：
  6、40、41、44、46、48、49；
- **ownership-managed**（REPLACEMENT_MAP 所有权切片）：57（connection
  local slice）、61（routing SCRIPT_RECORDED_PASS 之外的生命周期）、
  64（Asset host-resize viewport owner，现值 x=-160）；
- **媒体/交互伪影与旧时代合同**：29（播放器 hover 帧菜单点击，
  2026-08-25 时代）、39（timeline currentTime 媒体元数据伪影，
  同 batch 184 模式）、89（Director scene settings，导演台重建前）。

## 结论

- 近期批次（332–335）**零回归**：所有产品侧验证器与维护集全绿；
- 残余失败均有在档归因，不作为当前合同通过依据（AGED_GATE 处置
  惯例不变）；
- 后续可按 REPLACEMENT_MAP 逐项现代化（低优先）。

## 验收

- 修复后复跑：14/17/19/97/101/107/202 全绿；
- 维护集 44 项（42 基线 + 332/334）全绿；
- `npm run check` 0 errors；docs check 通过（894 Markdown）。
