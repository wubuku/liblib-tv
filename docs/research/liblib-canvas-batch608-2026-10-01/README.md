# Batch 608 — 底部胶囊的「动画时间轴」开关 + 时间轴视图态上提 store

- 日期：2026-10-01
- 源站：<https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429>，CDP `http://127.0.0.1:9222`，1920×1150 @DPR2
- 验证器：`scripts/verify-liblib-batch608.py`（15 项）
- 参考图：`docs/design-references/liblib-timeline-toggle-608-1920.png`

## 一句话

源站底部第一枚胶囊里有一枚 `aria-pressed=true` 的「动画时间轴」开关，而 clone 的时间轴**常驻、根本没有整条开关**；本批把它补上，并把两个时间轴视图态从组件本地 state 上提到 store，让开关与拖拽把手操作同一份状态。

## 一、源站实测

底部第一枚胶囊只有三项 —— 移动 / 截图 / **动画时间轴**，各 32×32、图标 20px、
`rounded-lg`，选中态追加 `bg-white/8`（实测 8% alpha）。其中：

```
button 动画时间轴   32×32 @(869,976)   aria-label="动画时间轴"
                    aria-pressed="true"   icon size-5 (20×20 @(875,982))
                    cls: group relative flex size-8 shrink-0 items-center
                         justify-center rounded-lg text-white transition-colors
                         hover:bg-white/8 disabled:cursor-not-allowed
                         disabled:opacity-35 bg-white/8
```

取样时它 `aria-pressed=true`，且时间轴面板同时可见。

## 二、clone 改动前

- 时间轴**永久可见**，`DirectorTimeline` 直接挂在 `DirectorDesk` 下，没有整条开关；
- 底部胶囊里也**没有**「动画时间轴」这枚控件（clone 那枚胶囊装的是变换模式/画幅/
  九宫格/虚拟相机/群众/模型库/保存构图）；
- 面板高度是 `DirectorTimeline` 的组件本地 `useState`（batch 607 引入）。

## 三、改了什么

### 1. 两个视图态上提到 `directorStore`

新增 `timelinePanelOpen: boolean` 与 `timelineHeight: number`，外加
`setTimelinePanelOpen` / `toggleTimelinePanel` / `setTimelineHeight` 三个 action；
三个初始化点（restore / createDefault / 种子）都给 `true` 与 `182`。

**刻意不进持久化 schema**：这与 `viewportPanelsCollapsed` 同款，也与 batch 599 的
`timeline.zoom` 同款——文档 schema 只描述工程内容，不描述面板此刻的开合与高度。
batch 599 的 10/10 契约在本批之后依然全过，说明没碰坏那条线。

三个高度常量（`DEFAULT_HEIGHT=182` / `MIN=88` / `MAX=420`）随之从
`DirectorTimeline.tsx` 搬到 store 所在模块并 export，组件改为引用。

### 2. `DirectorTimeline` 读 store、`timelinePanelOpen === false` 时 `return null`

面板整条消失，视口顺势长高填满腾出的空间。

### 3. 底部胶囊补上「动画时间轴」

`data-director-timeline-toggle`，`aria-label` / `title` 逐字为「动画时间轴」，
`aria-pressed={timelinePanelOpen}`，选中态 `bg-white/8`；
位置放在变换模式之后、画幅比例之前。图标 20px。

## 四、实测行为

| 状态 | `aria-pressed` | 底色 | 面板 | 视口高 | store |
|---|---|---|---|---|---|
| 初始 | `true` | `white/8` (0.08) | 存在，182 | 880 | `{open:true, h:182}` |
| 点一下 | `false` | 透明 | **不存在** | **1062** | `{open:false, h:182}` |
| 再点 | `true` | `white/8` | 存在，**182 保留** | 880 | `{open:true, h:182}` |

视口底边 968 → 1150 → 968，page error 0。

**两个面板动词相互独立**：「动画时间轴」整条隐藏；面板内的「时间线最小化」
仍按 batch 591/592 的 182 → 88 收窄，面板仍在。验证器专门断言了这一点。

## 五、一处必须说清的推断

**源站那枚按钮的点击行为从未取证。** 点源站控件可能改用户真实工程，按约定需要授权，
所以本批没点。它的语义取自三个互相印证的读数：按钮名「动画时间轴」+
`aria-pressed="true"` + 面板此刻可见。这是 clone 侧推断，**不声称源站的确切结果**。

之所以仍然落成一个开关而不是不写：既定规则是「行为不可验证时宁可不加也不加一个
不工作的按钮」——而这里可以落成一个在 clone 上**端到端可验证**的真开关
（`aria-pressed` ↔ 面板存在性 ↔ 视口高度三者联动，全部有断言）。
源站与 clone 的行为是否一致，仍属未取证。

## 六、门禁与回归

- `verify-liblib-batch608.py`：**15/15**
- 回归：607 / 604 / 605 / 606 / 599 / 593 / 592 / 591 / 86 / 82 / 70 / 49 / 47 / 41 / 40 / 36 / 35 —— 全过
- `tsc --noEmit`：clean
- `eslint src/`：0 error，warning 数与基线一致
- `npm run build`：通过
- `python3 scripts/verify-docs.py`：通过

### 验证器里一处自查修正

初版把选中态断言写成 `alpha == 0.1`，实测是 `0.08`——**`bg-white/8` 就是 8%**，
断言写错而非实现错。已改为 0.08 并在验证器里注明。这与源站实测的
`bg-white/8` 是同一个值（batch 604 已记录源站选中态同样是 8%）。

## 七、下一批候选（batch 609）

- **源站底部胶囊缺的另两项**：`截图`（32×32 @(829,976)，源站点它可能写真实工程，
  暂不接）与 `移动`（源站无 `aria-pressed`，可能是开菜单而非切档，
  clone 现有 transformMode=translate 可作为近似）。
- 时间轴头行右端 244px 簇（时间轴缩放 + 时间线最小化 + 导出）在非某状态下的构成。
- 源站非跟随态下右头的完整内容（batch 606 只采到跟随态）。
