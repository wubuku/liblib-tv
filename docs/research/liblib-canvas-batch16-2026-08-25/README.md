# Batch 16：画布下拉与项目元数据生命周期

> 日期：2026-08-25
> 范围：LibTV clone 顶部画布入口、项目名和多画布导航操作。
> 目标：把项目上下文和画布 CRUD 放回同一个可发现、可收口的导航生命周期。

## 当前缺口

- `TopNavBar` 的项目名是组件局部 state，组件重建后会丢失，且没有进入 `canvasStore`。
- `CanvasTabDropdown` 只显示“画布”标题，缺少原站下拉中的“当前项目 / 项目名”层级。
- 新建、切换、复制、删除、重命名完成后没有统一关闭下拉，菜单容易残留在旧上下文上。
- 画布下拉和项目名没有一组稳定的自动化 selectors，后续 agent 只能依赖可见文字。

## 证据入口

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站画布下拉截图的单次识图台账。
- [`CANVAS_METADATA.spec.md`](CANVAS_METADATA.spec.md)：本批 UI/状态合同。
- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)：原站高价值缺口排序中对画布下拉 CRUD 的审计结论。
- [`../../design-references/liblib-original-canvas-menu-2026-08-25.png`](../../design-references/liblib-original-canvas-menu-2026-08-25.png)：原站菜单证据。

## 边界

- 项目名和画布数据只进入浏览器内存，不伪造服务端保存、协作同步或刷新恢复。
- 新建、切换、重命名、复制、删除继续复用已有 `canvasStore` 语义；本批只修正生命周期和可发现性。
- 原站截图未显示行级更多菜单的展开态，因此不重写重命名/复制/删除菜单的未证实视觉，只保证其动作收口。

## 导航

- [`PLAN.md`](PLAN.md)
- [`CANVAS_METADATA.spec.md`](CANVAS_METADATA.spec.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
