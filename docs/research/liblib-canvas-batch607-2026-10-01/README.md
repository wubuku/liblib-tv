# Batch 607 — 时间轴面板外壳 + 顶边拖拽调高把手

- 日期：2026-10-01
- 源站：<https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429>，CDP `http://127.0.0.1:9222`，1920×1150 @DPR2
- 取证脚本：`/tmp/src593/probe64.py`（面板外壳 + 把手 + 头行三子块）、`/tmp/src593/clone607.py`（clone 侧实测 + 拖拽 + 双向钳制）
- 验证器：`scripts/verify-liblib-batch607.py`（21 项）
- 参考图：`docs/design-references/liblib-timeline-resize-607-1920.png`

## 一句话

源站时间轴面板顶边有一条 1920×8 的 `cursor-ns-resize` 把手，拖它调面板总高——clone 完全没有这个交互，面板底色/边框/阴影/背板模糊也全都不是源站那套。

## 一、源站实测结构

```
div.pointer-events-auto.relative.flex.w-full.min-w-0.flex-col
    .overflow-hidden.rounded-tl-none.rounded-tr-none
    .border-t.border-white/10.bg-[#1f1f1f].text-white
    .shadow-[0_-18px_48px_rgba(0,0,0,0.24)].backdrop-blur-xl
                                                    1920×130 @(0,1020)
  ├ div.absolute.inset-x-0.top-0.z-40.h-2.cursor-ns-resize
  │                            1920×8 @(0,1021)
  │    touch-action: auto   user-select: none   底色透明、无子节点
  ├ div.absolute.inset-x-0.top-0.z-30.flex.min-w-0.gap-[2px]
  │                            1920×36 @(0,1021)
  │   ├ div.shrink-0.bg-[#1f1f1f]                     320×36 @(0,1021)
  │   └ div.relative.min-w-0.flex-1.overflow-hidden
  │        .bg-[#212121]                              1598×36 @(322,1021)
  ├ div.pointer-events-none.absolute.bottom-0.top-0.z-50.overflow-hidden
  │                                                  1598×129 @(322,1021)
  └ div.min-h-0.flex-1                                1920×129 @(0,1021)
```

关键点：把手 `z-40` **压过头行的 `z-30`**，所以它盖住 36px 头行的上沿 8px。
实测 `elementFromPoint` 落在把手中心返回的就是把手自己——源站这个把手是真能抓的。

## 二、clone 改动前 vs 源站

| | 源站 | clone（改前） |
|---|---|---|
| 底色 | `#1f1f1f` | `#161616` |
| 顶边框 | `border-white/10` 1px | `border-white/[0.08]` |
| 阴影 | `0_-18px_48px_rgba(0,0,0,0.24)` | 无 |
| 背板模糊 | `backdrop-blur-xl`（blur 24px） | 无 |
| 上圆角 | `rounded-tl-none rounded-tr-none` | 无显式声明 |
| `min-w-0` | 有 | 无 |
| **调高把手** | **1920×8 `z-40 cursor-ns-resize`** | **完全没有** |

clone 原有的 `cursor-ew-resize` 是车道分隔片与播放头，不是面板级把手——本批之前
时间轴面板无法调高。

## 三、改了什么（`DirectorTimeline.tsx`）

1. 面板外壳照抄源站：`#1f1f1f` / `border-white/10` / `rounded-tl-none rounded-tr-none`
   / `shadow-[0_-18px_48px_rgba(0,0,0,0.24)]` / `backdrop-blur-xl` / `min-w-0`。
2. 新增把手 `data-director-timeline-resize-handle`：
   `absolute inset-x-0 top-0 z-40 h-2 cursor-ns-resize`，透明无子节点；
   `role="separator" aria-orientation="horizontal" aria-label="拖动调整时间轴高度"`；
   `pointerdown` 记起点 → `pointermove` 改高（**往上拖面板变高**，故取 `startHeight - (clientY - startY)`）→ `pointerup/cancel` 收尾，pointer capture 挂在把手自身。
3. 高度是**视图态**：按 batch 599 的结论（文档 schema 故意不含视图态字段，
   `timeline.zoom` 走的是同一条路）它**不进持久化 schema**，因此放在组件本地，
   与 `timelineCollapsed` 同级。新增 `data-director-timeline-height` 便于观测。

实测行为（`clone607.py`）：

| 动作 | 面板高 | 位置 |
|---|---|---|
| 初始 | 182 | @(0,968) |
| 向上拖 80 | **262** | @(0,888) |
| 向下拖 40 | 222 | — |
| 向上拖 900（越界） | **420**（钳制上限） | — |
| 向下拖 1800（越界） | **88**（钳制下限） | — |

page error 0。

## 四、有意偏离与不声称

- **`overflow`**：源站 `overflow-hidden`，clone 保留 `overflow-visible`。时间轴内部有若干
  绝对定位的下拉/浮层（轨道右键菜单、曲线编辑器等）依赖不被裁切；改成 hidden 要连带把
  这些浮层 portal 出去，超出本批范围。**记录在案，不假装一致。**
- **拖拽量程 88..420 是 clone 自定**：源站的量程未取证——拖它的把手会改用户真实工程里的
  面板高度，按约定需要授权。
- **头行右端那枚 244px 的簇**（`absolute right-0 top-0 z-20 … pr-2`，含时间轴缩放与
  时间线最小化）在 `probe54` 那次快照里有、`probe64` 这次没有，判为状态相关，不声称。
- 源站头行**左**格两子块（320px `#1f1f1f` / 1598px `#212121`，gap 2px）本批只复核未改——
  batch 598/600/601 已分别覆盖车道区与工具条两格的几何。

## 五、为什么本批没做「动画时间轴」开关

源站底部胶囊里的「动画时间轴」是 `aria-pressed=true` 的开关，但**要确认它切什么就必须点它**，
而点击源站控件可能写入用户真实工程。按既定规则「行为不可验证时宁可不加也不加一个不工作的
按钮」，本批不碰它，改做可只读取证的把手。要接这个开关，需要把 `DirectorTimeline` 内部的
`timelineCollapsed` 上提到 store——但那属于下一次的结构调整，留给 batch 608。

## 六、门禁与回归

- `verify-liblib-batch607.py`：**21/21**
- 回归：606 / 605 / 604 / 603 / 602 / 601 / 598 / 596 / 593 / 592 / 591 / 587 / 586 / 37 / 36 —— 全过
- `tsc --noEmit`：clean
- `eslint src/`：0 error，warning 数与基线一致
- `npm run build`：通过
- `python3 scripts/verify-docs.py`：见下方（他人在途的 jimeng 手册链接问题仍在，不属本批）

## 七、下一批候选（batch 608）

- **动画时间轴开关**：把 `timelineCollapsed` 从 `DirectorTimeline` 本地 state 上提到
  directorStore（视图态，不进持久化 schema），由底部胶囊的「动画时间轴」驱动。
  注意本批新增的 `timelineHeight` 可一并上提，让两个视图态同源。
- 源站非跟随态下右头的完整内容（batch 606 只采到跟随态）。
- 时间轴头行右端 244px 簇在**非某状态**下的完整构成。
