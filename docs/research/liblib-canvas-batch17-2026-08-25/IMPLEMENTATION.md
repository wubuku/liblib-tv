# Batch 17 实施结果：资产管理上下文与层级浏览

## 1. 实施内容

- `AssetManagerPanel` 绑定 `canvasStore.projectName`、`activeCanvasId` 和 active canvas name。
- 抽屉顶部新增 source-shaped 项目/画布上下文行。
- 点击抽屉中的画布名会通过 `uiStore.toggleCanvasDropdown`：
  - 关闭资产抽屉；
  - 在顶部导航位置打开画布菜单；
  - 保持 Batch 11 顶层 overlay 互斥合同。
- `TopNavBar` 在资产抽屉打开时：
  - 隐藏重复的画布按钮；
  - 将工作台/分镜 mode 控件移到约 `x=264`，避让 240px 抽屉。
- 画布列表按保存的原站顺序呈现，并用 `parentId` 显示一层组树：
  - 视频组下的失败视频为 `data-asset-manager-depth="1"`；
  - 组行显示展开箭头和文件夹图标。
- 增加本地浏览控件：
  - 画布顺序 / 名称顺序；
  - 全部 / 图片 / 视频 / 文本 / 分组；
  - 当前画布 label 搜索。
- 空态按页签区分：
  - `当前画布暂无节点`
  - `当前画布暂无媒体资产`
- Batch 12 的画布/资产 tab、节点数和 React Flow selection 合同保持。

## 2. 证据边界

### Source fact

- 原站截图直接支持项目/画布上下文、mode 避让、`画布元素` 工具行、10 项顺序、组展开层级和底部计数。

### Inference

- `canvasStore.projectName`、active canvas name 和 `parentId` 是 clone 内表达这些事实的可靠数据源。

### Clone-only decision

- 排序、筛选项和搜索匹配规则是本地交互原型；原站展开态没有保存证据。
- `资产` tab 继续过滤当前画布图片/视频，不连接账户资产服务。

## 3. 验证

专项命令：

```bash
python3 scripts/verify-liblib-batch17.py
```

结果：通过。

- 项目名、active canvas name 和 mode 几何通过。
- 默认 10 项顺序和失败视频 child depth 通过。
- 图片筛选、label 搜索、名称排序通过。
- 节点点击同步 React Flow selection。
- 抽屉到画布菜单的 handoff 和空 `画布 1` 上下文通过。
- 画布/资产空态通过。
- 桌面与 390px 无页面级横向溢出。
- 浏览器 console/page error 为空。

跨批回归：

```bash
for script in scripts/verify-liblib-batch{11..17}.py; do
  python3 "$script" || exit 1
done
```

结果：Batch 11、12、13、14、15、16、17 全部通过。回归刷新出的旧批次截图已还原，只保留 Batch 17 新证据。

工程检查：

```bash
npm run check
npm run docs:check
git diff --check
```

结果：

- `npm run check` 通过：0 error，9 个既有 warning。
- `npm run docs:check` 通过：151 个 Markdown，327 个本地目标。
- `git diff --check` 通过。

## 4. 证据文件

- 原站/旧 clone 识图：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
- 结构合同：[ASSET_CONTEXT_TREE.spec.md](ASSET_CONTEXT_TREE.spec.md)
- Default tree：[liblib-clone-batch17-asset-tree-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch17-asset-tree-desktop-929-2026-08-25.png)
- Search：[liblib-clone-batch17-asset-search-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch17-asset-search-desktop-929-2026-08-25.png)
- Empty canvas：[liblib-clone-batch17-asset-empty-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch17-asset-empty-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch17-asset-tree-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch17-asset-tree-mobile-390-2026-08-25.png)
