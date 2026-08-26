# Batch 51：普通画布图片顶部工具条几何 parity

> 状态：已完成（2026-08-26）。本批只处理标准图片选中态的顶部
> `ImageToolbar` host 几何，不扩展图片工具态或真实生成能力。

## 目标

```text
selected image
  -> source-confirmed screen-space top host
  -> node center horizontal anchor
  -> zoom-aware vertical gap
  -> existing node-internal bottom editor remains unchanged
```

## 文档入口

- [`PLAN.md`](PLAN.md)：缺口、证据、范围和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：已复用的源站事实、clone 差异和本轮无法新增的 freshness 证据；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证、截图台账和接力记录。

## 本批决定

- 保留 React Flow `NodeToolbar`，只把 `offset` 从固定值映射为
  `10 + 24 * viewportZoom`；
- 保留图片底部面板的节点内 `scale(1 / zoom)` 与 `16 * zoom` gap；
- 保留源站允许的自然裁切，不增加 viewport clamp 或自动避让；
- 不把 `元素编辑`、`图层分离`、`标注`、`旋转`、`下载`、`预览` 的入口
  伪装成已实现行为；
- 不因当前环境没有可调用的有头浏览器控制工具而声称完成新的
  LibTV authenticated freshness reinspection。

## 边界

本批验证的是 clone-owned DOM 几何和回归合同。它不证明：

- Director shell 与 LibTV 源站 source-exact；
- 图片工具条当前 action set 已全部复刻；
- active image tool 的保存、任务、graph mutation 或权限流程；
- 真实 Provider、上传、下载、水印和远程持久化。
