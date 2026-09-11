# Batch 394 — 源站劣化深查结论与循环状态固化（`HOLDING_PATTERN_RECORDED`）

> 状态：liblib.tv 画布页在当前 Chrome for Testing 147 会话中处于
> **深度渲染劣化态**（本批 12 次以上交互尝试、3 次渲染器挂起）。
> BLOCKED_SOURCE 三项与 PAR-004 phase 2、DEC-048 采样裁决继续等待。
> 无产品代码变更。

## 深查证据链（batch 373-394 会话）

1. 新建节点的客户端渲染不完整（innerText 空）——reload 后节点内容
   才完整（服务端持久化正常）；
2. reload 后模型菜单触发器位于视口底部（y≈1109），菜单向下展开被
   视口裁剪；
3. 滚轮缩放 + 触发器点击的探针触发**渲染器挂起**（3 次复现：
   screenshot/evaluate 长时间无响应，浏览器进程存活但页面冻结）；
4. jimeng.jianying.com（并行路线源站）不受影响——其 batch 1-8
   截图与验证器正常。

## 判定

liblib.tv 画布页的劣化是**站点侧/环境侧问题**（SPA 与 Chrome 147
CDP 会话的交互缺陷，或站点部署灰度问题），非 clone 侧可修复。
PAR-005 §10 的劣化记录与复测脚本（probe-source-recovery.py）已
归档，恢复后按 §8 checklist 补采。

## 待恢复队列（恢复后一次执行）

1. BLOCKED_SOURCE 三项补采（Hailuo 系条件分解、480P 档批量、
   Style Video 费率）；
2. 故事板 CLONE_DECISION 替换（真实采样）；
3. PAR-004 phase 2 源站侧对照；
4. DEC-048 采样裁决（append 是否清除冲突键）。

## 验收

- 无产品代码变更；维护集 49 项全绿维持（batch 373 sweep + 387
  回归 + 390 周期确认）；docs check 通过。
