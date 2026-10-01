# Batch 593 — 时间轴左列两级结构：对象行 + 轨道行

日期：2026-10-01
取证：源站导演台 CDP 实测（`http://127.0.0.1:9222`，Chrome 151.0.7922.34，1920×1150，导演视角）
原始证据：`/tmp/src593/`（probe1–probe12 + 两张全屏截图）
验收：`scripts/verify-liblib-batch593.py`（28 项检查全过）

---

## 一、源站事实

### 1.1 时间轴是**两层**，不是「一条工具条 + 一张列表」

```
root    1920 x 182 @ (0, 968)   pointer-events-none，flex-col items-center gap-1
panel   1920 x 130 @ (0, 1020)  pointer-events-auto
  strip 1920 x  36 @ (0, 1021)  absolute inset-x-0 top-0 z-30，flex gap-[2px]
    left   320 x 36   工具条左格
    right 1598 x 36   标尺 + 缩放 + 最小化 + 导出
  track area                      flex min-h-full gap-[2px]
    left   320 x 130  bg-[#1f1f1f] z-10 shrink-0
    right 1598 x 129
```

工具条是**覆盖层**（`z-30`），压在轨道区上；轨道区左列顶部第一格是一个 320×36 的
**空占位 div**（`bg-[#1f1f1f]`，`innerHTML` 长度为 0），专门给这条覆盖层让位。
面板总高 130 由内容撑不满（36+32+32=100），底部留 30px 空。

工具条左格内容（`h-[36px]` + `px-2 py-1`），逐项实测盒模型：

| 控件 | 可及名 | 盒 | 备注 |
| --- | --- | --- | --- |
| 播放 | `播放` | 26×24 @(8,1027) | |
| 自动帧 | `自动帧` | 24×24 @(34,1027) | `aria-pressed="false"` |
| 循环播放 | `循环播放` | 26×24 @(58,1027) | 选中态 `bg-white/10` |
| 播放头位置 | `播放头位置` | 46×24 @(88,1027) | 连体左框，`rounded-l-lg` |
| 总时长 | `总时长` | 46×24 @(135,1027) | 连体右框，直角 |
| 单位 | `切换时间单位为 s` | 33×24 @(182,1027) | 当前值 `ms`，`rounded-r-lg`，`min-w-[31px]` |
| 新建轨道 | `选中角色、道具或分组后建立轨道` | 82×24 @(230,1027) | `disabled` |

工具条左格**没有**任何标题文字（此前 clone 自造的「动画时间轴」h2 已在本批删除）。

### 1.2 左列 320px 是**两级**：对象行 + 该对象的轨道行

**对象行** 320×32 @(0,1057)，`grid-template-columns: 16px minmax(0,1fr) 220px`：

| 列 | 内容 | 实测 |
| --- | --- | --- |
| 16px | `收起属性` 按钮 | 20×20 @(8,1063)，`aria-expanded="true"`，chevron `rotate-90`（收起时 `rotate-0`），**无 title** |
| 1fr | `主机位` | `div[role=button][tabindex=0][title="主机位"] > span.truncate`，60×19 @(28,1064) |
| 220px | `绘制轨迹` | 86×24 @(226,1061) **真 `<button>`**，`aria-pressed="false"`，图标 14×14 + 文字 13px，右对齐 |

**轨道行** 320×32 @(0,1089)，`grid-template-columns: 40px 36px 78px minmax(0,1fr)`：

| 列 | 内容 | 实测 |
| --- | --- | --- |
| 40px | **纯装饰加号** | `span[aria-hidden].h-full.w-10`，内含 `absolute left-5 top-0 w-px[bottom:50%]` 竖线 + `absolute left-5 top-1/2 h-px w-4` 横线，均 `#363636`。竖线只画到行中点、横线落在中点，所以是「上半加号」 |
| 36px | `位置` | `div[role=button][title="位置"] > span.truncate`，36×19 @(52,1096) |
| 78px | 三个 24×24 按钮 | `flex h-6 items-center justify-center gap-0.5`，位于 @(93,1093) / @(119,1093) / @(145,1093) |
| 1fr | `3.3,2.2,10` | `span.text-right.text-[13px].tabular-nums`，138×20 @(174,1095) |

