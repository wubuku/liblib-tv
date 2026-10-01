# Batch 601 — 时间轴工具条左格逐项对齐（间隙 / 尺寸 / 圆角 / 配色 / 默认时间单位）

日期：2026-10-01
取证：源站导演台 CDP 实测 + 4x 截图（`/tmp/src593/probe47`、`/tmp/src601/src-toolbar-4x.png`）
验收：`scripts/verify-liblib-batch601.py`（24 项检查全过）
迁移：`scripts/verify-liblib-batch591.py`（默认时间单位 s → ms）

---

## 一、源站事实

源站时间轴 strip 的左格一共**七项**，逐项实测（x / 宽 / 与前一项的间隙 / 圆角 / 配色，
全部 24px 高、y=1027）：

| 控件 | x | 宽 | 间隙 | 圆角 | 底色 | 文字 |
|---|---|---|---|---|---|---|
| 播放 | 8 | 26 | – | `rounded-md` 6px | 透明 | `text-white/80` |
| 自动帧 | 34 | 24 | **0** | `rounded-lg` 8px | 透明 | `text-white/80` |
| 循环播放 | 58 | 26 | **0** | `rounded-md` 6px | `bg-white/10` | `text-neutral-50` |
| 播放头位置 | 88 | 46 | **4** | `8px 0 0 8px` | `bg-white/10` | 12px `#F7F7F7` |
| 总时长 | 135 | 46 | **1** | **0** | `bg-white/10` | 12px `#F7F7F7` |
| 切换时间单位 | 182 | **33** | **1** | `0 8px 8px 0` | `bg-white/10` | 12px `#F7F7F7` |
| 新建轨道 | 230 | **82** | **15** | `rounded-lg` 8px | 透明 | 13px |

**间隙不是统一的 4px**：前三项贴死（gap 0），4px 跳到读数组，组内 1px 连体，
再 15px 才到「新建轨道」。clone 原先在 header 上挂了一个统一的 `gap-1`，
导致 播放 之后每一项都逐级右偏（到 总时长 已偏 11px、单位钮偏 14px）。

读数组的 class 逐字为
`h-6 border-0 bg-white/10 px-0 text-center text-[12px] tabular-nums leading-none
text-[#F7F7F7] outline-none transition-colors placeholder:text-white/30
hover:bg-white/[0.16] focus:bg-white/[0.18] focus:ring-1 focus:ring-[#5DDCFF]/70 w-[46px]`。
clone 原先是 `bg-[#222] px-1 text-xs text-[#c8c8c8]`。

### 1.1 默认时间单位是 **ms**，不是 s

源站打开时：单位钮**文字 `ms`**、aria `切换时间单位为 s`、播放头位置读数 `0`、
总时长读数 **`10000`**（该项目时长 10s × 1000）。clone 默认 `s`，
总时长显示 `8.00`——而源站是 `10000`。这是 clone 侧无源站依据的选择，
batch 591 沿用了它，本批按实测翻转。

### 1.2 「自动帧」里是秒表图标，不是圆点

4x 截图 + DOM 实测：源站该按钮内是一个 `svg.h-3.5.w-3.5`（14px）的**秒表**图标。
clone 画的是 8px 圆点。

### 1.3 「新建轨道」：显示文字与可及名并存

源站按钮**显示文字是「新建轨道」**（13px），`aria-label` 才是那句
「选中角色、道具或分组后建立轨道」的前置条件提示。两者并存，不是二选一——
clone 原本只有 aria，视觉上没有文字。

---

## 二、clone 改动

`src/components/director/DirectorTimeline.tsx`

1. **默认时间单位** `s` → `ms`（新增 `DIRECTOR_DEFAULT_TIME_UNIT` 常量，附取值依据）
2. **header** `gap-1` → `gap-0`；读数组包进 `ml-1 flex gap-px`；新建轨道 `ml-[15px]`
3. **尺寸** 单位钮 `w-8` → `w-[33px]`；新建轨道 `w-[82px]`（原为内容自适应 77px）
4. **圆角** 播放/循环 `rounded` → `rounded-md`；自动帧 `rounded` → `rounded-lg`；
   总时长**去掉** `rounded-r-lg`（源站中框 radius 0）；单位钮 `rounded` → `rounded-r-lg`
5. **配色** 播放 `text-white/80`；自动帧 `text-white/80` + 换 `Timer` 图标（lucide）；
   循环 on → `bg-white/10 text-neutral-50`；读数与单位钮 → `bg-white/10 text-[12px]
   text-[#F7F7F7]` + `hover:bg-white/[0.16]` + focus ring
6. **新建轨道** 补上 `text-[13px]` 与居中，文字/可及名并存

---

## 三、未取证 / 不声称（记录，不臆造）

1. **自动帧的「开」态外观没量到。** 源站该钮 `aria-pressed="false"`，只能量到关态
   （透明 + `text-white/80`）；clone 的开态染色是自己的。验收脚本改为**切到关态再比对**。
2. **自动帧的默认值没改。** 源站读到 false，但那是用户自己工程的状态，不是可考的默认值
   （与 zoom 同理），且 batch 36 把它钉成 `true`。
3. **循环播放的关态外观没量到。** 源站该钮没有 `aria-pressed`，当前处于点亮态。
4. **「新建轨道」的启用条件没改。** 源站在选中**机位**（主机位）时该钮**仍是 disabled**，
   但它自己的可及名承诺「选中角色、道具或分组」、源站的引导气泡又写
   「请选择一个角色或者摄像机后，可新建轨道」——三者互相矛盾，所以 clone 的
   `character || camera` 条件原样保留，这条观察只记录不猜。

---

## 四、迁移的既有合同

`verify-liblib-batch591.py`：原先把 clone 的初始单位断言成 `s`
（`unit:initial-aria == 切换时间单位为 ms`、`unit:initial-text == "s"`、
`fields:*:unit-s`、`SOURCE_PREFIX` 里的第 6 项）。这些都不是源站事实，
按 batch 601 的实测改为 **ms 优先**：初始态断言 ms → 点一下切到 s → s 态与
编辑提交测试照旧在 s 态跑 → 再切回 ms 验证往返。切换行为、连体几何、
提交语义全部未动。38 项检查全过。

---

## 五、参考图

- `docs/design-references/liblib-timeline-toolbar-601-1920.png` — clone 改后的工具条左格
- 源站对照：`/tmp/src601/src-toolbar-4x.png`
