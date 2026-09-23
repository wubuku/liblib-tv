# FrameOS 画布用户手册回走审计

## 审计基线

- URL：`https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- commit：探索取证在 `d85758e9`（第一轮）/ `dae333dc` 之后的 master 工作区进行
  （2026-09-23 收尾留档提交为本文件所在 commit）；Gate B 正式回走开始时应把本节
  commit 更新为当时实际 HEAD。
- 角色：已登录普通创作者
- viewport：正式证据与截图固定为 1280x720
- locale：zh-CN
- 审计时间：2026-09-23（备注更新；正式回走未开始）

## 结果

| 任务 | 结果 | 级别 | 证据 | 修复 |
|---|---|---|---|---|
| create-first-node | 未开始（已有两轮交互取证） | - | `SOURCE_OBSERVATIONS.md` §1、§13.2 | 待按手册 Gate B 回走 |
| navigate-canvas | 未开始（已有交互取证） | - | §13.8 | 待回走 |
| edit-selected-node | 未开始（已有交互取证） | - | §2、§13.3、§13.4 | 待回走 |
| connect-nodes | 未开始（已有交互取证） | - | §4、§13.5 | 待回走 |
| duplicate-delete-history | 未开始（已有交互取证） | - | §7、§13.1、§13.6 | 待回走 |
| organize-and-search | 未开始（已有交互取证） | - | §5、§13.7 | 待回走 |
| canvas-context | 未开始（已有观察取证） | - | §13.10 | 待回走 |
| help-and-shortcuts | 未开始（已有交互取证） | - | §6、§13.9 | 待回走 |

## 未覆盖与已接受限制

- 正式 Gate B 回走未开始；上表“取证”指探索轮的交互证据，不替代按手册回走。
- 帮助面板声明但环境限制未独立执行的项（⌘V、M、?、双击节点聚焦、滚轮、触摸板
  手势、空格拖动）在手册正文中必须保持“声明/待验证”分类，不得标 `verified`。
- 实际文件上传、面包屑层级切换动作、新建/重命名/删除画布、图片生成与积分消耗
  未验证（超出安全边界或需真实副作用）。
- 不将 `docs/research/frameos/BEHAVIORS.md` 的 clone 行为写成源站事实。
- 截图 17 已对用户自有项目名称模糊遮蔽；后续新截图如涉及用户内容须同样处理。
