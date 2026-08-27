# StoryAI 借鉴决策矩阵

> 本文判断“方法是否值得继续借”，不把 StoryAI 行为升级为 LibTV 产品事实。

## 1. 决策等级

| 决策 | 含义 |
|---|---|
| `KEEP` | 当前 clone 已正确采用，继续作为架构边界 |
| `KEEP_METHOD` | 保留方法或 ownership 思想，但不保留上游产品边界、协议名或实现形态 |
| `ADAPT_NEXT` | 高价值，应在合同和编码授权后改造采用 |
| `RESEARCH_FIRST` | 值得借鉴，但需先取得 LibTV source/product 决策 |
| `DEFER` | 有价值但不是当前阻塞项 |
| `REJECT_DIRECT_COPY` | 可借意图，不复制具体实现/资产/协议 |

## 2. 模式卡

| ID | StoryAI 方法 | 当前 clone | 决策 | 理由与适配要求 |
|---|---|---|---|---|
| `STORY-PATTERN-01` | 三栏 R3F workbench | 已有 desktop/mobile shell | `KEEP` | Director 继续是独立 authoring island，不倒灌普通 React Flow store |
| `STORY-PATTERN-02` | selection -> typed Inspector route | 已扩展到 path/group/capture | `KEEP` | 新对象类型必须先进入 selection union，再挂 Inspector |
| `STORY-PATTERN-03` | project document + version + migration | 当前只有单例 store shape | `ADAPT_NEXT` | 定义 clone-owned V1 schema、strict decoder、migration 和 owner key |
| `STORY-PATTERN-04` | mutation snapshot + undo batch | 当前无 Director history | `ADAPT_NEXT` | 区分 pointer gesture/local history、Director semantic history、canvas graph return history |
| `STORY-PATTERN-05` | copy/paste/delete object workflow | 当前通用对象 CRUD 不完整 | `ADAPT_NEXT` | 先定义 object/group/track/path/camera/capture reference repair，不能简单 filter |
| `STORY-PATTERN-06` | camera object + shot record 双实体 | clone 把 camera data 内嵌 object | `RESEARCH_FIRST` | LibTV multi-shot 语义未证实；先决定 camera rig、shot、capture 的 identity |
| `STORY-PATTERN-07` | panorama 作为 project asset + scene projection | Director 无 panorama ingress | `ADAPT_NEXT` | 可连接普通 LibTV panorama/media node，但需 media lease 与 source owner 合同 |
| `STORY-PATTERN-08` | model/panorama loaders 与 asset refs 分层 | clone descriptor/proxy 混合 | `ADAPT_NEXT` | intent -> validate -> probe/parse -> lease -> asset -> scene instance；不存 runtime refs |
| `STORY-PATTERN-09` | scoped local persistence / latest snapshot | 仅 local model catalog 持久化 | `ADAPT_NEXT` | key 至少包含 route/canvas/director-node/schema-version；quota/error 可见 |
| `STORY-PATTERN-10` | ready/session/panorama/capture host bridge | 同应用 direct store/callback | `KEEP_METHOD` | 保留 typed envelope/owner 思想，不复制 `storyai:*` message name 或 iframe boundary |
| `STORY-PATTERN-11` | aspect-aware helper-free capture | 已有 still/video return | `KEEP` | capture surface 与 editing helper 必须继续分离，输出事务保持原子 |
| `STORY-PATTERN-12` | numeric field drag + undo batch | clone numeric input 较多但无统一 gesture history | `ADAPT_NEXT` | 高价值微交互；必须与 pointer capture、one-gesture-one-entry 联动 |
| `STORY-PATTERN-13` | scene transform、ground、labels、snap | clone scene settings 较薄 | `RESEARCH_FIRST` | 低风险能力，但名称/范围/默认值先查 LibTV source 或标 clone-owned |
| `STORY-PATTERN-14` | multi-camera creation and camera capture grouping | clone 单默认机位 | `RESEARCH_FIRST` | 先取 source evidence，再实现 camera/shot lifecycle |
| `STORY-PATTERN-15` | broad upstream unit-test corpus | clone 以 batch Playwright 为主 | `ADAPT_NEXT` | math/store/schema 用 unit tests；关键用户流保留 Playwright；建立 current manifest |

## 3. 不直接复制

| 上游做法 | 决策 | 原因 |
|---|---|---|
| `JSON.parse(...) as DirectorProject` | `REJECT_DIRECT_COPY` | 只有 cast，没有 runtime schema validation；clone 数据结构更复杂 |
| 把 data URL 长期写入 localStorage | `REJECT_DIRECT_COPY` | quota、性能和资源释放不可控；只适合有界 prototype |
| 外部 `模型库/` 路径和缩略图 URL | `REJECT_DIRECT_COPY` | 构建已警告缺失路径，且资产许可独立于 MIT code |
| 上游 CSS 尺寸和色值 | `REJECT_DIRECT_COPY` | 它们是 StoryAI 视觉事实，不是 LibTV source measurement |
| 上游模型/贴图/README screenshots | `REJECT_DIRECT_COPY` | 代码许可证不自动覆盖第三方资产再分发 |
| 继续嵌套 Vite app / iframe | `REJECT_DIRECT_COPY` | 当前 Next.js 内的 R3F island 已拥有更清晰类型与 graph transaction 边界 |
| `storyai:*` postMessage 协议原样照搬 | `REJECT_DIRECT_COPY` | 当前同应用架构不需要保留上游品牌协议；owner/version/result envelope 才是可借方法 |
| 把上游 304/312 当作可信基线 | `REJECT_DIRECT_COPY` | 8 个 test drift 证明源码和断言未完全同步 |

## 4. 对当前代码组织的启发

StoryAI 的 `schema / store / selectors / io / loaders / runtime / panels / canvas`
分层比当前 `3,846` 行 `directorStore.ts` 和 `2,368` 行 `DirectorViewport.tsx`
更利于后续并行工作。未来若获得编码授权，重组应由真实边界驱动：

```text
director/schema       serializable project + migration
director/commands     typed mutations + reference repair + history
director/resources    import intents, leases, metadata and parsers
director/runtime      R3F-only objects, loaders and sampling adapters
director/io           project import/export + canvas result bridge
director/surfaces     shell/tree/viewport/inspector/timeline panels
```

这不是立即大重构建议。先把 schema、command 和 resource 合同写清，再按新增能力
搬迁；不得以“像上游目录”为目标做无行为收益的文件移动。

## 5. 当前采纳优先级

1. `STORY-PATTERN-03` project/version/migration；
2. `STORY-PATTERN-04/05` Director history 与 reference-aware CRUD；
3. `STORY-PATTERN-08/09` resource lifecycle 和 scoped persistence；
4. `STORY-PATTERN-07` panorama/media host input；
5. `STORY-PATTERN-15` current verifier manifest；
6. `STORY-PATTERN-06/14` multi-camera/shot，在 source/product 语义明确后推进。
