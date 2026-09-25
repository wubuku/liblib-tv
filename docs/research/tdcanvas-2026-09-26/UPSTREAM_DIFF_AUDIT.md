# TDCanvas ← basketikun/infinite-canvas 归属审计

> 目的：回答「TDCanvas 的画布机制哪些承自上游 `basketikun/infinite-canvas`、哪些是 TDCanvas 原创/改造」（REPORT.md §6 的未决问题）。
> 方法：浅克隆上游 `main` 至 /tmp（审计基准 `dab19adc0847e32e39b7fc8ff90cb392561fb826`，2026-09-23，**v0.19.0**——注意上游比 TDCanvas 的 v0.14.0 更新，两边是**同源分叉、双向演化**，非简单父子差异）；对关键文件做 `cmp`/`diff`/符号 grep。
> 证据等级：文件级 `cmp` IDENTICAL / diff 行数 / 符号在两仓的出现次数，均为可复核的机械事实；「继承/原创」判断据此得出。

## 1. 总体关系

- TDCanvas README 自述「基于 `basketikun/infinite-canvas` 二次开发」；上游约 7k star、官网 canvas.best、MIT。
- 顶层骨架同构：`web/ + canvas-agent/ + plugins/ + docker-compose + nginx.conf + render.yaml + vercel.json + SECURITY.md + skills-lock.json`。上游多出 `assets/`、`canvas-proxy/`（服务端代理，TDCanvas 已删）；TDCanvas 多出 `modules/`、`CLA.md`、`CONTRIBUTING.md`。
- `web/src` 顶层差异极小：TDCanvas 多 `integrations/`（comfyui-local）与 `splashscreen.ts`。
- 两仓**都在活跃演进**（上游 2026-09-23 仍在提交），因此「上游无 = TDCanvas 原创」的判断对 v0.19.0 时点成立，不排除上游后来也实现了同类机制。

## 2. 机制归属表（对照 PATTERN_CARDS TD-01..15）

| 机制（模式卡） | 归属 | 机械证据 |
|---|---|---|
| node-registry 注册表（TD-04） | **继承（逐字节相同）** | `cmp` IDENTICAL（61 行） |
| plugin-loader 插件加载（TD-12 基座） | **继承（逐字节相同）** | `cmp` IDENTICAL（170 行） |
| 小地图纯 div（TD-01 附属） | **继承（逐字节相同）** | `cmp` IDENTICAL（137 行） |
| canvas-agent 整个 Agent 通道（TD-11） | **继承（结构相同，小改）** | `canvas-agent/src` 目录 diff 仅上游多 `config.test.ts`；schemas 75 处 `canvas_` 工具；`canvas-agent-ops.ts` 仅差 15 行 |
| wheel=zoom 公式（TD-02） | **继承** | 上游 `infinite-canvas.tsx:91-92` 同为 `pow(1.1, delta/100)` |
| 项目文档含 chatSessions/viewport/backgroundMode（TD-10 部分） | **继承** | 上游 `use-canvas-store.ts:17-21` 同三字段；上游默认背景 `"lines"`（TDCanvas 迁移为 dots 的动因） |
| 几何式分组 groupId（TD-15） | **继承** | 上游有 `canvas-node-geometry.ts` 且含 `groupId`；上游 builtin-nodes 注册 Group |
| 主题系统 canvasThemes（SOURCE_ANALYSIS §2.8） | **继承** | 上游同路径 `web/src/lib/canvas-theme.ts:4` 同名导出 |
| i18n 双语 | **继承** | 上游有 `web/src/i18n/`（index+locales） |
| 图片快捷工具自定义（`image-quick-tools`） | **继承** | 两仓各 1 个文件引用同 key |
| 连线渲染贝塞尔+命中层（TD-01 附属） | **继承（小改）** | `canvas-connections.tsx` 仅差 42 行 |
| 画布 surface 文件 | **改造（改名+重写）** | 上游 `infinite-canvas.tsx` → TDCanvas `td-canvas-surface.tsx`（315 行新文件）；上游 Space=临时工具（`temporaryTool = ctrlKey \|\| isSpacePressed`，`infinite-canvas.tsx:114,206`），TDCanvas 改为禁用 Space |
| 对齐辅助线 + 网格吸附（TD-15） | **TDCanvas 原创** | 上游无 `canvas-alignment-guides.*`；`snapToGrid` 上游 0 文件 vs TDCanvas 6 |
| 氛围网格/视差/指针 focus 层（TD-14） | **TDCanvas 原创** | 上游 surface 与 globals.css 中 parallax/depth/focus 变量 0 命中 |
| 图片历史 imageHistory + pinned（TD-09 部分） | **TDCanvas 原创** | `imageHistory` 上游 0 文件 vs TDCanvas 13 |
| 批量堆叠 batchChildIds（TD-08） | **TDCanvas 原创** | 上游 0 vs 3 |
| providerTask 任务状态机（TD-07 壳） | **TDCanvas 原创** | 上游 0 vs 13（上游生成走 OpenAI 兼容 `image.ts/video.ts/audio.ts + local-proxy.ts + model-plugin.ts + prompt-source-runtime`，无任务轮询状态机） |
| objectReferences 无线引用（TD-06 部分） | **TDCanvas 原创** | 上游 0 vs 16；上游用 Group-作为资源集合 + `canvas-node-reference-bar.tsx`（`getGroupResourceNodes`）表达引用，该组件 TDCanvas 已删 |
| Aitudou 生成后端 | **TDCanvas 原创** | 上游无 `aitudou*.ts`（TDCanvas 1003 行） |
| Tauri 桌面壳 + media_cache + comfyui-local + modules/ | **TDCanvas 原创** | 上游无 `src-tauri`、无 `integrations/`、无 `modules/`；上游另有 `canvas-proxy/` 服务端组件（TDCanvas 移除，改 Rust 中继） |
| 上游独有：`canvas-selection-toolbar.tsx`（多选浮动工具条）、`canvas-node-reference-bar.tsx` | **上游独有（TDCanvas 移除）** | 文件仅存在于上游 |

## 3. 对本项目结论的影响

1. **归属修正**：REPORT.md/PATTERN_CARDS 中 TD-04/05/11/12/15 与主题系统、Group、i18n 应读作「infinite-canvas 生态机制（TDCanvas 继承）」；TD-07/08/09（任务状态机、批量堆叠、图片历史）、TD-02 的 Space 禁用与框选改造、TD-14 氛围层、对齐辅助线、连线/objects 双模式是 **TDCanvas 层的增量**。若引用本调研，请按此归属表述。
2. **上游本身值得独立调研**：infinite-canvas 的 `canvas-selection-toolbar`（多选浮动工具条）、`canvas-proxy`（服务端代理与 BYOK 渠道：chatgpt2api/grok2api/newapi）、Group-资源集合引用模型、prompt-source 的 OpenAI 兼容 provider 层，是与 TDCanvas 不同的另一组可迁移机制；上游 v0.19.0 比 TDCanvas 新，可能还有 TDCanvas 未曾有的新能力。是否立项为独立研究包（如 `infinite-canvas-2026-09-26/`）等待用户决定。
3. **审计时效**：本审计基准为上游 `dab19ad`（浅克隆 /tmp，非 submodule）；上游演进后需重跑（见 ITERATION_LOG Q1 停止条件已满足的部分）。
