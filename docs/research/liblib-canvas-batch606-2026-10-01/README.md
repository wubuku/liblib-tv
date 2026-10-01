# Batch 606 — 导演台顶栏的左右两条 280px 定宽列

- 日期：2026-10-01
- 源站：<https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429>，CDP `http://127.0.0.1:9222`，视口 1920×1150 @DPR2，已选中一个机位
- 取证脚本：`/tmp/src593/probe61.py`（52px 悬浮带）、`probe62.py`（左/右头，**首次选错元素已作废**）、`probe63.py`（按类名精确定位的左右头，逐控件间隙）、`/tmp/src593/clone606.py`（clone 侧同口径）
- 验证器：`scripts/verify-liblib-batch606.py`（28 项）
- 参考图：`docs/design-references/liblib-header-606-1920.png`

## 一句话

源站导演台顶区不是一条通栏，而是「52px 悬浮带 + 左头 280px 定宽列 + 右头 280px 定宽列」三件东西；clone 此前是一条横跨全宽的三列 grid，且左右两列的内容与源站对不上。

## 一、源站实测结构

```
（1）52px 悬浮带 —— 只装 batch 605 那对视角切换
    div.pointer-events-none.absolute.inset-x-0.top-0.z-30.h-[52px]
                                              1920×52 @(0,0)

（2）左头：定宽 280px
    header.border-white/8.flex.h-[52px].items-center.border-b
                                              280×52 @(0,0)
    三个直接子节点，**间隙全为 0**（40 + 200 + 40 = 280）
      ├ button 关闭  40×40 @(0,5.5)
      │    .text-white/72.flex.size-10.shrink-0
      │     .items-center.justify-center.hover:text-white
      │    icon 16×16 @(12,17.5)
      ├ div         200×22.5 @(40,14.5)
      │    .min-w-0.flex-1.truncate.text-[14px].leading-[22px].text-white/90
      └ button 收起  40×40 @(240,5.5)   与「关闭」同类
           icon 16×16 @(252,17.5)

（3）右头：定宽 280px
    div.flex.shrink-0.items-center.justify-between.h-12.px-3
                                              280×48 @(1640,0)
    里面只有一行——选中对象名
      span.text-[15px].font-medium.text-neutral-50
                                              45×23.3 @(1652,11.9)
      （x=1652 = 1640 + 列的 12px px-3）
```

左头两枚图标按钮的**圆角是 0**（`size-10` 方块，非 `rounded-lg`），配色
`text-white/72` + `hover:text-white`，都是 clone 没有的。

## 二、clone 改动前

| | 源站 | clone（改前） |
|---|---|---|
| 顶栏高 | 52px | 48px（`h-12`） |
| 底边框 | `border-white/8` 1px | `border-white/[0.07]` |
| 左列 | **280px 定宽**，`关闭 + 标题 + 收起`，间隙 0 | 横跨全宽 1fr：返回画布(32×32) + 竖线 + 两行标题 + 收起(32×32) |
| 关闭 | 唯一一个，在**最左端**，40×40 `size-10 text-white/72` | **两个**：返回画布(32×32 `rounded #a3a3a3`) 与 关闭导演台(32×32 `rounded #8d8d8d`)，**都在调同一个 `closeWorkspace`** |
| 收起 | 40×40 `(240,5.5)`，icon 16px | 32×32 `ml-2 rounded #a3a3a3`，icon 17px |
| 右列 | 280px 定宽 `px-3`，只有选中对象名 15px | 无定宽，只有状态文案 + 导入导出项目 + 关闭导演台，**没有对象名** |

## 三、改了什么（`DirectorDesk.tsx`）

1. 顶栏 `h-12` → `h-[52px]`，底边框 `white/[0.07]` → `white/[0.08]`。
2. 左列改成 ≥900px 时的 **280px 定宽列**（窄屏仍流式，断点与 clone 既有的
   `max-[899px]` 面板折叠一致）：`关闭`(40×40) + 标题(flex-1) + `收起`(40×40)，
   两枚按钮的尺寸/配色/图标逐字照抄源站。
3. **删掉冗余的「返回画布」**：它和「关闭导演台」是同一个 `closeWorkspace`，
   源站左头只有一个关闭。`data-close-director` 移到新的「关闭」上——
   8 个依赖该属性的验证器（35/40/41/70/78/93/94/96）继续可用，行为不变。
   `title="关闭"` 也保留了（batch 586 要求）。