### 1.3 关键帧三按钮的语义（**按轨道**，不是按整条时间轴）

| 播放头 | ‹ 上一关键帧 | ◆ 中间 | › 下一关键帧 |
| --- | --- | --- | --- |
| 0 ms | `disabled` | `当前帧有关键帧` `aria-pressed="true"` | `disabled` |
| 977 ms | 可用 | `当前帧无关键帧` `aria-pressed="false"` | `disabled` |

源站相机轨道只有 0 ms 一帧。播放头挪到 977 ms 后 ‹ 变可用而 › 仍禁用 —— 证明
**seek 范围是本轨道**，不是全局时间轴（clone 的 `seekTimelineKeyframe` 是全局的）。
中间按钮内含 `span.h-[9px].w-[9px].rotate-45.rounded-[2px].border`（9×9 菱形，
`border-[#A8A8A8] bg-[#A8A8A8]`）。

### 1.4 值读数不是插值，是「播放头处生效的关键帧」

播放头 977 ms（该帧无关键帧）时读数仍是 `3.3,2.2,10`，与 0 ms 相同。格式上
z=10 印作 `10` 而不是 `10.0` —— 不是定长小数。

### 1.5 两个折叠控件并存

| 控件 | 位置 | 作用 |
| --- | --- | --- |
| `时间线最小化` | 工具条右格，缩放簇内 24×24 | 收起**整条**时间轴（batch 592 已对齐） |
| `收起属性` / `展开属性` | 对象行第 1 列 20×20，`aria-expanded` | 只收起**该对象的轨道行**；对象行保留，**面板总高前后都是 130px 不变** |

展开态与收起态实测对照：

```
expanded   对象行 32px @(0,1057) + 轨道行 32px @(0,1089)   toggle=收起属性 aria-expanded=true
collapsed  对象行 32px @(0,1057)                            toggle=展开属性 aria-expanded=false
           面板 (0,1020) 1920x130 两种状态一致
```

### 1.6 顺带纠正一处历史误判

batch 591/557 曾把「上一/下一关键帧」判为源站没有、clone 独有的工具条后缀。
本批复测证明**源站有**，只是位于每条轨道行内。591 的合同已迁移。

---

## 二、clone 改动

`src/components/director/DirectorTimeline.tsx`

1. **左列 220px → 320px**（`<899px` 降级 220px），底色 `bg-[#1f1f1f]`。
2. **工具条 `h-10` → `h-9`**（40→36px），删除自造的 `<h2>动画时间轴</h2>`。
3. **轨道列表两级化**：按 `objectId`（分组轨道按 `groupId`）分组，每个有轨道的
   对象渲染一条对象行 + 其轨道行。新增 `timelineTrackGroups` memo。
4. **对象行**按源站栅格 `16px minmax(0,1fr) 220px` 落地；首列是 20×20
   `收起属性`/`展开属性` 按钮（`aria-expanded`，无 title，chevron 旋转）；
   新增 `collapsedObjects` 状态，**只收起该对象的轨道行**，对象行与时间轴总高不变。
5. **轨道行**按源站栅格 `40px 36px 78px minmax(0,1fr)` 落地：
   - 40px 装饰加号（`aria-hidden`，`#363636`，竖线到中点 + 中点横线）；
   - 36px 轨道名 `div[role=button][title=完整 label]`；
   - 78px 三个 24×24 按钮，逐条轨道独立：‹/◆ 按**本轨道**关键帧判定禁用与
     `当前帧有关键帧`/`当前帧无关键帧` 可及名，◆ 点击在本帧有空/有帧时增/删关键帧；
   - 1fr 值读数 `x,y,z`（`Number(v.toFixed(3))` 后走默认数字转字符串，对齐源站
     `10` 而非 `10.0` 的写法）。
