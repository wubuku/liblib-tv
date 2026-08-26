# Director Local Model Library Specification

## Evidence Classification

| Contract | Basis |
|---|---|
| multiple local FBX/OBJ input | fixed upstream loader and toolbar code |
| populated `我的模型` cards | fixed upstream toolbar code/tests |
| refresh recovery | fixed upstream store code/tests |
| delete removes linked scene instances | fixed upstream store code/tests |
| proxy visual mapping and card styling | clone-owned calibration |
| actual uploaded mesh rendering | explicitly out of scope |

## Local Descriptor

The clone stores a bounded browser-local descriptor:

```ts
interface DirectorLocalModelLibraryItem {
  id: string;
  categoryId: "my-models";
  name: string;
  fileName: string;
  dataUrl: string;
  visual: "bottle" | "chair" | "lamp" | "plant" | "box";
  color: string;
}
```

The data URL is a local prototype transport, not a remote asset URL.

## Interaction Contract

- `我的模型` starts empty when no persisted local descriptors exist;
- `本地导入` opens one multiple-file input;
- only `.fbx` and `.obj` files become cards;
- importing does not add objects to the scene immediately;
- local cards expose add and delete commands;
- adding a card closes the panel and selects the new local proxy prop;
- deleting a card removes linked local proxy props;
- refresh restores cards from the clone-owned local storage key;
- Escape/outside pointer still closes the model-library panel.

## Scene Contract

- local cards use the existing `DirectorObject` prop boundary;
- the object stores local asset identity and `my-models` category metadata;
- the existing R3F proxy geometry expresses a bounded visual mapping;
- no Three.js loader object or non-serializable runtime reference enters the
  Zustand state.
