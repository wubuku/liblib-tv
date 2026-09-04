# Batch 98 Plan：添加节点面板对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 97（`batch/97-agent-drawer-current-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §3（添加节点面板、脚本/素材库子菜单）。

## 1. 范围

### 包含

1. **入口标签**（`SOURCE_FACT`）：`视频编辑` → `智能剪辑`（type 仍为 `video-clip`，`Beta` 角标保留）。
2. **脚本子菜单**（`SOURCE_FACT`）：脚本入口改为 flyout，两项：`脚本`（`NEW` 角标）与 `脚本（旧版）`（`Beta` 角标）。`脚本（旧版）` 执行既有 script 节点创建；`脚本 NEW` 为可见入口 + 本地 status `本地原型：新脚本节点能力未采样`（新脚本节点 UI 未采样，`SOURCE_UNKNOWN`）。
3. **素材库子菜单**（`SOURCE_FACT`）：`我的素材库/预设素材库` → `风格库/特效库`，两者打开既有 material 面板（默认 tab；tab 直达留待后续）。
4. **搜索**（`SOURCE_FACT`+`CLONE_DECISION`）：面板头部右侧搜索 icon，展开 `搜索画布节点` 输入框，按 label 子串过滤 9 个节点入口；无匹配显示提示；`添加资源` 区不受过滤影响。展开/过滤细节为 `CLONE_DECISION`。

### 不包含

- 添加资源上传/生成历史的真实服务（保持既有本地 status，media ingress 合同未授权）；
- 空画布状态与 4 个快捷芯片（Batch 99 候选，需要空画布 fixture 研究）；
- 面板几何（`196x481` 已与源站一致）；导演台/逐帧拉片角标（已在先前批落地）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 智能剪辑命名、脚本 NEW/（旧版）Beta 双入口、素材库 flyout 风格库/特效库、搜索图标与 `搜索画布节点` 文案、9 入口集合 |
| `CLONE_DECISION` | 搜索展开交互与过滤规则、子菜单定位、`脚本 NEW` 的本地 status、素材库 flyout 打开默认 tab |
| `SOURCE_UNKNOWN` | 新脚本节点能力、搜索无结果态源站样式、上传/从生成历史选择点击后的真实流程 |

## 3. 影响面与兼容

- `src/components/AddNodePanel.tsx`；
- `scripts/verify-liblib-batch15.py`：素材库子菜单断言 `预设素材库` → `特效库`（replacement 协议记录）；
- `data-add-node-entry` 仍为 9 个，type/选择器不变，batch23/24/25/28 的入口点击不受影响。

## 4. 验证

- 新增 `scripts/verify-liblib-batch98.py`：desktop `1440x900`，标签/角标、搜索过滤与清除、脚本 flyout 两项与本地 status、旧版创建 script 节点、素材库 flyout 打开 material 面板、上传/历史 status、零诊断。
- 复跑 `verify-liblib-batch15.py`（断言更新后）、`verify-liblib-batch23/24/25.py` 抽查相邻入口。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 面板 9 入口与源站命名/角标一致（智能剪辑、导演台 NEW、逐帧拉片 SD 2.5）。
2. 脚本/素材库 flyout 与源站两项一致；旧版脚本可创建节点。
3. 搜索可过滤并可复原。
4. 相邻 verifier、全量检查通过；特性分支 commit/push。
