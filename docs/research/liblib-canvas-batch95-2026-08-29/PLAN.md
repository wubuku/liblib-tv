# Batch 95 计划：Director 画布媒体入口与全景环境预览

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`ef7e4ba`。

## 1. 背景与目标

Director 当前已经具备 R3F 工作区、对象/相机/时间线、项目文档、浏览器本地
模型资源 lease 和截图回流，但它与普通 LibTV 画布之间只有 Director capture
向画布回流，没有画布媒体向 Director 场景进入的纵向链路。

本批目标：

1. 从当前 Director 节点的直接上游识别图片媒体；
2. 用 typed descriptor 将可渲染图片交给 Director 会话；
3. 在 Director 场景中显示/隐藏一个非交互的 equirectangular 环境球；
4. 在 Inspector 的场景设置中提供输入选择、清除和状态反馈；
5. 选择变化不进入 Director project document/history，明确标记为
   `SESSION_ONLY_HOST_PROJECTION`；
6. 保持普通画布、Director project schema、local model resource lifecycle 和
   capture/export 不变。

## 2. 高价值理由

这是当前评估意见中“panorama/media node -> Director scene input”的最小真实
纵切。它连接了两个现有产品岛，同时暴露资源是否可渲染、输入是否仍属于当前
canvas/Director owner、清除后是否释放运行时 texture 等关键边界。

它不等同于完成真实 panorama 资源系统：全景派生节点若没有 URL，必须显示为
不可用，而不是把占位符误当作可加载媒体。

## 3. 证据分层

| 标签 | 本批含义 |
|---|---|
| `LIBTV_SOURCE_FACT` | 来自既有 2026-08-27 认证媒体入口研究；本批不重新解释源站 |
| `CLONE_FACT` | 当前仓库中的节点、边、Director route/store 和 R3F 实现 |
| `STORYAI_FACT` | 上游有资源/场景投影的分层启发，不是 LibTV 事实 |
| `DECISION` | clone-owned 的直接上游图片选择、环境球和 session-only 投影 |
| `INFERENCE` | 该纵切对 host handoff 和 runtime cleanup 的合理推断 |
| `SOURCE_UNKNOWN` | LibTV 原站是否使用同样的 Three.js/R3F 全景实现 |

## 4. 范围

### P0：typed host input

- 新增纯函数，将 `CanvasData`、Director node id 和 edges 转换为
  `DirectorCanvasMediaInputV1[]`；
- 只收集直接入边的 `image` 节点；
- 只接受非空 `imageUrl`；
- 标记 `sourceKind` 为 `panorama` 或 `image`，保留 source node id、文件名、
  intrinsic dimensions 和 URL；
- 不读取 `File`、不调用上传接口、不改普通 graph。

### P0：Director session projection

- Director 打开时默认选择第一个可用上游图片；
- 可在场景 Inspector 切换输入或清除；
- 选择与清除只影响当前 Director mount/session；
- 当前输入失效时自动清除，且不抛异常。

### P1：R3F environment preview

- 以 `TextureLoader` 加载当前 URL；
- 使用反面材质的 sphere 作为环境预览；
- URL 变化或组件卸载时 dispose texture；
- 加载失败显示 DOM 状态，不阻断其他 Director 对象和控件；
- 不让环境球拦截对象点击或 TransformControls。

### P1：验证与文档

- 新增 Batch 95 Playwright verifier，覆盖候选发现、默认投影、切换/清除、
  stale source、WebGL runtime 和 zero diagnostics；
- desktop `1440x900`、mobile `390x844` 至少各跑一条关键路径；
- 不生成截图，不重复截图识别；
- 更新稳定索引和验证台账。

## 5. 不在本批范围

- 不改变 `DirectorProjectDocumentV1` schema，不新增 migration；
- 不把 session-only 输入写入 project JSON、Director history 或 localStorage；
- 不实现普通画布文件上传、资源 registry、remote URL 校验或 cloud persistence；
- 不把没有 `imageUrl` 的占位全景节点伪装为真实资源；
- 不宣称 LibTV 原站的 exact DOM/CSS、Three.js/R3F 实现或 panorama 协议；
- 不新增截图或视觉识别；
- 不引入 worktree。

## 6. 稳定选择器

| 选择器 | 用途 |
|---|---|
| `[data-director-panorama-source]` | 场景输入选择器 |
| `[data-director-panorama-source-option]` | 可选画布媒体项 |
| `[data-director-panorama-clear]` | 清除当前媒体 |
| `[data-director-panorama-state]` | `empty` / `ready` / `loading` / `error` |
| `[data-director-panorama-source-id]` | 当前 source node id |
| `[data-director-panorama-runtime]` | R3F 环境球投影状态 |
| `[data-director-panorama-error]` | 纹理加载失败反馈 |

## 7. 完成条件

1. `DirectorCanvasMediaInputV1` 只输出当前 canvas、当前 Director node 直接上游
   的可渲染图片；
2. 默认输入、切换、清除和 source stale 都有可观察状态；
3. R3F 环境球在有效 URL 下渲染，且不覆盖对象选择/变换；
4. 明显非法 data URL 在进入浏览器加载器前被拒绝；texture load failure 不导致
   page/request error；
5. 专项 verifier、相关 Director current gates 和项目质量门通过；
6. 实施结果、运行时 JSON、稳定索引和证据边界已落档；
7. commit/push 后 `master == origin/master` 且工作区干净。

## 8. 预定命令

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch95.py

LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch94.py

npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```
