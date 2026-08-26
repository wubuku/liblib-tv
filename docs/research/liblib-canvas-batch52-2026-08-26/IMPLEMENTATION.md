# Batch 52 实施记录

> 状态：已完成（2026-08-26）。本批完成当前源站图片工具条的
> `13` 项动作壳层和只读图片预览闭环。代码与运行证据先以
> `a17b590` 提交并 push，文档 closeout 随后记录。

## 1. 实施清单

- [x] 将 `ImageToolbar` 更新为当前源站顺序：9 个文字动作和 4 个图标动作。
- [x] 固定当前动作的 source test id、按钮宽度、高度和独立可访问名称。
- [x] 将工具条外框更新为 `1092.5x49px`，保留节点中心和
  `10 + 24 * zoom` 顶部 host 几何。
- [x] 在 `uiStore` 增加 page-level `ImagePreviewState`。
- [x] 新增 `ImagePreviewOverlay`：`fixed inset-0`、`85vw x 80vh` 内容区、
  intrinsic-ratio contain 媒体、水印和 `32x32` 关闭按钮。
- [x] Preview 打开时阻断底层 Delete/Space/Tab/undo 等画布快捷键。
- [x] Preview 的关闭按钮和 Escape 只关闭预览，不清除 selection、Prompt、
  nodes、edges、viewport 或 graph history。
- [x] 元素编辑、图层分离、标注、旋转和下载保持独立入口，但在专用批次前
  不伪造任务、保存或派生节点副作用。
- [x] 增加 Batch 52 focused Playwright 和结构化 `runtime-audit.json`。
- [x] 保留 desktop、mobile 两种一次性 clone 截图及本批识图台账。

## 2. 关键代码边界

| 文件 | 责任 |
|---|---|
| `src/components/ImageToolbar.tsx` | 当前 13 项动作的可见壳层和 source-sized geometry |
| `src/components/nodes/ImageNode.tsx` | 预览 action 到 page store 的 dispatch；未完成高风险动作不落 graph |
| `src/components/ImagePreviewOverlay.tsx` | 页面级只读媒体预览、焦点和 Escape/Tab 边界 |
| `src/store/uiStore.ts` | top-level overlay mutual exclusion 与 preview 生命周期 |
| `src/app/page.tsx` | overlay mount owner 和底层 page keyboard boundary |

本批没有修改 FrameOS、Director、视频流程、真实 provider、上传/下载服务
或远程持久化。

## 3. 验证记录

### 专项验证

```text
python3 scripts/verify-liblib-batch52.py
```

结果：

```text
Batch 52 Playwright verification passed: current 13-action image toolbar,
source-sized button geometry, page-level preview, watermark and close geometry,
keyboard isolation, unchanged graph/selection, responsive bounds, and browser errors.
```

覆盖：

- `929x874` 下工具条 `1092.5x49`、13 个按钮顺序/宽高/disabled 状态；
- 节点中心、`10 + 24 * zoom` 顶部间距、`16 * zoom` 底部面板间距；
- page-level overlay、`85vw x 80vh` 内容区、2:1 媒体 contain；
- 水印 `48x23`、媒体左上 `+10/+10`、关闭按钮 `32x32` 和 `-12px` 外扩；
- close/Escape/Tab 与 Delete/Space/Ctrl+Z 的底层隔离；
- graph、selection、Prompt 和 viewport 不变；
- `390x844` 下固定宽工具条自然裁切、预览媒体 contain 和无横向溢出；
- console、page error 和 request failure。

移动端第一次运行只暴露验证器问题：固定宽工具条末端“预览”按钮在视口
外，Playwright 物理点击会拒绝执行。验证器随后增加了“按钮确实在视口外”
断言，并用原生 `HTMLElement.click()` 激活同一个 React handler；产品代码未为
测试改变自然裁切行为。修正后 desktop/mobile 均通过。

### 相邻回归

```text
python3 scripts/verify-liblib-batch10.py
python3 scripts/verify-liblib-batch11.py
```

两者均通过。Batch 10 继续保护五种历史图片面板状态和旧 AutoLink clone
合同；Batch 11 继续保护顶层浮层互斥、Escape cleanup、Storyboard/Agent
生命周期。它们不覆盖当前 13-action source contract，旧截图在运行后已恢复。

### 静态检查

```text
npx tsc --noEmit
npx eslint src/app/page.tsx src/components/ImageToolbar.tsx \
  src/components/ImagePreviewOverlay.tsx \
  src/components/nodes/ImageNode.tsx src/store/uiStore.ts
git diff --check
python3 -m py_compile scripts/verify-liblib-batch52.py
```

以上均通过。

## 4. 证据与截图

- 结构化测量：[`runtime-audit.json`](runtime-audit.json)
- 截图识别台账：[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- 工具条截图：[`../../design-references/liblib-clone-batch52-current-image-toolbar-929-2026-08-26.png`](../../design-references/liblib-clone-batch52-current-image-toolbar-929-2026-08-26.png)
- 桌面预览截图：[`../../design-references/liblib-clone-batch52-image-preview-929-2026-08-26.png`](../../design-references/liblib-clone-batch52-image-preview-929-2026-08-26.png)
- 移动预览截图：[`../../design-references/liblib-clone-batch52-image-preview-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch52-image-preview-mobile-390-2026-08-26.png)

截图是本批 clone 运行证据，不是源站原图，也不取代源站 DOM/bundle
证据。后续应先读本文件和 `SCREENSHOT_ANALYSIS.md`，只有新问题或截图改变
时才重新识图。

## 5. 提交历史

| Commit | 内容 | 状态 |
|---|---|---|
| `192a66b` | Batch 52 计划、source evidence 和组件预览合同 | 已 push |
| `a17b590` | 13-action toolbar、Preview、verifier、runtime audit、clone 截图 | 已 push |

Batch 52 文档 closeout 应以单独文档提交记录，提交前运行
`python3 scripts/verify-docs.py`、`git diff --check` 和 `npm run check`，
并恢复任何被历史 verifier 重写的截图。

## 6. 结果判断与未完成项

本批已闭环：

```text
selected image
  -> current 13-action toolbar shell
  -> preview action
  -> page-level read-only overlay
  -> close/Escape
  -> same selected image and graph
```

本批没有声称完成：

- 标注绘制、保存、dirty state 或远程提交；
- 元素编辑的 point/box/brush record 和生成任务；
- 旋转/镜像的派生节点语义；
- 图层分离的异步 composition；
- 下载副作用、水印偏好、会员校验和文件写入；
- 源站 exact CSS、真实任务服务或远程持久化。

## 7. 接力

下一批是 Batch 53：源站证据完整且低风险的**空标注替换态**。目标仅为：

```text
standard toolbar/panel
  -> dedicated 536x49 annotate toolbar
  -> bottom panel removed
  -> DPR=2 canvas over selected image
  -> Escape/discard restores standard state
```

不在 Batch 53 实现绘制保存、远程任务、结果节点或 graph mutation。
