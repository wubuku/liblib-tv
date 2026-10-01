# Batch 360 — 补上两块从未普查的面：3 个死控件，以及一条漏掉的门禁

日期：2026-10-01
工具：`scripts/probe_liblib_batch360_new_nodes.py`（浮层普查一度单独成探针，
最终并入门禁——同一套判据不维护两份实现）
门禁：`scripts/verify-liblib-batch360.py`（31 项）

## 补的是哪两块

358/359 覆盖的是画布外框 16 态 + fixture 里 10 个节点的编辑面。剩下两块没测：

1. **能通过「添加节点」新建、但默认画布里没有的节点类型**——音频 / 智能剪辑 / 逐帧拉片。
   它们的编辑面板一次都没进过。
2. **浮层**——预览大图（`ImagePreviewOverlay`）、图片标注画布、标注画布里的颜色菜单。
   节点编辑面那批只普查了工具条与编辑面板；标注态进去之后，画布上的控件是另一层。
   frameos batch 350 的裁剪框也正是这种「浮在上面的编辑层」。

**跳过「导演台」（script-execution）**：它打开 `DirectorDesk`，那是另一条线，
且有并行 session 正在改（`src/components/director/*` 有未提交 WIP）——
现在去普查会把人家的在途改动混进结果。**跨线不碰。**

## 结果：浮层干净，节点类型里 3 个死控件

| 位置 | 控件 |
|---|---|
| `AudioNode.tsx:59` | 播放音频（白色圆形主按钮，最像能点的一个） |
| `VideoClipEditPanel.tsx:73` | 默认模式（`data-video-clip-mode-setting`） |
| `VideoClipEditPanel.tsx:83` | 输出设置 16:9 · 720P · 30s（`data-video-clip-output-setting`） |

三个都**无 `onClick`、也没 `disabled`**，却各带悬停反馈（`hover:bg-[#ededed]` /
`hover:bg-white/[0.06]`）。修法同 358/359：保持启用 + 去悬停反馈 + `cursor: default`
+ `title` + `data-inert`，文案与几何不动（`batch25` 读的正是文案，改后仍通过）。

浮层三面（预览大图 / 标注画布 / 标注颜色菜单）**0 问题**。

## 探针踩的坑，以及它为什么没变成假零

第一版把 CSS 类名当成了 `data-add-node-entry` 的值（正确值是 `AddNodePanel` 里的
`entry.type`：`audio` / `video-clip` / `shot-breakdown`），于是三个类型全部
「面板里没有该类型」被跳过。

关键在于探针**如实报了跳过，没有假装测过**——输出里是三行「跳过 —— 面板里没有
该类型」，不是「0 问题」。如果当时报「0 问题」，这三个编辑面就会以「已覆盖」的名义
混过去。**探针宁可说自己没测到，也不谎报干净。**

## 门禁补上一条漏掉的断言

变异测试里有一项**没被抓到**：把「默认模式」的 `hover:bg-white/[0.06]` 加回去，
门禁是绿的。

原因很清楚：判据只管「有没有 handler」，没管「看起来能不能点」。而 **hover 变色
恰恰是这类缺陷最核心的视觉特征**——用户就是被这个骗的。已补成门禁断言
`no-lying-affordance`：**声明了惰性的控件若还带 `hover:` 暗示，就还是在骗人。**

> 这条属于「元缺陷踩到即变门禁」：它不是某个控件的问题，是判据少了一个维度。
> 补完之后 4 项变异全红。

变异第 4 项第一版挑错了目标：选了标注「重做」，但它本来就是 `disabled`——
禁用的控件本来就不该被判成死控件，那样这个变异测不到任何东西。改成摘掉
标注工具切换按钮的 `onClick`，红在 `overlay:annotate:no-dead-control`。

## 变异测试（4/4 全红）

| 变异 | 结果 |
|---|---|
| 撤销修复：音频「播放音频」去掉 `data-inert` | 红（`new:音频:no-dead-control`） |
| 半修：输出设置保留 `data-inert` 但抹掉 `title` | 红（`new:智能剪辑:no-dead-control`） |
| 半修：「默认模式」把 hover 底色加回来 | 红（`new:智能剪辑:no-lying-affordance`） |
| 浮层：摘掉标注工具切换按钮的 `onClick` | 红（`overlay:annotate:no-dead-control`） |

## 防假零

- 三种新节点**必须真的被创建出来**（`new-node:{类型}:created`），创建失败直接红；
- 每个浮层**必须真的打开**（预览层 / 标注画布 / 颜色菜单各有独立标志）；
- 每个面至少扫到 30 个控件，否则红——面板没打开时不能算「干净」。

## 顺带记录（只记录不修）

`CameraConfigDialog` 与 `CameraMovementDialog` 两个组件**全项目无人渲染**——
死组件。与 `batch359` 记的 uiStore 五个零读取开关、`toggleUserMenu` 无人调用，
是同一类残留。

## 覆盖

实测 6 个面：音频 / 智能剪辑 / 逐帧拉片三种新节点类型，加上预览大图、标注画布、
标注颜色菜单三层浮层。
