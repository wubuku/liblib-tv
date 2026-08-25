# Batch 25 计划：智能剪辑空态与节点下方 Prompt 面板

## 1. 缺口与价值

| 缺口 | 当前 clone | 源证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 节点职责 | 节点内同时承载空态和完整编辑器 | 节点只显示空态/尝试入口 | 5 | 拆分 |
| Prompt 位置 | textarea 在节点内部 | `660px` 屏幕固定面板位于节点下方 | 5 | 新增 panel |
| 标题层级 | 节点内自创“智能剪辑 Beta” header | 外部标题为“智能剪辑 1” | 4 | 移除内部 header |
| 空态 | 没有连接提示 | `空空如也，请连接视频节点后操作` | 5 | 补齐 |
| 模式布局 | 2x2 active grid | 空态“尝试：”下四个命令 | 4 | 改为空态命令 |
| 参考入口 | 节点内 dashed row | panel 左上 `+参考` pill | 5 | 移到 panel |
| Prompt | 节点内 flex textarea | panel 主体 `描述想剪成什么效果` | 5 | 移到 panel |
| Footer | 节点内 compact row | panel 底部“默认模式 / 16:9 · 720P · 30s / submit” | 5 | 对齐 |
| 面板锚定 | 无独立 panel | 中心对齐、约 `660x191`、`16 * zoom` gap | 5 | 复用已验证合同 |
| 后端能力 | 本地 UI | 当前无真实智能剪辑服务 | 5 | 明确 mock 边界 |

该节点已有专门原站截图、live type、世界尺寸、完整文案和 button 集合。结构纠偏的证据置信度高于继续实现工具栏中尚无截图的后处理菜单。

## 2. 实施步骤

1. 新增 `VideoClipEditPanel`：
   - node-relative absolute wrapper；
   - `660x191` screen size；
   - `1 / zoom` 反缩放；
   - source semantic `16 * zoom` gap；
   - `+参考`、expand、Prompt、mode/settings、disabled submit。
2. 重构 `VideoClipNode`：
   - 保留外部标题“智能剪辑 1”；
   - 内部居中剪刀空态；
   - 文案“空空如也，请连接视频节点后操作”；
   - “尝试：”和四个 source-confirmed mode command；
   - 单选时挂载 panel，多选时隐藏。
3. 本地交互：
   - mode command 更新 panel footer；
   - `+参考` 显示“请连接视频节点”的本地反馈；
   - Prompt 输入启用 submit；
   - submit 只显示本地任务反馈。
4. 新增 Batch 25 Playwright：
   - 空画布添加 video-clip；
   - 验证 node/panel 内容分层；
   - `350x350` world size；
   - panel `660x191`、中心和 gap；
   - 28%/50% zoom 后 panel 屏幕尺寸不变；
   - node drag/pan 跟随；
   - mode、reference、Prompt、submit；
   - multi-selection hide；
   - 390px 自然裁切与无 document overflow；
   - 生成桌面、detail、mobile 截图。

## 3. 事实边界

### Source fact

- live React Flow type：`react-flow__node-video-clip`。
- world size：约 `350x350`。
- 外部标题：`智能剪辑 1`。
- 节点文本：
  - `空空如也，请连接视频节点后操作`
  - `尝试：`
  - `讲解视频 / 批量广告 / 口播视频 / 素材混剪`
- 选中态按钮集合：
  - 四模式
  - `参考`
  - `默认模式`
  - `16:9 · 720P · 30s`
  - disabled `发送`
  - 一个无文本命令
- Prompt placeholder：`描述想剪成什么效果`。
- screenshot 显示 Prompt editor 位于节点下方，而不是节点内部。

### Pixel-backed inference

- source screenshot viewport：`929x874`，zoom 文案 `28%`。
- source node screen box：`98.979x98.979`，与 `350x350 * 0.282798` 一致。
- panel 约 `660x191`，中心与节点约 `x=513.29` 对齐。
- node/panel gap 约 `4.5px`，与 `16 * 0.282798` 一致。
- panel 几何来自截图边缘估计，不是 live DOM rect。

### Clone-only decision

- mode command 只更新 footer 文案。
- `+参考` 在未连接视频时显示本地提示。
- submit 只产生本地“已创建任务”反馈。
- 不根据现有 edge 推断真实剪辑输入或生成结果。

## 4. 验收标准

- 节点内部不存在 textarea、参考 row 或 output settings footer。
- 节点显示 source-confirmed 空态和四模式。
- 单选节点时显示 `[data-video-clip-edit-panel]`。
- panel 为 `660x191`，中心等于节点中心，gap 为 `16 * zoom`。
- panel 在 28%/50% zoom 下仍保持 `660x191` screen size。
- mode、reference、Prompt 和 submit 均有本地可验证反馈。
- 多选时 panel 隐藏；恢复单选后重新显示。
- 390px 下 panel 自然左右裁切，但 document 不产生横向 overflow。
- Batch 9、15、23-25 与完整工程门禁通过。
