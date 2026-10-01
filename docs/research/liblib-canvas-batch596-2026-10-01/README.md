# Batch 596 — 「导出视频到画布」归位到时间轴右格 + 工具条两格结构

日期：2026-10-01
取证：源站导演台 CDP 实测（1920×1150，`/tmp/src593/probe14`、`probe20`）
验收：`scripts/verify-liblib-batch596.py`（10 项检查全过）

---

## 一、源站事实

### 1.1 工具条右格

```
div.absolute.right-0.top-0.z-20.flex.h-9.items-center.gap-2.bg-[#212121].pr-2
    244 x 36 @ (1676, 1021)
  |- div.flex.h-9.w-[120px]...border-l.border-white/[0.08].bg-[#212121].px-2
  |    120 x 36  缩放簇（batch 594 已对齐）
  |- button  108 x 28 @ (1804, 1025)
```

### 1.2 导出按钮是**浅色主按钮、纯文字**

```html
<button type="button" data-director-timeline-guide-target="export-to-canvas"
        data-practice-anchor="director.exportToCanvas"
        class="relative flex h-7 shrink-0 items-center gap-2 rounded-lg
               bg-[#f7f7f7] px-3 text-[12px] font-medium leading-none
               text-[#141414] transition-colors hover:bg-white
               disabled:cursor-not-allowed disabled:opacity-60">
  <span aria-hidden="true" class="pointer-events-none absolute left-8 top-1/2 size-px"
        data-director-timeline-guide-icon="true"></span>
  <span>导出视频到画布</span>
</button>
```

实测：`bg rgb(247,247,247)` / `color rgb(20,20,20)` / `border-radius 8px` /
`font-size 12px` / `font-weight 500` / **108×28**。

**里面没有任何图标** —— 那个 `absolute left-8 size-px` 的 span 是引导系统的
1px 命中标记（`aria-hidden`），不是可见图标。

### 1.3 全文档只有这一颗导出按钮，且在时间轴里

遍历整篇文档找文案为「导出视频到画布」的 `<button>`，**只命中 1 个**，位置就是
上面的 (1804,1025)。导演台**顶栏没有**导出按钮。

（clone 原来把它放在顶栏：`h-8 px-2 text-[11px] text-[#b5b5b5]` 深色幽灵按钮 +
`FileVideo2` 图标，窄屏时用 `max-[640px]:hidden` 藏掉文字。）

---

## 二、clone 改动

### 2.1 工具条改成两格（`DirectorTimeline.tsx`）

源站的 strip 是「左格 320 + 右格 1598」的 flex。clone 的工具条比源站长得多（多了
预设运镜 / 创建运动轨迹 / 曲线编辑器 / 轨道 / 关键帧 / 缩放等 clone 能力），必须
横向滚动，所以做成：

```
section (timeline)
 |- header[data-director-timeline-controls]   h-9 overflow-x-auto pr-[260px]
 |    左格：源站七项 + clone 能力，可横向滚
 +- div[data-director-timeline-strip-right]  absolute right-0 top-0 z-30
      h-9 flex items-center gap-2 bg-[#212121] pr-2
      |- 缩放簇 120x36（从 header 搬进来）
      `- {trailing}  ← 导出按钮 + 面板
```

**右格必须在 header 之外**，这是一个实测踩出来的坑：`overflow-x-auto` 按 CSS 规范
会把 `overflow-y` 从 `visible` 算成 `auto`，于是向上弹出的导出面板被裁掉。实测
裁剪后 `elementFromPoint(面板中心)` 命中的是 WebGL canvas 而不是面板。

### 2.2 导出按钮（`DirectorDesk.tsx` + `DirectorExportPanel.tsx`）

- 从顶栏搬进 `DirectorTimeline` 的 `trailing` 插槽（新增的可选 `ReactNode` prop，
  避免 `DirectorTimeline` 反向依赖 `DirectorDesk` 的导出状态）。
- 样式逐项对齐实测：`h-7 shrink-0 items-center gap-2 rounded-lg bg-[#f7f7f7] px-3
  text-[12px] font-medium leading-none text-[#141414]`，**去掉 FileVideo2 图标**，
  纯文字。随之移除 `max-[640px]:hidden`（源站窄屏也没有这个）。
- 面板定位 `absolute right-2 top-11` → `absolute bottom-full right-0 mb-1`（向上）。

---

## 三、迁移的合同

| 批次 | 原合同 | 原因 |
| --- | --- | --- |
| 40 | 移动端面板右边距 `x + width <= 378`（12px） | 触发按钮换到源站位置后，右格自带 `pr-2`（8px，源站实测），右边距变成 8px，上界改 382。下界 12px 与「不越出视口」的意图不变 |

---

## 四、未取证 / 未验证（记录，不臆造）

- **源站导出面板的几何与内容**。点那颗按钮有可能直接在用户项目上启动一次真实
  视频导出——属于对外可见 / 付费级动作，**未授权不点**。所以 clone 的面板改为
  「向上弹出」，理由是时间轴贴着视口底边、向下没有空间，这是**推断**。
- 面板本身的尺寸（286px）、字段（时长 / 画幅）是 clone 自有实现，源站未对照。

---

## 五、参考图

`docs/design-references/liblib-timeline-export-1920.png` — clone 1920×1150 下
打开导出面板的样子（verifier 产出）。
