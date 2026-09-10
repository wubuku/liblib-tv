# Batch 314 — CDP 原生全点击序列亦失败：菜单末两行最终定论 BLOCKED（源站 2026-09-11）

> 状态：`BLOCKED_AUTOMATION_FINAL`（五次跨批尝试穷尽；无代码变更）。
>
> 证据：`cdp-log.json`、`StyleVideo.png`、`Kling3.0动作迁移.png`。

## 本轮结果

- 完整 CDP `Input.dispatchMouseEvent` 序列（mouseMoved 预热 +Pressed
  +Released）驱动菜单末两行点击：**Style Video 与 Kling3.0 动作迁移
  均未切换**（页脚保持长视频态 14700）；
- 附带：面板状态被图片节点（1080×1446，尺寸徽章被触发器探针误配）
  干扰——探针bookkeeping 受多节点画布影响。

## 最终判定（batch 243 / 259 / 272 / 314 四配方汇总）

| 配方 | 结果 |
|---|---|
| scrollIntoView + Playwright 点击 | 失败 |
| 最小额外长度行匹配 + 再定位 | 失败 |
| 菜单容器 scrollTop 手动定位 | 失败 |
| **CDP 原生全点击序列** | **失败** |

**Style Video 与 Kling3.0 动作迁移费率最终定论 BLOCKED_AUTOMATION**
（35 模型中 33 项已有费率/数据点；此 2 项需人工采样）。

## 附带发现

- 多节点画布下触发器探针会被图片节点尺寸徽章（1080×1446）误配——
  后续探针需按面板上下文过滤；
- 清理遇阻时 reload-then-clean 规则再次生效。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
