# Batch 33 Screenshot Analysis Ledger

> 本文已记录对长视频文章截图的一次性完整识别。后续 Agent 在现有问题范围
> 内不得重复打开整图；先读本页，只在出现新问题时检查最小裁剪。

## Source Screenshot

| Field | Value |
|---|---|
| Path | `docs/research/liblib-seedance-2.5-2026-08-25/evidence/long-video-generation-graph.png` |
| Source | 外部 LibTV Seedance 2.5 调研文章 |
| Evidence class | `article-screenshot` |
| Pixel size | `1080x1504` |
| SHA-256 | `70cb23486fd369852c02e21ca744cbf2d483b6890d4e3eeb0a8f589042af30af` |
| Inspection date | `2026-08-26` |
| Login-state DOM | 否 |

## One-Time Recognition Result

- 画面主体是深灰色大画布，而非 modal、drawer 或生成输入面板；
- 左侧是多列输入素材和镜头图片：
  - 多张角色多视图素材；
  - 山水、院落、室内等场景图；
  - 多个带 `Sxx` 标识的镜头卡；
- 输入素材与镜头卡之间存在大量多对多连线；
- 中部有小型深色配置/处理节点；
- 中右部有两组横向候选生成结果，每组可见上下两张画面；
- 候选结果继续汇聚到右侧处理节点；
- 最右侧是横向最终成片卡；
- 画面表达“素材 -> 镜头 -> 批次候选 -> 拼接/成片”的画布过程；
- 截图中文字多数不可辨认，不能把具体标签、节点数量、精确尺寸或后端拆分
  协议写成事实。

## Layer And Relationship Notes

```text
left
  input materials
    -> shot cards
      -> small process/config nodes
        -> candidate batch A / B
          -> merge/process
            -> final horizontal video
right
```

连线密度是重要视觉事实：它表达素材被多个镜头复用，而不是单一线性步骤条。
候选区和最终区之间也有明确汇聚关系。

## Classification

| Observation | Classification |
|---|---|
| 大画布、素材/镜头/候选/最终层级 | direct article screenshot fact |
| 多对多连线和候选汇聚 | direct article screenshot fact |
| 具体节点业务名称 | unresolved / illegible |
| 精确节点数、尺寸、间距和边端口 | unresolved |
| “提交应创建 graph transaction” | product-flow inference |
| 本批的 3/3/4/1/1 节点数量 | clone calibration |
| 本地 pending 状态和 metadata | clone-only prototype |

## Reinspection Policy

只有以下情况允许重新检查图像：

1. 需要回答此前未记录的局部图标或颜色问题；
2. 获得更清晰原图，需要核对同一区域；
3. 登录态原站成功触发过程图，需要做 source-vs-article 对照。

届时只打开最小必要裁剪，并把新增观察补写到本文件。

## Clone Evidence Result

Batch 33 专项脚本生成了：

- 长视频提交前参数状态；
- 提交 busy 状态；
- 画布过程图 fit-view；
- 重复批次避让；
- atomic undo/redo；
- `390x844` 响应式裁切；
- 一张 contact sheet。

一次性视觉检查结论：

- `process graph` 在清除 source selection 后 fit-view，完整展示 source、
  三列素材/镜头、两批候选、汇聚节点和最终成片；
- source -> shot、material -> shot 和 candidate -> assembly 的连线密度能
  表达文章截图中的多对多过程，而不是旧的线性四步卡；
- candidate 与 final 的缩略图被压暗并覆盖 `等待生成` / `等待拼接`，没有把本地
  咖啡馆图片误标为本次已完成生成；
- 提交后的 source selection 会保留，因此 source 下方生成面板仍然可见；截图
  专门在视觉检查前清 selection，避免编辑面板遮挡 graph；
- mobile 截图保持节点浮层的自然裁切，不产生 document 横向 overflow。

这些 clone 截图只能证明实现和回归，不能升级为原站事实。
