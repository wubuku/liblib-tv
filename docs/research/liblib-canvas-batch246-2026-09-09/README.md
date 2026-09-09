# Batch 246 — batch125 WIP 收尾：`.first` 节点选择歧义根因与修复

> 状态：`IMPLEMENTED`（batch 245 WIP → 根因实锤 → 修复 → batch125
> 22 checks 全绿 → 12 项视频面板回归绿）。

## 根因实锤（batch 245 遗留的 `firstframe:destroy-reverts` 未决）

batch125 用 `.react-flow__node-video` **first** 选择节点——预设画布自带
1 个视频节点（`v-UGQZzZOpbv`，DOM 首位），**`.first` 命中的是预设节点**
而非新建节点。预设节点图中已有既有 image→video 边，导致：

1. **首帧提交被守卫跳过**：`createFirstFrameReference` 的 `hasImageRef`
   防重守卫检测到既有入边图片节点 → 不创建（提交前后 11/11 不变），
   但面板仍进入首帧态（槽/说明文案照常渲染）；
2. **销毁误拆预设边**：`destroyFirstFrameReference` 找到并移除的是
   **预设的**图片节点与连线（节点 11→10、边 11→**8**，连带 3 条边）。

## 修复（`verify-liblib-batch125.py`）

选择器改为 **`.last`**（= 添加面板新建的节点，图状态干净、语义即
batch 125 的测试主体），附根因注释。无产品代码变更。

## 验收

- `verify-liblib-batch125.py`：**22 checks 全绿**（attempts 三芯片
  选择/重击保持、首帧面板断言、销毁回退、placeholder/工具行/生成流）。
- 视频面板回归组绿：125 / 149 / 160 / 176 / 177 / 178 / 236 / 237 /
  238 / 239 / 240 / 244。
- batch 245 记录的其余老化门（batch6/14/19/57/61/64/97）维持
  「先于本会话」结论不变。
