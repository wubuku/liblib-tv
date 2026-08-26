# Batch 34 Portability Matrix

> 状态：待完成上游依赖和架构分析后填写。

候选能力将按当前项目边界评估：

| 能力 | 上游依赖 | 当前 LibTV 对应边界 | 适配成本 | 决策 |
|---|---|---|---:|---|
| 导演台工作区 | React UI | `src/app/page.tsx` + `uiStore` | 待评估 | 待定 |
| 对象树/属性面板 | React + Zustand | `canvasStore` + 侧栏/浮层 | 待评估 | 待定 |
| 3D 场景视口 | Three.js / R3F | 当前无 3D runtime | 待评估 | 待定 |
| 镜头/截图记录 | 本地数据模型 | 节点和派生 graph transaction | 待评估 | 待定 |
| 模型/贴图资源 | 上游 public assets | 当前 design references / 本地 mock | 待评估 | 默认不直接复用 |

本文件不会把“能实现”误写成“应该实现”。最终决策需要结合证据、维护成本
和当前 clone 的两条路线边界。

