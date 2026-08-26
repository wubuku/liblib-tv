# Batch 48 Source Evidence

## Fixed Upstream Reference

```text
repository: research/upstream/storyai-3d-director-desk
commit: 8c8bd361790be4d37158a7430365e65546e358fe
```

The evidence is code archaeology of the fixed StoryAI LibTV-oriented clone.
It is not direct evidence of the current LibTV production runtime.

## Reusable Upstream Contracts

The upstream `ViewportToolbar` and `directorStore` establish these behaviors:

- `我的模型` is populated from local model assets;
- the file input accepts multiple local model files;
- local model files are read as browser data URLs;
- imported local assets are persisted in browser storage;
- a local model card can add a scene object later without re-importing;
- deleting a local model removes its persisted asset and scene instances;
- refresh initialization restores the local model cards.

The upstream loader accepts `.fbx` and `.obj` filenames. Its actual scene
renderer uses a separate model loader/runtime and external asset boundary.

## Current Clone Gap

Batch 47 currently has:

- a `我的模型` empty state;
- no local model collection in `directorStore`;
- no browser file input owned by the model-library panel;
- no persisted local asset records;
- no delete/re-add lifecycle for local cards.

## Explicit Non-Claims

- this does not prove current LibTV uses the exact same local storage key or
  file-reader implementation;
- this does not prove production local model files are stored as data URLs;
- this does not prove FBX/OBJ parsing or model-loader support is required for
  the current LibTV canvas;
- no upstream model, thumbnail or external asset is copied.
