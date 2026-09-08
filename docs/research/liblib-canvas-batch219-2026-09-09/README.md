# Batch 219 — 剧本预填内容采样（部分完成，prefill 保持「剧本」）

## 尝试与发现

- 目标：采集源站「故事脚本生成」芯片成对创建时 text 节点的完整预填
  「剧本」markdown 内容。
- 空画布芯片可开（Batch 206 已证），选中态 text 节点 textContent 含
  `markdown-content` CSS 类——即渲染层含样式块，真实 prefill 文本被
  渲染层包裹无法从 textContent 直接提取。
- 尝试从 textarea `value` 读取：text 节点的 textarea 仅在编辑态
  （双击进入）出现——未采样到编辑态。
- 处置：clone 预填维持「剧本」（与 Batch 206 截图文本开头一致），
  完整 markdown 留待后续双击编辑态采样。

## 清理

- 源站测试节点全部删除（0 残留）。

## 验收

- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：完整「剧本」markdown 预填内容；script-v2 双击编辑器入口。
