# LibTV + FrameOS Canvas Clones

> 两条独立的画布前端原型：复刻 `liblib.tv/canvas` 与 `frameos.cn` 的核心画布、节点和浮层交互。
> Next.js 16 · React 19 · TypeScript strict · React Flow 12 · Zustand · Tailwind CSS 4

本项目用于研究、验证和持续复刻 AI 画布产品的前端 UI/UX。它是前端原型，不提供真实生成、上传、账户、协作或服务端持久化。

## Routes

| Route | Product | Purpose |
|---|---|---|
| `/` | LibTV clone | 视频故事板画布、图片/视频生成面板、素材与画布工具 |
| `/frameos` | FrameOS entry | 重定向到 `/frameos/canvas/demo` |
| `/frameos/canvas/[id]` | FrameOS clone | Prompt + 节点画布、素材库、历史、快捷键与生成 mock |

## Features

- LibTV：10 节点、11 条边、分组与视频 parent-child 层级
- LibTV：选择、框选、多选、移动、复制、成组、整理、pan、zoom、grid snap
- LibTV：图片上下浮层、Seedance 2.5 视频生成、片段重拍、逐帧拉片、智能剪辑原型
- LibTV：真实 R3F 导演台、对象/机位/时间轴/路径编辑、截图与可播放动画视频回流
- FrameOS：独立 store、独立节点系统、浮动工具条、Prompt 编辑器、右键菜单、undo/redo
- 研究证据：原站 DOM/JSON、截图、组件规格、批次计划与实施历史
- 自动验证：Batch 4-40 专项 Playwright 脚本、lint、typecheck、production build

## Quick Start

Prerequisite: Node.js 24+.

```bash
npm install
npm run dev
```

Open:

- LibTV: `http://localhost:3000`
- FrameOS: `http://localhost:3000/frameos/canvas/demo`

Verification:

```bash
npm run lint
npm run typecheck
npm run build
npm run check
python3 scripts/verify-docs.py
```

## Documentation

| Need | Start here |
|---|---|
| Agent navigation and red lines | [`AGENTS.md`](AGENTS.md) |
| Full documentation map | [`docs/index.md`](docs/index.md) |
| Architecture and route boundaries | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Development and verification | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) / [`docs/HARNESS.md`](docs/HARNESS.md) |
| Research evidence and batch history | [`docs/research/README.md`](docs/research/README.md) |
| Current detailed system picture | [`docs/BIG_PICTURE.md`](docs/BIG_PICTURE.md) |
| Contribution and documentation rules | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

## Prototype Boundaries

- Zustand stores are in-memory; refresh loses graph changes.
- AI generation, upload, download, sharing, authentication and collaboration are local UI mocks.
- LibTV organize coordinates are evidence-based for the current 10-node project, not a general layout engine.
- FrameOS supports only its currently registered text/image/video renderers; other model kinds remain outside this prototype.

## License

MIT. See [`LICENSE`](LICENSE).