4. 右列改成 ≥900px 时的 **280px 定宽列 `px-3`**，并新增**选中对象名**
   （`data-director-header-object-name`，`truncate text-[15px] font-medium
   text-neutral-50`）。clone 自己的状态文案与项目导入导出保留（源站导演台
   顶栏无对应物，clone-only）。
5. **命令反馈移到中间网格轨**：左列定宽 280px 之后塞不下它
   （`max-w-[220px] ml-3 pl-3`）。它仍在 header 内，batch 83 的包含性断言不受影响。

标题槽保留 batch 587 钉住的 `h1`「3D导演台」；场景名作为 clone-only 的第二行小字
（因此标题槽实测 200×37 而源站是 200×22.5——源站是单行）。

## 四、一处不可靠读数的记录

`probe55` 那次顶区全量扫描曾读到左头里有 `项目名称`（`border-b border-dashed`
的可内联编辑 input）、`画布 1` 芯片、`工作流` / `故事板` 四个控件。这份读数
**内部自相矛盾**，本批不采信：

- 四个控件要塞进 200px 的标题槽，但扫描给的 x 是 69.5 / 164.5 / 241.1 / 273.1，
  后两个落在 `收起` 自己的 40×40 盒子里；
- 「三件东西」的读数（40 + 200 + 40 = 280、三个直接子节点、间隙全 0）
  则是自洽的，且与 batch 605 独立测到的视角对坐标（`left-1/2 top-2` → 875,8）
  相互印证。

按既定规则「历史/瞬态读数不可靠，以结构自洽的实时读数为准」，本批采用后者。
源站标题槽在另一种状态下是否真的可内联编辑，留作未取证项。

## 五、本批不声称

- 源站 `项目名称` 内联编辑 input 与 `画布 1` 芯片（读数不可靠，见上）。
- 源站非导演态顶栏的 `发布与分享` / `积分超市` / 积分数字 / `工作流` / `故事板`
  ——那些是画布级控件，导演台打开时不在这条顶区里。
- 源站视角对的点击副作用（同 batch 605）。
- 源站标题槽「正在跟随」浮层会盖住视角对时，关闭按钮的命中归属
  （batch 605 已实测源站那枚按钮点不动）。

## 六、门禁与回归

- `verify-liblib-batch606.py`：**28/28**
- 回归：605 / 604 / 603 / 587 / 586 / 83 / 50 / 117 / 35 / 70 / 78 / 93 / 94 / 96 / 40 / 41 —— 全过
  （batch 93 在 1440 与 390 两档都报 `noHorizontalOverflow: true`，
  说明新的定宽列没有破坏窄屏布局）
- `tsc --noEmit`：clean
- `eslint src/`：0 error，warning 数与基线一致
- `npm run build`：通过
- `python3 scripts/verify-docs.py`：通过

### 验证器里加的一条环境噪声过滤

`verify-liblib-batch606.py` 过滤了 `webpack-hmr` / `WebSocket` 的 console error。
原因：4317 的 dev server 是多人共用的，被别人重启时正在跑的页面会刷一串
HMR 断连错误——这是环境噪声不是应用错误。与既有的 `TransformControls`
瞬态过滤同一性质。

## 七、环境记录（值得记一笔）

本批中途 4317 的 dev server 变成不可用：先是 `/` 返回 404，再是 500
（`.next/dev/server/middleware-manifest.json` / `routes-manifest.json` 缺失）。
成因是**并发 `npm run build` 与 dev server 抢同一个 `.next`**——正是本项目
已知的运维陷阱的更重形态。修复顺序：

1. `pkill -f "next dev"` / `next-server`，等它真正退出；
2. **完整**删掉 `.next/dev`（只删目录会让仍在关停的 server 来不及重建 manifest）；
3. 重新 `npm run dev -- --port 4317`，等到 `/` 与 `/?batch70=1` 都 200。

Next 16 不允许同一目录起第二个 dev server（报 `⨯ Another next dev server is
already running`，并提示 `Run kill <pid>`），所以换端口这条路走不通。

## 八、下一批候选（batch 607）

- 动画时间轴开关：源站「动画时间轴」是 `aria-pressed=true` 的开关，clone 的
  时间轴常驻。接这个开关要把 `DirectorTimeline` 内部的 `timelineCollapsed`
  上提到 store；按 batch 599 的结论它属视图态，不进持久化 schema。
- 源站导演台顶区在**非跟随态**下右头的完整内容（本次只采到跟随态）。