6. **`绘制轨迹` 从 `span[role=button]` 改成真 `<button>`**，86×24，带 `aria-pressed`。
7. **工具条移除 clone-only 的 `上一/下一关键帧`**（源站在轨道行）；`删除轨道`
   改挂工具条紧跟 `轨道` 按钮（源站四列栅格没有删除位），`aria` 保持 `移除<label>轨道`。
8. 组件不再订阅 `seekTimelineKeyframe`（store 动作保留，batch 69 直接调用）；
   移除随之失效的 `SkipBack`/`SkipForward`/`Info`/`PersonStanding`/`Users` 导入。

### 轨道名显示

源站轨道名是**属性名**（位置 / 旋转 / 缩放），因为源站一个属性一条轨道。clone 一条
轨道同时驱动位置+旋转+缩放（机位轨道另含 target/fov），无法一一对应；且源站的
36px 名字列放不下 clone 的 `${对象名} · 变换`。故第 2 列按 kind 取两字短名
（变换 / 机位 / 姿势 / 分组），完整 label 留在 `title`。**clone-only**。

---

## 三、迁移的合同

| 批次 | 原合同 | 原因 |
| --- | --- | --- |
| 591 | 工具条里 `上一/下一关键帧` 必须排在源站七项前缀**之后**（clone-only 后缀） | 复测证明源站在轨道行有这两个按钮，工具条里不该有。改为断言工具条**不含**它们，且每条轨道行都有三按钮 |
| 36 / 42 | `get_by_role("button", name="下一关键帧")` 全局单选 | 现在每条轨道行各有一组，role+name 会命中多个。改为先按 `timeline.selectedTrackId` / `pose_track` 收敛到 `[data-director-track-row=...]` 再点 |
| 37 | `[data-director-track-label="X"] button`（点行内第一个 button） | 行内第一个真 button 现在是 `上一关键帧`。改为 `[role="button"]`（轨道名） |

---

## 四、顺带解除的两处**既有**失败（基线对照确认）

本批把轨道列做高之后，暴露出两处此前被更早失败挡在后面的既有失败。两处都在
`HEAD`（`e7ecc3c8`）上复现过，故属既有失败，按既有约定最小解除。

### 4.1 引导气泡压住轨道列（batch 37 在 HEAD 上就已跑不通）

基线：把 `DirectorTimeline.tsx` / `DirectorScenePromptBar.tsx` / `verify-liblib-batch37.py`
都还原到 HEAD 后重跑，batch 37 在**同一处**点击就超时：

```
waiting for locator('[data-director-track-label="director-track-camera-main"] button')
  - <p class="text-xs leading-5 text-[#d8d8d8]">请选择一个角色或者摄像机后，可新建轨道</p>
    from <div role="status" data-director-timeline-coachmark="true"
         class="absolute bottom-3 left-3 z-30 w-[300px] ..."> intercepts pointer events
```

根因是 clone 的引导气泡是**自造**的：`absolute bottom-3 left-3` + `w-[300px]`，
落在 182px 时间轴**内部**，把 320px 宽轨道列的下半整块盖住。本批复测源站后按实测
重建（见 1.7），气泡不再压轨道行。

### 4.2 气泡重建的实测数据

源站气泡是 `position: fixed` 的独立浮层，**不在**时间轴内部：

```
box 260 x 114 @ (163, 920)  @1920x1150
style="left: 163px; top: 920px; width: 260px"
rounded-xl(12) / border-white/[0.08] / bg-[#242424] / p-4(16)
shadow-[0_4px_16px_rgba(0,0,0,0.18)] / z-[1] / overflow-hidden
正文  h-10 overflow-hidden text-[12px] leading-[19.2px] text-white/90
页脚  mt-3 flex items-center justify-between gap-1
  1/5    min-w-0 flex-1 text-[14px] leading-3 text-white/55
  跳过    h-7 rounded-lg bg-transparent  px-3 text-[13px] leading-none text-white/70
  下一步  h-7 rounded-lg bg-white/10     px-3 text-[13px] leading-none text-white/85
```

