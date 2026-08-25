# Batch 22 计划：Seedance Source-visible 模型菜单

## 1. 缺口与价值

| 缺口 | 当前 clone | 原站截图 | 价值 | 决策 |
|---|---|---|---:|---|
| 菜单尺寸 | `330x216` | 约 `380x410` | 5 | 修复 |
| 模型数量 | 4 | 截图可见 7 | 5 | 使用 source-visible 集合 |
| 错误模型 | `Kling O3` | 截图未出现 | 5 | 移除 |
| 缺失模型 | Fast/Mini/Wan Prime/Wan | 截图可见 | 5 | 增加 |
| 行层级 | 4 行全部显示说明 | 仅选中行展开说明 | 4 | 重建 row state |
| Premium 标识 | 无一致语义 | 前五项显示金色 diamond | 3 | 使用 icon 表达 |
| 完整模型库 | 当前代码暗示列表完整 | 截图底部边界不能证明完整 | 4 | 文档明确 source-visible |

## 2. 实施步骤

1. 将 `modelItems` 改为 source-visible 七项：
   - Seedance 2.5 / `2min`
   - Seedance 2.0 VIP / `2min`
   - Minimax H3 / `2min`
   - Seedance 2.0 Fast VIP / `2min`
   - Seedance 2.0 Mini / `2min`
   - Wan 3.0 Prime / `1min`
   - Wan 3.0 / `3min`
2. 前五项显示 gold premium icon；Wan 两项不显示。
3. menu：
   - `380x410`
   - 相对 generation panel `left≈0`
   - `top≈-176.7`
   - trigger-relative `left:-9px; bottom:32px`
4. 非选中行保持单行 title + estimate；选中行增加 surface、border 和已确认 description。
5. 为 trigger/menu/options/premium/description 增加稳定 selectors。
6. 新增 Batch 22 Playwright：
   - geometry
   - 七项顺序、estimate、premium count
   - `Kling O3` 不存在
   - 2.5 与 Fast 选择/展开
   - params dialog 切换仍可用
   - 390px overflow、console/page error
7. 更新组件规格、Harness、Big Picture 和 Changelog。

## 3. 事实边界

### Source fact

- 截图可见七个模型及其 estimate。
- 前五项有金色 diamond，Wan 两项没有。
- 截图状态中 `Seedance 2.0 Fast VIP` 被选中并展开：
  - `最强视频模型快速版，会员专属通道，15s音画同步`
- `Seedance 2.5` 当前 live 文案：
  - `最强视频模型，全能参考，30s音画同步`

### Inference

- 聚焦 crop 和像素边缘反推外框约为：
  - `x≈458, y≈126, w≈380, h≈410`
- 相对 source generation panel 约为 `left 0`, `top -176.7`。
- clone trigger 布局使用 `left:-9px; bottom:32px` 复现该相对位置。

### Clone-only decision

- 使用 Lucide/CSS icon 近似模型 logo 和 premium diamond，不声称 SVG path 相同。
- 对没有可靠说明文案的模型，选中时只保留高亮，不补写描述。
- 七项命名为 source-visible，不宣称完整、实时或可调用。

## 4. 验收标准

- menu 约 `380x410`，左边与 generation panel 对齐。
- 七项顺序和 estimate 与截图一致。
- 前五项 premium icon 可见，Wan 两项无 premium。
- `Kling O3` 不存在。
- 默认 2.5 与选择 Fast 后，只有当前选中项显示 description。
- Batch 9、21、22 与完整工程门禁通过。

