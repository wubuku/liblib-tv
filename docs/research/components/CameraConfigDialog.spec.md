# CameraConfigDialog Specification

## Overview

- **Target file:** `src/components/CameraConfigDialog.tsx`
- **Triggered from:** `ImageEditPanel` "摄像机" button (selected image node)
- **Interaction model:** Modal dialog — pick from preset grid → apply

## Purpose

Configure a virtual camera setup (camera body + lens + focal length + aperture) before generating a derivative image. Imitates LibTV's per-asset camera configuration UI.

## DOM Structure

```
<div className="fixed inset-0 z-[60] flex items-center justify-center">  ← backdrop + center
  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
  <div className="relative z-10 w-[480px] rounded-xl bg-[#1f1f1f] shadow-2xl">
    <header>
      <h2>摄像机</h2>
      <button>X</button>
    </header>
    <div className="space-y-6 p-6">
      <section>  <!-- Camera Selection -->
        <CameraCategoryRow />  <!-- "←" backward arrow -->
        <div>
          <label>相机</label>
          <value>{config.camera}</value>
        </div>
        <div className="chip-grid">
          {cameras.map(...)}  <!-- 9 cameras as chips -->
        </div>
      </section>
      <section>  <!-- Lens Selection -->
        <CameraCategoryRow />
        <div>
          <label>镜头</label>
          <value>{config.lens}</value>
        </div>
        <div className="chip-grid">
          {lenses.map(...)}  <!-- 10 lenses as chips -->
        </div>
      </section>
      <section>  <!-- Focal Length -->
        <CameraCategoryRow />
        <div>
          <label>焦距</label>
          <value>{config.focalLength} mm</value>
        </div>
        <div className="chip-grid">
          {focalLengths.map(...)}  <!-- 7 focal lengths as chips -->
        </div>
      </section>
      <section>  <!-- Aperture -->
        <CameraCategoryRow />
        <div>
          <label>光圈</label>
          <value>{config.aperture}</value>
        </div>
        <div className="chip-grid">
          {apertures.map(...)}  <!-- 3 apertures as chips -->
        </div>
      </section>
    </div>
    <footer>
      <button>使用</button>  <!-- calls onApply with config -->
    </footer>
  </div>
</div>
```

## Presets (from original LibTV)

### Cameras (9)

- Sony Venice
- Arri Alexa 35
- Arri Alexa 65
- Red V-Raptor
- Panavision DXL2 (default)
- Arricam LT
- ArriFlex 435
- IMAX Keighley
- IMAX Film Camera

### Lenses (10)

- Zeiss Ultra Prime
- Cooke SF 1.8x
- Canon K-35
- Cooke S4
- Cooke Panchro
- Arri Signature Prime (default)
- Helios
- Panavision C-series
- Panavision Primo
- Hawk Class X

### Focal lengths (7)

`8, 14, 24, 35, 50, 75, 125` mm. Default: `35`.

### Apertures (3)

`ƒ/1.4, ƒ/4 (default), ƒ/11`.

## States & Behaviors

| State | Trigger | Effects |
|-------|---------|---------|
| Open | `isOpen === true` | Modal renders centered with backdrop; body scroll locked. |
| Click category chip | onClick `{cameras/lenses/focalLengths/apertures}.map` | Set state: `setConfig({ ...config, category: value })`; chip becomes selected (blue `bg-blue-500`), others `bg-white/10`. |
| Apply | Click "使用" | Calls `onApply(config)`, then closes dialog. |
| Close | Click backdrop, X button, or `Escape` (no Escape handler currently) | Calls `onClose()`. |

## API

```ts
interface CameraConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onApply?: (config: CameraConfig) => void;
}

interface CameraConfig {
  camera: string;       // default: "Panavision DXL2"
  lens: string;         // default: "Arri Signature Prime"
  focalLength: number;  // default: 35
  aperture: string;     // default: "ƒ/4"
}
```

## Where the result goes

`onApply` is invoked with the `CameraConfig` object. Currently `ImageEditPanel.tsx` only does `console.log(...)` — there is no API integration. To persist:
- Pass an `onApply` callback that writes to `useCanvasStore().updateNodeData(selectedImageNodeId, { cameraConfig: config })`.

## Files Referenced

- `src/components/CameraConfigDialog.tsx` — implementation
- `src/components/ImageEditPanel.tsx` — caller (`isCameraConfigOpen` state)
