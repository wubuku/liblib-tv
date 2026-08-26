# LibTV Model Catalog Freshness 2026-08-27

> Queue：`OC-EQ-002`
>
> 状态：`PARTIAL_RECORDED`；catalog 已记录，per-model mode/control 未选择、未验证
>
> 安全边界：共享登录态项目只读；没有选择新模型、改变参数、编辑 Prompt、切换偏好或触发任务

## 1. 观察上下文

| 字段 | 值 |
|---|---|
| 日期 | 2026-08-27 |
| URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| Viewport | `929x874`，device pixel ratio `2` |
| Canvas zoom | 通过 `适合屏幕` 从 41% 变为 28%，仅改变本地 viewport |
| Fixture | `LIBTV-FIX-SOURCE-SHARED-01` / `SHARED_READ_ONLY` |
| Existing node | `v-UGQZzZOpbv`，`video`，已有 `failed` 状态，失败文案 `vip专属模型-会员` |
| Current model | panel short label `2.0 Fast`；catalog selected row `Seedance 2.0 Fast VIP` |
| Current mode/params | `全能参考`；`16:9 · 720P · 6s · 1个`；当前 credits sample `132` |

实际只读动作：fit view、清除既有图片 selection、选择已有失败视频、展开/关闭模型菜单、滚动菜单。没有点击任何模型行。

## 2. 证据资产

- 结构化 catalog：[`libtv-model-catalog-audit-2026-08-27.json`](libtv-model-catalog-audit-2026-08-27.json)
- 顶部截图：[`liblib-original-oc-eq-002-video-model-catalog-top-929x874-2026-08-27.png`](../../design-references/liblib-original-oc-eq-002-video-model-catalog-top-929x874-2026-08-27.png)
- 底部截图：[`liblib-original-oc-eq-002-video-model-catalog-bottom-929x874-2026-08-27.png`](../../design-references/liblib-original-oc-eq-002-video-model-catalog-bottom-929x874-2026-08-27.png)

Dialog 外框约 `369x409`，内部滚动 viewport 高 `400px`，内容高 `1956px`，共 `35` 个 `52px` row。

## 3. 当前 loaded DOM catalog