clone 之前是 `p-3` + `shadow-[0_16px_40px_rgba(0,0,0,0.5)]` + 深色小药丸按钮，与实测
全部不符。本批逐项对齐，`top` 用 `calc(100vh - 230px)` 表达（1150−230=920）。

**一处有意偏离**：源站气泡是 `pointer-events-auto`，clone 改成
`pointer-events-none` + 两个按钮 `pointer-events-auto`。源站工具条左格只有 320px，
气泡只压住「新建轨道」顶端 7px；clone 的工具条是一整行（多了预设运镜 / 曲线编辑器 /
缓入等 clone 能力），同一块屏幕会被压住一整排控件——`opacity-0` 之外的惰性文字区
吞点击会让工具条在引导期间完全不可用。外观与几何完全按实测。

### 4.3 隐藏态 prompt 状态条吞掉视口工具条的点击

解除 4.1 之后，batch 37 继续往下走，撞上第二处既有失败：

```
waiting for locator("[data-director-capture]")
  - <span aria-live="polite" data-director-scene-prompt-status="true"
         class="... pointer-events-auto ... opacity-0">场景描述已记录（本地草稿）</span>
    intercepts pointer events
```

基线实测（HEAD，1440×900）：

```
[data-director-capture]        63 x 32 @ (920, 660)   中心 (951, 676)
[data-director-scene-prompt-status]  163 x 25 @ (845, 668)  opacity=0  pointer-events=auto
boxesOverlap = true, centerInsideStatus = true
```

`opacity-0` 的元素仍有盒模型，`pointer-events-auto` 会把底下整条吞掉。改为
`submitted ? "opacity-100" : "pointer-events-none opacity-0"`——隐藏的 toast 不该
吃点击，这是纯 bug 修复，不涉及源站对齐判断（源站是否也有同类状态条未取证）。

### 4.4 38 / 39 / 40 的 TransformControls 瞬态

这三批与本批无代码交集（都在断言函数尾部），失败原因只有一个已知瞬态：
`TransformControls: The attached 3D object must be a part of the scene graph.`
（three.js 在对象被替换的那一帧抛出）。batch 36 / 37 / 89 / 96 / 85 / 580 / 587–592
早已按同一约定过滤并在 audit 留 `filtered_transformcontrols` 计数，38–40 是漏网。
本批补齐同一过滤，`run_desktop` 返回过滤条数并在结尾打印。

**未解除**（与本批无关，只报告）：batch 41 等的 `[data-director-phone-vcam-trigger]`
在 `HEAD` 上就不存在，30s 点击超时，既有问题，本批不动。

---

## 五、未取证 / 未验证（记录，不臆造）

- **源站的按属性拆轨**（位置 / 旋转 / 缩放三条）。要看到它必须在源站新建轨道，
  那会写入用户真实项目 `spaceId 7709759`，未获授权。故 clone 保留「一对象一轨」
  模型，只对齐两级版式与按钮语义。
- **`收起属性` 是按对象还是全局**。源站只有一个对象，chevron 位于对象行首列，
  按标准树形交互读作「按对象」，已写进代码注释。
- **旋转 / 缩放轨道的值读数格式**。源站只暴露了位置轨道的 `3.3,2.2,10`。
- `3.3,2.2,10` 是源站相机自身的位置，clone 按同样格式打印自己的对象位置。
- 源站是否也有 prompt 提交后的状态 toast（4.3 的修复未做源站对照）。

---

## 六、参考图

`docs/design-references/liblib-timeline-two-level-1920.png` — clone 1920×1150
下的两级轨道区（verifier 产出）。
