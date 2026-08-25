# Panorama Derivation Specification

## Scope

- `src/components/ImageToolbar.tsx`
- `src/components/nodes/ImageNode.tsx`
- `src/components/ImageEditPanel.tsx`
- `src/store/canvasStore.ts`

## Action contract

When the selected image toolbar dispatches `全景`:

```text
source image
  └── edge
      └── selected empty image node: 720°全景图
          └── panorama edit panel
```

The action adds one node and one edge in one graph history transaction.

## Derived node contract

```ts
{
  type: "image",
  width: 700,
  height: 350,
  data: {
    filename: "720°全景图",
    width: 700,
    height: 350,
    imageUrl: null,
    placeholderKind: "panorama",
    editorVariant: "panorama",
    editorHeight: 252,
    references: [source.imageUrl],
    generationSettings: "2:1 · 标准画质 · 2K · 1张"
  }
}
```

Position:

```text
x = source absolute x + source width + 120
y = source absolute y - 110
```

The new node remains top-level even if the source is parented.

## Placeholder contract

- dark `#212121` media surface;
- centered muted image icon;
- no copied source media;
- filename and dimensions remain in the standard floating node title;
- standard handles and selected border remain active.

## Panel contract

- same node-centered, inverse-scaled anchor model as other image editors;
- width `660px`;
- source-derived height `252px`;
- one reference thumbnail from the source image;
- visible copy:
  - `+参考`
  - `720全景`
  - `点击生成，直接将场景图像转为720全景图，支持文生/参考图`
  - `Lib Image`
  - `2:1 · 标准画质 · 2K · 1张`
- submit only sets explicit local prototype feedback.

## Stable selectors

- `[data-image-placeholder="panorama"]`
- `[data-panorama-edit-panel]`
- `[data-panorama-reference]`
- `[data-panorama-prompt]`
- `[data-panorama-submit]`

## Non-goals

- No real 720° conversion.
- No generated panorama media.
- No panorama viewer.
- No claim that other image toolbar actions share this exact node/panel structure.

