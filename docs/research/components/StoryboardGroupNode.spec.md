# StoryboardGroupNode Specification

## Overview

- **Target file:** `src/components/nodes/StoryboardGroupNode.tsx`
- **Type ID:** `storyboard-group`
- **Interaction model:** Static group container with image thumbnails inside.

## DOM Structure

```
<div className="w-[320px] overflow-visible rounded-xl bg-[#1f1f1f] border shadow-xl">
  <Handle type="target" position={Left} id="target" />
  <Handle type="source" position={Right} id="source" />

  <div className="px-4 py-2 text-xs text-[#919191] truncate">
    {title}  <!-- e.g. "分镜图 · 第一集：咖啡馆对峙-图片组" -->
  </div>

  <div className="grid grid-cols-1 gap-2 p-3 pt-0">
    {images.map(img => (
      <div className="relative aspect-video rounded-lg overflow-hidden bg-[#171717] border border-[#363636]">
        <img src={img.url} alt={img.label} className="w-full h-full object-cover" />
        {img.label && (
          <div className="absolute top-1 left-1 text-[10px] px-1.5 py-0.5 bg-black/60 text-white rounded">
            {img.label}
          </div>
        )}
      </div>
    ))}
  </div>
</div>
```

## Data Shape

```ts
interface StoryboardGroupData {
  title?: string;
  images?: Array<{ url: string; label?: string }>;
}
```

## Files Referenced

- `src/components/nodes/StoryboardGroupNode.tsx`
