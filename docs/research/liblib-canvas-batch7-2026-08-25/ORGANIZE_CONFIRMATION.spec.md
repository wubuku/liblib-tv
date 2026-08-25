# Organize Confirmation Spec

## 1. 原站截图直接事实

参考：`docs/design-references/liblib-original-organize-preview-2026-08-25.png`。

- 固定在画布左下，而不是底部居中；
- 文案为“是否保留此次整理结果？”；
- 第二行是“还原”“保留”两个按钮；
- “保留”为浅色实心按钮；
- 卡片位于左侧画布控制上方，不覆盖中央主工具条；
- 截图中外框约 `168px` 宽，左边约 `49px`，底边约距视口 `53px`。

截图压缩和阴影使高度边缘不够稳定，因此实现以约 `88px` 外框和两行内容为目标，不把单像素测量登记为 DOM 原始事实。

## 2. Clone 几何

### 桌面与平板

```text
position: fixed
left: 49px
bottom: 53px
width: 168px
min-height: 88px
z-index: 72
padding: 12px
border-radius: 10px
```

### 移动端

原站移动端整理确认态尚无直接截图。为避免与两组底部工具重叠，clone 使用：

```text
left: 12px
bottom: 106px
```

这项是响应式实现决策，不描述为原站事实。

## 3. 内容结构

```text
confirmation card
├── question
└── actions
    ├── 还原
    └── 保留
```

- 问题独占第一行；
- actions 右对齐；
- 两个按钮高度 `32px`；
- “还原”为透明按钮；
- “保留”为浅灰实心按钮；
- 按钮使用现有文案，不增加说明文字或图标。

## 4. 状态与交互

- 整理后显示；
- 点击“还原”：恢复整理前节点和 viewport，关闭卡片；
- 点击“保留”：保留整理位置，关闭卡片；
- 再次触发整理会覆盖旧预览快照；
- 卡片不使用 modal backdrop，不阻塞画布其他区域；
- 自动化通过 `data-organize-confirmation` 定位，不依赖文案模糊匹配。

