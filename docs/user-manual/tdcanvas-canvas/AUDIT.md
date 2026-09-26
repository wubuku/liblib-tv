# TDCanvas 手册回走审计（AUDIT）

> Gate B 回走证据与问题分级台账。基线：被测应用 TDCanvas `v0.14.0`（`16b3127`）@ localhost:3000。
> 状态：scaffold——Gate B 未开始。首轮探索性发现已记入 SOURCE_OBSERVATIONS.md（§3 视口语义、
> §9 官方文档差异）与 RUNTIME_AUDIT.md（调研包），不在此重复。

## 回走结论表（Gate B 逐任务追加）

| 任务 id | 回走日期 | 结果 | 发现（Blocker/Major/Minor） |
|---|---|---|---|

## 已知问题清单

| 级别 | 描述 | 影响 | 处置 |
|---|---|---|---|
| Minor | 新项目默认标题为「TDCanvas 2」（0 画布时新建即为 2），编号规则未查证 | 手册措辞避免写死「TDCanvas 1」 | 手册用「自动命名的项目标题」表述，待查证后更新 |
| Minor | 悬浮工具条在节点偏左时不做视口 clamp（左端按钮可被视口裁切） | 宽屏影响小 | 手册不承诺工具条始终完整可见 |
| Major(环境) | Playwright locator 点击被画布覆盖层拦截；page.evaluate 通道不稳定 | 仅影响自动化回走，不影响真人 | 回走一律 CUA 坐标路径 + locator("body").evaluate |

## 未覆盖清单（交付报告中须列出的已知限制）

- 生成类流程（图片/视频/音频/反推提示词/AI 角度）：付费边界，正文仅描述（来源标注），无回走。
- 视频/音频真实字节上传：素材已登记，IAB 环境限制未注入（方法见 TEST_MEDIA_ASSETS.md）。
- ComfyUI 本地环境全流程、Agent（Codex/Claude）连接全流程：超出画布手册范围。
