# Batch 77 Director Transform Controls Static And Runtime Audit

> 日期：2026-08-28。
>
> 范围：当前 clone `DirectorViewport.tsx`、Drei 10.7.8
> `TransformControls` 和 fresh-page 本地运行态。

## 1. 交互合同

Batch 35 workspace spec 定义：

- 对象树 row 或 R3F mesh 可以选择物体；
- 底部工具条切换移动、旋转、缩放；
- selected unlocked object 显示 TransformControls；
- 用户拖动三轴 gizmo 修改 transform；
- Inspector position XYZ 是并行输入路径。

因此“拖动轴”本来就是公开操作，不存在需要额外开启的隐藏编辑模式。

## 2. 当前源码事实

`SceneObject` 先创建：

```tsx
const content = <group ref={groupRef} position={object.transform.position} />;
```

selected 时再使用：

```tsx
<TransformControls onMouseUp={commitTransform}>
  {content}
</TransformControls>
```

而 `commitTransform` 读取 `groupRef.current`。

Drei 10.7.8 在没有 `object` prop 时会创建自己的 wrapper group，并把
TransformControls attach 到 wrapper，不是 attach 到 children 内部的
`groupRef`。因此当前形成：

```text
attached wrapper at identity/world origin
  -> inner content group at object transform
```

gizmo 跟随 wrapper，提交却读取 inner group。

相同错误结构也存在于：

- `DirectorGroupTransformRig`；
- `PathControlPoint`。

## 3. Fresh-page 运行证据

环境：

- URL：`http://localhost:3001/`；
- viewport：`1440x900`；
- browser：Playwright Chromium headless；
- source node：默认 canvas 的 `3D导演台`；
- selected object：`director-prop-mug`。

选择后状态：

```json
{
  "selectedObjectId": "director-prop-mug",
  "selectedGroupId": null,
  "transformMode": "translate",
  "position": [0.25, 1.08, 0.05],
  "authored": [0.25, 1.08, 0.05],
  "selectedMotionPathAnchorId": null,
  "motionPathDraft": null
}
```

直接观察：

- mug 位于桌面；
- gizmo 位于场景原点、桌下地面附近；
- gizmo 与 selected object 明显不重合。

实际 pointer 命中 gizmo 后：

```json
{
  "gesture": "object-transform",
  "lastCommand": {
    "commandKind": "GESTURE_BEGIN",
    "disposition": "COMMITTED"
  }
}
```

pointer move/up 后：

```json
{
  "position": [0.25, 1.08, 0.05],
  "historyPast": 0,
  "gesture": "object-transform"
}
```

这证明现有 Batch 35/70 verifier 只验证 Inspector/store adapter，未覆盖实际
gizmo drag，导致用户可见回归没有被 current gate 捕获。

## 4. 风险判断

| 风险 | 级别 | 原因 |
|---|---|---|
| 物体无法通过视口直接移动 | P0 interaction regression | Director 核心 staging workflow 失效 |
| gizmo 错位 | P0 interaction regression | 用户无法发现正确操作对象 |
| active gesture 泄漏 | P1 reliability | 后续 command 可能 conflict，Escape/undo 语义受污染 |
| group/path 同构缺陷 | P1 latent regression | 同一 attachment 模式，历史 verifier 未证明真实 drag |
| Inspector 输入仍可用 | mitigation only | 不能替代直接 manipulation 合同 |

## 5. 结论

这是 clone implementation defect，不是用户没有找到操作方法。修复必须同时
恢复 attachment geometry、pointer commit、gesture cleanup，并用实际 gizmo
pointer drag 替换仅调用 store 的伪覆盖。
