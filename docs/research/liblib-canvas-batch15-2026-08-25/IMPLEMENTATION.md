# Batch 15 实施结果：添加节点菜单语义与音频入口

## 1. 实施内容

- `AddNodePanel` 从旧的“网格/占位按钮”合同更新为原站截图支持的 9 项竖向入口。
- 入口 action 显式区分：
  - 创建节点；
  - 打开素材库子菜单；
  - 本地资源反馈。
- “音频”现在调用 `addNode("audio")`，不再错误创建文本节点。
- 新增 `AudioNode`：
  - React Flow handles；
  - 文件名和“音频”标题；
  - 保守的波形占位；
  - 播放按钮和时长；
  - 明确的本地音频预览说明。
- “素材库”先打开“我的素材库 / 预设素材库”子菜单；选择任一项会关闭添加菜单并打开现有 `MaterialLibraryPanel`。
- “上传”和“从生成历史选择”显示本地 prototype 状态，不创建虚假节点。
- 增加 `data-add-node-*` 选择器和 `.react-flow__node-audio` 验收合同。

## 2. 证据边界

### Source fact

- 原站截图支持 9 项入口的顺序、文案、徽标、脚本/素材库箭头和资源区。
- 原站 bundle 字符串支持音频节点和素材库/脚本入口语义。

### Clone-only decision

- 音频内部卡片没有对应原站截图，因此只做低承诺本地预览，不实现音频播放或解析。
- 素材库子菜单的具体内容未在截图中展开，本批使用已有本地素材库入口。
- 上传和历史资源操作没有接真实文件/服务。

## 3. 验证

专项命令：

```bash
python3 scripts/verify-liblib-batch15.py
```

结果：通过。

- 9 个添加节点入口按源站顺序呈现。
- `音频` 创建 `.react-flow__node-audio`，不会错误创建文本节点。
- `素材库` 展开子菜单，两个本地入口都能打开素材库面板。
- 上传/生成历史点击后显示本地 prototype 状态。
- 点击外部区域或按 `Escape` 能关闭菜单。
- 桌面和 390px 移动视口无页面级横向溢出。
- 专项截图已生成，浏览器控制台无错误。

跨批回归：

```bash
for script in scripts/verify-liblib-batch{11..15}.py; do
  python3 "$script" || exit 1
done
```

结果：Batch 11、12、13、14、15 全部通过；旧批次截图刷新噪声已还原，只保留本批新证据。

工程检查：

```bash
npm run typecheck
npm run check
npm run docs:check
```

Batch 15 当前已通过 `npm run typecheck`。最终 `npm run check`、`npm run docs:check` 和 `git diff --check` 在提交前统一执行。

## 4. 证据文件

- 原站识图：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
- 组件合同：[ADD_NODE_MENU.spec.md](ADD_NODE_MENU.spec.md)
- Add-node menu：[liblib-clone-batch15-add-node-menu-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch15-add-node-menu-desktop-929-2026-08-25.png)
- Audio node：[liblib-clone-batch15-add-node-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch15-add-node-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch15-add-node-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch15-add-node-mobile-390-2026-08-25.png)
