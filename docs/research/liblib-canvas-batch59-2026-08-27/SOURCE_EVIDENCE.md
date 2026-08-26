# Batch 59 Source Evidence

## 1. 本轮源站只读尝试

观察日期：2026-08-27。

目标：

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

结果：

- 画布 URL 在当前浏览器会话中重定向到 `https://www.liblib.tv/` 首页；
- 首页可见“导演台 独家 3D 虚拟场景，精准控制空间”入口；
- 点击该入口打开登录对话框，显示“微信一键登录”，而不是认证后的
  Director 资源库；
- 本轮没有输入账号、扫码、上传、生成、保存、下载或修改源站项目；
- 因此本轮没有取得资源库 DOM/CSS、筛选器、卡片或真实资产 schema 证据。

这些是本轮浏览器可见事实，不代表 LibTV 的完整产品能力边界。

## 2. 仍然有效的已有证据

- Batch 34：Director 是独立的 3D/R3F 工作区，具有场景、对象、摄像机、
  时间轴和导出 vocabulary；
- Batch 45：对象树、Inspector、场景对象和 group/crowd authoring 已形成
  clone-owned shell；
- Batch 48：`我的模型`、本地 `.fbx/.obj` 描述符、localStorage persistence
  和 proxy object insertion 已形成 bounded contract；
- 上游 `storyai-3d-director-desk`：资源库/对象插入的组件边界和交互组织可
  作为借鉴，但不等同于 LibTV source evidence。

## 3. 本批证据分类

| 主张 | 类型 |
|---|---|
| 首页有“导演台 独家 3D 虚拟场景，精准控制空间”入口 | `SOURCE_FACT` |
| 点击入口在本轮会话打开登录弹窗 | `SOURCE_ACCESS_FACT` |
| LibTV 资源库包含模型/环境/我的模型 tabs | `CLONE_CONTRACT`，由现有 clone/上游边界驱动 |
| 资源卡 query、preview 和 add-object 语义 | `CLONE_DECISION` |
| exact panel size、asset thumbnails、remote persistence | `UNKNOWN` |

## 4. 复核条件

只有在用户重新完成认证且画布路由保持可访问时，才重新采集：

- 资源库入口位置和名称；
- 模型/环境/我的模型分类；
- 搜索、筛选、排序和空状态；
- 资源预览与加入场景动作；
- asset identity、对象树显示名和 Inspector 映射；
- desktop/mobile panel geometry。

