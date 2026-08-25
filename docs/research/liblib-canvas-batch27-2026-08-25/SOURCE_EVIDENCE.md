# Batch 27 Source Evidence

> 采样日期：2026-08-25  
> 原站：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. 证据方法

本批先读取既有截图台账，没有重复识别原站整张画布。新的高置信信息来自当日画布 HTML 引用的线上 JavaScript bundle：

| 本地采样 | 字节数 | SHA-256 | 内容 |
|---|---:|---|---|
| `/tmp/liblib-chunks/5.js` | 343745 | `19ae080ffa0c23788cc3a6543cf835d34d50da331ab739fdafd558f994bb441e` | 当前中文文案 |
| `/tmp/liblib-chunks/33.js` | 1564549 | `3c976a417d35ead78e44a985f3d6d47cf1f9c5c6ae3c31221d82c5ebe70cef00` | video node、region overlay、panel、graph handoff |
| `/tmp/liblib-chunks/61.js` | 46446 | `4380cf7e54d07a899f801718fa369331f3c43d5418c386ff37947ed54f3274d8` | video toolbar dropdown |

`/tmp` 文件不是仓库制品；本文件保存可接力结论。已有文案摘录还可从 [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json) 复核。

## 2. Source Fact：顶部入口

`VideoNodeToolbar` 把去字幕渲染为一个 dropdown entry：

- 图标：remove-caption；
- tooltip：`AI一键去除视频字幕，仅支持中英文字幕`；
- item 1：`智能去字幕`，回调参数 `smart`；
- item 2：`框选去字幕`，回调参数 `region`；
- disabled reason 同时作用于 entry 和 item。

进入 `smart`：

- 设置 subtitle mode；
- 清理既有 region session；
- 打开节点下方 compact panel。

进入 `region`：

- 设置 subtitle mode；
- 创建 `{ outputNodeId, sourceNodeId, locations }` session；
- 激活区域编辑；
- 聚焦 source node，目标 zoom 至少为 `1`，动画 `220ms`。

## 3. Source Fact：紧凑下方面板

线上 `SubtitleErase` panel 的结构为：

```text
wrapper
  absolute -bottom-4 left-1/2 z-20
  w-max -translate-x-1/2 translate-y-full

surface
  flex w-max items-center gap-3
  rounded-xl px-2 py-2

children
  close 32x32
  divider 1x24
  mode label 13px
  region only: help
  region only: divider + select/undo/redo/reset 32x32
  power cost
  submit 28x28
```

模式文案：

- smart：`智能去字幕`
- region：`框选去字幕`

region help 内容：

1. `在画面上拖拽鼠标,框选要擦除的区域`
2. `支持框选多个区域,所有框内文字将被擦除`
3. `擦除作用于整段视频,不仅是当前帧`

当 region 没有 `erase_ratio_location` 时，submit disabled，并以 `请选择字幕擦除区域` 作为 disabled reason。

## 4. Source Fact：区域编辑层

region editor 覆盖视频内容：

- root：`absolute inset-0`，active cursor 为 `crosshair`；
- rectangle 使用相对坐标 `relX / relY / width / height`；
- border：`1.5px solid #0690ae`；
- fill：`rgba(7, 184, 221, 0.15)`；
- rectangle 可被选择和拖动；
- 选中矩形显示四条 edge resize hit area 和四个 corner handles；
- 右键打开 delete context menu；
- 支持多个矩形；
- store 暴露 undo、redo、reset 和当前 revision。

生成参数通过 `erase_ratio_location` 传递相对矩形数组。

## 5. Source Fact：请求参数与图拓扑

两模式共用：

```text
model: volcano-subtitle-eraser
videoList: [sourceUrl]
videoListV2: [{ url, width, height, duration }]
```

模式差异：

| UI mode | Request mode | Region data |
|---|---|---|
| smart | `Subtitle` | none |
| region | `Text` | `erase_ratio_location` |

确认后，原站会：

- 在源节点右侧最近可用位置创建 video target；
- 创建 source-to-target edge；
- target 名称：`视频一键去字幕-{nodeLabel}`；
- target generator type：`SUBTITLE_ERASE`；
- target 初始为 pending/generating；
- smart target 文案：`点击生成自动去除字幕`；
- region target 文案：`框选区域生成去字幕视频`。

真实提交成功后关闭 mode 和 region session；提交失败、重复或商业流程接管时会删除临时 target。

## 6. 当前 Clone 审计

| 项目 | 当前 clone | 当前原站证据 |
|---|---|---|
| 入口 | dropdown | dropdown |
| tooltip | 无 | 中英文支持说明 |
| item click | 临时文字 | 打开专用 mode |
| lower panel | 无 | compact 48px control bar |
| region overlay | 无 | multi-rectangle editor |
| undo/redo/reset | 无 | region session history |
| submit guard | 无 | region 为空 disabled |
| graph handoff | 无 | pending video + edge |
| target semantics | 无 | SUBTITLE_ERASE + mode-specific copy |

结论：入口文案虽然存在，但当前行为不是源站工作流，必须替换而不是继续补充临时反馈。

## 7. 边界

### Source fact

本文件第 2-5 节来自当前线上 bundle 的组件结构、状态分支和请求构造。

### Inference

bundle 中的 design token 变量由主题系统解析；clone 使用现有深色 token 的近似值，不声明为 computed color 精确采样。

### Clone-only decision

clone 不实现模型 schema 校验、上传、计费、任务提交、失败回滚或跨会话 region store。图事务和 pending target 仅验证前端画布体验。
