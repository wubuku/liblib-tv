# Batch 95：Director 画布媒体入口与全景环境预览

> 状态：`PLANNED`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`ef7e4ba`。

本批把当前普通 LibTV 画布中已有可渲染图片，以 typed、session-only 的方式交给
Director 作为环境预览输入。目标是补齐 Director 纵向体验中的第一个真实 host
handoff，而不是把普通画布的资源系统或远程上传能力一次性搬入 Director。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界、停止条件和验证计划。
- [DIRECTOR_CANVAS_MEDIA_INGRESS.spec.md](DIRECTOR_CANVAS_MEDIA_INGRESS.spec.md)：
  实施合同和稳定选择器。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：实施与验证结果，完成后更新。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据，完成后生成。

## 证据边界

- `LIBTV_SOURCE_FACT`：既有媒体入口和全景节点研究；本批不新增认证源站 DOM/CSS
  结论。
- `CLONE_FACT`：当前 Director 由普通画布的 `script-execution` 节点打开；普通
  画布图片节点可携带 `imageUrl`，全景派生节点可能仍是占位态。
- `STORYAI_FACT`：上游的 panorama/asset 分层只作为数据边界启发。
- `DECISION`：本批的环境球、入口选择器和会话投影是 clone-owned；输入只限
  Director 节点的直接图片上游，且仅接受已有 URL 的图片。
- `INFERENCE`：这条链路能验证 host handoff、选择/清除和 R3F 渲染，但不能证明
  LibTV 原站采用同样的 3D 全景协议或 UI。

## 截图识别策略

本批不需要截图识别。实施和验证只使用 DOM、store snapshot、WebGL canvas
nonblank 和浏览器 diagnostics；`screenshotsWritten=false`。

