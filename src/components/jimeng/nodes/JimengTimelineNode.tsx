"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Magnet,
  Maximize2,
  Plus,
  Redo2,
  Scissors,
  Trash2,
  Undo2,
  Upload,
  Volume2,
  VolumeX,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import { useTakeFocusAtOpen } from "@/components/jimeng/jimengMenuChrome";
import type { JimengTimelineNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK, mockMsg } from "@/components/jimeng/jimengFeedback";

/**
 * 时间线节点 (Batch 805 SOURCE_FACT @1680×826，登录态)。
 *
 * 这是**左栏「时间线」按钮点下去之后出现的东西** —— 源站实测落点是
 * `data-testid="rf__node-*" role="group"`，位于 `.react-flow__viewport` 内，
 * 顶栏节点计数同步 +1。此前复刻把它当"打开浮层"理解，所以按钮点了没反应。
 *
 * 结构 (源站截图逐层量得)：
 *   顶行  导入 · 删除 | 播放 ▶ · "00:00 / 00:00" | 下载 · 全屏编辑
 *   刻度  00:00 → 00:30，每 5s 一个主刻度
 *   轨道  「+ 添加素材到时间线」虚线占位
 *   左侧槽 静音钮
 *
 * 真交互（不是静态图）：
 *   「添加素材到时间线」往轨道塞一个片段，标题栏的 时长/片段数 随之变化；
 *   删除钮移除当前节点；导入/下载/全屏编辑沿用既有 mock 语义。
 */
/** Batch 813 SOURCE_FACT：点「导出时间线」弹出的菜单，逐字取自源站 */
const EXPORT_ITEMS = {
  mp4: { label: "导出为 MP4", blocked: "当前时间线暂不支持此操作" },
  xml: { label: "导出为 XML", hint: "批量导出时间线素材 · 请选择至少一个组、文本、图片或视频项" },
} as const;
/** SOURCE_FACT: 源站原文「导出到剪映」无空格、「导出到 DaVinci Resolve」有空格 ——
 *  CJK 名与拉丁名在源站就是不同排法，所以显示名逐条写死，不靠拼接。 */
const EXPORT_TARGETS = [
  { name: "剪映", label: "导出到剪映" },
  { name: "DaVinci Resolve", label: "导出到 DaVinci Resolve" },
  { name: "Premiere", label: "导出到 Premiere" },
  { name: "Final Cut Pro", label: "导出到 Final Cut Pro" },
] as const;

/** Batch 813 SOURCE_FACT：点「全屏编辑」打开的编辑器，逐字取自源站 */
const FS_SOURCES = ["已导入资产", "画布资产", "全部"] as const;
const FS_KINDS = ["图片", "视频", "音频"] as const;
const FS_SUBTITLE = "Edit the main visual track and multiple audio tracks";

const TOTAL_SECONDS = 30;
const TICK_STEP = 5;
/**
 * Batch 819 SOURCE_FACT：刻度尺的**世界坐标步长** = 32.1 px/s
 * （源站实测 00:00→00:30 跨 963px，100% 缩放，三次加载一致）。
 *
 * 它是**本表面专属**的常量，不是全局值：源站全屏编辑器的同一套刻度是
 * 9px 字号 / 21.4px·s⁻¹，比值 1.5 恰为字号比 13.5/9 —— 源站按刻度标签
 * 字号定间距。改字号时这个数也要跟着走，别当成绝对物理量。
 *
 * 轨道宽 1126px ÷ 32.1 = **35.1s 可见窗口**，而标签只画到 30s，
 * 右侧留白约 163px。复刻此前用百分比把 30s 拉满全宽，窗口会随
 * 面板宽度浮动 —— 与源站模型相反。
 */
const RULER_PX_PER_SEC = 32.1;

/**
 * Batch 821 SOURCE_FACT：全屏编辑器底栏那一套刻度**是另一组定值** ——
 * 9px 字号 / **21.4px·s⁻¹**（819 §29.2 双表面实测），且跨度到 **01:10**
 * （14 格 5s），不是内嵌节点的 13.5px / 32.1 / 30s。
 * 同一模型两个表面各自的定值，**别混用**。
 */
const FS_RULER_PX_PER_SEC = 21.4;
const FS_TICK_STEP = 5;
const FS_RULER_SECONDS = 70;

/** Batch 821 SOURCE_FACT：底栏「Timeline editing tools」六枚，实名逐字取自源站。 */
const FS_EDIT_TOOLS = [
  { label: "撤销", icon: Undo2, kind: "undo" },
  { label: "重做", icon: Redo2, kind: "redo" },
  { label: "分割", icon: Scissors, kind: "split" },
  { label: "向左剪裁", icon: ChevronLeft, kind: "trimStart" },
  { label: "向右剪裁", icon: ChevronRight, kind: "trimEnd" },
  { label: "删除", icon: Trash2, kind: "delete" },
] as const;

/** 片段 id 序号。
 *
 *  ⚠️ 这里**不能**用 `Date.now()`。`addClip` / `fsSplit` 是组件体内定义的函数，
 *  而 React Compiler 的 `react-hooks/purity` 规则把组件体内出现的 impure 调用
 *  一律判成「渲染期调用」并报错 —— `Cannot call impure function during render`。
 *  讽刺的是这个报错**在 825 之前就存在**：批 805 写的 `addClip` 里早就有
 *  `Date.now()`，也就是说 `npm run check` 一直退出 1，而我却在 §31–§34 里
 *  写了四次「`npm run check` EXIT=0」—— 那是 `… | tail -4; echo $?` 读到
 *  **`tail` 的退出码**造成的假绿。教训：**别用管道的 `$?` 汇报门禁结果**。
 *
 *  模块级计数器在渲染之外，天然合法；片段 id 本来也只需要**进程内唯一**。 */
let clipSeq = 0;
const nextClipId = (prefix: string) => `${prefix}-${(clipSeq += 1)}`;

