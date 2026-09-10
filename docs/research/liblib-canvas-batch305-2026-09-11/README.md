# Batch 305 — clone 筛选联动取舍决策入档（源站 2026-09-10 对照）

> 状态：`DECISION_RECORDED`（保留 + CLONE_DECISION 标注入码；无行为
> 变更）。
>
> 依据：batch 304 的混合类型对照发现（源站筛选选择后列表全显不过滤）。

## 决策：保留 clone 筛选联动

clone 抽屉的 类型筛选→列表过滤 联动（batch 205 合同）**保留**：

1. **原型可用性**：本地 mock 数据下，过滤联动使抽屉具备真实管理
   功能；移除后抽屉列表不可管理，可用性倒退；
2. **合同成本**：移除将作废 batch 205 的 8-check 合同与 batch 102 的
   联动断言，回归面大于收益；
3. **先例一致**：batch 153 的「常驻尝试行」同为超出源站的
   CLONE_DECISION 附加行为，先例为保留并标注。

## 落地

`AssetManagerPanel.tsx` 类型菜单注释补入 batch 305 标注（源站不过滤
+ CLONE_DECISION 保留），语义就地可查。

## 验收

- typecheck 通过；`npm run check` 0 errors（8 warnings 基线）；
  docs check 通过；无源站操作。
