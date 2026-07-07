# TopNavBar Specification

## Overview

- **Target file:** `src/components/TopNavBar.tsx`
- **Position:** Top of viewport (above canvas). Height 48px.
- **Interaction model:** Mixed — inline-editable input, dropdown trigger, link, etc.

## DOM Structure (left → right)

```
<nav className="h-12 px-4 flex items-center justify-between bg-[#141414] border-b border-[#262626]">
  <div className="flex items-center gap-3">          ← Left section
    <div className="cursor-pointer hover:opacity-80"> ← Logo (24×24 SVG film glyph)
      <svg .../>
    </div>
    <div className="w-px h-5 bg-[#363636]" />          ← Separator

    {isEditing ? (
      <input className="bg-[#363636] ... w-40" autoFocus />  ← Project name input
    ) : (
      <span onClick={() => setIsEditing(true)} className="cursor-text hover:bg-[#353639] px-2 py-1 rounded">
        {projectName}                                    ← "未命名项目"
      </span>
    )}

    <CanvasTabDropdown />                              ← "画布 2 ▾"
  </div>

  <div className="flex items-center gap-2">            ← Right section
    <button className="p-2 hover:bg-[#353639] rounded-lg"> ... </button>  ← Notification bell

    <div className="relative flex items-center">     ← VIP + credits combo
      <span className="absolute -top-2 right-3 z-10 text-[10px] px-1.5 py-0.5 bg-[#ff7d00] text-white rounded-md font-medium">
        限时 37 折                                       ← orange badge above
      </span>
      <button className="flex items-center gap-1.5 pl-3 pr-1 h-10 rounded-xl bg-[rgba(38,38,38,0.8)] border border-[#363636] hover:bg-[#353639]">
        <svg className="w-4 h-4 text-[#FFDBA4]" />      ← Lightning icon
        <span className="text-sm text-[#FFDBA4]">会员特惠37折</span>
        <span className="text-[#363636]">|</span>
        <svg className="w-4 h-4 text-[#FFDBA4]" />      ← Lightning icon
        <span className="text-sm text-[#f7f7f7]">64</span>
      </button>
    </div>

    <Link href="/frameos/canvas/demo" className="..."> ... </Link>  ← FrameOS link

    <button className="w-8 h-8 rounded-full overflow-hidden hover:ring-2 hover:ring-[#525252]">
      <Image src="/images/avatar.png" alt="用户头像" width={32} height={32} className="w-full h-full object-cover" />
    </button>
  </div>
</nav>
```

## Interactions

| Element | Click Effect |
|---------|-------------|
| Logo | Hover: `opacity-80`. Click: no-op (could navigate home). |
| Project name | Click → toggle to input mode. Press `Enter` / click outside → save & exit edit mode. |
| Canvas tab dropdown | Click → toggles dropdown. See `CanvasTabDropdown.spec.md`. |
| Notification bell | Hover bg changes. Click: no-op. |
| VIP + credits button | Hover bg changes. Click: no-op (would open membership modal). |
| FrameOS link | Click → navigate to `/frameos/canvas/demo`. Hover bg + border color change. |
| User avatar | Hover: `ring-2 ring-[#525252]`. Click: no-op (would open user menu). |

## Files Referenced

- `src/components/TopNavBar.tsx`
- `src/components/CanvasTabDropdown.tsx`
- `public/images/avatar.png`
