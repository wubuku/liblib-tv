# Batch 23 计划：片段重拍时间带与 Prompt 编辑器

## 1. 缺口与价值

| 缺口 | 当前 clone | 源证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 时间带层级 | 放在编辑器内部 | 独立位于编辑器上方 | 5 | 拆成独立层 |
| 标题栏 | 自创“片段重拍”标题、计数和关闭 | 流程图无该标题栏 | 5 | 移除 |
| Prompt 结构 | 纯文本投影 | 视频 token + range chip + 用户意图 | 5 | 重建 |
| 参考视频 | 只有时间带图片 | Prompt 区有源视频缩略项 | 4 | 增加 |
| 空意图提交 | disabled | bundle 明确“留空 = 原样重跑一次” | 5 | 允许提交 |
| 生成器命令 | 缺失 | `参考 / 标记 / 角色库` 与展开命令 | 4 | 增加 |
| Footer | 简化为两项参数 | 模型、清晰度/数量、音频与积分反馈 | 4 | 对齐层级 |
| 后端结果 | 本地确认 | 当前项目无可用源视频，未真实提交 | 5 | 保持 mock 边界 |

该动作是 Seedance 2.5 的近期主推工作流，也是当前 clone 中“行为已做、结构却明显脑补”的高价值区域。

## 2. 实施步骤

1. 重构 `SegmentReshootPanel`：
   - 外层继续使用节点相对定位与 `1 / zoom` 反缩放；
   - `660px` 宽度不变；
   - 上层独立 filmstrip，编辑器在其下方；
   - 移除内部标题栏。
2. Filmstrip：
   - 7 个可选 `4.0s` 区间；
   - 最后 `2.0s` remainder disabled；
   - selected 区间使用 cyan outline 和 `4.0s` badge；
   - 右侧显示 `{current}/5 个片段`。
3. Editor：
   - 顶部 `参考 / 标记 / 角色库` 与展开按钮；
   - 源视频 reference tile；
   - 有选择时显示视频 token 和 `00:00-00:04` range chip；
   - 无选择时显示整段重跑 helper；
   - 用户意图与 token 分层呈现。
4. Footer：
   - Seedance 2.5、`720P · 1个`、音频状态；
   - 本地积分占位与 submit；
   - 空意图可提交，反馈区分整段重跑与选段重拍。
5. 新增稳定 selectors 和 Batch 23 Playwright：
   - ready video 创建；
   - filmstrip/editor 分层和 geometry；
   - `0/5 -> 1/5 -> 5/5`；
   - range token；
   - 空意图提交；
   - 输入意图提交；
   - 390px 自然裁切、页面无 overflow、console/page error。

## 3. 事实边界

### Source fact

- 文章流程图显示四个连续状态：`0/5`、选择首个 `4.0s`、自动插入 range token、输入修改意图并提交。
- 时间带和 Prompt editor 是两个分开的 surface。
- editor 顶部可见 `参考 / 标记 / 角色库` 和展开命令。
- Prompt 区可见源视频缩略项、视频 token 与 `00:00-00:04` range chip。
- 当前线上 bundle 明确：
  - 源视频至少 4 秒；
  - 最多 5 个片段；
  - 未选择时编辑整段视频；
  - `留空＝原样重跑一次`。

### Inference

- 流程图是 `1104x886` 的四状态拼图，不保留原始 DOM 尺寸；不能从该图声称 editor 的精确 source rect。
- clone 延续已验证的 `660px` video panel 锚定合同。
- editor 高度和 filmstrip 间距按截图比例与现有画布密度做 source-shaped 校准，不写成原站 DOM 值。

### Clone-only decision

- 使用仓库本地静态图模拟连续缩略时间带。
- submit 只产生本地“已创建任务”反馈。
- 不实现真实视频裁剪、真人校验、Seedance 调用、积分扣除或结果节点。
- `智能续写` 共享组件但不纳入本批 source fidelity 声明。

## 4. 验收标准

- filmstrip 与 editor 为两个独立可测 surface。
- editor 内不再出现 clone-only 标题栏。
- 首个 `4.0s` 片段选中后出现 `视频 1` 与 `00:00-00:04`。
- 最多选择五段，第六次选择不增加计数。
- 空意图 submit 可用并产生整段重跑本地反馈。
- 有区间和意图时产生选段重拍本地反馈。
- Batch 9、15、21、22、23 与完整工程门禁通过。

