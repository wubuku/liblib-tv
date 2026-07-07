# ScriptExecutionNode Specification

## Overview

- **Target file:** `src/components/nodes/ScriptExecutionNode.tsx`
- **Type ID:** `script-execution`
- **Interaction model:** Static node showing 3 execution steps + open-script-node CTA. No editing.

## DOM Structure

```
<div className="w-[260px] overflow-visible rounded-xl bg-[#2a2d3d] border shadow-xl">
  <Handle type="target" position={Left} id="target" />
  <Handle type="source" position={Right} id="source" />

  <div className="py-4 text-center cursor-grab">
    <MenuIcon className="text-[#919191]" />  <!-- 3 horizontal lines -->
  </div>

  <div className="flex items-center justify-between px-3 py-4">
    {steps.map((step, i) => (
      <div className="flex items-center">
        <div className="flex flex-col items-center gap-1.5">
          <div className={completed-or-pending circle}>
            {completed ? <CheckIcon /> : i + 1}
          </div>
          <span>{step.label}</span>
        </div>
        {i < steps.length - 1 && <div className="connector-line" />}
      </div>
    ))}
  </div>

  <div className="px-3 pb-3">
    <button>打开脚本节点 →</button>  <!-- non-functional CTA -->
  </div>
</div>
```

## Data Shape

```ts
interface ScriptExecutionData {
  steps?: Array<{ label: string; completed?: boolean }>;
}
```

Default steps (from `canvasStore.ts`): `[确认镜头 ✓, 准备资产 ✓, 合成提示词]`.

## Computed Styles

| Element | Styles |
|---------|--------|
| Wrapper | `w-[260px] rounded-xl bg-[#2a2d3d] border border-[#363636] shadow-xl` (background darker than other nodes for hierarchy) |
| Step circle (completed) | `w-7 h-7 rounded-full bg-[#09caf5] text-[#171717]` |
| Step circle (pending) | `w-7 h-7 rounded-full bg-[#363636] text-[#919191] border border-[#525252]` |
| Connector line (between completed steps) | `bg-[#09caf5]` |
| Connector line (between incomplete steps) | `bg-[#525252]` |
| Open button | `w-full py-2 rounded-lg bg-[#363636] hover:bg-[#525252]` |

## Files Referenced

- `src/components/nodes/ScriptExecutionNode.tsx`
