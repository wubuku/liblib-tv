# Batch 605 — 顶栏视角对 + 「正在跟随」浮层

- 日期：2026-10-01
- 源站：<https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429>，CDP `http://127.0.0.1:9222`，视口 1920×1150 @DPR2
- 取证脚本：`/tmp/src593/probe55.py`（顶栏全量扫描）、`probe58.py`（视角对容器链 + 跟随浮层）、`probe59.py`（浮层逐节点）、`probe60.py`（pointer-events 实测）、`/tmp/src593/clone605.py`（clone 侧同口径）
- 验证器：`scripts/verify-liblib-batch605.py`（38 项）
- 参考图：`docs/design-references/liblib-follow-banner-605-1920.png`

## 一句话

源站顶栏的「导演视角 / 机位视角」不是顶栏 grid 的一格，而是**浮在视口正中**的 170×36 胶囊；而机位跟随时源站会在同一位置挂一条橙色「正在跟随」浮层——clone 两样都没有。

## 一、视角对：源站实测

```
div.pointer-events-auto.absolute.left-1/2.top-2.-translate-x-1/2
  div.border-white/8.flex.h-9.items-center.justify-center.gap-0.5
      .overflow-hidden.rounded-xl.border.bg-[#212121].p-0.5.w-[170px]
                                                    170×36 @(875,8)
    ├ button h-8.rounded-[10px].text-[13px].leading-5.transition-colors
    │        .min-w-0.flex-1.px-2.bg-white/10.text-neutral-50
    │                                                    81×32 @(878,10) ← 选中
    └ button …text-neutral-50.hover:bg-white/10          81×32 @(961,10) ← 未选中
```

要点：

- 容器 `w-[170px] h-9` **定宽**，两枚 `flex-1 min-w-0` 因此等分，各 81px，间隙 2px（`gap-0.5`）。
- 两枚按钮的**文字色相同**（都是 `text-neutral-50`），只有底色区分选中态——不是 clone 之前那种「选中变白、未选中变灰」。
- 容器 `rounded-xl`（12px）`border-white/8`（1px rgba(255,255,255,0.08)）`bg-[#212121]` `p-0.5`。
- 源站这两枚按钮**没有 `aria-label`**，可及名来自可见文字。clone 保留 `aria-label`（可及名等价，且便于定位），记为有意保留。

| | 源站 | clone（改前） |
|---|---|---|
| 容器 | 170×36 `w-[170px] h-9 rounded-xl border-white/8 bg-[#212121] p-0.5 gap-0.5` 绝对定位居中 | 140×32 `flex h-8 rounded bg-[#242424] p-0.5`，顶栏 grid 中间格 |
| 按钮 | 81×32，间隙 2 | 68×28，`dx=0`（无间隙） |
| 圆角 | `rounded-[10px]` | `rounded`（4px） |
| 字号 | 13px / line-height 20px | 11px / 16.5px |
| 内距 | `px-2`（8px） | `px-3`（12px） |
| 选中 | `bg-white/10 text-neutral-50` | `bg-[#3a3a3a] text-white` |
| 未选中 | `text-neutral-50 hover:bg-white/10` | `text-[#858585]` |

## 二、「正在跟随」浮层：源站实测

```
div.pointer-events-none.fixed.left-1/2.top-0.z-[305].-translate-x-1/2
    .motion-safe:transition-opacity.motion-safe:duration-200
                                                    173.7×34 @(873.1,0)
  div.flex.items-center.gap-2.rounded-b-xl.border.px-3.py-1.5.text-white
      .shadow-md.pointer-events-none
      底色与描边 rgb(228,101,37) = #E46525
      border-radius 0 0 12px 12px（rounded-b-xl）
    ├ span.inline-block.size-2.shrink-0.rounded-full.bg-white
    │                                    8×8 @(886.1,13)  静态白点（animation: none）
    ├ span.text-sm 「正在跟随」            56×20 @(902.1,7)  14px
    └ span.relative.ml-1.inline-flex
        ├ button[aria-label=退出跟随]
        │   .peer.rounded-full.bg-white.px-2.py-0.5.text-xs.font-medium
        │   .leading-none.text-gray-900.hover:bg-white/90
        │                                63.7×16 @(970.1,9)  文案「取消ESC」
        └ span.pointer-events-none.absolute.left-1/2.top-full.z-10.mt-2
            .-translate-x-1/2.whitespace-nowrap.rounded-md.bg-black/90
            .px-2.py-1.text-xs.font-normal.text-white.opacity-0.shadow-md
            .transition-opacity.peer-hover:opacity-100
                                     82.1×24 @(960.9,33)  文案「按 ESC 退出」
```

`#E46525` 是源站的新品牌橙（此前 clone 里没有这个色）。那个 8px 白点是**静态**的
（实测 `animation-name: none`），照抄，没做呼吸动画。

## 三、跟着一起发现的一处源站缺陷（有意偏离）

