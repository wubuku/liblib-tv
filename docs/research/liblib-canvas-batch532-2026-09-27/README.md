# Batch 532 — 分镜脚本编辑器三步导航（准备资产/合成提示词）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 CDP 补采
> （浏览器重启后经 127.0.0.1:9222 重连，经画布「脚本 V2 1」进度卡的
> 「打开脚本节点 →」重新进入编辑器；JS el.click() 绕过浮层命中测试）：
> 截图 40-storyboard-step2.png / 41-storyboard-step3.png + DOM 文本采样。

## 源站实测结构（SOURCE_FACT）

- **第 2 步 准备资产**：stepper 第 2 步高亮（圆圈+文字外包浅色圆角块）；
  内容 = 三组纵向资产区「角色 / 场景 / 道具」，每组一张虚线边框
  「+ 新增」卡（≈195×190）；底栏左侧绿色 ✓ 提示「资产已生成，如再次
  生成将会覆盖之前的图片/场景/道具等资产」，右侧「→ 下一步：合成提示词」；
- **第 3 步 合成提示词**：stepper 第 3 步高亮；内容回到 10 列分镜表格，
  「最终提示词」列表头高亮（浅底白字），单元格仍为「待生成提示词」；
  底栏左侧「+ 添加镜头」，右侧「一键合成全部提示词」（白底胶囊）；
- 无「上一步」按钮（仅前进导航）；右上恒为「0/3 完成后可批量生成视频」；
- 未点击 一键合成/批量生成（付费 AI 动作，约束禁触发）。

## clone 合同（batch 531 组件扩展）

- `step` 本地状态 1/2/3；stepper 高亮随步进（激活步包浅底圆角块）；
- 第 2 步：三组 `data-storyboard-asset-group` + `data-storyboard-asset-add`
  虚线新增卡 + `data-storyboard-asset-notice` 覆盖提示（无「添加镜头」）；
- 第 3 步：表格回归 + 「最终提示词」表头高亮 + `data-storyboard-synthesize-all`
  可视按钮（真实合成为付费 AI 动作，clone 不触发任何生成）；
- 前进按钮 `data-storyboard-next="assets"/"prompts"`；无上一步（源站如此）；
- batch 531 全部合同保持不变（回归 531 绿）。

## 附带证据

- 画布现态：脚本 V2 节点在编辑器会话后转为「分镜脚本进度卡」
  （1 确认镜头 | 2 准备资产 | 3 合成提示词 | 打开脚本节点 →）——
  编辑器持久化的节点卡形态（NOTES 已记，未克隆）；
- 图片节点选中工具栏实测：人像质感调节(NEW) | 全景 | 多角度 | 打光 |
  九宫格▾ | 高清▾ | 元素编辑 | 图层分离 | 宫格切分▾（未克隆，候选 batch）。

## 内容

- `src/components/StoryboardScriptEditor.tsx`（三步导航扩展）；
- `scripts/verify-liblib-batch532.py`（16 检查）；
- 回归：batch 531/528 全绿；lint 0 error；typecheck 仅并行 WIP 错误。
- 截图 40/41：exploration 目录；`runtime-audit.json`：本目录。
