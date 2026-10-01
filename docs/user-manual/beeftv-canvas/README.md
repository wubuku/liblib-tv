# BeefTV 用户手册

> 适用版本：BeefTV `v1.6.16`（Web 与桌面端）。界面文字逐字取自真实运行界面或对应版本源码，不做翻译或改写。
> 面向读者：使用 BeefTV 进行 AI 视频/图片创作、时间线剪辑与导演台编排的普通用户、Agent 用户与管理员。
> 覆盖情况：**29 篇任务指南** + 任务索引 + 快速上手 + 参考表 + 概念解释 + 故障排查，共 **35 个内容页**（另加首页与 404）、**67 张实拍截图**；任务账本共 **35 项**——其中 **29 项**已在 v1.6.14 上逐条走查验证，**6 项**因产品侧入口未开放或属已退场功能而无法验证，已在对应页面写明原因。逐条状态见 `task-inventory.yml`。
> v1.6.14 之后的增量：**v1.6.15** 生成排查信息升级到版本 2（新增请求 ID 与上游代码、保留错误来源与请求证据、丢失提交回执改为「未确认」而非静默重发）；**v1.6.16** 视频任务失败可「取回结果」——复用原任务拿回结果、**不重新计费**，下载断线支持后台有界恢复。详见 [generate-video.md](10-tasks/generate-video.md) 与 [90-troubleshooting.md](90-troubleshooting.md)。

## 这是什么

BeefTV 是一个「无限画布 + 时间线剪辑 + 三维导演台 + 云端 Agent」的 AI 影视创作工作台：

- **无限画布**：把提示词、参考素材、图片、视频、音频放在同一张画布上，连线组织「素材 → 生成」流程；
- **时间线剪辑**：把生成的片段拖上轨道剪辑，配字幕、导出成片；
- **导演台**：三维场景里摆机位、设运镜、录关键帧动画，一键渲染白膜视频；
- **云端 Agent**：用自然语言让 Agent 替你操作画布，关键操作需你审批。

## 从这里开始

| 我想做的事 | 从哪读起 |
|---|---|
| 第一次打开 BeefTV | [00-quickstart.md](00-quickstart.md) |
| 建节点、传素材、连参考 | [10-tasks/](10-tasks/README.md) |
| 整理画布库：搜索、文件夹、导入导出 | [10-tasks/manage-canvases.md](10-tasks/manage-canvases.md) |
| 把画布给别人看、留一份副本 | [10-tasks/readonly-canvas.md](10-tasks/readonly-canvas.md) |
| **先配一个模型渠道**（生成前的前置步骤） | [10-tasks/model-channels.md](10-tasks/model-channels.md) |
| 生成图片或视频 | [10-tasks/generate-images.md](10-tasks/generate-images.md) · [10-tasks/generate-video.md](10-tasks/generate-video.md) |
| 剪辑、配字幕、导出成片 | [10-tasks/timeline-editing.md](10-tasks/timeline-editing.md) · [10-tasks/subtitle-highlights.md](10-tasks/subtitle-highlights.md) · [10-tasks/timeline-export.md](10-tasks/timeline-export.md) |
| 搭三维场景与运镜 | [10-tasks/director-basics.md](10-tasks/director-basics.md) |
| 查快捷键、路由、接口 | [20-reference.md](20-reference.md) |
| 搞懂名词与设计取舍 | [30-concepts.md](30-concepts.md) |
| 报错了先看这里 | [90-troubleshooting.md](90-troubleshooting.md) |

## 需要先知道的四件事

1. **生成前得先有模型——这一步挡在所有生成动作前面**。新装好的 BeefTV **默认一个可用模型都没有**（出厂配置里渠道是空的、也没有 API Key，源码注释写明「不能内置供应商模型」）。直接去点「生成」会看到提示「**当前没有可用模型，请联系管理员或检查模型配置**」——**但本地部署里没有管理员可找，模型是你自己配的**：去 [10-tasks/model-channels.md](10-tasks/model-channels.md) 配一个渠道和 Key 再说。
2. **生成类操作按量计费**——提交图片/视频生成会消耗渠道额度，相关页面都标注了费用提示与「可能再次消耗积分」的防重复扣费确认；
3. **字幕入口不在视频节点上**——要在多轨时间线里点选 S 轨字幕片段，再点「精细编辑」；
4. **部分功能需要本地或后台配合**——深度/线稿/姿态需要本机伴随进程，语音转写字幕需要本机 whisper.cpp，缺配置时会有明确报错（见 [90-troubleshooting.md](90-troubleshooting.md)）。

## 约定

- 界面文字（按钮、菜单、提示）均逐字取自 BeefTV 真实界面；
- 快捷键以 macOS 修饰键书写（⌘/⇧/⌥），Windows 对应 Ctrl/Shift/Alt；
- 标注「源码核查」的段落表示该功能在当前版本界面上尚未开放，只说明已确认的事实，不外推操作步骤。

---

## 维护者

站点由 `./build-site.sh` 一键构建为纯静态产物到 `.vitepress/dist/`，完整说明见同目录的 `PUBLISH.md`（该文件不进入发布站点，因此上文不用超链接引用）。**改动正文后必须重新构建**——否则发布产物里仍是旧内容，这类静默过期已发生过多次。截图清单与逐张 sha256 见 `screenshots/manifest.yml`。
