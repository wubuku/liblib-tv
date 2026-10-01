# Batch 597 — 轨道列表的选中态是**背景**（青色底），不是文字色

日期：2026-10-01
取证：源站导演台 CDP 实测（`/tmp/src593/probe10`、`probe30`、`probe31`）
验收：`scripts/verify-liblib-batch597.py`（12 项检查全过）

---

## 一、源站事实

源站的轨道列表**选中态只改背景**，文字色在选中/未选中之间**完全不变**。

### 1.1 选中态（位置轨道被选中；鼠标停在远处、悬停轨道行、点对象名——三种状态读数完全一致）

```
对象行  span[aria-hidden].absolute.inset-0   320x32 @(0,1057)
        background rgba(60, 181, 204, 0.25)      class="... bg-[rgba(60,181,204,0.25)]"
        文字色   rgb(247, 247, 247)

轨道行  background rgba(60, 181, 204, 0.1)       320x32 @(0,1089)
        文字色   rgb(168, 168, 168)
        轨道名   font-medium text-[#F7F7F7]
        值读数   text-[13px] text-[#A8A8A8]

40px 装饰加号  两笔都是 rgba(7, 184, 221, 0.4)
```

### 1.2 未选中态（在收起/展开对象行之后读到，probe4 + probe10）

```
对象行  覆盖层 background  bg-white/10
轨道行  background        bg-transparent  +  hover:bg-white/[0.04]
        文字色            rgb(168, 168, 168)      <- 与选中态相同
40px 装饰加号  两笔都是 #363636
```

### 1.3 关键点

「idle / 悬停轨道行 / 点对象名」三种交互读数**一字不差**，说明青色底是**选中态**而不是
hover 态。clone 原来用「选中时把行文字色从 `#A8A8A8` 换成 `#F7F7F7`」来表达选中，
并且对象行根本没有覆盖层——两处都与源站不符。

---

## 二、clone 改动

`src/components/director/DirectorTimeline.tsx`

1. **对象行**新增常驻覆盖层
   `span[aria-hidden].absolute.inset-x-0.inset-y-0`，颜色按
   `groupSelected ? "bg-[rgba(60,181,204,0.25)]" : "bg-white/10"` 切换；
   新增 `data-director-timeline-object-selected` 供验收定位。
   `groupSelected` = 该对象的任一轨道是 `timeline.selectedTrackId`。
2. **轨道行**选中态由「文字色」改为「背景」：
   `selected ? "bg-[rgba(60,181,204,0.1)]" : "bg-transparent"`，
   保留 `hover:bg-white/[0.04]`；行文字色固定 `text-[#A8A8A8]`；
   新增 `data-director-track-row-selected`。
3. **文字色恒定**：对象名与轨道名都固定 `font-medium text-[#F7F7F7]`。
4. **40px 装饰加号**两笔按选中态在
   `rgba(7,184,221,0.4)` 与 `#363636` 之间切换。

---

## 三、未取证 / 未验证（记录，不臆造）

- 源站只有**一条**轨道，所以「未选中态」是在收起/展开对象行之后读到的，不是点第二条
  轨道读到的。**折叠/展开是否真的取消了选中**，还是只是重渲染导致读数变化，没有分开。
- 源站多条轨道并存时，未选中行之间是否还有别的区分（除背景外）未测。

---

## 四、参考图

`docs/design-references/liblib-timeline-selection-1920.png` — clone 1920×1150 下的
轨道列表选中态（verifier 产出）。
