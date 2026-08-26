# Batch 49 成熟度评估

## 结论

Batch 49 已达到 **clone-owned Director 视口方向控件** 的成熟有界原型
状态：

```text
主 R3F 相机 snapshot
  -> 独立 gizmo canvas
  -> 六个可访问 DOM 轴向命中区
  -> 离散 Director 视角切换
```

它没有达到“当前 LibTV 源站精确复刻”的证明标准。当前可确认的是
clone 行为、固定上游的可借鉴结构和本地浏览器验证；LibTV authenticated
source 的 renderer、DOM、CSS、拖拽 gizmo 和相机持久化仍是未知或未覆盖。

## 已关闭合同

- Director 和 Camera 两种视角都显示独立坐标反馈；
- 六个方向按钮拥有稳定 selector、`aria-label` 和 title；
- 方向按钮只改变 clone-local Director camera snapshot；
- Camera mode 点击方向后回到 Director mode，不修改 active camera 对象；
- 轴向投影位置随当前相机变化，前后轴在重合时按深度排序；
- path drawing、phone recording 不会被 gizmo 命中层抢走；
- capture/export 不把 gizmo overlay 带入截图输出；
- desktop/mobile overlay 保持在 viewport 内且无水平溢出；
- main R3F canvas 与 gizmo R3F canvas 均通过非空像素检查；
- focused Playwright 已覆盖浏览器错误、相机方向、selection、timeline、
  capture 和 responsive 边界。

## 明确不声明

- 不声明 LibTV 使用和上游相同的 Three.js/R3F 实现；
- 不声明上游 80×80px、20px offset、15×15px hit button 是 LibTV
  authenticated source 的精确几何；
- 不实现拖动 gizmo、面/角点选择或自由旋转；
- 不把方向切换写入 camera object、timeline keyframe、graph history 或
  远端项目；
- 不实现真实 FBX/OBJ/GLB loader、环境资产、远端模型库或 source persistence；
- 不把 clone screenshot 当作 source screenshot。

## 残余风险

| 风险 | 当前原因 | 触发条件 |
|---|---|---|
| source exactness | 当前 source evidence 没有 authenticated gizmo DOM/CSS | 取得安全的源站方向控件 DOM/截图样本 |
| gizmo 连续操作 | 本批只有六个离散方向命令 | 源站证据确认拖动/面/角点交互 |
| camera authoring 关系 | 方向切换是 viewport-only snapshot | 源站确认是否创建 camera shot/keyframe |
| focus/keyboard ownership | 当前按钮有键盘可访问性，但 Director shell 未统一 focus contract | 下一批研究 Director panel/keyboard lifecycle |
| layout integration | 侧栏打开时仍使用固定右上角 clone calibration | 源站或上游证据要求 panel-aware reposition |

## Director 总体成熟度判断

Batch 35-49 已覆盖真实 R3F 视口、timeline、motion path、camera follow/
preset、phone vcam、pose、groups/crowd、capture gallery、model library、
local model descriptor 和 viewport gizmo。作为前端原型，这些已形成较完整
的纵向闭环；作为 LibTV source-exact clone，仍受 source DOM、真实资产、
远程任务和持久化证据限制。

因此下一批仍保持 Director 优先，选择低风险但高频的
**workspace shell keyboard/focus 与面板折叠关系**，先做研究和 clone
delta 盘点；只有该 slice 的 source evidence 不足时才回到普通画布的
授权队列。

## 证据入口

- [`DIRECTOR_VIEWPORT_GIZMO.spec.md`](DIRECTOR_VIEWPORT_GIZMO.spec.md)
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
