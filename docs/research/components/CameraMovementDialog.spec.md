# CameraMovementDialog Specification

## Overview

- **Target file:** `src/components/CameraMovementDialog.tsx`
- **Triggered from:** 
  - `VideoNode` "运镜" button (the canonical trigger)
  - `ImageEditPanel` "运镜" button (also exposes this — for image nodes)
- **Interaction model:** Modal dialog — pick movement type + speed + sliders

## Purpose

Configure a camera movement (shot motion) for video generation or as a hint for image variants. Replicates LibTV's "运镜" config.

## DOM Structure

```
<div className="fixed inset-0 z-[60] flex items-center justify-center">  ← backdrop + center
  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
  <div className="relative z-10 w-[560px] rounded-xl bg-[#1f1f1f] shadow-2xl">
    <header>
      <h2>运镜</h2>
      <button>X</button>
    </header>
    <div className="space-y-6 p-6">
      <section>  <!-- Movement Type — 5×2 chip grid -->
        <label>运镜类型</label>
        <div className="grid grid-cols-5 gap-2">
          {movementTypes.map(...)}  <!-- 10 movement types as circular buttons -->
        </div>
        <p>{description for selected type}</p>
      </section>
      <section>  <!-- Speed — 5 chips -->
        <label>速度</label>
        <div>
          {speeds.map(...)}  <!-- 极慢/慢速/标准/快速/极快 -->
        </div>
      </section>
      <section>  <!-- Duration slider (1s–10s, 0.5s step) -->
        <label>时长 {config.duration} 秒</label>
        <input type="range" min="1" max="10" step="0.5" value={config.duration} />
        <div>1s | 10s</div>
      </section>
      <section>  <!-- Amplitude slider (0–100%, 5% step) -->
        <label>幅度 {config.amplitude}%</label>
        <input type="range" min="0" max="100" step="5" value={config.amplitude} />
        <div>0% | 100%</div>
      </section>
    </div>
    <footer>
      <button>取消</button>
      <button>使用</button>  <!-- calls onApply with config -->
    </footer>
  </div>
</div>
```

## Movement Types (10)

Each chip is a 40×40 circular button with an icon-specific SVG. Each has an in-component helper `CameraIcon({ type })` that returns the right SVG.

| ID | Label (Chinese) | English | Description |
|----|-----------------|---------|-------------|
| `static` | 静止 | Static | Fixed position |
| `pan` | 横摇 | Pan | Horizontal rotation |
| `tilt` | 俯仰 | Tilt | Vertical rotation |
| `dolly` | 推拉 | Dolly | Forward/backward motion |
| `truck` | 横移 | Truck | Lateral motion |
| `pedestal` | 升降 | Pedestal | Vertical motion |
| `roll` | 旋转 | Roll | Rotation around optical axis |
| `zoom` | 变焦 | Zoom | Change focal length |
| `orbit` | 环绕 | Orbit | Revolve around target |
| `crane` | 摇臂 | Crane | Arc motion |

## Speeds

`极慢` (very slow) / `慢速` (slow) / `标准` (standard, default) / `快速` (fast) / `极快` (very fast).

## Computed Styles

- Modal: `w-[560px] rounded-xl bg-[#1f1f1f]` with `shadow-2xl`.
- Movement chip (selected): `bg-[#09caf5] text-[#171717]`.
- Movement chip (idle): `bg-white/10 text-white/80 hover:bg-white/20`.
- Slider track: `h-1 bg-white/10`; thumb: `w-4 h-4 bg-[#09caf5] rounded-full`.

## States & Behaviors

| State | Trigger | Effects |
|-------|---------|---------|
| Open | `isOpen === true` | Modal renders centered. |
| Pick movement | Click movement chip | `setConfig({ ...config, movementType: id })`. Description text below the grid updates to e.g. "围绕目标旋转". |
| Pick speed | Click speed chip | `setConfig({ ...config, speed })`. |
| Adjust duration | Drag duration slider | Live updates `config.duration`. Range 1–10s, step 0.5s. |
| Adjust amplitude | Drag amplitude slider | Live updates `config.amplitude`. Range 0–100%, step 5%. |
| Apply | Click "使用" | Calls `onApply(config)` then `onClose()`. |
| Cancel | Click "取消", backdrop, or X | Closes dialog without applying. |

## API

```ts
interface CameraMovementDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onApply?: (config: CameraMovementConfig) => void;
}

interface CameraMovementConfig {
  movementType: string;  // one of the 10 IDs above (default: "dolly")
  speed: string;          // default: "标准"
  duration: number;       // 1–10 seconds (default: 3)
  amplitude: number;      // 0–100 percent (default: 50)
}
```

## Where the result goes

- In `VideoNode.tsx`: writes to local state; could be persisted into `data.cameraMovement` for global access.
- In `ImageEditPanel.tsx`: console.log only.

To persist, propagate through `useCanvasStore().updateNodeData(selectedNodeId, { cameraMovement: config })`.

## Files Referenced

- `src/components/CameraMovementDialog.tsx` — implementation
- `src/components/nodes/VideoNode.tsx` — primary caller
- `src/components/ImageEditPanel.tsx` — secondary caller
