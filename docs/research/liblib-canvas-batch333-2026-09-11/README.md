# Batch 333 — 480P 档建模落地 + 源站模型菜单交互失效记录（`PARTIAL_BLOCKED_SOURCE`）

> 状态：clone 侧 `MODEL_RATES_480P` 档位实装并通过验证；
> 源站侧 Hailuo 系条件分解与 480P 批量采样
> `BLOCKED_SOURCE`（模型菜单交互失效，复现 8+ 次）。

## Clone 变更

- 新增 `MODEL_RATES_480P` 表并接入积分公式
  （`480P → 480P 表 ?? 720P 表 ?? 27`）：
  - `Wan 3.0 Prime: 9`——batch 332 同会话 A/B 直证
    （480P=45、720P=90，16:9·5s·1个）；
  - 其余模型未采样（`SOURCE_UNKNOWN`），暂回退 720P 表；
- batch 332 验证器的 `clone-gap` 检查升级为真实行为断言
  （`wan3prime:480p-credits-45`）。

## 源站事实（`SOURCE_DATAPOINT` / `BLOCKED_SOURCE`）

1. **菜单新行「Style Video」**：位于列表最底部
   （Kling3.0 动作迁移之后），描述「图生视频效果稳定，画面表现…」，
   时长标注 2min。batch 320 时该行仅以 DOM 禁用态存在，现为完整行
   （证据 `evidence/menu-dump-with-style-video.json`）。
2. **菜单虚拟化重叠缺陷**：滚动后菜单同时渲染两个虚拟化窗口，
   行在 DOM 中成对出现（同 text 同 y），顶层副本的点击事件死锁
   ——elementFromPoint 命中验证通过、原生点击仍无效果（连错误
   模型都不选中）。batch 332 的「行错位选相邻模型」与本次的
   「点击无效」为同一缺陷族的两种表现。
3. **自动化复现性注记**（影响后续采样批次）：
   - CDP 视口覆盖（`Emulation.setDeviceMetricsOverride`）在页面
     reload 后**复位**——必须 reload 后再设视口，否则视口外坐标
     点击全部落空（elementFromPoint 返回 null 可作探测）；
   - 重载后首次打开模型菜单可能需要**双击**触发器（首击被节点
     激活消费）；
   - 长会话多次开合菜单后出现僵尸层叠加（本批 8+ 次复现），
     唯一可靠恢复是整页 goto，但部署期水合可达 25s+。

## `BLOCKED_SOURCE` 项（待源站恢复后补采）

- Hailuo 2.3 的 5s vs 6s 条件分解（现有并列数据点：36/5s·720P
  与 36/6s·1080P·自适应）；
- Hailuo 2.3 Fast 菜单行错位绕过（scrollTop=max 亦受僵尸层影响）；
- 480P 档批量采样（Wan 2.6/2.7/3.0、Vidu Q2、Happy Horse 1.1、
  Kling 2.6、Minimax H3、Q2 Pro）。

## 验收

- `verify-liblib-batch332.py`（含 480P 新断言）全绿；
- 维护集 43 项全绿；`npm run check` 0 errors；docs check 通过；
- 源站画布 0 节点残留。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 三项补采；
- 故事板双视图（资源总览三栏）复刻；
- Style Video 新模型费率采样与 clone 菜单行入表评估。
