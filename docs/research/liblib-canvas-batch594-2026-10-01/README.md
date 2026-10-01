# Batch 594 — 时间轴右列缩放簇：自绘轨道 + 0-100 量程 + 标尺宽度公式

日期：2026-10-01
取证：源站导演台 CDP 实测（1920×1150，`/tmp/src593/probe14–19`）
验收：`scripts/verify-liblib-batch594.py`（12 项检查全过）

---

## 一、源站事实

### 1.1 缩放簇是一个 120×36 的独立块

工具条右格里，缩放与「时间线最小化」被包在同一个 120px 簇里：

```html
<div class="flex h-9 w-[120px] items-center gap-2 border-l border-white/[0.08] bg-[#212121] px-2">
  <div class="relative h-4 min-w-0 flex-1">           <!-- 71 x 16 @(1685,1031) -->
    <div class="pointer-events-none absolute inset-x-0 top-1/2 h-1 -translate-y-1/2
                overflow-hidden rounded-full bg-white/40">   <!-- 71 x 4 轨道 -->
      <div class="h-full rounded-full bg-[#F7F7F7]" style="width: 43.7751%"></div>
    </div>
    <div class="pointer-events-none absolute top-1/2 h-3 w-3 rounded-full
                border border-[#F7F7F7] bg-[#F7F7F7]"
         style="left: 43.7751%; transform: translate(-43.7751%, -50%)"></div>  <!-- 12 x 12 圆钮 -->
    <input min="0" max="100" aria-label="时间轴缩放" title="时间轴缩放" type="range"
           class="absolute inset-x-0 top-1/2 m-0 h-6 w-full -translate-y-1/2
                  cursor-pointer appearance-none bg-transparent opacity-0">  <!-- 71 x 24 -->
  </div>
  <button class="group relative flex h-6 w-6 shrink-0 items-center justify-center
                 rounded-lg text-white/65 ..." aria-label="时间线最小化">...</button>
</div>
```

要点：

- **没有放大镜图标，也没有 `<label>` 包裹**（clone 原来有 `<ZoomIn size={13}/>`）。
- `min=0 max=100`，**没有 `step` 属性**（浏览器默认步长 1）。clone 原来是
  `min=0.75 max=2.5 step=0.25`。
- 轨道 71×4 `rounded-full`，底色 `white/40`，填充段 `bg-[#F7F7F7]`。
- 圆钮 12×12 `rounded-full`，`border` + `bg` 都是 `#F7F7F7`；定位用
  `left: <pct>%` + `translate(-<pct>%, -50%)`（pct 与 left 相同，所以不是恒定
  −50%）。
- 原生 `range` 只是透明的命中层（71×24，`appearance-none`、`opacity-0`）。
- 「时间线最小化」24×24 就在簇内，不在簇外。

### 1.2 标尺宽度与 zoom 的关系（总时长 = 10000ms）

源站的标尺是 `<canvas>`（`width=4424 height=136`，2× DPR，CSS 2212×68
`@(322,1021)`，`transform: translateX(0px)`）。逐点采样（在滑杆上真实点击，
再读 canvas 的 CSS 宽度与 input 的精确值）：

| zoom | 0 | 16 | 31 | 49 | 64 | 82 | 100 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 标尺宽 | 1598 | 1598 | 1598 | 2473 | 3220 | 4116 | 5012 |

49 / 64 / 82 / 100 四点**严格共线**：

```
斜率 = (5012 - 2473) / (100 - 49) = 49.7843 px / zoom
截距 = 2473 - 49.7843 * 49        =  33.57 px
```

换算成「每秒像素」：`3.357 + 4.978 * zoom` px/s。zoom ≤ 31 时宽度等于**容器宽**
（1598），即源站把内容宽度夹在容器宽上。

---

## 二、clone 改动

### 2.1 `src/store/directorStore.ts`

| 位置 | 改前 | 改后 |
| --- | --- | --- |
| `zoom` 初值 | `1` | `44`（**推断**，见下） |
| `setTimelineZoom` 钳制 | `0.75 – 2.5` | `0 – 100` |
| 恢复工程（`restore`）里的钳制 | `0.75 – 2.5` | `0 – 100` |

### 2.2 `src/components/director/DirectorTimeline.tsx`

- 缩放改成源站的自绘簇：120×36 `flex h-9 w-[120px] gap-2 border-l
  border-white/[0.08] bg-[#212121] px-2`；71×16 容器里放 71×4 圆角轨道 +
  12×12 圆钮 + 透明原生 `range`；**删掉** `ZoomIn` 图标与 `<label>`。
- 「时间线最小化」收进簇内（原来在滑杆外面）。
- 标尺宽度公式 `max(640, duration * 80 * zoom)` → `max(640, duration * (3.36 +
  4.978 * zoom))`。
- 填充段宽度与圆钮 `left` 都按 `zoom` 百分比渲染；`zoom === 0` 时圆钮不做
  `translateX(-50%)`，避免它被轨道左边缘裁掉一半。

### 2.3 为什么初值取 44

源站被采样时 zoom = 43.7751，但那是**用户自己拖过的值**，默认值不可考（要拿到
默认值必须重置用户项目）。取 44 是为了让 clone 打开时的标尺密度与源站当前观感
一致（10s ≈ 2212px）。代码注释与 audit 的 `not_verified` 都标了这是推断。

---

## 三、迁移的合同

| 批次 | 原合同 | 原因 |
| --- | --- | --- |
| 36 | `[data-director-timeline-zoom]").fill("2.5")` 测最大缩放 | 量程改成 0–100，端点随之改成 `fill("100")` |

---

## 四、未取证 / 未验证（记录，不臆造）

- **源站的默认 zoom**。43.7751 是用户拖出来的值；clone 的 44 是推断。
- **px/s 斜率随总时长怎么变**。源站只有 10s 一个采样点；改总时长要写用户项目，
  没测。clone 按总时长线性外推。
- **源站把内容宽度夹到容器宽**，而容器宽是动态的（1920 视口下 1598 = 1920 − 320
  左列 − 2px 间隙）。clone 的 `min-w-full` 天然产生同样的下限，但 640px 那个
  兜底下限是 clone 自己的。

---

## 五、参考图

`docs/design-references/liblib-timeline-zoom-cluster-1920.png` — clone 1920×1150
下的缩放簇（verifier 产出）。
