# Batch 610 — 属性面板列宽归位 280 + 三枚 select 换源站形态 + FOV 段重建

日期：2026-10-01
取证脚本：`/tmp/src593/probe66.py`（源站右头整棵子树）、`/tmp/src593/probe68.py`（FOV 段精确计算样式）、`/tmp/src593/clone610.py`（clone 侧同一套 dump）
验收脚本：`scripts/verify-liblib-batch610.py`（97 项）
参考图：`docs/design-references/liblib-fov-section-610-1920.png`

## 靶心

接着 batch 609 的差集往下看。源站右头除了三轴行，还剩两处大块没复刻：**三条 248×28 的 select** 和 **视野角度 (FOV) 段**。两者都在 `probe66` 里采到了完整几何，都在 `DirectorInspector.tsx` 一个文件里，且都能做成端到端可验证的真交互。

## 源站实测（source fact）

**列与内容宽** — `div.flex.min-h-full.flex-col` 280 宽 @x=1640，`px-4` → 内容 248 @x=1656。

**三枚 select**（probe66 + probe67）全部 `h-7 w-full rounded-lg border-0 bg-white/10 px-2 text-[12px] text-neutral-50 outline-none placeholder:text-white/30 focus:bg-white/13 appearance-none`，248×28：

| 字段 | 选项 | 位置 |
|---|---|---|
| 切换机位 | `机位1` | [1656, 393, 248, 28] |
| 跟随目标 | `不跟随` / `角色A` | [1656, 537, 248, 28] |
| 注视目标 | `手动坐标` / `手动旋转` / `角色A` | [1656, 681, 248, 28] |

字段标签统一 `mb-1 flex h-7 items-center text-[13px] font-normal leading-none text-white/45`（28 高 + mb-1 + 28 高控件 = 组高 60）。

**FOV 段**（`section [1640,798,280,89]`，`border-b border-white/8 px-4 py-4`）：

- 标题行 `mb-3 flex items-center gap-1`（高 16）：标签 `视野角度 (FOV)` 91.7×13 `text-[13px] font-medium leading-none text-white/45` + 16×16 `?` 徽标 `h-4 w-4 rounded-full border border-white/20 text-[10px] text-white/45`，装在 `group relative` 里；
- 文案是**hover 浮层**，不是可点开的展开块：
  ```
  z-1700 pointer-events-none absolute bottom-[calc(100%+8px)] left-1/2
  w-52 -translate-x-1/2 rounded-lg bg-[#2b2b2b] px-2 py-1 text-xs
  leading-5 text-white/85 opacity-0
  shadow-[0_8px_20px_rgba(0,0,0,0.35)] transition-opacity group-hover:opacity-100
  ```
  实测 208×68 @(1655.7,738)，静置 computed `opacity: 0`；
- 控件行 `flex items-center justify-center gap-2` = **170 + 8 + 70 = 248**（正好铺满内容宽）：
  - 滑块盒 170×20：4px `bg-[#5c5c5c]` 圆角轨道 + `bg-[#09caf5]` 填充段 + 12×12 `bg-white border-[#262626]` 圆钮，外盖一层 `opacity-0` 的 `input[type=range]`；
  - 数值框 70×28 `focus-within:bg-white/13 flex h-7 min-w-px flex-1 overflow-hidden rounded-lg bg-white/10`，内含 49×28 `text-center text-[13px] tabular-nums` 输入 + 20×28 关键帧开关；
- range 属性直接读到：**`min=15 max=90 step=1 value=50`**。交叉验证：填充段实测 79.3/170 = 46.6%，而 (50−15)/(90−15) = 46.67% —— 量程与填充算法互证。

## clone 原本长什么样

- 列是 `w-72 border-l`（288），**与它自己的 280px 右头（batch 606）不一致**，也与源站的 280 不一致；那圈 1px 左边框是 clone 自造的，源站该列没有（只有 section 之间的 `border-b`）；
- 三枚 select 是 `h-8 rounded border border-white/[0.08] bg-[#222]`，标签 `mb-1.5 block text-[11px] text-[#777]`；内容宽 263，三轴格 85；
- FOV 控件是面板**顶部**一条裸 `accent-[#09caf5]` range，读数是 `FOV 43°` 文字；面板下方另有一个 `视野角度 (FOV)` 标签 + 可点开/收起的说明段落。

## 本批推翻的一处历史读数

batch 581 断言 `fov:above-name`（FOV 在名称之上），依据是历史截图。live 读数显示：源站 y=134 那个 `FOV 50°` 是 **sticky 预览缩略图里的角标**（`div.pointer-events-none.absolute.left-3.top-3`，实测 @(1669,134)），不是控件；真正的控件在 y=798，位于「名称」(321) 与「注视坐标」(721) **之后**。

同样地，batch 582 的 `help:expanded-by-default` + 点击开关也不成立——源站是 `opacity-0` + `group-hover:opacity-100` 的 hover 浮层。

