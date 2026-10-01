# TDCanvas 用户手册

> 适用版本：TDCanvas `v0.14.0`（Web 与桌面客户端，界面一致）。
> 面向读者：使用 TDCanvas 进行 AI 图片/视频/音频创作的普通用户。
> 手册中所有界面文字均取自当前版本的真实界面；生成类操作涉及按量计费，请留意各页的费用提示。

## 这是什么

TDCanvas 是一个**本地优先**的 AI 无限画布：把提示词（文本）、参考素材、图片、视频和音频放在同一张无限画布上，通过连线组织「素材 → 生成」的流程，节点内容自动保存在本机。

## 快速开始

从零到第一个节点只需 2 分钟：[00-quickstart.md](00-quickstart.md)。

## 任务指南（How-to）

| 我想…… | 页面 | 深度 |
|---|---|---|
| 创建画布项目并认识工作区 | [create-canvas-project.md](10-tasks/create-canvas-project.md) | 旗舰 |
| 平移、缩放、用小地图导航 | [navigate-canvas.md](10-tasks/navigate-canvas.md) | 旗舰 |
| 创建文本/图片/视频/音频/组节点 | [create-nodes.md](10-tasks/create-nodes.md) | 旗舰 |
| 上传本地图片、视频、音频 | [upload-materials.md](10-tasks/upload-materials.md) | 旗舰 |
| 重命名、改文字、缩放节点 | [edit-nodes.md](10-tasks/edit-nodes.md) | 旗舰 |
| 连线引用与无线引用 | [connect-references.md](10-tasks/connect-references.md) | 旗舰 |
| 发起图片生成、理解任务状态 | [generate-images.md](10-tasks/generate-images.md) | 完整 |
| 裁剪、切图、放大（免费本机处理） | [image-operations.md](10-tasks/image-operations.md) | 完整 |
| 分组、主题与背景外观 | [organize-canvas.md](10-tasks/organize-canvas.md) | 完整 |
| 撤销重做与自动保存 | [undo-persistence.md](10-tasks/undo-persistence.md) | 完整 |
| 管理项目（列表/重命名/导出/删除） | [project-management.md](10-tasks/project-management.md) | 完整 |
| 收藏、检索、导出我的资产 | [manage-assets.md](10-tasks/manage-assets.md) | 完整 |
| 浏览提示词库（当前版本为空） | [use-prompt-library.md](10-tasks/use-prompt-library.md) | 简明 |
| 快捷键与帮助 | [shortcuts-help.md](10-tasks/shortcuts-help.md) | 简明 |

## 参考

- [20-reference.md](20-reference.md)：键位表、格式与限制、任务状态、设置项。

## 概念解释

- [30-concepts.md](30-concepts.md)：节点类型、连线语义、连线/无线双模式、项目与自动保存。

## 排障

- [90-troubleshooting.md](90-troubleshooting.md)：按症状查找原因与修复方法。

## 费用与安全提示

- 画布的节点创建、素材上传、连线、裁剪/切图/放大等操作**全部在本机完成，免费**。
- 点击「生成」类按钮会调用 AI 服务**按量计费**：请先在「配置」中确认 API Key 与模型，再开始生成。
- 手册中的生成流程说明以当前版本真实界面为准；涉及计费的细节以 Aitudou 平台账单为准。

## 以网站形式查看本手册

本手册已构建为 **VitePress 静态网站**（含侧边栏导航与中文全文搜索 ⌘K），构建产物在本目录 `.vitepress/dist/`（2026-10-01 构建：21 页 / 58 张截图 / 17M）。

**本地查看（二选一）**：

```bash
# 方式一：预览服务（浏览器打开 http://localhost:4173）
# 端口被其他手册预览占用时换一个（如 4174）：截图在 dist 内为 /assets/ 哈希路径
python3 -m http.server 4174 -d .vitepress/dist

# 方式二：直接用浏览器打开文件
open .vitepress/dist/index.html
```

**重新构建**（手册内容更新后）：

```bash
./build-site.sh            # 六步一键构建，产物刷新到 .vitepress/dist/
./build-site.sh --preview  # 构建后自动启动 :4173 预览
```

构建/发布的完整说明（含子路径部署与运维 FAQ）见 [PUBLISH.md](PUBLISH.md)。
