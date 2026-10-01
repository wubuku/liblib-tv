# Batch 609 — 属性面板三轴字段行换源站形态 + 20×28 关键帧菱形开关

日期：2026-10-01
取证脚本：`/tmp/src593/probe66.py`（源站右头属性面板整棵子树）、`/tmp/src593/probe67.py`（关键帧开关与名称输入框的精确计算样式）、`/tmp/src593/clone66.py`（clone 侧同一套 dump 做对照）
验收脚本：`scripts/verify-liblib-batch609.py`（73 项）
参考图：`docs/design-references/liblib-keyframe-diamond-609-1920.png`

## 靶心是怎么定的

batch 609 起手先跑了一次**控件全集差集**（源站 113 个可访问名 vs clone 126 个），「源站有 / clone 无」共 64 项。剔除主画布页（非导演台）的控件后，导演台内最有结构价值的一簇是右头属性面板：

- `属性` / `NEW 运动轨迹` / `截图` 三枚 28 高页签 chip；
- 三条 248×28 的 `select`（切换机位 / 跟随目标 / 注视目标）；
- 每条三轴行右端挂着 **`当前帧无关键帧`** ×4 与 **`当前帧有关键帧`** ×4。

最后一项是关键：clone 的三轴行**一个都没有**，而源站是每格一枚可点开关。两态配色、aria 文案、svg 字形全部可只读测到，且点它是**真交互**——正好符合「复刻体验而非静态组件、可用 mock 数据支撑交互」这条约束。所以本批锁定「三轴字段行形态 + 关键帧开关」。

## 源站实测（source fact）

probe66 把源站右头整棵树导了出来。右列是 `div.flex.min-h-full.flex-col`，280 宽，x=1640，y=48 起。字段区由四件可复用的东西拼成：

**1. 字段组高 60** — 28 高标签盒 + `mb-1`（4）+ 28 高控件：

```
div [1656,289,248,60]
  div.mb-1.flex.h-7.items-center.text-[13px].font-normal.leading-none.text-white/45
  input.h-7.w-full.rounded-lg.border-0.bg-white/10.px-2.text-[12px].text-neutral-50
       .outline-none.placeholder:text-white/30.focus:bg-white/13        → 248×28
```

`select` 与 input 同款，只多一个 `appearance-none`（probe67 采到三条：切换机位 248×28、跟随目标、注视目标）。

**2. 三轴行** — `grid grid-cols-3 gap-1`，格宽 80（80+4+80+4+80 = 248）：

```
div [1656,465,80,28]  focus-within:bg-white/13 relative flex h-7 min-w-0
                      overflow-hidden rounded-lg bg-white/10 transition-colors
  button [1656,465,20,28]  absolute left-0 top-0 z-10 flex h-7 w-5
                           cursor-ew-resize touch-none select-none
                           rounded-l-lg border-0 bg-transparent
                           text-[12px] uppercase text-white/45
                           aria-label="左右拖动调整 X 轴"（字形 "x"）
  input [1656,465,59,28]   h-full min-w-0 flex-1 border-0 bg-transparent
                           pl-6 pr-0 text-[12px] tabular-nums text-neutral-50
                           [appearance:textfield]        ← 左对齐，不是右对齐
  button [1716,465,20,28]  见下
```

注意轴片是 `absolute` 的，x 与数值框**同起点**（都 1656）——它压在数值框左边 20px 上，数值框用 `pl-6` 让开。

**3. 关键帧开关**（probe67 精确读数）：

| | 无 | 有 |
|---|---|---|
| aria-label | `当前帧无关键帧` | `当前帧有关键帧` |
| 实测出现次数 | 4 | 4 |
| 底色 | `lab(100 … / 0.04)` = `bg-white/[0.04]` | `rgb(38,62,67)` = `#263E43` |
| 图标色 | `lab(100 … / 0.75)` = `text-white/75` | `rgb(93,220,255)` = `#5DDCFF` |
| hover | `bg-white/[0.07] hover:text-[#5DDCFF]` | — |
| 字形 `rect` | `fill=none` | `fill=currentColor` |

两态共用的 class：
`ml-px flex h-full w-[20px] shrink-0 items-center justify-center border-l border-black/20 transition-colors`；
`marginLeft: 1px`，`borderLeft: 1px lab(0 0 0 / 0.2)`。

字形是 9×9 的 svg，`viewBox="0 0 10 10"`，里面一个
`<rect x="1.95" y="1.95" width="6.1" height="6.1" rx="1" transform="rotate(45 5 5)" stroke="currentColor" stroke-width="1.2">`。

**4. 哪些行没有开关** — 源站的「注视坐标」格（实测 `[1656,753,80,28]`）**只有轴片 + 数值框**，数值框宽 80（吃满整格），右端没有关键帧尾钮。即开关只挂在对象变换的行上，不挂在相机专属的行上。

**标签色**：源站字段标签是 `text-[13px] leading-none text-white/45`；clone 原本是 `text-[11px] text-[#777]`，两者透明度差了好几档。

## clone 原本长什么样

同一套 dump 跑 clone（`/tmp/src593/clone66b.json`）：

```
label [1645,363,83.7,32]  flex h-8 … rounded border border-white/[0.08] bg-[#222]
  button [1652,365,24,28]  h-7 w-6（流内）  text-[10px] uppercase text-[#8c8c8c]
  span  …                  size-1.5 rotate-45 rounded-[1px] bg-[#09caf5]   ← 只读 6px 菱形
  input [1680,370.8,41.7,16.5]  text-right text-[11px]                    ← 右对齐
```

`grid-cols-3 gap-1.5`、格子 32 高带 1px 描边、名称框 `h-8 rounded border bg-[#222]`、标签 11px 灰字。

