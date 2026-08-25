# Batch 21 计划：Seedance 视频参数 Dialog

## 1. 缺口与价值

| 缺口 | 当前 clone | 原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 普通 dialog 高度 | `341x299.3` | `341x445` | 5 | 修复 |
| 超长 dialog 高度 | `341x267.3` | `341x397` | 5 | 修复 |
| 水平位置 | 相对 panel left `+149.8` | 普通 `+82.0`、超长 `+90.0` | 4 | 按模式校准 |
| 比例输入 | 小文字 pills | 7 个带比例 glyph 的卡片 | 4 | 重建卡片 grid |
| 时长输入 | 只有 slider 和 min/max | label、当前值框、slider | 5 | 重建 |
| 音频/数量 | 紧凑内联 segmented | 整宽二段/三段控件 | 4 | 重建 |
| 超长说明 | 无 | slider 下有时长设计说明 | 4 | 增加 source-shaped copy |
| 模型菜单 | 只有四项，原站截图显示更多模型 | 没有本批精确 DOM rect/list extraction | 3 | 留待后续专项 |

## 2. 实施步骤

1. 为 video footer model/mode/params/advanced controls 增加稳定 `data-*` selectors。
2. 重建 `ParamsMenu`：
   - normal `341x445`
   - long `341x397`
   - `bottom: 32px`，贴合 trigger 顶边
   - normal 相对当前 params trigger `left: -68px`
   - long 相对当前 params trigger `left: -60px`
3. 比例改为 5+2 卡片 grid，保留：
   - `Auto`
   - `16:9`
   - `4:3`
   - `1:1`
   - `3:4`
   - `9:16`
   - `21:9`
4. 清晰度使用三段整宽选择。
5. 时长增加当前值框，slider 继续用 `onInput`。
6. 音频和数量使用整宽 segmented；long 模式隐藏数量并显示时长说明。
7. 新增 Batch 21 Playwright：
   - normal/long dialog geometry
   - ratio/resolution/duration/audio/count controls
   - disabled mode state
   - `300s / 14700`
   - node/panel anchor不变
   - 390px 自然裁切和页面 overflow
   - console/page error
8. 更新视频参数组件规格、Harness、Big Picture 和 Changelog。

## 3. 事实边界

### Source fact

- normal dialog rect：`x=541.320, y=90.961, w=341, h=445`。
- long dialog rect：`x=549.305, y=138.961, w=341, h=397`。
- normal 参数包含比例、清晰度、`4-30s`、生成音频、生成数量。
- long 参数包含比例、清晰度、`30-300s`、时长说明和生成音频；没有生成数量。
- ratio/resolution/audio/count 的选项集合来自当前登录原站。

### Inference

- 相对 generation panel：
  - normal `left + 82.0`, `top - 211.7`
  - long `left + 90.0`, `top - 163.7`
- clone 当前 trigger 布局下，用 `left: -68/-60px; bottom: 32px` 可复现该相对几何。
- glyph 的具体 SVG path 未提取；本批使用 CSS aspect-ratio outline 表达同一语义。

### Clone-only decision

- 继续使用 component-local state，不写入项目持久化。
- 积分只是原站参数的本地估算显示，不产生计费。
- 不补齐模型菜单的完整模型清单，避免只凭截图中可见部分声称完整。

## 4. 验收标准

- normal dialog 约 `341x445`，相对 panel 几何符合 source contract。
- long dialog 约 `341x397`，相对 panel 几何符合 source contract。
- 七个 ratio cards、三段 resolution、duration value/slider、audio 和 normal count 均可交互。
- 切到 long 后范围为 `30-300s`、count 消失、说明出现。
- 拖到 `300s` 后 footer 显示 `300s`，积分显示 `14700`。
- Batch 9 anchor regression、Batch 21 专项、`npm run check` 和 docs check 全部通过。

