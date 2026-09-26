# Batch 531 — 自写分镜脚本全屏编辑器

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 经有头浏览器
> CDP（9222 端口既有实例，单实例原则）补采：脚本生成器
> 「自己编写分镜脚本」入口实际打开全屏分镜脚本编辑器
> （截图 38-script-selfwrite-clicked.png + 抽屉 DOM 采样）。
> 本批修正 batch 528 时代 round-8 的「未展开子流程」结论——该结论
> 仅对「剧本生成/角色生成」两个入口成立。

## 源站实测结构（SOURCE_FACT）

- 顶部 3 步 stepper：①确认镜头/1个镜头待核对（激活态）②准备资产/暂无资产
  ③合成提示词/0/1 已合成；右上「0/3 完成后可批量生成视频」+ ✕；
- 10 列分镜表格：镜号 | 时长 | 画面描述 | 景别 | 光影氛围 | 对白/旁白 |
  音效 | 运镜 | 最终提示词（占位「待生成提示词」）| 操作（···）；
  首行 1/5s，空单元格左上角 + 号；
- 底部：左「+ 添加镜头」，右「→ 下一步：准备资产」。

## clone 合同

- 「自己编写分镜脚本」入口 → `data-storyboard-editor` 全屏遮罩
  （z-280，uiStore `isStoryboardEditorOpen` 阻塞面，ESC 经
  `storyboard-editor` 分支关闭，✕ 亦可）；
- 剧本/角色生成入口保持 batch 528 跟随合同（横幅、无编辑器）；
- 表格：单元格点击进入本地编辑（Enter/blur 提交草稿），添加镜头追加
  行（镜号自增、时长 5s），stepper 副标题随行数联动（1个镜头待核对、
  0/N 已合成）；
- 「下一步：准备资产」为可视按钮——源站第 2/3 步未采样
  （SOURCE_UNCERTAIN），不推进；
- 全部编辑为本地草稿，不触发任何 AI 生成（与禁真实生成约束一致）。

## 内容

- `src/components/StoryboardScriptEditor.tsx`（新组件）；
- `src/store/uiStore.ts`（isStoryboardEditorOpen + open/close +
  OverlayState/closedOverlayState + closeTopForegroundSurface case）；
- `src/lib/libtvSelectionCommandContext.ts`（阻塞面联合 + 快照字段 +
  解析器 storyboard-editor 分支，优先级仅低于 follow-banner）；
- `src/components/nodes/ScriptGeneratorNode.tsx`（自写入口改开编辑器，
  batch 531 注释修正 round-8 结论）；
- `src/app/page.tsx`（挂载编辑器）；
- `scripts/verify-liblib-batch531.py`（31 检查）；
- 回归：batch 528（跟随合同）/116 全绿；lint 0 error；typecheck 仅
  并行开发者 JimengGenPanel WIP 错误。
- `runtime-audit.json`：本目录。
