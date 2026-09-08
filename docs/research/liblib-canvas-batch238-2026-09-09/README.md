# Batch 238 — 模型平价率定价决定性直证 + 2.0 Mini 数据（源站 2026-09-09 直采）

> 状态：`IMPLEMENTED`（决定性采样 → 公式重构 → 11 checks 验收 → 30 项回归绿）。
>
> 环境：外部 Chrome for Testing 147（CDP 9222）；CDP 度量覆盖 1920×2400。
> 证据：`t4-decisive-169.png`、`hover/afterdown-*` 截图、`sample-log.json`、
> `phase2-log.json`。

## 决定性源站事实（`SOURCE_FACT`）

### 2.5·16:9·5s = 230（同会话双向 A/B，t4 截图）

菜单滚动修复后成功切到 2.5：

| 读数 | 积分 |
|---|---|
| 2.5 · Auto · 720P · 5s · 1个 | 230 |
| 2.5 · **16:9** · 720P · 5s · 1个 | **230** |
| 2.5 · Auto（切回） | 230 |

比例切换生效（芯片标签变 `16:9 · 720P · 5s · 1个 ·`）而积分不变 →
**2.5 模型内比例同样不影响单价**。

### 模型平价率定价模型（最终确立）

| 模型 | 平价率 | 数据点 |
|---|---|---|
| Seedance 2.5 | **46/s** | 230/5s（双比例）、690/15s |
| Seedance 2.0 VIP | **27/s** | 405/15s、135/5s（batch130 读数重新归属） |
| Seedance 2.0 Fast VIP | **22/s** | 110/5s（双比例，batch 237） |
| Seedance 2.0 Mini | **16/s** | 80/5s（16:9） |
| 超长视频管线 | 49/s | 14700/300s（batch 176 复认） |

- Batch 130 的「比例影响积分」（135 vs 230）**彻底归因于模型混淆**：
  135 = 2.0 VIP 态 27×5，230 = 2.5 态 46×5，两读数分属不同模型；
- 其余模型族未采样（`SOURCE_UNKNOWN`），clone 按 27/s 缺省。

### 2.0 Mini 补采

- 清晰度列表 **[480P, 720P]**（与 Fast VIP 同为 2 项）；
- 触发器标签 **「2.0 Mini」**（clone 的 `replace(/ VIP$/)` 规则天然正确）；
- 平价率 16/s。

### 采样根因诊断（方法学沉淀，hover 截图）

- **模型菜单打开时滚动定位到当前选中模型**：Seedance 2.5 行被滚出可视区
  （DOM 存在、`getBoundingClientRect` 返回裁剪前位置）→ 点击落在别的行。
  修复配方：先对滚动容器 `scrollTop = 0` 再找行点击。这解释了 batch 237
  全部行点击失效而 batch 236 偶然成功（当时选中模型恰在顶部）。
- clone 验证器注意：参数菜单上部的比例瓦片可能与节点浮动工具栏 z 序重叠，
  菜单内点击用 `force=True`。

## 实施（`VideoGenerationPanel.tsx`）

1. **`MODEL_RATES` 平价率表**：`credits = isLongVideo ? duration*49 :
   duration*count*(MODEL_RATES[model] ?? 27)`；「16:9 恒 27」合并式废止，
   batch 236/237 的两段过渡公式被本表替代。
2. `MODEL_RESOLUTIONS` 增补 2.0 Mini（2 项）。
3. 迁移 **batch149/151** 默认态断言 135→230（16:9·5s 在 2.5 下的源站真值；
   135 重新归属 2.0 VIP 态 27×5），附迁移说明。

## 验收

- `verify-liblib-batch238.py`：**11 checks**（默认 230；21:9/16:9 双向
  比例无关；Mini 标签/80/2 项清晰度；VIP 135；回切 230；Fast VIP 110）。
- 回归绿：21 / 22 / 26 / 33 / 100 / 111 / 128 / 141 / 145 / 146 / 149 /
  151 / 155 / 160 / 165 / 166 / 172 / 173 / 174 / 175 / 176 / 177 / 178 /
  189 / 191 / 213 / 215 / 218 / 236 / 237（30 项）。
- `npm run check`：0 errors（8 warnings 基线）。
- 源站测试残留清理：**0 节点**。

## 不证明（`SOURCE_UNKNOWN`）

- 其余 30 个视频模型的平价率与清晰度列表（Minimax/Wan/Kling/Vidu/Hailuo
  /Pixverse/Happy Horse/OmniHuman/Style/1.x 系）；
- 平价率的清晰度/音频维度依赖（现有读数均在 720P·关闭音频态）；
- 首帧自动图片节点流的素材来源机制（batch 237 记录，待复刻评估）。
