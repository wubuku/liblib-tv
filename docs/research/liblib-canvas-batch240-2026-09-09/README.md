# Batch 240 — 模型族平价率补全 + 分辨率定价直证 + 模型默认清晰度（源站 2026-09-09 直采）

> 状态：`IMPLEMENTED`（三轮采样 → 表扩展实施 → 16 checks 验收 → 32 项回归绿）。
>
> 环境：外部 Chrome for Testing 147（CDP 9222）；CDP 度量覆盖 1920×2400。
> 证据：`m-*/r3-*` 截图、`sample-log.json`、`round2/round3-log.json`。

## 采样方法（配方沉淀）

- 模型菜单 35 项内部滚动：目标行用 `scroll_into_view_if_needed()` 带入
  可视区后再取 box 点击（batch 238 的 scrollTop=0 配方一般化）；
- **前缀碰撞行**（Minimax H3/H3 Max、Wan 3.0/Prime、Kling 3.0/Turbo、
  Hailuo 2.3/Fast）：按「`t.length - name.length` 最小」选行 = 精确模型行；
- 触发器查找器须**约束页脚 y 波段**并排除百分比/含 `·` 文本（曾误配左下
  缩放控件 217% 与设置芯片）；
- 读取基准：16:9·720P·5s·1个（Auto 与 16:9 同价，batch 238）。

## 源站事实（`SOURCE_FACT`）

### 720P 平价率补全（受控读数，16:9·720P·5s·1个）

| 模型 | 积分 | 速率 |
|---|---|---|
| Minimax H3 Max | 60 | 12/s |
| Wan 3.0 Prime | 45 | 9/s |
| Wan 2.7 | 65 | 13/s |
| Kling O3 | 55 | 11/s |
| Kling 3.0 Turbo | 60 | 12/s |
| Vidu Q2 | 40 | 8/s |
| Vidu Q3 Pro | 50 | 10/s |
| Hailuo 2.3 Fast | 24 | 4.8/s |
| Hailuo 02 | 36 | 7.2/s |

### 分辨率影响积分（首个受控 A/B）

Seedance 1.5 Pro（16:9·5s·1个）：**720P = 40 vs 1080P = 90**（切回可逆）
→ 积分 = 模型平价率 × 分辨率因子 × 时长 × 数量；720P 基准外的因子结构
未采样（`SOURCE_UNKNOWN`）。

### 模型默认清晰度与模式

- 切入 **Seedance 1.5 Pro 即 1080P**（模型默认清晰度）；2.0 系多轮直证
  切换保持当前清晰度；
- **模式保持**：从首帧/图生视频态切换模型不重置模式（图生视频保持）——
  batch 236 的「模型切换重置模式」仅适用于长视频态；
- 触发器标签：**Seedance 1.5 Pro → 「Seedance1.5」**（无空格无 Pro）；
  其余模型显示全名（Minimax H3 Max、Wan 3.0 Prime 等）；2.0 系沿用缩写。

## 实施（`VideoGenerationPanel.tsx`）

1. `MODEL_RATES` 扩至 13 项（+9 模型 720P 速率，含分数速率 4.8/7.2，
   `Math.round` 兜底浮点）；
2. `MODEL_RATES_1080P`：Seedance 1.5 Pro→18、1.0 Pro→15、1.0 Lite→6
   （受控 1080P 读数）；积分公式按当前清晰度查表；
3. `MODEL_DEFAULT_RESOLUTIONS`（1.5 Pro→1080P）+ `selectModel` 应用
   （默认值优先于钳制结果，均在目标列表内才生效）；
4. `MODEL_TRIGGER_LABELS`（Seedance 1.5 Pro→Seedance1.5）。

## 验收

- `verify-liblib-batch240.py`：**16 checks**（6 模型 720P 费率；分数速率
  15s 线性 72；1.5 Pro 默认 1080P/触发器/90；720P↔1080P 可逆 A/B；
  S1.0 Pro 75；回切 2.5 → 230）。
- 回归绿：21 / 22 / 26 / 33 / 100 / 111 / 128 / 141 / 145 / 146 / 149 /
  151 / 155 / 160 / 165 / 166 / 172 / 173 / 174 / 175 / 176 / 177 / 178 /
  189 / 191 / 213 / 215 / 218 / 236 / 237 / 238 / 239（32 项）。
- `npm run check`：0 errors（8 warnings 基线）。
- 源站测试残留清理：**0 节点**。

## 不证明（`SOURCE_UNKNOWN`）

- Pixverse V5.5/V5、OmniHuman 1.5、Style Video、Wan 2.6 积分、Vidu Q2
  清晰度列表（采样中途面板状态漂移未获取；Vidu Q2 参数菜单疑无清晰度区）；
- Minimax H3（区别于 H3 Max）、Wan 3.0（区别于 Prime）、Kling 3.0（区别于
  Turbo）、Hailuo 2.3（区别于 Fast）的速率（round-3 读数缺芯片上下文，
  记为数据点不作表项：Minimax H3 110、Wan 3.0 90、Kling 3.0 55、
  Hailuo 2.3 36、Happy Horse 1.1 100）；
- 480P 定价、Auto/16:9 等价性在 1080P 下的推广、模式（图生/全能参考）
  对定价的影响。