## 本批改了什么

全部落在 `src/components/director/DirectorInspector.tsx`：

1. **`AxisFields` 换源站形态** — 格子 `h-7` / 无描边 / `bg-white/10` / `focus-within:bg-white/13`；`grid-cols-3 gap-1`；轴片改 `absolute left-0 top-0 z-10 w-5`（20 宽）`rounded-l-lg` `text-[12px] text-white/45`；数值框改 `h-full pl-6 pr-0 text-[12px]` **左对齐**并用 `appearance-none` + webkit 伪元素藏掉步进箭头；字段标签改 `mb-1 flex h-7 items-center text-[13px] leading-none text-white/45`。
2. **新增 `KeyframeToggleButton`** — 20×28，两态 class 逐字照抄，9×9 svg + 旋转 45° 的 `rect`，`aria-label` 两态互斥。挂在 位置 / 旋转 / 缩放 三行共 9 枚；`target` / `followOffset` 这类不属于对象变换的行**不挂**（对应源站注视坐标格没有尾钮）。
3. **接上真交互** — 新增 `keyframeAtPlayheadId` memo 取出播放头处那一枚关键帧的 id，`toggleKeyframeAtPlayhead` 做「有则删、无则按当前变换补一枚」。补帧走 `recordObjectKeyframe(id, true)`，`force=true` 让这个全局开关管不住用户显式的一击。
4. **对象「名称」输入框换源站形态** — `h-7 rounded-lg border-0 bg-white/10 px-2 text-[12px] text-neutral-50 focus:bg-white/13`，标签同步换成 28 高 13px `text-white/45`。
5. **保住 batch 575 的选择器合同** — `data-director-keyframed-axis` / `-axis-index` 从原来那个 6px 只读菱形迁到「有」态的开关按钮上，batch575.py 的定位器一字未改。

## 顺带修掉的一个既有 bug

`keyframedAxes` 原来只读 `keyframe.value.transform`——那是**相机轨道**的形态。角色 / 道具走的是 `transform` 轨道，`keyframe.value` 本身就是 `DirectorTransform`，取 `.transform` 得到 `undefined`，判定恒为 false。也就是说**角色的关键帧菱形从来没亮过**。batch 575 只测了相机（`addDirectorCamera()` 之后），把这个洞盖住了；本批把开关做成可点的之后，它立刻暴露。

修法是两种形态都认：`const values = (raw?.transform ?? raw)`。

## 推断（inference）

- **「点开关 = 打/删关键帧」是推断。** 源站那枚按钮**没有被点过**——点源站控件会写进用户真实工程，需要授权。依据是 `当前帧无关键帧` / `当前帧有关键帧` 这对互斥 aria 出现在一个 `<button>` 上，且两态配色分明。clone 侧的打/删行为本身在本批验收里端到端验证了。
- **on/off 的粒度是「字段」而不是「轴」。** clone 的轨道关键帧存的是整份 `DirectorTransform`，做不到轴级关键帧（那要改持久化 schema，超出本批范围）。所以一枚关键帧会把 位置/旋转/缩放 三行一起点亮，九枚开关里任意一枚删的都是同一枚关键帧。验收脚本把这个诚实行为**断言下来**而不是绕开。

## 不声称（not claimed）

- 源站关键帧开关的点击行为；
- 源站右列 280px 宽度、页签栏三枚 chip（含 `运动轨迹` 上的 `NEW` 角标 `#5DDCFF` / `rounded-t-lg rounded-bl-sm rounded-br-lg -translate-y-[70%]`）、sticky 预览画布（240×135 + `FOV 50°` 角标 + 右下 24×24 放大钮）、三条 248×28 `select`——**都已实测**，留给下一批，因为改这些会牵动大量既有 verifier 的几何断言；
- 源站「截图」按钮在属性面板里的行为。

## 验收结果

`verify-liblib-batch609.py` **73/73 通过**，page error 0。覆盖：

- 格子 28 高 / 8px 圆角 / 0 描边 / `bg-white/10`（按 alpha 0.1 断言，不比序列化字符串）；
- `gap` 4px、三格等宽同 y、组高 60、标签 28 高 13px 400 `text-white/45`；
- 轴片 `absolute` / 20×28 / `ew-resize` / 12px / 与格子同起点 / `text-white/45`；
- 数值框 28 高 12px `padding-left: 24px` 左对齐；
- 开关 20×28、`当前帧无关键帧`、`bg-white/[0.04]`、`text-white/75`、`border-left: 1px black/20`、`margin-left: 1px`、字形 `viewBox 0 0 10 10` / 9×9 / `fill=none` / `stroke-width 1.2` / `stroke=currentColor`；
- 9 枚开关（3 行 × 3 轴），且 `target` / `followOffset` 行不挂；
- 端到端：点 off → 轨道多一枚、落在播放头时间、三行转 on、底色 `rgb(38,62,67)`、图标 `rgb(93,220,255)`、`fill=currentColor`、batch 575 合同仍在（3 枚）；再点 → 关键帧归零、aria 与底色回退、合同清空；跨行点任意一枚删的都是同一枚；播放头移走全 off、移回全 on；对象锁定后 9 枚全 `disabled`。

读数前脚本会先把指针挪到 (5,5)——off 态有 `hover:bg-white/[0.07]`，Playwright 点完会把光标留在按钮上，不挪开会读成 hover 值。

回归：`575`（4）、`583`（24）、`47`、`86`、`84` 全绿；`35/36/37/43/49` 亦绿。门禁 `tsc` clean、`eslint src/` 0 error、`npm run build` 通过、`verify-docs` 全过。
