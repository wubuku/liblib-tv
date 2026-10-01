# Batch 333（2026-10-01）：画布内容跨刷新持久化（对齐源站「内容保留、历史清空」）

## 结论一句话

源站**刷新后内容保留、撤销历史清空**（有采样证据），但克隆只把内容放在内存，
刷新即回到 fixture 初值 → 编辑全部丢失。这是**真实的源站对齐缺口**，
不是发明。已补 localStorage 持久化。

## 依据：这次有源站证据，不是 clone-only

与 Batch 332 不同，本批**有直接源站证据**：

- 手册 `20-reference.md`「持久化与历史」：**刷新后内容保留；撤销/重做历史清空**；
- Batch 251 采样记录：「采样后源站画布已复原（…，**刷新确认持久化**）」。

所以「内容跨刷新保留、历史清空」是**已采样确认**的源站行为，克隆此前不符合。

## 运行时证据（修复前）

```
ADDED_SURVIVED : False    新增节点刷新后消失
MOVE_SURVIVED  : False    移动坐标回到 fixture
GROUP_SURVIVED : False    分组消失
HISTORY_RESET  : True     （这一条本来就对）
VERDICT        : CONTENT-LOST
```

## 顺带发现：Batch 208 的断言方向是反的

Batch 208 声称验证「刷新后内容保留」，但断言写作：

```python
check("reload:content-persisted", nodes_after == nodes_before)
```

上下文是「删掉一个节点 → 刷新 → 节点数**回到删除前**」。
也就是说，它把**内容丢失**当成了「持久化」的成功条件 ——
克隆把内容放内存时它通过，一旦真的持久化，它反而失败。

已改为正确语义（源站：刷新后内容保留 → 删除的节点刷新后**仍然不在**）：

```python
check("reload:content-persisted", nodes_after == nodes_before - 1)
```

**这是本批最重要的收获**：一个「通过」的绿色断言，可能正锁着一个缺陷。
Batch 208 的 5 项检查全部 PASS，却从未真正验证过持久化。

## 修复

1. `FRAMEOS_CANVAS_STORAGE_KEY = "frameos.canvasData.v1"`；
   `readPersistedCanvases` / `writePersistedCanvases` 沿用 `directorStore`
   的既有模式（`typeof localStorage === "undefined"` 守卫 + try/catch 降级，
   配额超限/隐私模式静默退化为仅内存，不打断交互）；
2. 读取时**逐条校验结构**（必须是 `{nodes:[], edges:[]}`），损坏数据被忽略；
3. 写入用**单一 store 订阅**，不在 13 个写入点各加一行 ——
   Batch 329 的教训（13 处各自手写快照，漏带 groups）反过来用：
   集中到唯一出口，天然不会漏；
4. **只持久化内容，不持久化 `past`/`future`** —— 与源站
   「内容保留、历史清空」严格一致。

## 关键实现约束：SSR hydration

第一版把持久化内容直接灌进 store 初值，结果控制台报 **hydration mismatch**：
服务端渲染时 `localStorage` 不存在（拿不到），客户端 hydrate 时才有，
两边渲染出**不同的树**，React 只能丢弃服务端 HTML 重新生成。

改为：store 初值一律用 fixture，持久化内容在**挂载后**由
`restorePersistedCanvas()` 应用（`page.tsx` 的 `useEffect`）。修复后
`reload errors: []`。

> 教训：任何「读浏览器存储」的初始化都不能放进渲染路径。
> 写入侧用订阅没问题（只在客户端事件后触发），读取侧必须延后到挂载后。

## 验证器

`scripts/verify-frameos-batch333.py` — **19 项断言全 PASS，0 诊断**：

1. 新增节点跨刷新存活；
2. 移动坐标跨刷新保持；
3. 删除节点跨刷新仍被删除；
4. 连线跨刷新存活；
5. 分组跨刷新存活（成员集一致）；
6. **撤销历史跨刷新清空**（与源站一致，`past === 0`）；
7. 各画布内容独立：切到 B 不含 A 的节点；在 B 上编辑后切回 A 再切到 B，
   B 的编辑仍在，A 也没被污染；
8. **损坏的 localStorage**（`{not-json`）被安全忽略、不崩溃；
9. **非法结构**（`[1,2,3]` 数组）被安全忽略；
10. 清空 localStorage 后回落到 fixture 初值（不残留脏数据）；
11. 控制台/页面错误为 0 —— 这一项同时锁住了 hydration mismatch 不再复发。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch333-refresh.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 334：**审计其余「声称验证但断言方向可能相反」的验证器** ——
  Batch 208 证明绿色断言可能锁着缺陷。同类嫌疑：任何断言
  「操作后某计数回到操作前」的持久化/历史类检查。
  建议做法：grep 验证器里形如 `== nodes_before` / `== initial` 的断言，
  逐个核对它到底该等于操作前还是操作后。