| # | Label | Estimate | Premium | Current fixture style | Source-visible description |
|---:|---|---|---|---|---|
| 1 | `Seedance 2.5` | 2min | yes | `STYLED_SELECTABLE` | 最强视频模型，全能参考，30s音画同步 |
| 2 | `Seedance 2.0 VIP` | 2min | yes | `STYLED_SELECTABLE` | 最强视频模型，会员专属通道,15s音画同步 |
| 3 | `Minimax H3` | 2min | yes | `STYLED_SELECTABLE` | 全模态输入，多参数控制，多场景商用级生成 |
| 4 | `Seedance 2.0 Fast VIP` | 2min | yes | `STYLED_SELECTABLE` / selected | 最强视频模型快速版，会员专属通道，15s音画同步 |
| 5 | `Seedance 2.0 Mini` | 2min | yes | `STYLED_SELECTABLE` | 最强视频模型mini版，高性价比生成，15s音画同步 |
| 6 | `Wan 3.0 Prime` | 1min | no | `STYLED_SELECTABLE` | 超快速生成，全模态参考，超写实高一致性 |
| 7 | `Wan 3.0` | 3min | no | `STYLED_SELECTABLE` | 全模态参考，支持文档与网页输入，超写实高一致性生成 |
| 8 | `Happy Horse 1.1` | 3min | yes | `STYLED_SELECTABLE` | 阿里最新视频模型，一致性与视听质量更可控 |
| 9 | `Happy Horse 1.0` | 3min | yes | `STYLED_SELECTABLE` | 阿里视频模型，支持多参生成 |
| 10 | `Kling O3` | 3min | yes | `STYLED_SELECTABLE` | 视频编辑模型、参考一致性、音画同出、多镜头 |
| 11 | `Wan 2.7` | 3min | no | `STYLED_SELECTABLE` | 全能参考，支持修改视频画面、剧情、环境 |
| 12 | `Kling O1` | 3min | yes | `STYLED_SELECTABLE` | 可灵一代编辑模型、支持多模态输入 |
| 13 | `Vidu Q2` | 3min | yes | `STYLED_SELECTABLE` | 多图主体参考，精确控制效果佳 |
| 14 | `Vidu Q2 Pro` | - | yes | `STYLED_SELECTABLE` | Vidu Q2 Pro |
| 15 | `Kling 3.0 Turbo` | 3min | yes | `STYLED_UNAVAILABLE` | 视频生成模型，高质感、支持多镜头 |
| 16 | `Kling 3.0` | 3min | yes | `STYLED_UNAVAILABLE` | 视频生成模型，高质感、支持多镜头 |
| 17 | `Wan 2.6` | 3min | no | `STYLED_UNAVAILABLE` | 音画同步，支持多机位镜头，最长可生15秒视频 |
| 18 | `Hailuo 2.3 Fast` | 1min | no | `STYLED_UNAVAILABLE` | 善于表达动作、表情、镜头，更快速 |
| 19 | `Hailuo 2.3` | 2min | no | `STYLED_UNAVAILABLE` | 善于表达动作、表情、镜头，更高质感 |
| 20 | `Seedance1.5 Pro` | 2min | no | `STYLED_UNAVAILABLE` | 音画同步，支持多机位镜头，最长可生12秒视频 |
| 21 | `Seedance 1.0 Pro` | 2min | yes | `STYLED_UNAVAILABLE` | 高精度提示词理解，40秒生成1080P视频 |
| 22 | `Seedance 1.0 Lite` | 1min | yes | `STYLED_UNAVAILABLE` | 轻量快速，一键进行日常视频生成 |
| 23 | `Kling 2.6` | 2min | yes | `STYLED_UNAVAILABLE` | 视频生成模型、直出音画同步 |
| 24 | `Kling3.0 动作迁移` | 8min | yes | `STYLED_UNAVAILABLE` | 动作控制模型，需输入1张图片、1条视频 |
| 25 | `Style Video` | 2min | yes | `STYLED_UNAVAILABLE` | 图生视频效果稳定，画面表现力强 |
| 26 | `Hailuo 02` | 2min | no | `STYLED_UNAVAILABLE` | 画质稳定，适合打造运动特效场景 |
| 27 | `Vidu Q2 Turbo` | - | yes | `STYLED_UNAVAILABLE` | Vidu Q2 Turbo |
| 28 | `Vidu Q3 Pro` | 2min | yes | `STYLED_UNAVAILABLE` | 支持主体参考，精确控制效果佳 |
| 29 | `OmniHuman 1.5` | 3min | yes | `STYLED_UNAVAILABLE` | 多模态数字人视频生成 |
| 30 | `Kling 2.5` | 2min | yes | `STYLED_UNAVAILABLE` | 速度快、效果稳定、性价比高 |
| 31 | `Kling 2.1` | 3min | yes | `STYLED_UNAVAILABLE` | 支持首尾帧，图生视频效果更出色 |
| 32 | `Wan 2.2` | 3min | no | `STYLED_UNAVAILABLE` | 支持特效、玩法千变万化 |
| 33 | `Wan 2.5` | 3min | no | `STYLED_UNAVAILABLE` | 支持特效、直出音画同步 |
| 34 | `Pixverse V5.5` | 3min | yes | `STYLED_UNAVAILABLE` | 支持特效、玩法丰富 |
| 35 | `Pixverse V5` | 3min | yes | `STYLED_UNAVAILABLE` | 支持特效、玩法丰富 |

前 14 行在当前 fixture 中使用 `cursor-pointer`；后 21 行使用 `cursor-not-allowed opacity-50`。但 35 个元素的 native `disabled` 均为 `false`，`aria-disabled` 均缺失。因此本文使用 `STYLED_SELECTABLE` / `STYLED_UNAVAILABLE`，不把 CSS 状态升级为可访问性或业务 disable contract。

