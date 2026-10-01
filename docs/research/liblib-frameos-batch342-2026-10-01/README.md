# Batch 342（2026-10-01）：节点搜索「点击结果聚焦」用错了坐标系（+ 一个否定结论）

## 结论一句话

`FrameosNodeSearch.focusNode()` 把节点的**屏幕坐标**（`getBoundingClientRect()`）
喂给了 `useReactFlow().setCenter()`，而后者要的是**画布流坐标**。默认视图下
偏移小、几乎看不出来；一旦用户缩放/平移过画布，点击搜索结果就会把**目标节点
推出屏幕**。修复后同一场景从 (1272, −66) 变成 (800, 475) 正中心。

## 运行时证据（修复前）

探针 `scripts/probe-frameos-batch342-search-focus.py` 把视口改成
`translate(400px, 260px) scale(0.5)`（模拟用户缩放+平移过）：

```
目标节点 video-1 flow 坐标 {'x': 996, 'y': 39}
点击前屏幕中心: (973, 322)
点击后屏幕中心: (1272, -66)      ← 中心比视口顶边还高 66px
视口中心应为  : (800, 475)
偏离视口中心  : dx=+472px  dy=-541px
选中态: video-1 (正确)   缩放: scale(2.73) (正确)
```

**选中对了、缩放对了，只有「聚焦」是错的** —— 组件注释声明的意图是
「选中该节点并把视野缩放聚焦到它」，实际效果是把节点挪出视野。

修复后同一探针：`offset_x_px: 0, offset_y_px: 0, centered: true`。

## 修复

```ts
const node = nodes.find((n) => n.id === id);
if (!node) return;
const w = (node.style?.width as number | undefined) ?? 300;
const h = (node.style?.height as number | undefined) ?? 200;
setCenter(node.position.x + w / 2, node.position.y + h / 2, {
  zoom: 2.73, duration: 600,
});
```

缩放值 2.73 保持不变（源站实测值），只把「中心点」的坐标系换对。

## 为什么这个 bug 之前没被发现

它在**默认视图**下几乎不可见：默认视口原点接近 (0,0)、缩放接近 1，屏幕坐标与
流坐标只差一个画布内边距，量出来「差不多居中」就过去了。

因此本验证器**先做非默认视图**再点结果 —— 用真实用户手势（点 3 次「缩小」+
空白处拖拽平移），不是改 DOM 伪造状态。这条前置本身就是断言之一
（`precondition:viewport-distorted`）：没有它，后面的居中断言会在旧代码上
假通过。

## 变异测试

把修复临时改回屏幕坐标后，验证器如期失败：

```
AssertionError: batch342 check failed: focus:centered
  node center=(547,-38) expected=(800.0,475.0) dx=-253 dy=-513
```

注意 `cy = -38` —— 节点又一次被推出屏幕顶边。改完必须再证它会红。

## 同批的**否定结论**：持久化每帧写 localStorage —— 不修

Batch 333 的持久化订阅按引用判「内容变更」，而拖拽每帧产生新 `nodes` 引用
（分组拖拽 `FrameosGroupCanvas.tsx:76` 每帧调 `moveGroup`）→ **每帧一次
`JSON.stringify` + 同步 `setItem`**。探针
`scripts/probe-frameos-batch342-persist-io.py` 实测：

| 规模 | 载荷/次 | 每帧耗时 | 40 帧写入次数 |
|---|---|---|---|
| fixture 7 节点 | 3 KB | 0.025 ms | 41 次（每帧一次，结构问题属实） |
| 扩容 287 节点（组内 60 成员） | 111 KB | 0.11 ms | 40 次 |

**结构上确实每帧都写**，但即使载荷涨到 111 KB，每帧也只有 0.11 ms —— 远低于
16 ms 的帧预算，**不构成用户可感知的卡顿**。

所以**不改**。「每帧写 localStorage 听起来很糟」这句话在没有实测前不能当缺陷
来修。数字留档，便于日后画布体量增长时重新评估（外推：要到 ~2 万节点才会吃掉
一帧预算，而那时 localStorage 5 MB 配额早已先撞上）。

> 这是本会话第二个**有价值的否定结论**（第一个是 Batch 339 的「断言方向」门禁）。
> 拒绝修一个听起来像缺陷、实测不是缺陷的东西，和修掉一个真缺陷同样重要。

## 验证器

`scripts/verify-frameos-batch342.py` — **10 项断言全 PASS，0 诊断**：

1. 前置：视口已被真实手势弄成非默认状态；
2. 「搜索节点」能打开面板；
3. 输入后目标节点出现在结果里；
4. 点击结果后**选中**该节点；
5. 缩放达到源站实测的 2.73；
6. 目标节点落在视口中心（容差 60px）；
7. 目标节点**四边完整可见**；
8. 点**另一条**结果时聚焦的是那条（防「恒定聚焦第一条」的假实现）；
9. 诊断零错误。

写验证器时踩到的坑（值得记）：点搜索结果**不会**关闭面板（组件注释即声明
「× / Esc 关闭」）。我最初在第二段又点了一次 toggle 按钮 → 面板被**关掉** →
后续 `fill` 超时，一度以为是应用缺陷。**验证器失败先看失败在哪一步**，
这是 Batch 208 之后反复用到的那条。

证据：`runtime-audit.json`（本目录）。
复现探针：`probe-frameos-batch342-search-focus.py`、
`probe-frameos-batch342-persist-io.py`（均只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- `FrameosNodeEditPanel` 的「复制节点」「锁定位置」两个 `ActionButton` **没有
  onClick**（空壳），且整个面板只在 `isDebugMode` 下渲染，而 `toggleDebugMode`
  全仓**没有任何 UI 入口**。是否该接线属于源站对齐问题 → 阻塞，先记录不动。
- `generations` 数组在 store 里有字段、**从未被写入也从未被读取**（死状态）。
