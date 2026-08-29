# Batch 84 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 本批为 clone-owned Director 编辑保护，不是 LibTV 原站 source-exact 结论。

## 1. 实施内容

### 1.1 对象树锁定入口

`DirectorObjectTree` 每个对象行现在同时提供：

- 可见/隐藏按钮；
- 锁定/解锁按钮；
- 稳定 `data-director-object-lock`、`data-director-object-locked`；
- 基于对象名称的 `aria-label` 与 tooltip。

锁定对象仍然可以选择、查看、隐藏/显示和删除。锁定按钮本身是一个独立的
Director mutation，会进入项目 history。

### 1.2 Inspector 编辑保护

普通对象 Inspector 在锁定后停用名称、颜色、位置、旋转和缩放控件，并显示
“对象已锁定，属性与变换编辑已停用”提示。相机的 FOV、注视、跟随及跟随偏移
也会停用；姿态预设和姿态滑杆同样停用。

路径 Inspector 在所属对象锁定后停用名称、启用、闭合、路径变换、锚点类型、
锚点位置、控制柄和 reset 操作，并显示锁定提示。分组 Inspector 在含有锁定
成员时停用分组变换。

### 1.3 store 直接调用防线

除了 UI disabled 外，store action 也会返回 typed
`DIRECTOR_TARGET_LOCKED`，覆盖：

- 对象属性和对象变换；
- 相机属性和相机预设运镜；
- 姿态预设、姿态控制和关键帧；
- 分组变换和分组关键帧；
- 运动路径创建、绘制、锚点、控制柄、路径元数据、路径变换、曲线开关；
- Timeline 关键帧和速度曲线编辑。

被拒绝操作保持 zero document mutation / zero history entry。删除仍走既有
reference-aware delete command，因此不会因为锁定而产生“无法删除”的隐藏状态。

## 2. 验证

### 2.1 Pure verifier

```bash
node --experimental-strip-types scripts/verify-liblib-batch84.mjs
```

结果：`PASS`。验证对象树/Inspector/Viewport 入口、稳定 reason 以及对象、分组、
路径、时间线保护代码存在。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch84.py
```

结果：`SCRIPT_RECORDED_PASS`。

覆盖：

- 对象树锁定按钮和状态切换；
- Inspector disabled controls；
- 直接 `updateObjectTransform` 的 locked rejection；
- 拒绝前后 transform 不变；
- locked rejection 不增加 history；
- locked object 仍可切换 visible；
- 解锁后恢复变换；
- mobile 下锁定入口仍可发现；
- console/page/request errors 均为 0。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

## 3. 证据边界

| 标签 | 结论 |
|---|---|
| `UPSTREAM_INSPIRATION` | StoryAI 对象树在每行提供 visibility/lock 并列控制，store 维护 `locked` |
| `CLONE_FACT` | 当前 clone 已有 `locked` 数据字段和部分 Viewport 控制器隐藏行为 |
| `CLONE_DECISION` | 锁定是 clone-owned 编辑保护；选择、可见性和结构删除与属性/变换编辑分离 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有相同 lock UI、文案、键盘和拒绝语义 |

## 4. 当前限制

- 本批没有重新读取截图；没有新增 screenshot artifact；
- 没有宣称 LibTV Director DOM/CSS parity；
- 未改变普通 LibTV React Flow graph、FrameOS、资源 loader 或 remote sync；
- 当前 Director 的部分低级 transient action 仍由既有 store 直接写入，后续 batch
  需要继续检查是否应纳入统一 command/history，而不能仅依赖本批锁定保护。