`Vidu Q2 Pro` 与 `Vidu Q2 Turbo` 当前没有 estimate text，description 只是重复 label。这里保留 DOM 原样，不补写 estimate 或营销能力。

## 4. 相对 2026-08-25 七行样本的变化

旧样本只看见顶部七行，并正确保留“列表可能还有内容”的边界。新日期审计通过滚动容器和完整 loaded DOM 确认当前 dialog 有 35 行：

- 前七行顺序保持不变；
- 旧样本只确认两个 description，新审计直接读取了全部 35 行的当前 description；
- 新增可见 Happy Horse、Kling、Vidu、Hailuo、旧 Seedance、Style Video、OmniHuman、Wan 2.x 和 Pixverse 家族；
- 当前失败视频上下文把第 15-35 行样式化为 unavailable；原因没有直接证据；
- 35 行是当前登录态、当前节点和当前部署的 loaded DOM catalog，不是平台跨账号、跨权限、跨输入条件的永久完整模型库。

## 5. 当前 fixture 的 authoring snapshot

在打开菜单前，已选失败视频的面板直接显示：

- model short label：`2.0 Fast`；
- selected catalog row：`Seedance 2.0 Fast VIP`；
- mode：`全能参考`；
- params：`16:9 / 720P / 6s / 1个`；
- credits sample：`132`；
- advanced rows：联网搜索、自动校验素材、智能引用 AutoLink 均为 checked。

这些只说明一个既有 draft 的当前 authoring snapshot。失败文案与会员提示不能证明模型本身不可执行，也不能推出 credits 公式、请求 enum、adapter 或重试行为。

## 6. 对 capability projection 的影响

### 已升级

- `L0 Source-visible catalog` 从七行顶部样本升级为 35 行 current loaded DOM catalog；
- model label、estimate、premium、description、selected row 和当前上下文 style 均有结构化证据；
- short label `2.0 Fast` 与 catalog label `Seedance 2.0 Fast VIP` 的 alias 关系在当前节点得到直接证明。

### 仍未升级

- 没有选择其他模型，所以 per-model mode/control/default/range 仍为 `UNKNOWN`；
- `STYLED_UNAVAILABLE` 的原因仍未知，不能写成输入不兼容、账户权限或 rollout 结论；
- 没有 descriptor、request enum、adapter、billing、run、poll、result write-back 证据；
- 没有授权将 35 行复制进 clone model menu，更不能宣称 clone 支持执行这些模型。

## 7. 下一步与停止条件

`OC-EQ-002` 保持 `PARTIAL_RECORDED`。当前安全只读研究已经把 catalog 问题显著收窄；剩余高价值问题是逐模型 mode/control capability。

在共享项目中切换模型会改变现有节点 draft，因此本轮在菜单读取后关闭 disclosure，没有选择行。后续只有在独立可丢弃 source parameter fixture 中，才能按一次一个模型记录 mode、ratio、resolution、duration、audio、count、reference requirement 和 normalization。

没有该 fixture 时，未知项保持 `UNKNOWN_NOT_SELECTED`，不从 description、estimate、Open Canvas registry 或 Seedance 2.5 controls 推断。

## 8. 不可推出的结论

本次审计不能证明：

- 35 个模型都能被当前账户或 current runner 执行；
- `cursor-pointer` 行提交一定成功，或 `cursor-not-allowed` 行永远不可用；
- estimate 是 SLA、生成时长、轮询超时或费用；
- description 中“音画同步/最长秒数/全模态”已经映射为当前 request controls；
- 当前 clone 应立即引入 capability registry 或 Provider adapter；
- 选择模型后的参数 normalization、Prompt/reference 保留和失败恢复已经复核。

## 9. 安全结论

本轮只改变本地 selection、viewport 和 disclosure/scroll 状态，没有改变 graph、Prompt、模型、模式、参数、偏好、任务、媒体或账户。菜单关闭后仍选中原失败视频，model control 仍显示 `2.0 Fast`。
