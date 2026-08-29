# Batch 84 计划：Director 对象树锁定与编辑保护

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是最多五个连续 batch 中的第一个。目标是补齐 Director 对象树的高频
> lock/visibility 可发现性，并把 `locked` 从“数据字段/隐藏 TransformControls”
> 提升为一致的编辑保护合同。

## 1. 背景与证据

固定 StoryAI 上游的 `ObjectTreePanel` 在每个对象行并列提供可见性和锁定按钮，
并在 store 中将 `locked` 作为对象状态。当前 clone 已有 `DirectorObject.locked`
字段，Viewport 也会因锁定而不渲染 `TransformControls`，但存在三个缺口：

1. 对象树没有锁定/解锁入口，用户无法发现如何解锁；
2. Inspector 的名称、颜色、变换、相机、姿态和路径控件仍然可操作；
3. store 的若干直接 action 没有统一拒绝锁定目标，UI 之外的调用仍可能绕过保护。

上游只作为实现方法参考。LibTV 原站 Director 的 authenticated lock UI、文案、
键盘和编辑语义仍为 `SOURCE_UNKNOWN`。

## 2. Clone-owned 合同

| 场景 | 规则 |
|---|---|
| 选择/查看 | 锁定对象仍可在对象树和 viewport 中选择、查看属性 |
| 可见性 | 锁定对象仍可切换可见性；隐藏/显示不是几何编辑 |
| 锁定切换 | 对象树和 Inspector 均可锁定/解锁；切换本身是一个 Director history entry |
| 对象属性 | 锁定后名称、颜色、位置、旋转、缩放均拒绝修改 |
| 相机属性 | 锁定后 FOV、注视和跟随配置拒绝修改 |
| 姿态/路径 | 锁定后姿态、路径锚点、路径变换和路径元数据拒绝修改 |
| 分组 | 选择仍可用；包含锁定成员的分组变换拒绝修改 |
| 删除 | 删除是结构命令，仍允许执行；它不等同于变换编辑 |
| 结果 | 拒绝使用 `DIRECTOR_TARGET_LOCKED`，零 document mutation、零 history entry |

## 3. 实施范围

纳入：

- 对象树每行增加 Lock/Unlock 图标按钮、tooltip、ARIA 和稳定 `data-*`；
- Inspector 增加锁定状态入口和锁定态说明；
- 让对象、相机、姿态、分组、路径编辑控件在锁定时 disabled；
- store 对主要对象/相机/姿态/路径/分组 mutation 增加锁定拒绝；
- 专项 pure/source verifier 与 fresh-page browser verifier；
- 更新 current verifier manifest、组件 coverage、verification ledger 和本批记录。

不纳入：

- 将 StoryAI 或 clone 视觉提升为 LibTV source-exact 证据；
- 新增 remote asset、真实模型、panorama 或多机位语义；
- 改变删除策略、普通画布 graph history 或 FrameOS；
- 为所有 transient viewport state 建立额外 history。

## 4. 验收标准

- 对象树和 Inspector 都能完成 lock/unlock；
- locked object 可选择、可隐藏/显示、可删除，但所有编辑入口拒绝；
- 直接调用受保护 store action 返回 `DIRECTOR_TARGET_LOCKED`；
- 拒绝前后 `authoredObjects`、`objects`、timeline/path/camera 数据不变；
- 锁定切换产生一条历史，锁定态编辑拒绝产生零条历史；
- desktop/mobile object-tree 和 Inspector 不发生溢出；
- 专项 verifier、current Director gate、`npm run check`、文档检查通过；
- 本批所有结论带有 `CLONE_FACT`、`CLONE_DECISION` 或 `SOURCE_UNKNOWN` 标签。

## 5. 实施与验证结果

本批已完成实施并通过：

```text
node --experimental-strip-types scripts/verify-liblib-batch84.mjs
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch84.py
npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

浏览器验证使用固定 `localhost:4317`，未产生截图，console/page/request
diagnostics 均为 0。结果见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md) 和
[`runtime-audit.json`](runtime-audit.json)。

## 6. 预定文件

- `src/components/director/DirectorObjectTree.tsx`
- `src/components/director/DirectorInspector.tsx`
- `src/components/director/DirectorViewport.tsx`
- `src/store/directorStore.ts`
- `scripts/verify-liblib-batch84.mjs`
- `scripts/verify-liblib-batch84.py`
- `docs/research/liblib-canvas-batch84-2026-08-29/*`
- current manifest、coverage、verification ledger 和相关治理入口，均已更新
