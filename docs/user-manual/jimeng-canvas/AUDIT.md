# 即梦画布用户手册回走审计

## 审计基线

- URL：`https://jimeng.jianying.com/ai-tool/ai-canvas/<project-id>`
  （正式取证开始时回填实际 project-id 与画布上下文，用户名去敏）。
- commit：正式探索尚未开始；Gate B 回走开始时把本节 commit 更新为当时实际 HEAD。
- 角色：已登录普通画布创作者
- viewport：正式证据与截图固定为 1280x720
- locale：zh-CN
- 审计时间：2026-09-23（账本建立；正式回走未开始）

## 结果

| 任务 | 结果 | 级别 | 证据 | 修复 |
|---|---|---|---|---|
| create-first-node | 未开始 | - | 候选线索：`SOURCE_OBSERVATIONS.md` §1 | 待探索、回走 |
| navigate-canvas | 未开始 | - | §1 | 待回走 |
| connect-nodes | 未开始 | - | §1（补录任务；连线交互无旧取证，全部当日实测） | 待回走 |
| use-node-toolbar | 未开始 | - | §1 + §1.1 漂移警报（工具条已改版） | 待回走 |
| prepare-generation | 未开始 | - | §1（扣费边界：只到发送前一步） | 待回走 |
| edit-text-node | 未开始 | - | §1 | 待回走 |
| media-playback | 未开始 | - | §1 | 待回走 |
| audio-node-voice | 未开始 | - | §1 | 待回走 |
| duplicate-delete-history | 未开始 | - | §1 | 待回走 |
| organize-group-layout | 未开始 | - | §1 | 待回走 |
| assets-and-upload | 未开始 | - | §1 | 待回走 |
| ai-agent-drawer | 未开始 | - | §1 | 待回走 |
| canvas-context | 未开始 | - | §1 | 待回走 |
| help-and-shortcuts | 未开始 | - | §1 | 待回走 |

## 未覆盖与已接受限制

- 任务范围已于 2026-09-23 由用户授权 Agent 定级定稿（14 项，FrameOS 等价或
  生成常识关键优先）；后续如发现新的重要面，按同一原则增补并记录。
- 一切真实生成与按积分计费的操作（生成发送、局部重拍、智能超清、补帧、提示词
  反推、智能改图、配音/音乐生成）永久超出探索边界；相关任务的成功判据是可回走的
  面板状态，不是生成结果。
- 充值、订阅、积分购买、账户页不在手册范围内。
- 复刻研究中的 `CLONE_DECISION` 与 `BLOCKED_BY_FIXTURE` 记录不作为源站事实；
  正式证据以当前登录会话实测为准。
