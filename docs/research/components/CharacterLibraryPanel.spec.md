# CharacterLibraryPanel Specification

## Purpose

`src/components/CharacterLibraryPanel.tsx` 是 LibTV 工作台的角色浏览 Modal。它展示角色详情、标签和横向角色列表；当前 clone 的“应用至画布”会创建一个本地图片节点。

## Evidence Boundary

| 层级 | 已确认内容 | 不能推出的内容 |
|---|---|---|
| `SOURCE_FACT` | 2026-08-25、`929x874` 视口中，Modal 为 `793x710`、居中于 `(68,82)`、圆角 `16px`；可见 4 张详情图和 23 张 `100x134` 角色缩略图 | 角色筛选/最近使用的真实数据模型、应用后的节点 identity、账户收藏和持久化 |
| `CLONE_FACT` | 当前组件切换 23 个本地角色，首个角色使用 4 张独立详情图，其他角色复用缩略图；箭头滚动列表 | 当前列表仍与线上最新角色库一致 |
| `CLONE_DECISION` | 标签由角色名称启发式派生；“最近使用”只改变 checkbox；应用创建普通 `image` 节点并关闭 Modal | 标签不是源站 metadata，checkbox 不是实际过滤，graph 副作用不是已提取的源站事务 |

证据入口：[`panel-audit.json`](../liblib-live-2026-08-25/panel-audit.json) 和 [`BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)。

## Structure

```text
CharacterLibraryPanel
├── backdrop
└── modal
    ├── header: 角色库 / close
    ├── selected-character detail
    │   ├── name + derived tags
    │   ├── 角色立绘 / 脸部近景 / 表情参考 / 三视图
    │   ├── description
    │   └── 应用至画布
    └── library rail
        ├── 角色筛选
        ├── 最近使用
        ├── previous / next
        └── 23 character buttons
```

## Geometry

Source snapshot at `929x874`:

| Property | Value |
|---|---|
| modal | `793x710` |
| position | `x=68`, `y=82` |
| z-index | `601` in sampled source |
| header | `56px` |
| detail images | three about `131x175`, one about `310x175` |
| thumbnails | first `100x134`, following sampled cards about `99x133` |

Clone constrains the modal to `calc(100vw - 24px)` and `calc(100vh - 24px)` and scrolls its content on smaller viewports. Those responsive constraints are clone decisions; the dated source audit only confirms desktop geometry.

## Local State

- `selectedIndex` starts at the first character and drives detail/title/thumbnail selection.
- `recentOnly` is a visual checkbox state only; it does not filter the list.
- Previous/next buttons call smooth horizontal scroll by `357px` and do not change selected identity.
- Selecting a thumbnail changes local detail state without mutating the graph.
- Backdrop mousedown and close button close the Modal; mousedown inside the Modal stops propagation.
- The panel participates in `uiStore.activePrimaryPanel === "character"` and shared top-level overlay mutual exclusion.

## Clone Graph Handoff

`应用至画布` currently calls `canvasStore.addNode("image", data)` with:

```text
filename = selected character name
width = 568
height = 761
imageUrl = localized thumbnail
watermarkUrl = /images/watermark.png
```

The Batch 1 clone check observed that node count increases and the new node becomes selected. This is a local prototype handoff, not a claim that LibTV uses an ordinary image node, the same dimensions or the same history transaction.

## Assets

- Character thumbnails: `public/images/liblib-panels/character-thumb-*.webp`.
- First-character detail images: `character-detail-1.webp` through `character-detail-4.webp`.
- Original source URLs and natural dimensions remain in `panel-audit.json`.

## Stable Selector

```html
data-liblib-overlay="primary:character"
```

Card, filter and apply controls currently rely on accessible names rather than dedicated test selectors.

## Verification Status

- Source screenshot: `liblib-original-character-library-2026-08-25.png`.
- Clone screenshot: `liblib-clone-batch1-character-library-2026-08-25.png`.
- Batch 1 manually recorded desktop/mobile layout and the local add/select handoff.
- Batch 11 verifies open/close, mutual exclusion and `Escape` lifecycle.
- No focused verifier proves filter semantics, persistence or source-equivalent graph output.

## Future Gate

Before extending this panel, re-inspect current source identity fields, filters, recent-use semantics, apply command, resulting node/reference role and persistence. Keep source character identity separate from temporary carousel index and ordinary clone image-node identity.
