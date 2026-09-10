# Batch 337 — 故事板视频栏交互：状态过滤与 ready 播放灯箱（`CLONE_DECISION` 实装）

> 状态：视频栏「全部 ∨」过滤下拉与 ready 播放灯箱实装并通过验证
> （`verify-liblib-batch337.py` 16 checks 全绿）。
> 源站选项/行为未采得——**CLONE_DECISION**，文档明标。

## 源站状态（2026-09-11）

- 源站画布资源总览持续无法水合（bodyLen≈311，无资源卡、无过滤
  控件），模型菜单僵尸层缺陷未恢复——「全部 ∨」选项清单、过滤
  语义、ready 播放行为均 `SOURCE_UNKNOWN`，BLOCKED_SOURCE 维持。

## Clone 实现（`CLONE_DECISION`，文档明标）

1. **状态过滤**：`data-storyboard-filter` 按钮标签随所选状态变化
   （全部/待确认/已完成/失败）；下拉
   `data-storyboard-filter-menu` 四选项
   （`data-storyboard-filter-option="all|pending|ready|failed"`，
   aria-pressed + ✓ 选中标记）；过滤按视频卡
   `data-storyboard-video-status`；过滤后空列显示「该状态下暂无
   视频」。
2. **ready 播放灯箱**：ready 卡播放钮
   （`data-storyboard-play`，span role=button——避免 button 嵌套）
   打开 `data-storyboard-lightbox`：节点有 `videoUrl` 时渲染
   `<video controls autoplay>`（`data-storyboard-lightbox-player`），
   无源时显示「本地原型：该视频节点无视频源」占位；关闭按钮
   （`data-storyboard-lightbox-close`）与背景点击均可关闭。

## 验收

- `verify-liblib-batch337.py` 16 checks：菜单开合/四选项/选中标记、
  过滤联动与标签、空列提示、无源占位灯箱、有源 `<video>`、关闭
  按钮与背景点击、console 零产品错误（mock-clip.mp4 404 为测试
  夹具预期伪影，按模式过滤）；
- 回归：334/336/100 全绿；`npm run check` 0 errors（8 warnings
  基线，清除了本批引入的未用 eslint-disable）；docs check 通过
  （896 Markdown）。

## 后续候选

- 源站恢复后：以真实选项/行为替换 CLONE_DECISION；
- BLOCKED_SOURCE 三项补采（Hailuo 分解、480P 批量、Style Video
  费率）；
- 故事板图片栏 对话 按钮与 展开图标 的目标行为采样。
