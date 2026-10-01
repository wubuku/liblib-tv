# Batch 344（2026-10-01）：分组右键菜单的「删除」弹了绿色成功提示，却什么都没删

## 结论一句话

分组右键菜单的「删除」项此前只是 `showToast("已删除分组 (mock)", "success")`
—— 一条**绿色成功提示说分组已删**，而**分组就在画布上原地不动**。
同一菜单标注的 ⌫ 快捷键在纯选中分组时**毫无反应**。两处都改用 store 已有的
`ungroup`，一个动作解决。

## 运行时证据（修复前）

探针 `scripts/probe-frameos-batch344-group-menu.py`：

```
菜单项: ['复制\n⌘C', '创建副本\n⌘D', '删除\n⌫']
[点「删除」] groupCount=1  hasGroup=True  DOM 分组盒=1   ← 组还在
  toast: []                                   ← 探针没抓到 toast 文本
[按 ⌫]      before: hasGroup=True selectedGroupId=group-… selectedNodeId=None
            after : hasGroup=True groupCount=1 pastDepth=1  ← 毫无反应
```

修复后：

```
[点「删除」] groupCount=0  hasGroup=False DOM 分组盒=0 pastDepth=2
[按 ⌫]      after : hasGroup=False groupCount=0 pastDepth=2
```

## 为什么这条比「两个死按钮」严重

死按钮点了没反应，用户一眼就知道不对。而这一条是**主动撒谎**：绿色对勾 +
「已删除分组」的字样 + 组仍在原地。用户会以为分组已经删掉了，于是继续操作，
直到某天发现它还在——而中间的判断已经基于错误前提了。

> **一个会撒谎的 UI 比一个明显坏掉的 UI 更危险**：坏掉的会让人停下，撒谎的
> 让人继续往下走。

## 修复 1：「删除」复用已有 action，且不发 toast

```diff
- onClick: () => showToast("已删除分组 (mock)", "success"),
+ onClick: () => ungroup(group.id),
```

`ungroup` 正是工具条「解组」用的那个 action —— 移除分组、成员位置保持，
自带入撤销栈、自带清理 `selectedGroupId`。

**不发 toast**：组从画布上消失本身就是反馈。这与 `FrameosGroupToolbar`
的解组保持一致（它也不发 toast），而且比一条可能不兑现的文案诚实。

## 修复 2：⌫ 快捷键接上

`page.tsx` 的 Delete/Backspace 分支此前只认 `selectedNodeId`。菜单上写着 ⌫，
用户按了却什么都不发生 —— **菜单上写着的快捷键必须能用**。

```ts
if (state.selectedNodeId) { ...removeNode... return; }
if (state.selectedGroupId) { ...ungroup... return; }
```

节点优先（Batch 177 的语义不变），仅在没选中节点时才走分组分支。

## CLONE_DECISION

「删除分组」也可能读作「连成员一起删」。那是**破坏性**操作、需要二次确认，
而源站行为**未采样**（人机验证阻塞，见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）
—— **不擅自发明**。本次取非破坏、可撤销的那一种读法（成员位置保持），
并在代码注释里写明：若日后源站可采样且确认是另一种读法，只需改这一处。

`复制` / `创建副本` 两项**仍然保留为 mock**：源站实测确认了这两个**条目存在**
（SOURCE_FACT），但没采样它们**做什么**。要实现就得发明语义 ——
比如「创建副本」是让新组与原组**共享成员**吗？那会打破「一个节点只属于一个组」
的模型。所以不动它们，但记录在案。

## 验证器

`scripts/verify-frameos-batch344.py` — **15 项断言全 PASS，0 诊断**：

1. 菜单三项齐全（复制/创建副本/删除）—— 源站确认过它们存在，不删；
2. 「删除」标注了 ⌫；
3. 点「删除」后分组从 **store** 消失；
4. 点「删除」后分组从 **DOM** 消失（两侧都验，不只看数据）；
5. 成员节点**一个不少**（ungroup 语义，不是删成员）；
6. 分组计数正确 −1；
7. 不留**悬空选中**（`selectedGroupId` 已清）；
8. **不再有「已删除分组」这类可能不兑现的 toast**；
9. 撤销能还原分组；
10. 选中分组时按 ⌫ **真的删掉分组**；
11. ⌫ 后成员仍在；
12. **选中节点时按 Delete 仍删节点**（Batch 177 不回归）；
13. 节点计数正确 −1；
14. 诊断零错误。

**变异测试**：把 `ungroup(group.id)` 改回 `showToast("已删除分组 (mock)")`
后，验证器如期失败于 `delete:group-gone-from-store (hasGroup=True)`。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch344-group-menu.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- `复制` / `创建副本` 仍是 mock —— 需源站采样才能实现，不发明。
- `FrameosGroupCanvas.tsx:236` 的「批量连线 (mock)」同样未实现（同一类）。
- `FrameosNodeEditPanel` 的「复制节点」「锁定位置」两个按钮仍无 `onClick`，
  且整面板只在 `isDebugMode` 下渲染而该开关全仓无 UI 入口。
- store 的 `generations` 字段**从未被写入也从未被读取**（死状态）。