浮层与它的面板都写了 `pointer-events-none`，而「取消」按钮**自己没写 `pointer-events-auto`**，
于是从浮层继承到 `pointer-events: none`。实测（`probe60.py`）：

```
cancel button   pointerEvents: "none"        （从祖先继承）
elementFromPoint(按钮中心) → button.h-8.rounded-[10px]…   ← 底下的「机位视角」
hitIsCancel: false
```

也就是说**源站这枚「取消」根本点不动**——浮层与视角对在屏幕上重叠，视角对在命中链上；
那句 `peer-hover` 的「按 ESC 退出」也因此永远显不出来。

本批的处理：**几何、配色、文案、圆角、内距全部照抄，只把命中打开**
（按钮加 `pointer-events-auto`）。理由是目标要求复刻的是**用户体验**而不是静态组件，
一个死按钮不构成可复刻的体验。ESC 键退出则是源站的真实语义（提示文案就写着
「按 ESC 退出」），clone 接上了。

## 四、改了什么

1. **视角对改源站外壳**（`DirectorDesk.tsx`）：从顶栏 grid 的中间格移出，改为
   `pointer-events-auto absolute left-1/2 top-2 -translate-x-1/2` + 内层
   `flex h-9 w-[170px] gap-0.5 overflow-hidden rounded-xl border-white/[0.08] bg-[#212121] p-0.5`；
   按钮 `h-8 min-w-0 flex-1 rounded-[10px] px-2 text-[13px] leading-5 text-neutral-50 hover:bg-white/10`，
   选中追加 `bg-white/10`。
   `data-director-view-mode` 属性与切换行为**未动**。
2. **新增「正在跟随」浮层**（`DirectorDesk.tsx`）：判据是活动机位的
   `camera.followTargetId` 非空——与 `DirectorInspector` 的「跟随目标」选择器、
   `DirectorTimeline` 的「跟随目标时不可使用预设运镜」、
   `DirectorPhoneVcamPanel` 的「请先关闭机位跟随」用的是同一个字段
   （`directorStore.ts:6308`）。新增 `data-director-follow-banner` /
   `data-director-follow-cancel` 两个定位属性。
3. **ESC 键语义**：原 Escape 处理链末尾直接 `closeWorkspace()`，现在在它之前插一档
   「有跟随目标 → 清空 `followTargetId` 并返回」。也就是说跟随中按 ESC 是**退出跟随**，
   不是关掉整个导演台。

## 五、本批不声称

- 源站顶栏其余控件本批只测未改：`收起`（40×40 `size-10 text-white/72 @(240,5.5)`，
  clone 是 32×32 `rounded #a3a3a3 @(155,7.5)`）、`项目名称`（可内联编辑的 input，
  `border-b border-dashed`、`min-w-[30px] max-w-[100px]`）、`画布 1` 芯片
  （67.5×32 `h-8 rounded-lg px-2 gap-1`）、`发布与分享` / `积分超市` / 积分数字
  （`20`，57.9×32）。没改的原因是结构不同：源站左头是**定宽 280px 的一列**
  （`header.border-white/8.flex.h-[52px].items-center.border-b`），右头也是定宽 280px
  （`flex.shrink-0.items-center.justify-between.h-12.px-3`），而 clone 顶栏是横跨工作区的
  三列 grid。硬套会牵动整条顶栏的布局，留给后续批次按整条顶栏一起做。
- 源站视角对那两枚按钮的点击行为未取证（切换的是导演/机位视角，与 clone 现有行为一致，
  但源站是否还有别的副作用未知）。
- 源站「取消 ESC」按钮的实际点击结果未取证（它在源站本就点不动，probe60 已实测）。
- 源站工程现状已被他人改动（新增「角色A」、几何模型浮层展开、机位位置 3.3/2.2/10），
  本批只做只读测量，未点击任何会写入工程的操作。

## 六、门禁与回归

- `verify-liblib-batch605.py`：**38/38**
- 回归：604 / 603 / 587 / 586 / 83 / 37 / 36 / 35 / 44 / 43 / 41 / 49 —— 全过
- `tsc --noEmit`：clean
- `eslint src/`：见下方
- `python3 scripts/verify-docs.py`：见下方

### 连带修好的既有失败

batch 49 此前失败于 `TransformControls: The attached 3D object must be a part of the
scene graph.` 基线对照（`git checkout --` 回到 HEAD 的 `DirectorDesk.tsx` 重跑）确认
在 HEAD 上同样失败，且报 2 条——与本批无关。按 batch 35 / 37 / 46 的既有写法加了同款
瞬态过滤，随后通过。

## 七、下一批候选（batch 606）

- 整条顶栏一起做：源站左头 280px 定宽列（`关闭` / `项目名称` / `画布 1` / `收起`）
  + 右头 280px 定宽列（`发布与分享` / `积分超市` / 积分数字）
- 动画时间轴开关（需把 `DirectorTimeline` 的 `timelineCollapsed` 上提到 store；
  按 batch 599 的结论属视图态，不进持久化 schema）
