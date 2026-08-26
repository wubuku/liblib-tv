# Batch 59：Director 资源库浏览与加入场景

> 状态：`SCRIPT_RECORDED_PASS`。优先级：Director Desk。
> 本批目标是补齐“资源库 -> 预览 -> 加入 3D 场景”的 clone-owned 前端闭环，
> 不宣称当前 LibTV 已认证资源库 DOM/CSS 或真实资产加载语义。

## 背景

Batch 48 已完成本地模型描述符、浏览器本地持久化和 proxy object 插入；但
Director 的资源库仍缺少一个接近真实工作流的可发现入口：

```text
打开资源库
  -> 切换模型/环境分类
  -> 搜索或筛选
  -> 预览资源
  -> 加入场景
  -> 在对象树和 Inspector 中继续编辑
```

这条链路直接影响 Director 的首屏可用性和场景搭建效率，且可以复用现有
serializable `DirectorObject`、local model library 和 R3F proxy 边界。

## 证据边界

- 当前 LibTV 画布入口在本轮浏览器中被重定向到首页；点击“导演台”触发
  登录弹窗。本轮没有把登录门槛后的未知内容写成源站事实。
- Batch 34/45/48 已保存 Director 的 source vocabulary、上游代码考古和
  clone-owned 资源库边界。
- `storyai-3d-director-desk` 提供可借鉴的资源库/对象插入信息架构，但其
  DOM、CSS、数据和资产实现不能自动升级为 LibTV source fact。

## 接力入口

- [`PLAN.md`](PLAN.md)：本批范围、价值排序、决策和验收；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：源站访问结果、已有证据和未知；
- [`DIRECTOR_ASSET_LIBRARY.spec.md`](DIRECTOR_ASSET_LIBRARY.spec.md)：实现合同；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、checkpoint；
- [`runtime-audit.json`](runtime-audit.json)：focused verifier 结果；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图识别台账。

## 已完成

- 五分类既有资源浏览和文本搜索；
- 预览 selection 与 scene object insertion 分离；
- 显式“加入场景”后对象树/Inspector 连续选中；
- 搜索无结果与清空恢复；
- 保留历史卡片主体快速加入路径；
- desktop/mobile、WebGL nonblank、graph isolation 和 diagnostics verifier。

真实模型解析、远程资源、生产持久化和认证后的 LibTV exact surface 仍明确
不在本批合同内。
