# Batch 355 — batch 57 定案：TextNode 把手缺 id（`PRODUCT_FIX`）

> 状态：真实产品一致性缺陷修复；batch 57 三连绿；台账 §5.z3
> 更新（57 → 已修复转绿，**清算 9/13**）。源站恢复探测：
> `RECOVERY: still-broken`。

## 根因（handle() 助手断言定位）

TextNode 的两个 `<Handle>`（target/source）**缺少 `id` 属性**——
React Flow 因此不给元素写 `data-handleid`，`batch 57` 的
`[data-handleid="source"]` 选择器找不到把手（count=0）。
其余全部节点类型（Image/Video/Script/StoryboardGroup/VideoClip/
ScriptExecution/LongVideoProcess）都显式带 `id="source"/"target"`
——统一加名的批次漏掉了 TextNode。

## 修复（产品）

`TextNode.tsx` 两个 Handle 补 `id="target"` / `id="source"`（与其余
节点类型一致；无视觉变化）。

## 验收

- batch 57 三连跑全绿（连接建立/撤销/重做/选区不变/历史长度等
  全量合同）；
- 回归：typecheck 通过；docs check 914 文件通过。

## AGED_GATE 清算进度（9/13）

已转绿：29/39/40/41/46/48/49/57/64。
维持归档：6（marquee 历史化）、61（LIBTV-VR-016 语料）、
89（移动面板生命周期取代）。

## 后续候选

- 61/89 深查收尾（61 语料断言、89 已有 339 结论可复核）；
- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