按既定约定，**迁移合同而不是删掉断言**：581 的 `fov:above-name` → `fov:below-name`（并新增 `fov:label-opens-section`），`help:*` 四条 → hover 显隐 + 浮层几何，读数从 `FOV 43°` 文本迁到数值框的 value。README 与 audit 都记下了这次矛盾。

## 本批改了什么

`src/components/director/DirectorDesk.tsx`：
- 去掉自造的 1px 左边框，列宽 `w-72` → `w-[280px]`。

`src/components/director/DirectorInspector.tsx`：
- 抽出 `FieldLabel` + `FIELD_CONTROL` 两个共享件，三枚 select 换源站形态；
- 面板体内边距 `px-3` → `px-4`，内容宽落到 248；
- 删掉失效的 `CameraFovHelp`（常显段落 + 点击开关），FOV 段重建为源站排布：`视野角度 (FOV)` + 16×16 `?` 徽标（hover 出 208 宽浮层）+ `170px 自绘滑块 | 8px | 70px 数值框（49 输入 + 20 关键帧钮）`；
- 滑块的填充段与圆钮按 `(fov − 15) / 75` 驱动，range 叠层 `opacity-0` 承接拖拽；
- 数值框与滑块走同一条提交路径，双向同步，两端钳到 15–90，空草稿不提交、失焦回填；
- FOV 数值框尾部的关键帧开关复用 batch 609 的 `KeyframeToggleButton` 与播放头关键帧 id。

`src/store/directorStore.ts`：
- 新增并 export `DIRECTOR_CAMERA_FOV_MIN = 15` / `DIRECTOR_CAMERA_FOV_MAX = 90`。

## 顺带修掉的第二个既有矛盾

`updateCamera` 的守卫写的是 `fov < 20 || fov > 120`，与源站实测的 15–90 冲突。旧 UI 只有 range 滑杆、提交不了区间外的值，所以这个矛盾一直藏着；本批给了可自由输入的数值框，一钳到 15 就被 store 拒掉，输入框与 store 说法不一。已把守卫改成引用同一组常量（沿用 batch 608 把时间轴高度常量提到 store 的做法），仓库内 `fov` 取值只有 55 与 61 两个，都落在新量程内。

## 推断（inference）

- 数值框两端钳到实测的 15–90；
- 数值框的关键帧开关与三轴格一样管「这一帧」——源站每个数值框右端都挂同一枚开关，结构上就是这个意思。源站按钮**没有被点过**（点源站控件会写真实工程，需授权）。

## 不声称（not claimed）

- 那个 sticky 预览缩略图（240×135 canvas + `FOV 50°` 角标 + 右下 24×24 放大钮）clone 还没有——这正是 `FOV n°` 文案在源站的位置，留给下一批；
- 源站 FOV 控件的拖拽行为。

## 验收结果

`verify-liblib-batch610.py` **97/97 通过**，page error 0。覆盖：

- 列 280 宽 @x=1640；
- 名称 input 与三枚 select 均 248×28、0 描边、8px 圆角、`bg-white/10`（按 alpha 0.1 断言）、12px、`appearance-none`；三个标签均 28 高 13px `text-white/45`；
- 三轴格 80×28、gap 4、轴输入 59×28 且 x 恰为 1656/1740/1824、轴片 20×28；`注视坐标` 格 80 宽且**无**关键帧钮；
- FOV：标签 13px 宽 91.7、`?` 16×16、浮层 208 宽 / 静置 opacity 0 / `pointer-events:none` / z-1700 / `#2b2b2b` / 文案逐字；
- 滑块 170×20、轨道 4px `#5c5c5c`、填充 `#09caf5`、圆钮 12×12 白 + `border-[#262626]`、range 透明 `cursor-pointer` 且 15/90/1；
- 数值框 70×28、输入 49×28 居中 13px、开关 20×28；控件行 170+8+70 恰好等于 248；
- 填充与圆钮位置 = `170 × (fov−15)/75`（与源站同一算法）；
- 交互：键盘左移 9 格 → store 43→34，数值框与填充同步；输入 200 → 钳到 90 且回填；输入 2 → 钳到 15 且回填；输入 61 → 落库且填充跟随；清空草稿不提交、失焦回填；
- FOV 开关：空态点一下落一枚在播放头、aria 转 `当前帧有关键帧`、底色 `rgb(38,62,67)`；再点删净、aria 回退；
- hover 显隐浮层；对象锁定后 range / 数值框 / 开关三者同时 `disabled`。

回归：`581`（迁移后 31）、`609`（73）、`47`、`84`、`86`、`93`（含 1440 与 390 两档无横向溢出）、`90` 全绿。
门禁：`tsc` clean；`eslint src/components/director/ src/store/directorStore.ts` 0 error（1 条 warning 是他人 `DirectorCameraMotionTab.tsx` 的未用 `RefreshCw`）；`npm run build` 通过；`verify-docs` 全过。
