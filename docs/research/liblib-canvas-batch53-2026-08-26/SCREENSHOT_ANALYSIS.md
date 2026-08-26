# Batch 53 截图识别台账

> 识别日期：2026-08-26
> 来源：本地 LibTV clone 运行态
> 目的：记录三张 Batch 53 截图的唯一识图结果，后续优先读本文。

## 1. 截图范围

| 文件 | viewport | 状态 |
|---|---:|---|
| [`liblib-clone-batch53-image-annotate-standard-929-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-standard-929-2026-08-26.png) | `929x874` | 标准图片双浮层 |
| [`liblib-clone-batch53-image-annotate-active-929-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-active-929-2026-08-26.png) | `929x874` | active annotate |
| [`liblib-clone-batch53-image-annotate-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-mobile-390-2026-08-26.png) | `390x844` | mobile active annotate |

这些是 clone 截图，不是源站截图。源站事实来自 Batch 53
`SOURCE_EVIDENCE.md` 引用的 live DOM/bundle 文档。

## 2. 标准态

直接可见：

- `1092.5px` 标准工具条仍按节点中心定位并自然裁切；
- standard bottom generation panel 在节点下方存在；
- `标注` 是标准工具条末端 icon action；
- 页面其他 graph、导航和整理确认卡保持原位。

该截图只用于 standard -> active 对照，不新增 Batch 52 的视觉结论。

## 3. Desktop active annotate

直接可见：

- standard `1092.5px` toolbar 被更短的专用 toolbar 替换；
- standard bottom generation panel 完全卸载，没有出现第三个浮层；
- 专用 toolbar 可见关闭+`标注`、`画笔`/`矩形`/`文字`、颜色、线宽、
  `撤销`、`重做` 和 enabled `保存`；关闭按钮在当前 viewport 左侧外自然裁切；
- 选中咖啡馆图片仍在原节点位置，canvas 是透明 overlay，因此底图可见；
- 页面 graph、底部工具栏和整理确认卡没有因 active state 重新布局。

DOM 事实：

```text
toolbar  -120.664,117.717,536,49
node       48,176.717,198.671,99.336
media      48.284,177.001,198.104,98.768
canvas CSS 48.284,177.001,198.104,98.768
backing    396x198
buttons    8
```

## 4. Mobile active annotate

直接可见：

- `536px` 专用 toolbar 仍以 node center 为 anchor，左右自然裁切；
- 工具切换、颜色、线宽、`撤销`/`重做` 和 enabled `保存`仍保持稳定尺寸；
- 节点缩放后 canvas 继续覆盖图片，而不是变成 fixed page overlay；
- 页面没有横向滚动，底部两排 toolbar 和整理确认卡无重叠。

DOM 事实：

```text
toolbar  -184.940,35.077,536,49
node       48,94.077,70.119,35.060
media      48.100,94.177,69.919,34.859
canvas CSS 48.100,94.177,69.919,34.859
backing    140x70
```

## 5. 证据边界

| 类型 | 结论 |
|---|---|
| Clone screenshot fact | toolbar replacement、bottom panel absent、自然裁切、透明 canvas 和无明显重叠 |
| DOM-backed clone fact | rect、8 buttons、DPR2、空态 undo/redo disabled、save enabled、Escape/close、graph immutability |
| Source-backed contract | `536x49`、DPR2、standard panel absent、Escape restore；当前 production chunk 还确认 pencil/rect/text、color、line width |
| Clone decision | 工具/颜色/线宽只作空态壳层；仅 `撤销`/`重做` disabled，`保存` enabled 但无副作用 |
| 未确认 | source exact icon SVG/CSS、非空 stroke、dirty/save/upload/result semantics |

后续若只需回答“Batch 53 画面中有什么”，无需重新打开 PNG。只有代码改变、
viewport 不同或要研究未确认 toolbar icon 时，才新增最小截图和记录。
