# Batch 54 截图识别台账

> 识别日期：2026-08-26
> 来源：本地 LibTV clone 运行态
> 目的：记录本批两张截图的唯一识图结果。后续先读本文，不重复打开
> 相同截图。

## 1. 截图范围

| 文件 | viewport | 状态 |
|---|---:|---|
| [`liblib-clone-batch54-image-element-edit-active-929-2026-08-26.png`](../../design-references/liblib-clone-batch54-image-element-edit-active-929-2026-08-26.png) | `929x874` | selected image 的 element-edit empty state |
| [`liblib-clone-batch54-image-element-edit-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch54-image-element-edit-mobile-390-2026-08-26.png) | `390x844` | mobile element-edit empty state |

两张图都是 clone 截图，不是源站截图。源站合同来自
[`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md) 引用的 live DOM/bundle 归档；
本记录只解释 clone 如何呈现已确认合同。

## 2. Desktop active element edit

直接可见：

- standard `1092.5px` toolbar 和节点下方 generation panel 均不再显示；
- 节点中心上方出现更短的深色专用 toolbar，当前可见的 control 语义是
  关闭、点选、框选、画笔、画笔尺寸和撤销；
- 图片节点仍在原 graph 位置，没有因为进入 active tool 而重新布局；
- 图片 media 上覆盖半透明 editing mask，guide 文案为
  `标记你想要修改的对象`；
- stage 下方是一个宽于图片的空 record panel，显示
  `编辑内容待添加`；
- 没有额外第三个 standard generation layer，也没有对象框、笔迹、结果图
  或 loading card。

DOM-backed geometry：

```text
node         48.000,176.717,198.671,99.336
media        48.284,177.001,198.104,98.768
toolbar      11.336,80.717,272.000,44.000
stage        48.284,177.001,198.104,98.768
mode root    48.284,177.001,198.104,160.764
record panel -52.664,287.760,400.000,50.000
```

空间关系：

```text
toolbar center ~= stage center ~= record panel center
stage top - toolbar bottom ~= 52px
record panel top - stage bottom ~= 12px
```

## 3. Mobile active element edit

直接可见：

- `272px` toolbar 仍以图片节点中心为横向 anchor，顶部和左右部分自然裁切；
- stage 继续覆盖缩放后的图片 media，没有升级成 page-level fixed overlay；
- `400px` record panel 保持稳定 screen size，因此在窄 viewport 中有明显
  左侧裁切；
- 画布底部工具、导航和整理确认卡仍保持原有页面结构；
- 没有观察到 document/body 横向滚动条；
- 空态没有对象识别 contour、record 内容或生成结果。

DOM-backed geometry：

```text
node         48.000,94.077,70.119,35.060
media        48.100,94.177,69.919,34.859
toolbar      -52.940,-1.923,272.000,44.000
stage        48.100,94.177,69.919,34.858
mode root    48.100,94.177,69.919,96.858
record panel -116.940,141.033,400.000,50.000
```

## 4. 证据分层

| 类型 | 本批结论 |
|---|---|
| Clone screenshot fact | standard 双浮层卸载、专用 toolbar、mask/guide、record empty panel、自然裁切和无明显页面重排 |
| DOM-backed clone fact | rect、`272x44`、`400x50`、`52px/12px` 几何、工具切换、brush size、空态 disabled、Escape/close 和 graph immutability |
| Source-backed contract | dedicated toolbar、stage/mask/guide、`编辑内容待添加`、`400x50`、默认点选、空态 undo disabled、Escape restore |
| Clone-only decision | stage 使用本地 `2:1` fixture 的 media ratio；tools 只改变空态 local visual state；generate 保持 disabled |
| 未确认 | source exact icon SVG/CSS、非空 record、对象识别、dirty/save/discard、生成、上传和结果节点 |

若后续只是询问“Batch 54 截图里有什么”，无需重新识别 PNG；只有代码、
viewport、截图内容或研究问题发生变化时，才追加新的最小截图和台账记录。
