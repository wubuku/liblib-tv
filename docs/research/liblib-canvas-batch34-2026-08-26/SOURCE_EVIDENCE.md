# Batch 34 Source Evidence

## 1. Research Source

| Field | Value |
|---|---|
| Repository | `jiguang132/storyai-3d-director-desk` |
| URL | `https://github.com/jiguang132/storyai-3d-director-desk` |
| Requested use | 作为当前项目的研究子模块，不直接接入运行时代码 |
| Initial remote observation | 2026-08-26 |
| Local fixed commit | 待引入子模块后填写 |

## 2. Initial Remote Facts

GitHub repository page and visible README currently describe it as a browser-based
3D director desk demo built with React, Vite, Three.js and React Three Fiber.
The repository page exposes `src/`, `public/models/`, `images/`, `package.json`,
`LICENSE` and Vite/TypeScript configuration files.

The visible README lists these capabilities:

- director view / camera view switching;
- built-in characters and poses;
- adding characters, extras, primitives and cameras;
- local FBX / OBJ model import and a custom model library;
- crowd arrays;
- panorama import and background adjustment;
- camera capture, screenshot records and basic shot management;
- aspect-ratio frame, grid, pan / rotate / zoom controls;
- local scene persistence, JSON export/import and recent-project recovery;
- host-page communication bridge for embedding.

The visible package metadata states MIT licensing, React 18, Vite 6,
`@react-three/fiber`, `@react-three/drei`, `camera-controls`, `three`, `zustand`
and `lucide-react`. These are remote metadata observations; the submodule commit
and local source inspection remain the authoritative evidence for this batch.

## 3. Evidence Classification

| Observation | Classification | Follow-up |
|---|---|---|
| README feature list | upstream README claim | verify against source and runtime |
| package dependency list | upstream package metadata | verify at fixed submodule commit |
| `LICENSE` is MIT | upstream repository metadata | inspect exact file text |
| no published release shown | remote GitHub page observation | record only as provenance context |
| model/image asset license | unresolved | inspect asset paths and notices; do not reuse |
| exact panel geometry and interaction timing | unresolved | inspect source; use browser only if needed |
| LibTV director-desk parity | not established | compare only after code archaeology |

## 4. Screenshot Policy

This batch begins with source code and repository metadata, not repeated whole-page
screenshot recognition. If a browser run is needed, record every visual observation
in this file or the relevant UX document immediately. Later agents should read the
ledger before opening the same screenshot or repeating the same visual inspection.

## 5. Known Boundaries

- The upstream project is an implementation reference, not evidence of LibTV behavior.
- README wording does not prove that a capability is complete or production-ready.
- The current LibTV prototype has no 3D runtime dependency and uses React Flow for
  a 2D node graph; Three.js integration therefore needs an explicit architecture
  decision.
- Local models, textures and panorama assets may have licenses separate from MIT.
