# Batch 16 实施结果：画布下拉与项目元数据生命周期

## 1. 实施内容

- `canvasStore` 新增项目级 `projectName` 与 `setProjectName`：
  - 与单个 `CanvasData.name` 分离；
  - 提交时 trim；
  - 空字符串不会覆盖当前项目名。
- 移除 `TopNavBar` 中独立、局部的项目名 pill；项目上下文统一进入画布下拉。
- `CanvasTabDropdown` 按原站截图重组：
  - `当前项目` 和可编辑项目名；
  - `画布` 标题和纯加号命令；
  - 当前画布置顶并显示右侧勾选；
  - 保留现有 rename/copy/delete 更多菜单。
- 新建、切换、重命名、复制、删除完成后统一关闭下拉。
- 外部点击和 `Escape` 会关闭菜单，并清理局部编辑/更多菜单状态。
- 增加 `data-canvas-*` selectors 和 Batch 16 Playwright 合同。

## 2. 证据边界

### Source fact

- 原站截图直接支持项目区块、画布区块、加号、当前画布置顶和勾选。
- 原站总体审计支持新建、切换、重命名、复制、删除的动作集合。

### Inference

- 项目名属于项目级元数据。
- 完成一次导航/CRUD 后关闭局部菜单是本批采用的生命周期闭环。

### Clone-only decision

- 项目名与画布列表仍只在 Zustand 内存中存在，刷新会恢复 mock 初始值。
- 行级更多菜单的展开视觉沿用 clone，因为没有取得原站该状态截图。

## 3. 验证

专项命令：

```bash
python3 scripts/verify-liblib-batch16.py
```

结果：通过。

- 项目上下文和当前画布勾选可见。
- 项目名编辑、画布切换、新建、复制、重命名、删除全部通过。
- 每个画布动作完成后下拉关闭。
- 外部点击和 Escape 清理通过。
- 桌面与 390px 移动视口无页面级横向溢出。
- 浏览器控制台和 page error 均为空。

跨批回归：

```bash
for script in scripts/verify-liblib-batch{11..16}.py; do
  python3 "$script" || exit 1
done
```

结果：Batch 11、12、13、14、15、16 全部通过。回归脚本刷新出的旧批次截图已还原，只保留 Batch 16 新证据。

工程检查：

```bash
npm run check
npm run docs:check
git diff --check
```

结果：

- `npm run check` 通过：0 error，9 个既有 warning。
- `npm run docs:check` 通过：146 个 Markdown，310 个本地目标。
- `git diff --check` 通过。

## 4. 证据文件

- 原站识图：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
- 状态合同：[CANVAS_METADATA.spec.md](CANVAS_METADATA.spec.md)
- Desktop：[liblib-clone-batch16-canvas-menu-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch16-canvas-menu-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch16-canvas-menu-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch16-canvas-menu-mobile-390-2026-08-25.png)
