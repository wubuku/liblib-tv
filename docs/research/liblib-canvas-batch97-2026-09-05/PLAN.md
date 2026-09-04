# Batch 97 Plan：Agent 抽屉对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：`86673b6`（Batch 96）。
>
> 源站证据：[`liblib-live-2026-09-05/`](../liblib-live-2026-09-05/README.md)（登录态空画布 shell 审计，含 2026-09-05 补采样的完整模型目录）。

## 1. 范围

把 `AgentDrawer` 对齐当前源站结构。只做 shell/菜单对齐，不接任何真实服务。

### 包含

1. **头部按钮集合**（`SOURCE_FACT`）：`新对话` 标题 + 按钮 `当前已是新对话`（disabled）、`历史对话`、`新对话无法分享`（disabled）、`Agent 设置`、`CLI & Skill`、`关闭`（执行既有 `toggleAgent`）。
2. **Skill 推荐区**（`SOURCE_FACT` + `CLONE_DECISION`）：
   - 标题随模式：分镜 `让 Skill 帮你迈出第一步`，工作台 `选一个 Skill，让创作更快一步`；
   - 第一批 4 张卡改为源站命名：皮克斯动画广告 `/pixar-animated-ad-creator`、爆款拉片复刻 `/viral-video-replicator`、新中式美学TVC `/neo-chinese-aesthetic-tvc`、古典武侠电影全流程导演 `/hujinquanwuxia`（id 保持 `pixar/viral/neo-china/wuxia`）；
   - 第二批保留现有 clone-shaped 备选作为 `换一批` 填充（`CLONE_DECISION`）。
3. **Composer 控件行**（`SOURCE_FACT`）：`添加附件`、`选择模型`（打开模型菜单）、`Skill`（本地 status 反馈）、`生成模式`（打开模式菜单）、`Send`（行为不变）。移除旧的 引用工作流/引用节点/刷新上下文 三钮。
4. **选择模型菜单**（`SOURCE_FACT`）：标题 `选择模型`；单一滚动列表，含 `图片`/`视频` 两个分区头；tab 为分区锚点；完整 15 项目录与描述、premium 角标（视频 6 项有、图片 0 项）按审计 §5.1。
5. **生成模式菜单**（`SOURCE_FACT`）：`手动模式`（Agent 在每次生成前询问）/ `自动模式`（Agent 完全自动生成），默认勾选 `自动模式`。

### 不包含

- 真实 Agent/模型调用、上传、历史对话、Agent 设置与 CLI & Skill 面板内容；
- 通知横幅（保留现状：本轮两次观察均未见，但可能是状态依赖，见 §4）；
- 故事板三分组（文本/图片/视频）改造——留给后续批次；
- 跟随状态条、顶栏 工作流/故事板 文案、添加节点面板、空画布芯片。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 头部按钮集合与 disabled 态；Skill 卡命名/handle；composer 控件集合；模型菜单分区结构、15 项目录、premium 分布；生成模式两项与默认项；抽屉约 `341px` 宽 |
| `CLONE_DECISION` | 模型行 `+` 点击后的选中态（源站未见选中样例）；菜单开合交互；第二批 Skill 填充；图标近似（lucide）；`Skill` 按钮点击给本地 status 反馈 |
| `SOURCE_UNKNOWN` | 模型行的真实选中/添加语义；`添加附件`/`Skill`/`CLI & Skill`/`历史对话`/`Agent 设置` 的点击行为；通知横幅是否仍存在；头部图标精确形状 |

## 3. 影响面与兼容

- `src/components/AgentDrawer.tsx`（主体重写控件行与新增两个菜单）；
- `scripts/verify-liblib-batch14.py`：两处历史断言随源站漂移更新（Skill 标题回填值 `皮克斯动画风格`→`皮克斯动画广告`；关闭按钮 aria `关闭 Agent`→`关闭`），并按协议记录到 `LIBTV_VERIFIER_REPLACEMENT_MAP.md`；
- 不触碰 `canvasStore`/`directorStore`/graph/普通画布交互；`uiStore` 仅读 `editorMode`。

## 4. 停止条件

- 源站补充采样与本文冲突（如模型目录变化）→ 停下更新审计再实施；
- 发现通知横幅/头部集合需要动 `uiStore` 结构 → 收窄为本批不做；
- batch13/14 相邻 verifier 无法在断言更新后通过 → 停下排查，不放宽无关断言。

## 5. 验证

- 新增 `scripts/verify-liblib-batch97.py`：desktop `1440x900`，头部按钮/disabled、Skill 命名与换一批、composer 控件、模型菜单 15 项与分区、生成模式默认与切换、关闭；零 console/pageerror/requestfailed。
- 复跑 `verify-liblib-batch13.py`、`verify-liblib-batch14.py`（断言更新后）。
- `npm run check`、`npm run docs:check`。

## 6. 完成定义

1. 抽屉头部六个动作与源站集合一致，两个 disabled 态可见。
2. 第一批 Skill 卡为源站命名与 handle，选择回填 prompt，换一批可循环。
3. Composer 为 添加附件/选择模型/Skill/生成模式/Send 五控件。
4. 模型菜单单列表双分区、15 项目录与 premium 角标正确，锚点 tab 切换，`+` 有本地选中反馈。
5. 生成模式菜单两项可切换，默认自动。
6. batch13/14/97 verifier、`npm run check`、docs check 通过；特性分支 commit/push。
