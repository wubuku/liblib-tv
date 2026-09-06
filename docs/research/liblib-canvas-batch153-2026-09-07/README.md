# Batch 153 — 采样第三轮：Auto 积分因子证实 + 节点面板行为边界（源站 2026-09-07）

## 采样方法突破

`tell application id "com.google.chrome.for.testing" to activate`（Chrome 自身
AppleScript 字典）可成功请求前置（System Events 路径会挂起）。激活后
`visibilityState=visible`，纯状态更新采样恢复。但 macOS 窗口遮挡跟踪器仍对
实际被遮挡的窗口限流 floating-ui 的 rAF → **菜单仍无法打开**；屏幕录制权限
未授予，无法用桌面级工具聚焦窗口。菜单类采样（模型菜单选中样式、300s 参数
展开、尝试取消联动）继续阻塞。

## 源站事实（第三轮）

### 1. Auto 比例积分因子证实（第 5 个数据点）

某尝试已选节点面板：`2.5 / 全能参考 / Auto · 720P · 5s · 1个` → 积分 **230**
= 5 × 46。Batch 135 的 Auto→46/s 校准在源站直接数据点上成立。

### 2. 积分块类名逐字吻合（Batch 151 实施验证）

源站积分块容器类 `min-w-[85px] justify-end text-fg-muted flex h-8 items-center
gap-2`、数值 `text-[12px] font-normal leading-[15px] text-fg-muted` —— 与
Batch 151 落地实现一致（等价 Tailwind）。

### 3. 节点面板行为边界

- **新建视频节点**（添加面板 → 视频）：选中后**无面板、无尝试建议** —— 面板
  只出现在有生成状态的节点上。
- 尝试建议列只在预设分组承载节点（622 宽）的「未选模式」状态出现；
  尝试已选节点直接打开面板（配置 2.5/全能参考/Auto·720P·5s）。
- 结论：clone 的常驻尝试行是 CLONE_DECISION（承载唯一采样过的芯片行为）；
  源站的「分组承载节点 → 一次性建议 → 面板」完整流需要分组/预设机制支撑，
  暂不重构。

### 4. 测试残留

本轮在测试项目内新建了一个视频节点（授权范围内可随意操作、用完删除）；
右键菜单依赖真实 OS 级交互，暂无法删除，随测试项目一并处理。

## 验收

- 文档/矩阵更新 batch；无代码行为变更（clone 积分公式与 Auto 因子已一致，
  batch135/149/151 回归保持绿）。
- `npm run check`：0 errors、8 warnings（既有基线）。