function fmt(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export function JimengTimelineNode({ id, data, selected }: NodeProps) {
  const d = data as JimengTimelineNodeData;
  /* 片段的增/删/分割/剪裁一律走**可撤销**通道：撤销按钮与 store 的历史栈
     必须对得上，否则在全屏编辑器里点「撤销」撤掉的是很久之前的别的动作。 */
  const updateClips = useJimengStore((s) => s.updateNodeDataUndoable);
  /* Batch 827：资产栏要列出画布上的媒体节点，所以得订阅 nodes。
     ⚠️ 这会让**画布上任何节点的增删改**都重渲染本节点。React Flow 的节点数
        是个位数（默认 4），重渲染成本可忽略；若将来上百再考虑按 kind 订阅。 */
  const nodes = useJimengStore((s) => s.nodes);
  const addLocalImage = useJimengStore((s) => s.addLocalImage);
  const addLocalUpload = useJimengStore((s) => s.addLocalUpload);
  const pushToast = useJimengStore((s) => s.pushToast);
  const removeNode = useJimengStore((s) => s.removeNode);
  /* Batch 825：撤销/重做直接用 store 里**真**的 undo/redo（批 336 建的节点级
     历史栈），与画布右键菜单里那两枚走的是同一条路径 —— 同一动作两条入口，
     行为必须一致，所以这里不另做一套。禁用态也跟着右键菜单的做法，
     由 `past`/`future` 是否为空决定。 */
  const undo = useJimengStore((s) => s.undo);
  const redo = useJimengStore((s) => s.redo);
  const canUndo = useJimengStore((s) => s.past.length > 0);
  const canRedo = useJimengStore((s) => s.future.length > 0);
  const clips = d.clips ?? [];
  // Batch 813 SOURCE_FACT（源站逐个按钮实测）：
  //   导出时间线 42×42 → 弹导出菜单（MP4/XML + 导出到剪映/DaVinci/Premiere/Final Cut）
  //   全屏编辑   126×42 → 打开全屏时间线编辑器
  //   静音       42×42  data-testid="timeline-mute-button"
  // 这三个此前全是死按钮：只画了图标没挂行为。
  const [muted, setMuted] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const fsLayerRef = useRef<HTMLDivElement>(null);

  /* 批 868：全屏时间线编辑器**开层即接管焦点**。
     审计 868 抓到实锤（修之前）：这一层 `modalish=True`
     （`fixed inset-0` + `background: rgb(20,20,22)`，**铺满视口且不透明**
     ⇒ 865 那条源站无关判据认定的**真模态**），可开层时焦点**留在触发器上**
     （`timeline-fullscreen-trigger` / aria「全屏编辑」），而那个触发器此刻
     已经被这一层**自己盖住**（4/4 边）；接着按 Tab 会走过 **26 个全部被盖住**
     的焦点位（`covered_n=26`，顶到 `top_anchor=tid:timeline-fullscreen`）——
     焦点环一路落在看不见的地方，键盘用户在这一屏里直接失明。
     与 863 的全屏预览同一类，本层**已经困 Tab**（`trapped=True`），缺的正是
     「把焦点先放进来」。依据是模态自身的定义，**不声称**源站也这样
     （源站时间线全屏的键盘行为未取样）。 */
  useTakeFocusAtOpen(fsLayerRef, fullscreen);
  // Batch 821：「关闭自动吸附」是源站底栏播放控件里的一个真实开关
  const [fsSnap, setFsSnap] = useState(true);
  // Batch 821：源站底栏播放控件是「关闭自动吸附 / 缩小视图 / Timeline zoom
  // span / 放大视图」四件，那枚 span 宽 **92**（由该组总宽 188 倒推：
  // 188 − 3×28 − 3×4 = 92）。span 的**文案源站没取到**，但左右各一枚
  // 减/加夹着它、自身又叫 "Timeline zoom" —— 按缩放读数实现最自洽，
  // 且让两枚按钮不再是死按钮。记为 OPEN_QUESTION 821-a。
  const [fsZoom, setFsZoom] = useState(1);
  /* Batch 825 SOURCE_FACT 缺口（全屏编辑器的轨道此前只画了刻度 + 投放区，
     **一个片段都没渲染**，所以「分割/剪裁/删除」这三枚工具即便接上动作也
     无从下手 —— 用户看不见自己在动什么）。本批补三件事，让它们成一套：
       ① 播放头可定位   fsTime 秒；点刻度尺 / 点片段都能挪
       ② 轨道渲染片段   与内嵌轨道同一套世界坐标映射（819 的教训）
       ③ 六枚工具真能用 作用于**播放头所在的那一片段**
     ⚠️ 片段在全屏轨道里的几何**不是源站实测值** —— 源站那个 fixture 的媒体
        全没加载（台账 §31 记过），轨道上根本没有片段可量。本批只把
        「按同一映射渲染」这件事做对，不把任何读数写成 SOURCE_FACT。 */
  const [fsTime, setFsTime] = useState(0);
  // 播放头定位要拿轨道盒做坐标换算，刻度尺/片段/播放头三处共用它
  const fsTrackRef = useRef<HTMLDivElement>(null);

  // Batch 821 SOURCE_FACT：源站全屏编辑器**按 Escape 能关**（2026-10-04
  // 实测：Escape 后 `[data-testid="timeline-fullscreen-editor"]` 从 DOM 消失）。
  // 复刻此前只能点右上角那枚 ✕ —— 源站有的关闭方式少一个，是功能缺口。
  // 捕获阶段：与批 794 起的既有写法一致（冒泡监听会被工作区先触发的
  // 同步重渲染跳过）。
  useEffect(() => {
    if (!fullscreen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setFullscreen(false);
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [fullscreen]);
  const [fsSource, setFsSource] = useState<(typeof FS_SOURCES)[number]>("已导入资产");
  const [fsKind, setFsKind] = useState<(typeof FS_KINDS)[number]>("图片");
  // Batch 832：拖放高亮态 + 真 file input。拖放与「导入」按钮共用 `ingestFiles`，
  // 所以两条入口不可能行为分叉（这正是本批要防的那类退化）。
  const [fsDragOver, setFsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // 注意别写成 Math.max(..., 1)：空轨道时那个下限 1 会漏进显示值，
  // 空态就成了 "00:00 / 00:01" 而不是源站的 "00:00 / 00:00"。
  const ends = clips.map((c) => c.start + c.length);
  const span = ends.length ? Math.max(d.duration ?? 0, ...ends) : (d.duration ?? 0);

  const addClip = (label?: string) => {
    /* ⚠️ 类型闸门：827 给 `addClip` 加了可选参数 `label`，而它有三处
       `onClick={addClip}` 的用法 —— 那样会把 **MouseEvent 当成 label** 传进来，
       于是片段名变成 "[object Object]"。调用点已全部改成 `onClick={() => addClip()}`，
       这里再加一道闸：**label 只接受字符串**。改签名时最容易漏的就是这种
       「函数被直接当事件处理器」的地方，用类型把它变成不可能。 */
    const name = typeof label === "string" && label.length > 0 ? label : undefined;
    const clip = {
      id: nextClipId("clip"),
      label: name ?? `片段 ${clips.length + 1}`,
      start: clips.length ? Math.min(30, clips[clips.length - 1].start + clips[clips.length - 1].length) : 0,
      length: 5,
    };
    updateClips(id, { clips: [...clips, clip], duration: clip.start + clip.length });
    pushToast(FEEDBACK.addTimelineClip(clip.label));
  };

  /* ── Batch 832：投放区接上**真拖放**，「导入」按钮接上**真 file input** ──
     此前这一栏的提示写着「将文件拖至此处添加」，而整个组件里**没有**
     `onDrop` / `onDragOver` / `createObjectURL` / `input[type=file]` ——
     用户真把文件拖进来，什么也不会发生。**一句会骗人的可见交互比没有它更糟。**

     两条入口（拖放 / 按钮）**共用这一个 `ingestFiles`**，所以它们不可能行为分叉。

     落点：排在画布上所有媒体节点的右侧，逐个右移 569+40，纵向排 320+40 ——
     与源站「本地上传落在源节点右侧」的既有规律一致（批 62/73）。

     ⚠️ 图片走 `FileReader` 读成 data URL 交给 store 的 `addLocalImage` ——
     图片节点渲染的是真 `<img src={d.poster}>`，所以画布上会出现**真的那张图**，
     不是占位。视频/音频走批 73 早就建好的 `addLocalUpload`（标题=文件名 +
     mock 海报）—— 本批**不自己造第二套上传逻辑**。 */
  const ingestFiles = (files: File[]) => {
    const accepted = files.filter((f) =>
      f.type.startsWith("image/") || f.type.startsWith("video/") ||
      f.type.startsWith("audio/"));
    if (accepted.length === 0) {
      pushToast(FEEDBACK.assetsImportSkipped(files.length));
      return;
    }
    // 落点：排在画布上已有媒体节点的右侧，一行放 3 个，满了换行
    const mediaNodes = nodes.filter(
      (n) => n.type === "image" || n.type === "video" || n.type === "audio");
    const rightMost = mediaNodes.reduce((m, n) => Math.max(m, n.position.x), -609);
    const topMost = mediaNodes.length ? Math.min(...mediaNodes.map((n) => n.position.y)) : 0;
    let x = rightMost + 649;
    let y = topMost;
    for (const f of accepted) {
      const pos = { x, y };
      if (f.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = () => {
          if (typeof reader.result === "string") {
            addLocalImage(f.name, reader.result as string, pos);
          }
        };
        reader.readAsDataURL(f);
      } else {
        // 视频/音频：复用批 73 的真上传路径（标题=文件名）
        addLocalUpload(f.name, pos);
      }
      x += 649;
      if (x > rightMost + 649 * 3) {
        x = rightMost + 649;
        y += 360;
      }
    }
    pushToast(FEEDBACK.assetsImported(accepted.length));
  };

  /* ── Batch 833：「导出时间线」从 toast 桩接成**真下载** ─────────────────
     此前点它只弹一句「导出时间线」—— 一个字都没产出。

     ⚠️ **格式与源站不同，说清楚**：源站导出的是**渲染好的视频**；复刻没有渲染器
     （本仓的时间线是数据，不是帧序列），所以导出的是**结构化 JSON**：节点名、
     时长、每个片段的 label/start/length。这是能力边界的诚实表达，不是偷懒 ——
     而 toast 里也把这句写给用户了，免得他以为拿到了视频。

     为什么用 Blob + `<a download>` 而不是 data URI：data URI 会把整个 JSON 内联进
     URL，对大文件不合适，且部分浏览器对超长 data URI 的下载名处理不稳。
     ⚠️ `URL.revokeObjectURL` 必须放在 `a.click()` **之后**（同步 revoke 会让
     还没开始的下载拿不到 blob）—— 放在 setTimeout 里。 */
  const exportTimelineJson = () => {
    const payload = {
      节点: d.title ?? "时间线",
      时长秒: span,
      导出时刻: new Date().toISOString(),
      片段: clips.map((c) => ({ 名称: c.label, 起点秒: c.start, 时长秒: c.length })),
      说明: "复刻导出的结构化时间线；源站此处导出的是渲染后的视频。",
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `时间线-${(d.title ?? "timeline").replace(/[\\/:*?"<>|]/g, "_")}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
    pushToast(FEEDBACK.exportTimeline(clips.length, a.download));
  };

  /* ── Batch 827：把资产栏从「装饰」接成真浏览器 ─────────────────────────
     此前这一栏是纯装饰：三个来源页签与三个类型页签点了只切一个 class，
     而那个「资产」框里显示的其实是**时间线的片段列表**
     （`clips.map(c => c.label).join(" / ")`）—— 名不副实。

     本批让它成为一个真浏览器：列出画布上的媒体节点，点一下就加进轨道。
     ⚠️ 三个来源页签的**内容语义没有源站依据**（源站那个 fixture 的媒体全没
        加载，没量到过），所以下面是**复刻自有的语义决策**，不写成 SOURCE_FACT：
          画布资产   = 画布上的全部媒体节点
          已导入资产 = 其中**还没被加进这条时间线**的那些
          全部       = 画布资产 ∪ 已导入资产（即全部媒体节点）
        三个页签因此各有可分辨的含义，而不是三个同义按钮。 */
  const onTimeline = new Set(clips.map((c) => c.label));
  const fsAssets = nodes
    .filter((n) => n.type === "image" || n.type === "video" || n.type === "audio")
    .map((n) => ({
      id: n.id,
      kind: n.type as "image" | "video" | "audio",
      title: (n.data as { title?: string }).title ?? "未命名",
    }));
  const KIND_BY_LABEL: Record<(typeof FS_KINDS)[number], "image" | "video" | "audio"> = {
    图片: "image",
    视频: "video",
    音频: "audio",
  };
  const fsVisible = fsAssets.filter((a) => {
    if (a.kind !== KIND_BY_LABEL[fsKind]) return false;
    if (fsSource === "已导入资产") return !onTimeline.has(a.title);
    return true;
  });

  const runFsTool = (kind: (typeof FS_EDIT_TOOLS)[number]["kind"]) => {
    if (kind === "undo") {
      undo();
      return;
    }
    if (kind === "redo") {
      redo();
      return;
    }
    if (kind === "split") {
      fsSplit();
      return;
    }
    if (kind === "trimStart") {
      fsTrimStart();
      return;
    }
    if (kind === "trimEnd") {
      fsTrimEnd();
      return;
    }
    fsDeleteAtPlayhead();
  };

  /* 播放头定位：刻度尺/轨道上点一下就跳到那一点。坐标换算与渲染**同一套**
     映射（`52 + t × px/s × zoom`）—— 819 换掉百分比模型之后，刻度、片段、
     播放头三者的横坐标必须由同一个式子算出来，否则缩放一按就各走各的。 */
  const seekFromClientX = (clientX: number) => {
    const el = fsTrackRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = FS_RULER_PX_PER_SEC * fsZoom;
    setFsTime(Math.max(0, Math.min(span, (clientX - rect.left - 52) / px)));
  };

  const removeClip = (clipId: string) => {
    const rest = clips.filter((c) => c.id !== clipId);
    updateClips(id, {
      clips: rest,
      duration: rest.length ? rest[rest.length - 1].start + rest[rest.length - 1].length : 0,
    });
  };

  /* ── Batch 825：全屏编辑器的剪辑动作 ──────────────────────────────────
     这四枚（分割 / 向左剪裁 / 向右剪裁 / 删除）此前是纯 toast 桩。
     它们要能真干活，前提是用户**看得见自己在动什么**，所以配套做了两件事：
     ① 轨道按同一套世界坐标映射渲染片段（与内嵌轨道一致，819 的教训）
     ② 播放头可定位（点刻度尺 / 点片段），四枚动作都作用于**播放头所在片段**

     片段总长取**所有片段末端的最大值**，不是「最后一个片段的末端」——
     分割与剪裁会改变片段顺序/长度，「最后一个」这个假设从 825 起不再成立。 */
  const spanOf = (list: typeof clips) =>
    list.length ? Math.max(...list.map((c) => c.start + c.length)) : 0;

  const commitClips = (next: typeof clips) =>
    updateClips(id, { clips: next, duration: spanOf(next) });

  // 播放头所在片段：左闭右开。播放头正好落在某片段**末端**时算「下一片」——
  // 与剪辑软件的直觉一致（末端就是下一段的起点）。
  const clipAtPlayhead = clips.find(
    (c) => fsTime >= c.start && fsTime < c.start + c.length,
  );
  const stamp = (t: number) =>
    `00:00:${String(Math.max(0, Math.floor(t))).padStart(2, "0")}`;

  const fsSplit = () => {
    const c = clipAtPlayhead;
    if (!c || fsTime <= c.start || fsTime >= c.start + c.length) {
      pushToast(FEEDBACK.needClipAtPlayhead("分割"));
      return;
    }
    const head: (typeof clips)[number] = { ...c, length: fsTime - c.start };
    const tail: (typeof clips)[number] = {
      ...c,
      id: nextClipId(`${c.id}-b`),
      start: fsTime,
      length: c.start + c.length - fsTime,
    };
    commitClips(
      [...clips.filter((x) => x.id !== c.id), head, tail].sort((a, b) => a.start - b.start),
    );
    pushToast(FEEDBACK.splitTimelineClip(c.label, stamp(fsTime)));
  };

  const fsTrimStart = () => {
    const c = clipAtPlayhead;
    if (!c || fsTime <= c.start) {
      pushToast(FEEDBACK.needClipAtPlayhead("向左剪裁"));
      return;
    }
    commitClips(clips.map((x) => (x.id === c.id ? { ...x, start: fsTime } : x)));
    pushToast(FEEDBACK.trimTimelineClipStart(c.label, stamp(fsTime)));
  };

  const fsTrimEnd = () => {
    const c = clipAtPlayhead;
    if (!c || fsTime >= c.start + c.length) {
      pushToast(FEEDBACK.needClipAtPlayhead("向右剪裁"));
      return;
    }
    commitClips(clips.map((x) => (x.id === c.id ? { ...x, length: fsTime - x.start } : x)));
    pushToast(FEEDBACK.trimTimelineClipEnd(c.label, stamp(fsTime)));
  };

  const fsDeleteAtPlayhead = () => {
    const c = clipAtPlayhead;
    if (!c) {
      pushToast(FEEDBACK.needClipAtPlayhead("删除"));
      return;
    }
    commitClips(clips.filter((x) => x.id !== c.id));
    setFsTime(0);
    pushToast(FEEDBACK.removeTimelineClip(c.label));
  };

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-testid="timeline-node"
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start text-left">
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      {/* Batch 818 SOURCE_FACT：源站这个节点带一段**英文**节点描述
          （1×1 隐藏 span，屏读专用），逐字取自源站：
            `时间线: 1 visual track, 0 audio tracks, 0 clips. Not selected.`
          复刻此前完全没有 —— 屏幕阅读器用户只会听到一个无名 group。
          片段数按当前 clips 实时算，选中态尾句跟着 `selected` 走。 */}
      <span
        className="pointer-events-none absolute left-0 top-0 h-px w-px overflow-hidden"
        style={{ clipPath: "inset(50%)" }}
      >
        {`时间线: 1 visual track, 0 audio tracks, ${clips.length} clips.${
          selected ? " Selected." : " Not selected."
        }`}
      </span>

      <div
        /* Batch 818 SOURCE_FACT（源站 100% 缩放，三次全新加载逐项一致）：
           壳 1200×207 / r8 / 底色 `color(srgb 0.12549 ×3)` = **rgb(32,32,32)**。
           复刻此前是 rgb(24,24,26) —— 差 (+8,+8,+6)，肉眼可见地比源站更黑。

           Batch 829 SOURCE_FACT：壳**带 1px 边框**，实测
           `border: 1px solid rgba(255,255,255,0.04)`，padding/margin 全 0。
           别处一行都查不到这 1px（槽、轨道行、视口、canvas 的 border/padding
           都是 0），只有壳有 —— 也就是**内容整体内缩 1px**。
           它一个根因解释掉五处偏差：

               工具条   源站 [1,1,1198,66]  复刻(无边框) [0,0,1200,66]
               轨道行   源站 [1,67,1198,139] 复刻(无边框) [0,66,1200,141]
               左槽     源站 [1,67,66,139]   复刻(无边框) [0,66,66,141]
               静音钮   源站 [13,121,42,42]  复刻(无边框) [12,120,42,42]
               滚动容器 源站 [67,67,1132,139] 复刻(无边框) [67,66,1133,141]

           宽度 1200→1198 是左右各让 1px；轨道行 141→139 是上下各让 1px。 */
        className="relative flex h-full w-full flex-col overflow-hidden rounded-lg border border-white/[0.04]"
        style={{
          background: "rgb(32,32,32)",
          boxShadow: nodeRingShadow(selected === true),
        }}
        data-testid="timeline-shell"
      >
        {/* 顶行：导入/删除 · 播放/时间码 · 下载/全屏编辑
            Batch 818 SOURCE_FACT：本行高 **66px**（源站 rel [1,1,1198,66]），
            控件间隙 **6px**（源站由右簇两枚反推：导出右缘 1055、全屏编辑左缘 1061，
             间隔 6；左簇那两枚也是 6 —— [13,13,42,42] 与 [61,13,42,42]）。

            ⚠️ 批 829 订正：818 当年写的左右内边距是 **13px**，那是**反推错了**。
            反推的前提是「工具条铺满 0..1200」，而源站壳有 1px 边框（批 829 实测
            `border: 1px solid rgba(255,255,255,0.04)`），内容盒其实是 1..1199。
            同样的按钮矩形在正确的盒子里对应的是 **12px**：
              全屏编辑右缘 1199 − 12 = **1187** = 源站 [1061,13,126,42] 的右缘
              左簇首枚左缘   1 + 12 = **13**  = 源站 [13,13,42,42] 的左缘
            两边独立验算都是 12，所以是 12，13 是那多出来的 1px。 */}
        <div
          className="flex h-[66px] shrink-0 items-center gap-[6px] px-[12px]"
          data-testid="timeline-toolbar"
        >
          <button
            type="button"
            aria-label="导入"
            onClick={() => addClip()}
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Upload size={16} />
          </button>
          <button
            type="button"
            aria-label="删除时间线"
            onClick={() => removeNode(id)}
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Trash2 size={16} />
          </button>

          {/* Batch 818 SOURCE_FACT：源站这一段是 `timeline-playback-clock`
              [566,22,123,24]，**18px**、由 `00:00` / `/` / `00:00` 三段组成，
              旁边**没有播放图标**（源站工具条左端那两枚是无 aria 的裸 div，
              见台账 §27.5）。复刻此前是 13px 且带一枚装饰性 <Play> ——
              那个图标既无 aria 也无 onClick，纯装饰且源站无对照物，删掉。 */}
          <div className="flex flex-1 items-center justify-center text-white/80">
            <span
              className="text-[18px]/[24px] tabular-nums"
              data-testid="timeline-time"
            >
              {fmt(0)} / {fmt(span)}
            </span>
          </div>

          {/* 源站这一枚的 aria 是「导出时间线」不是「下载」。
              Batch 818 SOURCE_FACT：源站 **42×42 / r8**（rounded-lg = 8px）。
              `verify-jimeng-batch813.py` 的文档头早就把 42×42 记成 SOURCE_FACT，
              而实现一直是 size-8(32) —— **实现与自己的取证文档矛盾**，本批修掉。 */}
          <button
            type="button"
            aria-label="导出时间线"
            data-testid="timeline-export-trigger"
            onClick={() => setExportOpen((v) => !v)}
            className="flex size-[42px] items-center justify-center rounded-lg text-white/70 hover:bg-white/10"
          >
            <Download size={16} />
          </button>
          {exportOpen ? (
            <div
              className="absolute right-3 top-11 z-[150] w-[260px] rounded-xl p-1.5"
              style={{ background: "rgb(38,38,38)" }}
              role="menu"
              aria-label="导出时间线"
              data-testid="timeline-export-menu"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setExportOpen(false);
                  pushToast(
                    mockMsg(
                      EXPORT_ITEMS.mp4.blocked
                        ? `导出为 MP4：${EXPORT_ITEMS.mp4.blocked}`
                        : EXPORT_ITEMS.mp4.label,
                    ),
                  );
                }}
                className="flex w-full flex-col items-start rounded-md px-2 py-1.5 text-left hover:bg-white/10"
              >
                <span className="text-[13px] text-white/85">{EXPORT_ITEMS.mp4.label}</span>
                {/* SOURCE_FACT: 空时间线点 MP4 导出，源站附「当前时间线暂不支持此操作」 */}
                <span className="text-[11px] text-white/45">{EXPORT_ITEMS.mp4.blocked}</span>
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setExportOpen(false);
                  pushToast(mockMsg(EXPORT_ITEMS.xml.label));
                }}
                className="flex w-full flex-col items-start rounded-md px-2 py-1.5 text-left hover:bg-white/10"
              >
                <span className="text-[13px] text-white/85">{EXPORT_ITEMS.xml.label}</span>
                <span className="text-[11px] text-white/45">{EXPORT_ITEMS.xml.hint}</span>
              </button>
              <div className="my-1 h-px bg-white/[0.08]" />
              {EXPORT_TARGETS.map((t) => (
                <button
                  key={t.name}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setExportOpen(false);
                    pushToast(mockMsg(t.label));
                  }}
                  className="flex h-8 w-full items-center rounded-md px-2 text-left text-[13px] text-white/85 hover:bg-white/10"
                >
                  {t.label}
                </button>
              ))}
            </div>
          ) : null}
          <button
            type="button"
            aria-label="全屏编辑"
            data-testid="timeline-fullscreen-trigger"
            onClick={() => setFullscreen(true)}
            /* Batch 818 SOURCE_FACT：源站 **126×42 / r8**，标签纯白
               （实测 color rgb(255,255,255)）。复刻此前 h-8 + px-2 自适应
               得 89×32、r6、文字 white/85 —— 宽差 37px、字号色都不同。
               宽 126 写死：源站就是定值，标签「全屏编辑」四字 19.5px。 */
            className="flex h-[42px] w-[126px] items-center justify-center gap-1.5 whitespace-nowrap rounded-lg text-[19.5px] leading-none text-white hover:bg-white/10"
          >
            <Maximize2 size={24} />
            全屏编辑
          </button>
        </div>

        <div className="flex min-h-0 flex-1">
          {/* 左侧槽：静音。
              Batch 828 SOURCE_FACT：源站左槽 [1,67,**66**,139]，静音钮
              [13,121,42,42] r6，其后跟一枚**独立的** 1px 竖分隔线
              [66,67,1,139]，轨道自 67 起。复刻此前是 w-32(128) + border-r
              （把分隔线糊在槽上）。

              128 的理由是台账 §27（批 813）那条：「槽若只有 48/96 会被左侧
              连接手柄命中盒整个吞掉，Playwright 报 handle intercepts pointer
              events，用户同样点不到」。批 828 把这条查穿了，**三处都不对**：

              1. 拦截者不是 `jimeng-connect-*` 那枚加号钮，而是 React Flow
                 **自带的** 60×120 隐形热区（`JimengConnectHandles` 的
                 `HOT_ZONE`，inline `left:-30` / `width:60`）。槽宽 48 时
                 `elementFromPoint(钮心)` 返回的是
                 `DIV.react-flow__handle react-flow__handle-left`。
              2. 「44×88」是**渲染**尺寸 —— 该节点 zoom≈0.727，60×120 CSS px
                 缩放而来。批 813 把它当世界像素使；热区在 CSS 坐标下恒为
                 **-30..+30**，与 zoom 无关，「往里吞 30px」的结论碰巧对，单位错。
              3. 「128 时余量 ~14px」「96 时只剩 1px」两个数都错。钮 42 宽、
                 槽内居中 ⇒ 钮心 = 槽宽/2，距热区右缘余量 = 槽宽/2 − 30：

                     48 → **−6**  挡死（实测命中 DIV.react-flow__handle）
                     66 →   3    可点（实测 aria-pressed false→true）← 源站值
                     96 →  18            128 → 34

              源站 66 落在 3px 余量上，照样可点；源站静音钮钮心在节点坐标 34，
              距 806 取证的热区右缘（30）也是 3px —— 这 3px 是**源站布局自带的**，
              不是复刻引入的。故回到 66。

              真正的护栏不是槽宽，是「**钮心必须落在热区右缘之外**」，已写成
              批 828 的行为断言（`elementFromPoint` + 真点一次翻 aria-pressed）。
              （手柄几何是批 806 的地盘，本批不动那边。） */}
          <div
            /* Batch 828 SOURCE_FACT：源站左槽类名
               `relative z-canvas-timeline-track-gutter flex-none w-canvas-timeline-node-track-gutter`，
               槽 [1,67,66,139]；槽内**只有**静音钮一枚，包裹层类名直接写着
               `inline-flex absolute top-[54px] inset-x-0 mx-auto` ⇒ 54px 是源站
               **写死的定位值**，不是「垂直居中算出来的」。所以源站钮在 139px 高的
               槽里上方留 54、下方留 43，是有意的留白。
               复刻此前用 `flex-col items-center gap-3 py-2` ⇒ 钮落在 y=8，
               与源站差 46px。本批改成同样的 absolute top-[54px] inset-x-0。 */
            className="relative w-[66px] shrink-0"
            data-testid="timeline-track-gutter"
          >
            <span className="absolute inset-x-0 top-[54px] mx-auto flex justify-center">
              <button
                type="button"
                aria-label={muted ? "取消静音" : "静音"}
                data-testid="timeline-mute-button"
                aria-pressed={muted}
                onClick={() => setMuted((v) => !v)}
                /* Batch 818 SOURCE_FACT：源站 **42×42 / r6**。
                   复刻此前 size-8(32) + `rounded-full`（32px 上 = 16px 圆角），
                   尺寸与圆角**同时**偏小/偏圆。同样是 813 文档头已记、
                   实现未跟上的那条契约。6px = rounded-md。 */
                className="flex size-[42px] items-center justify-center rounded-md text-white/70 hover:bg-white/10"
              >
                {muted ? <VolumeX size={24} /> : <Volume2 size={24} />}
              </button>
            </span>
          </div>
          {/* Batch 828：源站这枚分隔线是**独立元素**（`timeline-node-track-divider`
              [66,67,1,139]），不是左槽的 border。独立出来才能让左槽内容盒
              保持 66 —— 槽内居中的 42px 静音钮钮心因此落在 33（源站 34 的
              同侧），热区余量 3px，与上表 66 那行一致。 */}

          {/* ⚠️ 批 829 **删除**了这里原本的一枚 `timeline-node-track-divider`
              （`w-px bg-white/[0.06]`）。批 828 把它当成源站事实写进了台账与
              verifier，批 829 回源站查穿：**源站没有这枚元素**。

              取证：源站轨道行的**直接子元素只有两个** —— 左槽 [1,67,66,139] 与
              视口 [67,67,1132,139]，中间没有任何 1px 元素（槽内也没有）。
              槽的底色是 `color(srgb 0.12549 ×3)` = rgb(32,32,32)，与**壳同色**
              ⇒ 那条线上根本没有可见分隔线。批 818 台账里那条
              `[66,67,1,139] timeline-node-track-divider` 是**我们**给「槽与轨道
              的边界」起的名字，不是源站的 testid。⚠️ 我当时顺口写的
              「源站全站用类名，一个 testid 都没有」是**错的** —— 批 831 普查发现
              源站节点壳**是有 testid 的**（`video-flow-node-surface` /
              `timeline-flow-node` / `director-stage-flow-node-shell` /
              `timeline-flow-node-main-track`）。只是那个位置确实没有分隔线元素。

              教训见台账 §41：**照抄本仓台账里的 SOURCE_FACT 不等于验证过它。**
              批 828 抄了，批 829 查了，才发现那条从来不是源站的。 */}

          <div
            /* Batch 820 SOURCE_FACT：源站有独立的横向滚动容器
               `[data-testid="timeline-track-scroll"]`
               [223,187,1132,151]，类名带 `[&::-webkit-scrollbar]:hidden`
               —— **滚动条隐藏但可滚**；内层 `timeline-track-canvas` 是
               `min-w-full`（贴住容器宽，片段超窗时才撑开并出现滚动）。
               复刻此前整条轨道 overflow-x: visible，一旦片段时间超过可见
               窗口（≈33.4s）就会直接溢出面板被裁掉，没有滚动通道。
               左侧静音槽在滚动区**之外**（源站 gutter 与 track-scroll 是
               兄弟节点），所以滚动时它不动 —— 与下面的结构一致。 */
            className="min-w-0 flex-1 overflow-x-auto [&::-webkit-scrollbar]:hidden"
            data-testid="timeline-track-scroll"
          >
            {/* Batch 830：补上源站那枚 canvas 包装层（解 OPEN_QUESTION 829-a）。
                批 820 的注释一直引用「内层 `timeline-track-canvas` 是 `min-w-full`」，
                但**复刻里从来没有这个元素** —— 刻度尺与片段轨道是滚动容器的直接
                孩子。本批按源站实测把它建出来，源站结构是：

                  滚动容器 [67,67,1132,139]  overflow:hidden
                    └ canvas [73,67,1126,139]  display:flex / flex-col
                        margin-left: 6px      min-width: **calc(100% - 6px)**
                        ├ 刻度尺   [73, 67,1126, 27]
                        └ 片段行   [73,100,1126, 84]   ← 尺下方 6px 间隙

                ⚠️ 829-a 记的那个「矛盾」（canvas 1126 但容器 1132，而它带
                `min-w-full`）到此解开：**源站设计系统里 `min-w-full` 不是
                `min-width:100%`，而是 `calc(100% - 6px)`**（实测
                `getComputedStyle(canvas).minWidth === 'calc(100% - 6px)'`）。
                那 6px 左边距正是在 min-width 里被**补偿**掉的 ——
                6 + (100% − 6) = 100%，所以既不溢出也不留缝。
                我当初以为矛盾，其实错在**假设了工具类的字面含义**。

                刻度尺与片段行之间那 6px 来自 canvas 的 `gap`（flex-col + gap），
                源站类名带 `gap-canvas-timeline-node-track-gap`。 */}
            <div
              className="ml-[6px] flex min-h-full min-w-[calc(100%-6px)] flex-col gap-[6px]"
              data-testid="timeline-track-canvas"
            >
            {/* 刻度尺：SOURCE_FACT 00:00→00:30，每 5s 一格
                Batch 819 SOURCE_FACT（解 818-a）：刻度位置是**世界坐标定值**，
                不是百分比。实测内嵌时间线节点 00:00→00:30 跨 963px
                ⇒ **32.1 px/s**，而轨道宽 1126px ⇒ 可见窗口 **≈35.1s**，
                30s 的标签只占 85.5%，右侧留白 ~163px。
                复刻此前用 `left: (t/30)*100%` 把 30s 拉满全宽（35.7px/s），
                刻度随轨道宽浮动 —— 与源站模型相反。

                附一条关键实测：**px/s 不是全局常量**。源站有两个时间线表面，
                全屏编辑器的刻度是 9px 字号 / 21.4px·s⁻¹，内嵌节点是 13.5px /
                32.1px·s⁻¹，两者比值 1.5 恰好等于字号比 13.5/9 ⇒ 源站按刻度
                标签的字号定间距。**所以不能找一个"全局 px/s"照搬**，
                只能按本表面的字号定 —— 这里的 32.1 就是 13.5px 字号对应值。*/}
            <div
              /* Batch 830：宽度职责上移到 canvas（`min-w-[calc(100%-6px)]`），
                 这里改成 `w-full` 贴住 canvas，避免两层 min-width 叠加。 */
              className="relative h-[27px] w-full border-b border-white/[0.06]"
              data-testid="timeline-ruler"
              aria-label="时间线刻度"
            >
              {Array.from({ length: TOTAL_SECONDS / TICK_STEP + 1 }, (_, i) => i * TICK_STEP).map((t) => (
                <span
                  key={t}
                  className="absolute top-0 flex h-full -translate-x-px flex-col items-start"
                  style={{ left: `${t * RULER_PX_PER_SEC}px` }}
                >
                  <span className="h-2 w-px bg-white/20" />
                  {/* Batch 818 SOURCE_FACT：源站刻度标签 **13.5px**（实测
                     `font-size: 13.5px`），复刻此前 10px。
                     注意 `getComputedStyle().fontSize` **不受** viewport
                     transform 影响，所以这个数不受缩放归一化影响，是直读值。 */}
                  <span className="text-[13.5px] leading-3 text-white/40 tabular-nums">{fmt(t)}</span>
                </span>
              ))}
            </div>

            {/* 轨道：片段 + 「+ 添加素材到时间线」
                Batch 818 SOURCE_FACT：源站刻度尺 **27** 高、片段轨道 **84** 高
                （ruler [73,67,1126,27] / clip-track [73,100,1126,84]）。
                复刻此前 h-6(24) / h-[76px]。

                Batch 830：去掉 `px-3 py-2`。源站片段行**零内边距**（实测
                `padding: 0px/0px`），投放区就是这一行的**满宽** ——
                源站新鲜读数投放区 `[73,100,**1126**,84]`，与片段行同宽同位。
                （台账 §27.5 记的 1113 本次量不到了，记 829/830 两次新鲜读数
                都是满宽 1126；差的 13 恰是当年那条同样错掉的「13px」。）
                片段自身的 12px 左内缩（`left: 12 + …`）**保持不动** ——
                源站片段矩形未取证（fixture 媒体长期不加载），改它等于拿猜的数
                换掉另一个猜的数，见 OPEN_QUESTION 830-a。 */}
            <div
              className="relative h-[84px] w-full"
              data-testid="timeline-clip-track"
            >
              {clips.map((c) => (
                <div
                  key={c.id}
                  className="absolute top-2 flex h-[60px] items-center justify-between gap-2 rounded-md px-2 text-[12px] text-white/85"
                  style={{
                    /* Batch 819：与刻度同一套世界坐标映射（32.1px/s），
                       否则刻度走定值、片段走百分比，两者会脱节。 */
                    left: `${12 + c.start * RULER_PX_PER_SEC}px`,
                    width: `${Math.max(1, c.length * RULER_PX_PER_SEC)}px`,
                    background: "rgba(255,255,255,0.10)",
                    border: "1px solid rgba(255,255,255,0.14)",
                  }}
                  data-testid="timeline-clip"
                >
                  <span className="truncate">{c.label}</span>
                  <button
                    type="button"
                    aria-label={`移除 ${c.label}`}
                    onClick={() => removeClip(c.id)}
                    className="shrink-0 text-white/50 hover:text-white"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {clips.length === 0 ? (
                <button
                  type="button"
                  onClick={() => addClip()}
                  data-testid="timeline-add-clip"
                  /* Batch 818 SOURCE_FACT：源站空态投放区是 **r6 + 实底
                     `rgba(255,255,255,0.04)`、高 84**，**不是**虚线框。
                     复刻此前是 `border-dashed border-white/20` 的虚线占位 ——
                     两者观感完全不同（虚线是"尚未实现"的暗示，实底是"空轨道"）。
                     文字：源站 19.5px 居中于投放区。 */
                  className="flex h-[84px] w-full items-center justify-center gap-2 rounded-md bg-white/[0.04] text-[19.5px] leading-none text-white/35 transition-colors hover:bg-white/[0.07]"
                >
                  <Plus size={24} />
                  添加素材到时间线
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => addClip()}
                  aria-label="添加素材到时间线"
                  className="absolute bottom-2 right-3 flex h-7 items-center gap-1 rounded-md px-2 text-[12px] text-white/50 hover:bg-white/10 hover:text-white/80"
                >
                  <Plus size={14} />
                  添加素材
                </button>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* 源站把空态说明放在 sr-only，不渲染成可见行 */}
        <span className="sr-only">
          {clips.length === 0
            ? "No clips. Drag clips to reorder them. With the keyboard, press Shift to move."
            : `${clips.length} clips on the timeline.`}
        </span>
      </div>

      {/* Batch 813 SOURCE_FACT：全屏时间线编辑器。此前「全屏编辑」是死按钮。
          源站结构：标题 + 副标题 + 来源/类型两排筛选 + 资产区 + 底部 playhead */}
      {fullscreen
        ? createPortal(
            <div
              ref={fsLayerRef}
              className="fixed inset-0 z-[300] flex flex-col px-3 pb-3"
              style={{ background: "rgb(20,20,22)" }}
              role="dialog"
              aria-label="时间线"
              data-testid="timeline-fullscreen"
            >
          <div className="flex h-[60px] shrink-0 items-center gap-2">
            <span className="text-[15px] font-medium text-white">{d.title}</span>
            <span className="text-[12px] text-white/45">{FS_SUBTITLE}</span>
            <span className="flex-1" />
            <button
              type="button"
              /* Batch 821 SOURCE_FACT：源站这一枚的实名是 **「导出时间线」**
                 （76×36 @[1380,12]），不是复刻的「导出」；关闭钮实名
                 **「Close timeline editor」36×36 @[1464,12]** —— 英文，
                 与源站其它 chrome 锚点（Canvas title / Zoom options /
                 Close timeline editor）同一套词汇，逐字沿用。
                 ⚠️ 这枚读数是**视口绝对值**，但**不是**因为「写了
                 `fixed` 就天然不受缩放影响」—— 821 实测证伪了那句话：
                 浮层此前就挂在 `.timeline-node` 里，而 React Flow 给每个
                 节点加 `transform`，**transform 祖先会收编 `position:fixed`**
                 （`fixed` 的包含块变成那个节点），实测整块只铺 1200×207。
                 现在靠 `createPortal(…, document.body)` 真的逃出去，
                 `parentElement` 是 BODY，读数才可以直接照搬源站。 */
              aria-label="导出时间线"
              data-testid="timeline-fullscreen-export"
              onClick={exportTimelineJson}
              className="flex h-9 w-[76px] items-center justify-center rounded-lg text-[13px] text-white/80 hover:bg-white/10"
            >
              导出
            </button>
            <button
              type="button"
              aria-label="Close timeline editor"
              data-testid="timeline-fullscreen-close"
              onClick={() => setFullscreen(false)}
              className="flex size-9 items-center justify-center rounded-lg text-white/70 hover:bg-white/10"
            >
              <X size={16} />
            </button>
          </div>

          <div className="flex min-h-0 flex-1 gap-2">
            {/* Batch 820 SOURCE_FACT：源站资产栏
               `[data-testid="timeline-fullscreen-canvas-assets"]` **360 宽**
               @[12,60] 高 652，tabs 行 `…-asset-primary-tabs` 高 **56**
               @[12,60]。全屏编辑器浮在 body 上（见上方 portal 注释），
               所以这个宽度是视口绝对值，可直接照搬。复刻此前 260 宽。
               注意它是**照搬源站的定值**，不是推导值 —— 别按内容去凑。 */}
            <div
              className="w-[360px] shrink-0 border-r border-white/[0.08] p-3"
              data-testid="timeline-fs-assets"
            >
              <div className="mb-2 flex flex-wrap gap-1">
                {FS_SOURCES.map((sname) => (
                  <button
                    key={sname}
                    type="button"
                    data-testid={`timeline-fs-source-${sname}`}
                    onClick={() => setFsSource(sname)}
                    className={`h-7 rounded-md px-2 text-[12px] ${
                      fsSource === sname ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/10"
                    }`}
                  >
                    {sname}
                  </button>
                ))}
              </div>
              <div className="mb-2 flex flex-wrap gap-1">
                {FS_KINDS.map((k) => (
                  <button
                    key={k}
                    type="button"
                    data-testid={`timeline-fs-kind-${k}`}
                    onClick={() => setFsKind(k)}
                    className={`h-7 rounded-md px-2 text-[12px] ${
                      fsKind === k ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/10"
                    }`}
                  >
                    {k}
                  </button>
                ))}
              </div>
              {/* 资产列表。`timeline-fs-asset-empty` 这个 testid 保留**给这个容器**
                 （名字已经不准了，但 821 的 verifier 依赖它恒在 —— 若在无资产时
                 把它条件渲染掉，那条断言会直接超时）。两句文案必须**始终**出现在
                 浮层里：批 813 逐条断言了「没有媒体可供预览」与「将文件拖至此处添加」，
                 所以拖放提示单独成行，不塞进列表里。 */}
              {/* 投放区：批 832 给它接上**真拖放**。
                  此前这里只有一句「将文件拖至此处添加」的提示，而整个组件里
                  **没有 onDrop / onDragOver / createObjectURL / input[type=file]**
                  —— 也就是说这句提示在**说谎**：用户真把文件拖进来，什么也不会发生。
                  一个会骗人的可见交互，比没有这个交互更糟。

                  拖放与下面那枚「导入」按钮**共用同一条** ingest 路径
                  （`ingestFiles`），所以两条入口的行为不会分叉。
                  新增 testid `timeline-fs-dropzone` 走**包裹层**，不动既有
                  `timeline-fs-asset-empty` / `-hint` —— 821/827 的 verifier
                  依赖那两个恒在。 */}
              <div
                data-testid="timeline-fs-dropzone"
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = "copy";
                  setFsDragOver(true);
                }}
                onDragLeave={() => setFsDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setFsDragOver(false);
                  const files = Array.from(e.dataTransfer?.files ?? []);
                  if (files.length) ingestFiles(files);
                }}
                className={`rounded-md transition-colors ${
                  fsDragOver ? "bg-white/[0.08] ring-1 ring-white/30" : ""
                }`}
              >
                <div
                  className="flex h-[120px] flex-col gap-1 overflow-y-auto rounded-md border border-dashed border-white/15 p-2 text-[12px] leading-[18px] text-white/60"
                  data-testid="timeline-fs-asset-empty"
                >
                {fsVisible.length === 0 ? (
                  <span className="m-auto text-center text-white/40">没有媒体可供预览</span>
                ) : (
                  fsVisible.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => addClip(a.title)}
                      /* `asset-row-` 而不是 `asset-`：容器叫 `timeline-fs-asset-empty`、
                         提示行叫 `timeline-fs-asset-hint`，用 `asset-` 前缀去选「资产行」
                         会把这两个一起选中 —— 827 的 verifier 初版就因此点到容器上，
                         一次连出 7 条假失败（前缀选择器多命中，与批 819 那次同族）。
                         **锚点命名要保证「前缀互不包含」**，否则选择器天然会多命中。 */
                      data-testid={`timeline-fs-asset-row-${a.id}`}
                      className="flex items-center justify-between gap-2 rounded px-1.5 py-1 text-left hover:bg-white/10"
                    >
                      <span className="truncate">{a.title}</span>
                      <span className="shrink-0 text-[11px] text-white/35">
                        {a.kind === "image" ? "图片" : a.kind === "video" ? "视频" : "音频"}
                      </span>
                    </button>
                  ))
                )}
                </div>
                <p
                  className="mt-1 text-center text-[11px] text-white/30"
                  data-testid="timeline-fs-asset-hint"
                >
                  将文件拖至此处添加
                </p>
              </div>
              <button
                type="button"
                data-testid="timeline-fs-import"
                onClick={() => fileInputRef.current?.click()}
                className="mt-2 flex h-8 w-full items-center justify-center rounded-md bg-white/10 text-[13px] text-white hover:bg-white/20"
              >
                导入
              </button>
              {/* 批 832：这枚 input 是「导入」的真身。**不可见但必须在 DOM 里**
                  —— Playwright 的 set_input_files 与 `input.click()` 都要求它
                  真实存在；用 display:none 的 input 仍可被 set_input_files 命中。
                  ref 而非 id：全屏浮层用 portal 渲染到 body，用 id 选择器在
                  同一页多实例时会选错。 */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,video/*,audio/*"
                className="hidden"
                data-testid="timeline-fs-file-input"
                onChange={(e) => {
                  const files = Array.from(e.target.files ?? []);
                  // 清空 value，否则同一个文件选第二次不会触发 change
                  e.target.value = "";
                  if (files.length) ingestFiles(files);
                }}
              />
            </div>

            <div className="flex min-w-0 flex-1 flex-col">
              <div className="flex-1 p-4 text-[13px] text-white/40">Timeline preview</div>
              {/* Batch 821 SOURCE_FACT：播放头读数在**预览区底部居中**，
                  源站 @[897,680]「Timeline playhead」1×1 隐藏 + 可见的
                  `00:00:00` 54×20 / `/` 5×20 / `00:00:00` 52×20，
                  基准是预览壳底边往上 32px（壳 60..712）。
                  ⚠️ 821 加底栏工作区时我把这个读数**顺手删掉了** ——
                  `verify-jimeng-batch813.py` 立刻抓到（它的文件头就写着
                  「底部 Timeline playhead 00:00:00 / 00:00:00」）。
                  底栏那条 1px 的 `timeline-fullscreen-playhead` 是另一回事
                  （播放头竖线，无文字），两者别混。 */}
              <div
                className="flex shrink-0 items-end justify-center gap-1 pb-3"
                data-testid="timeline-fs-playhead"
              >
                <span className="sr-only">Timeline playhead</span>
                <span
                  className="text-[18px]/[20px] tabular-nums text-white/80"
                  data-testid="timeline-fs-playhead-time"
                >
                  {stamp(fsTime)}
                </span>
                <span className="text-[18px]/[20px] text-white/80">/</span>
                <span className="text-[18px]/[20px] tabular-nums text-white/80">
                  00:00:{String(Math.floor(span)).padStart(2, "0")}
                </span>
              </div>
            </div>
          </div>

          {/* Batch 821 SOURCE_FACT：源站底栏整块
              `section[data-testid="timeline-fullscreen-workspace"]`
              **@[12,720] 1488×218 r12**，aria-label = 副标题那句英文。
              内部三层（全部 @1512×950 视口绝对值）：
                resize-handle  [12,704] 1488×24  「Resize timeline editor height」
                toolbar        [12,720] 1488×44
                  「Timeline editing tools」    [20,728] 208×28
                    撤销 / 重做 / 分割 / 向左剪裁 / 向右剪裁 / 删除  各 28×28
                  「Timeline playback controls」[1304,728] 188×28
                    关闭自动吸附 / 缩小视图 / 「Timeline zoom」span / 放大视图  各 28×28
                track-scroll   [12,756] 1488×182
                  ruler        [64,764] 1428×18  ← 00:00…01:10，**5s 步进**
                  visual-track [12,786] 1488×56  aria="Main visual track"
                    静音 [20,800] 28×28  /  添加素材到时间线 [64,786] **56×56**
                  playhead     [64,764] 1×174

              复刻此前**整块没有** —— 只有一条 playhead 文字行。
              本批把骨架补齐。刻度用 9px 字号 / 21.4px·s⁻¹（819 实测的
              全屏编辑器那一套，≠ 内嵌节点的 32.1 —— 同一模型两个表面
              各自的定值，别混用）。 */}
          <section
            className="relative mt-2 flex shrink-0 flex-col rounded-xl bg-[rgb(28,28,30)] pt-[36px]"
            style={{ height: 218 }}
            aria-label={FS_SUBTITLE}
            data-testid="timeline-fullscreen-workspace"
          >
            {/* 源站这枚把手 @[12,**704**] 1488×24 —— 它比底栏顶边(720)还高 16px，
                是**骑在内容区与底栏之间那道 8px 缝上**的，不是底栏的第一行。
                所以 `absolute -top-4`：section 加 `pt-[36px]` 把工具条抬成
                绝对定位，轨道区回到正常流正好落在 756 —— 与源站 track-scroll
                的 y=756 对上，负 margin 一个都不需要。 */}
            <div
              className="absolute inset-x-0 -top-4 flex h-6 items-center justify-center text-white/20"
              aria-label="Resize timeline editor height"
              data-testid="timeline-fullscreen-workspace-resize-handle"
            >
              <span className="h-px w-10 bg-current" />
            </div>

            <div
              className="absolute inset-x-0 top-0 flex h-11 items-center justify-between px-2"
              data-testid="timeline-fullscreen-toolbar"
            >
              <div
                className="flex items-center gap-2"
                role="group"
                aria-label="Timeline editing tools"
                data-testid="timeline-fullscreen-editing-tools"
              >
                {FS_EDIT_TOOLS.map((t) => {
                  /* 撤销/重做有真历史栈，禁用态与画布右键菜单同源；
                     另外四枚永远可点 —— 没片段可切时给的是**带信息的反馈**
                     （「请先把播放头移到某个片段上」），不是一颗点不动的灰钮。 */
                  const off = t.kind === "undo" ? !canUndo : t.kind === "redo" ? !canRedo : false;
                  return (
                    <button
                      key={t.label}
                      type="button"
                      aria-label={t.label}
                      data-testid={`timeline-fullscreen-tool-${t.label}`}
                      disabled={off}
                      onClick={() => runFsTool(t.kind)}
                      className={`flex size-7 items-center justify-center rounded-md ${
                        off ? "text-white/25" : "text-white/70 hover:bg-white/10"
                      }`}
                    >
                      <t.icon size={16} />
                    </button>
                  );
                })}
              </div>
              <div
                className="flex items-center gap-1"
                role="group"
                aria-label="Timeline playback controls"
                data-testid="timeline-fullscreen-playback-controls"
              >
                <button
                  type="button"
                  aria-label="关闭自动吸附"
                  onClick={() => setFsSnap(!fsSnap)}
                  aria-pressed={!fsSnap}
                  className={`flex size-7 items-center justify-center rounded-md ${
                    fsSnap ? "text-white/70 hover:bg-white/10" : "bg-white/10 text-white"
                  }`}
                >
                  <Magnet size={16} />
                </button>
                <button
                  type="button"
                  aria-label="缩小视图"
                  onClick={() => setFsZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))}
                  className="flex size-7 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
                >
                  <ZoomOut size={16} />
                </button>
                <span
                  className="w-[92px] text-center text-[12px] text-white/60"
                  aria-label="Timeline zoom"
                  data-testid="timeline-fullscreen-zoom"
                >
                  {Math.round(fsZoom * 100)}%
                </span>
                <button
                  type="button"
                  aria-label="放大视图"
                  onClick={() => setFsZoom((z) => Math.min(2, +(z + 0.1).toFixed(2)))}
                  className="flex size-7 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
                >
                  <ZoomIn size={16} />
                </button>
              </div>
            </div>

            {/* 刻度 + 视觉轨 */}
            <div
              className="relative min-h-0 flex-1 overflow-x-auto pt-2 [&::-webkit-scrollbar]:hidden"
              data-testid="timeline-fullscreen-track-scroll"
            >
              {/* `relative` 不能省：playhead 是 absolute，不加这层它的包含块
                  会退到 `track-scroll`，而那个盒是 **padding box**（756 起、
                  182 高），`inset-y-0` 就会把轨道区的 `pt-2` 一起吃进去 ——
                  实测读数 [64,756,1,182]，源站是 [64,**764**,1,**174**]。
                  锚到本层（764 起、174 高）才对得上。
                  `h-full` 同样不是装饰：刻度 18 + 轨道 56 只有 78，源站轨道区
                  182 高，差出来的 104 要靠整块撑满，playhead 才有 1×174 那么长。
                  刻度绝对定位、不产生内在宽度，但**会撑出可滚动溢出**
                  （实测 scrollWidth 1576 > clientWidth 1488）——
                  所以横向滚动不必另写 min-width，缩放时溢出量自己跟着长。 */}
              <div
                className="relative h-full min-w-full"
                ref={fsTrackRef}
                onClick={(e) => seekFromClientX(e.clientX)}
                data-testid="timeline-fullscreen-track-canvas"
              >
                <div
                  className="relative ml-[52px] mr-2 h-[18px]"
                  data-testid="timeline-fullscreen-ruler"
                >
                  {Array.from({ length: FS_RULER_SECONDS / FS_TICK_STEP + 1 },
                    (_, i) => i * FS_TICK_STEP).map((t) => (
                      <span
                        key={t}
                        className="absolute top-0 flex flex-col items-start"
                        style={{ left: `${t * FS_RULER_PX_PER_SEC * fsZoom}px` }}
                      >
                        <span className="h-1.5 w-px bg-white/20" />
                        <span className="text-[9px] leading-3 text-white/40 tabular-nums">
                          {fmt(t)}
                        </span>
                      </span>
                    ))}
                </div>
                <div
                  className="mt-1 flex h-14 items-center px-2"
                  role="group"
                  aria-label="Main visual track"
                  data-testid="timeline-fullscreen-visual-track"
                >
                  <button
                    type="button"
                    aria-label={muted ? "取消静音" : "静音"}
                    data-testid="timeline-fullscreen-mute-button"
                    aria-pressed={muted}
                    /* 轨道容器上挂了 `onClick` 做播放头定位（825），这里必须
                       阻断冒泡 —— 否则点「静音」会顺带把播放头挪到那个 x 上，
                       用户按了静音、播放头却跑了。投放区同理。 */
                    onClick={(e) => {
                      e.stopPropagation();
                      setMuted((v) => !v);
                    }}
                    className="flex size-7 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
                  >
                    {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                  </button>
                  {/* 片段：与内嵌轨道同一套映射（`52 + t × px/s × zoom`），
                      刻度 / 片段 / 播放头三者的横坐标由同一个式子算出来。
                      ⚠️ 这里的**尺寸不是源站实测值** —— 源站那个 fixture 的
                      媒体全没加载，轨道上根本没有片段可量（台账 §31）。
                      本批只保证「按同一映射渲染」这件事对，不写死任何读数。 */}
                  {clips.map((c) => (
                    <div
                      key={c.id}
                      className="absolute top-2 flex h-10 items-center overflow-hidden rounded-md px-2 text-[12px] text-white/85"
                      style={{
                        left: `${52 + c.start * FS_RULER_PX_PER_SEC * fsZoom}px`,
                        /* 下限是 **18** 不是 2：元素带 `px-2`(左右各 8) 与
                           1px 边框，而 Tailwind 全局 `border-box` 下盒子**不可能
                           窄于 padding+border**（16+1=17，取整 18）。
                           此前写 `Math.max(2, …)`，那个下限**永远达不到** ——
                           行内样式写着 2px、实际渲染 18px，样式在说谎；
                           一个被剪成 0 长的片段会显示成 18px 宽的一块。
                           下限必须等于真实的最小宽度，否则别写。 */
                        width: `${Math.max(18, c.length * FS_RULER_PX_PER_SEC * fsZoom)}px`,
                        background: "rgba(255,255,255,0.10)",
                        border: "1px solid rgba(255,255,255,0.14)",
                      }}
                      data-testid="timeline-fullscreen-clip"
                    >
                      <span className="truncate">{c.label}</span>
                    </div>
                  ))}
                  {/* 投放区 56×56。**空轨**时落在 x=64 —— 那是 821 实测的源站
                      读数（[64,786,56,56]），照搬；非空时改跟在最后一个片段之后。
                      源站的**非空态**读数我拿不到（fixture 无媒体），所以这里
                      是按「排得下、不压住片段」推的，不写成 SOURCE_FACT。
                      顺带解决一个真实问题：若像内嵌轨道那样「仅空态出现」，
                      全屏编辑器就永远加不了第二个片段。 */}
                  <button
                    type="button"
                    aria-label="添加素材到时间线"
                    onClick={(e) => {
                      // 同静音钮：点投放区只该加片段，不该顺带挪播放头
                      e.stopPropagation();
                      addClip();
                    }}
                    className="absolute top-[22px] flex size-14 items-center justify-center rounded-md bg-white/[0.04] text-white/35 hover:bg-white/[0.07]"
                    style={{
                      /* 52 = 刻度尺/播放头用的左槽宽。track-canvas 起点在绝对
                         x=12，所以 52 换算过去正好是源站实测的 x=64。
                         top-22 = 刻度 18 + 视觉轨的 mt-1 4 —— 投放区跟片段
                         一样锚在轨道画布上（同一套映射），但它要落在**视觉轨
                         内部**（源站读数 y=786），而视觉轨的顶边相对轨道画布
                         内容顶正好差 22px。 */
                      left: `${52 + spanOf(clips) * FS_RULER_PX_PER_SEC * fsZoom
                        + (clips.length ? 12 : 0)}px`,
                    }}
                    data-testid="timeline-fullscreen-drop"
                  >
                    <Plus size={24} />
                  </button>
                </div>
                {/* 播放头：位置由 fsTime 算出（同一套映射）。
                    不用 left/top 硬编码 —— t=0 时它仍然落在 52px 处，
                    与 821 实测的源站读数 [64,764,1,174] 保持一致。 */}
                <div
                  className="absolute inset-y-0 w-px bg-white/70"
                  style={{ left: `${52 + fsTime * FS_RULER_PX_PER_SEC * fsZoom}px` }}
                  aria-label="Timeline playhead"
                  data-testid="timeline-fullscreen-playhead"
                />
              </div>
            </div>
          </section>
            </div>,
            document.body,
          )
        : null}

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
    </div>
  );
}
