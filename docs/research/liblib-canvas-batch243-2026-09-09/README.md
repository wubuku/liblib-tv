# Batch 243 — 菜单末两行采样受阻记录（Style Video / Kling3.0 动作迁移）

> 状态：`BLOCKED_AUTOMATION`（三次配方尝试均未成功切换；无代码变更）。
>
> 证据：`sample-log.json`（每次尝试的 footer 状态）。

## 尝试记录

对 Style Video（菜单第 35 项）与 Kling3.0 动作迁移（第 34 项）的三种
自动化配方均失败：

1. `scroll_into_view_if_needed()` + 行框点击（batch 240 配方）——点击后
   状态未变（长视频态 14700 保持）；
2. 整行 BUTTON + 最小额外长度匹配 + 再定位——同失败；
3. 菜单容器 `scrollTop = row.offsetTop - clientHeight/2` 手动定位——
   Style Video 行点击落空（footer 仍 14700/Auto·720P·300s，疑似点击
   坐标与滚动后实际行错位）；动作迁移行再定位返回 None。

对照基线：长视频态（2.5·Auto·720P·300s·1个 = 14700）多次复认
（batch 176/238 合同）。

## 结论

- 35 个模型中 **33 个已有费率/数据点**；Style Video 与 Kling3.0 动作迁移
  记为 `BLOCKED_AUTOMATION`——自动化点击菜单最末两行不可靠，留待
  人工采样或更深度配方（如 CDP Input 原生事件序列）；
- 附带复认：长芯片 → 面板打开配方（JS 原子 click）稳定可用——本轮
  建节点/提交芯片/面板打开全链路一次成功（此前批次的开箱失败均因
  过期 bounding box，JS click 已根治）。

## 后续候选

- 首帧态紧凑页脚（单 pill）+ 参考槽「销毁」按钮复刻评估；
- OmniHuman 1.5 模式名与芯片上下文补采；
- 生成按钮点击后的任务流采样（本会话未触及）。
