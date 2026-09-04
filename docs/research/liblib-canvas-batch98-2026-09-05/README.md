# Batch 98：添加节点面板对齐 2026-09-05 源站

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 97（`batch/97-agent-drawer-current-source`）。

本批把添加节点面板对齐 2026-09-05 源站审计：智能剪辑命名、脚本
NEW/（旧版）Beta 双入口、素材库 风格库/特效库 子菜单与搜索画布节点。
上传/从生成历史选择保持既有本地 status，不接真实服务。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界、兼容影响与完成定义。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：实施结果、断言迁移、验证与剩余风险。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 智能剪辑命名、脚本双入口与角标、素材库 flyout 风格库/特效库、搜索图标与 `搜索画布节点` 文案、9 入口集合 |
| `CLONE_DECISION` | 搜索展开/过滤规则、子菜单定位与开合互斥、`脚本 NEW` 本地 status、素材库 flyout 打开默认 tab |
| `SOURCE_UNKNOWN` | 新脚本节点真实能力、搜索无结果源站样式、上传/生成历史的真实流程 |

## 实施结果

- `视频编辑` → `智能剪辑`（type 仍为 `video-clip`，相邻 batch25 断言不受影响）。
- 脚本入口改为 flyout：`脚本 NEW`（本地 status，不伪造能力）+ `脚本（旧版） Beta`
  （执行既有 script 节点创建）。
- 素材库 flyout：`风格库/特效库`（打开既有 material 面板）。
- 面板头部新增搜索 icon 与 `搜索画布节点` 过滤（label 子串、可复原、空态提示），
  `添加资源` 区不受过滤影响。
- `verify-liblib-batch15.py` 素材库子菜单断言按 replacement 协议更新
  （`预设素材库` → `特效库`）。

## 完成定义

1. `verify-liblib-batch98.py` 33 checks、`0/0/0` diagnostics 通过（desktop `1440x900`）。
2. 相邻 `verify-liblib-batch15/23/24/25.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 治理文档更新；特性分支 commit/push。

通过结果只证明 clone-owned 的添加面板当前源站对齐合同，不升级 LibTV
source-exact 行为，不触及 media ingress 运行时授权。
