# Batch 103 Plan：顶栏模式切换对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 102（`batch/102-asset-drawer-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §1/§5（顶栏 `工作流`/`故事板` 为 aria-pressed 双态 icon 按钮，32x32，位于画布下拉右侧）。

## 1. 范围

### 包含

1. **文案**（`SOURCE_FACT`）：顶栏模式切换 `工作台`→`工作流`、`分镜`→`故事板`（title + aria-label；内部 `editorMode: "workbench"|"storyboard"` 不变）。
2. **verifier 断言迁移**（replacement 协议）：batch11（`分镜`/`工作台` role 定位）、batch13/14（`button[aria-label="分镜"]`）、batch17（`工作台` bounding box）同步更名，版本注释内联。
3. 行为不变：切换仍联动 Agent 抽屉（故事板自动打开）、故事板投影、快捷键隔离。

### 不包含

- 故事板空态三组（文本/图片/视频）改造——Batch 104 候选；
- Skill 卡「分镜节奏优化」、工具箱「大师分镜九宫格」、VideoGenerationPanel「分镜」等内容性文案（非模式切换）；
- uiStore editorMode 值重命名。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 顶栏 `工作流`/`故事板` 命名与 aria-pressed 双态 |
| `CLONE_DECISION` | 内部 mode 值保留英文；icon 视觉沿用 lucide |
| `SOURCE_UNKNOWN` | 源站图标精确形状、按钮几何（clone 保持现有 32x32 附近布局） |

## 3. 验证

- 新增 `scripts/verify-liblib-batch103.py`：desktop `1440x900`，断言 `工作流` 初始 pressed、`故事板` 未 pressed；切换后故事板与 Agent 开、返回工作流 graph 保持；零诊断。
- 复跑 `verify-liblib-batch11/13/14/17.py`（断言迁移后）。
- `npm run check`、`npm run docs:check`。

## 4. 完成定义

1. 顶栏 aria 与源站一致。
2. 相邻 verifier 迁移后全部通过；全量检查通过；特性分支 commit/push。
