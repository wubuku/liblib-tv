# Batch 611 — 属性面板顶部 sticky 机位预览缩略图（真·离屏渲染）

日期：2026-10-01
取证脚本：`/tmp/src593/probe66.py`（源站右头整棵子树）、`/tmp/src593/crop611.py`（2× 截图裁切二次确认画布内容）
验收脚本：`scripts/verify-liblib-batch611.py`（49 项）
参考图：`docs/design-references/liblib-camera-preview-611-1920.png`、`docs/design-references/liblib-camera-preview-611-closeup.png`

## 靶心

batch 610 明确留的欠账：源站在页签栏正下方有一块 **sticky 预览缩略图**，而那个 `FOV n°` 文案（batch 581 误当成控件的那个角标）正是在这里。

## 源站实测（source fact）

```
section [1640,105,280,168]
  sticky top-0 z-20 border-b border-white/8 bg-[rgba(33,33,33,0.98)] px-4 py-4
  shadow-[0_8px_18px_rgba(0,0,0,0.18)] backdrop-blur-md
  div [1656,121,240,135]  relative overflow-hidden rounded-xl border
                          bg rgba(8,8,16,0.95)
    canvas [1657,122,240,135]
    div  [1669,134,51.3,13] pointer-events-none absolute left-3 top-3
                            text-[13px] leading-none text-white/55 → "FOV 50°"
    button [1859,219,24,24] hover:bg-white/16 absolute bottom-3 right-3
                            flex size-6 items-center justify-center
                            rounded-lg bg-white/10 text-white/85
                            14×14 svg（两支朝外的对角箭头）
```

高度自洽：`16 (py-4) + 135 + 16 + 1 (border) = 168`。
`left-3` / `right-3` 相对 **padding box**（盒 + 1px 边框）量：角标 1657+12 = 1669、122+12 = 134；放大钮右 1895−12−24 = 1859、下 255−12−24 = 219。四项都与读数逐字吻合。

## 画布里到底是什么（这一步决定做法）

`/tmp/src593/crop611.py` 把源站 2× 截图（3840×2300，需按 DPR=2 换算坐标）的预览区裁出来放大看：里面是**网格地面、地平线、以及站在桌边的角色** —— 是**该机位视角下的真 3D 渲染**，不是示意图、不是海报帧、不是占位图。

所以本批**不做 2D 示意图**。那会造出一个「看起来能用、其实在撒谎」的控件，与既有约定（死按钮不算可复刻的体验）冲突。

## 本批做法

**在已有的那个 WebGL 上下文里做离屏渲染**，不新增 context：

- 新增 `src/components/director/directorCameraPreview.ts`：模块级 sink（面板那块 2D canvas 挂进来）、`WebGLRenderTarget` 的建/复用/释放、以及
  `renderDirectorCameraPreview(gl, scene, previewCamera)` —— `setRenderTarget` → `render` → `readRenderTargetPixels` → 逐行翻转 Y → `putImageData` → 还原 render target；
- `DirectorViewport` 里在主 `<Canvas>` 内挂 `CameraPreviewRenderer`：用同一份 `scene`、一台按所选机位摆放的临时 `PerspectiveCamera`（朝向规则与视口 `CameraController` 一致：`lookAtMode === 'rotation'` 且无跟随时用欧拉角，否则 `lookAt(target)`）；
- `DirectorInspector` 里新增 `CameraPreviewSection`，几何逐字照抄，并挂上 `FOV n°` 角标与 24×24 放大钮。

### 为什么回读要按签名门控

`readRenderTargetPixels` 是**同步回读**，会 stall 管线。所以渲染只在签名变化时发生，签名含：机位 id/位置/旋转/FOV/lookAtMode/followTargetId、播放头时间与播放态、以及场景里**每个对象**的 id/可见性/位置/旋转。面板静止时一次都不触发；播放时因为播放头每帧变，退化成每帧一次 240×135 的小回读。

### 放大钮的行为是推断

源站这枚钮**没有被点过**（点源站控件会写真实工程，需授权）。图标与可访问名（差集里读作「切换到机位视角」）是实测的；行为取「切到该机位的机位视角」，复用既有已验证的 `selectShot` + `setViewMode`，**不新增 store 动作**。

## 顺带澄清的一件事

clone 本来就**已经有两个** WebGL 上下文（主场景 + 视口角落的方向轴小画布）。所以验收里 WebGL 那条断言写成**前后对比**（挂预览前后计数不变、取消选中后回到基线），而不是拍一个绝对值 —— 第一版写成 `== 1` 直接测出 2，是我的基线取错，不是本批引入了新上下文。

## 回归里逮到并修掉的一个真 bug：导出面板被属性面板吞点击

跑回归时 batch 40 报 `9:16` 点击超时。**基线对照**（把我的改动 `cp` 到 /tmp 再 `git checkout --`、不用 stash）确认这不是 611 引入的，而是**已推送的 batch 610 引入的**：

610 把 FOV 数值框移到了源站的位置 y=842，而导出面板的「比例」三枚按钮正好在 [1727, 832, 84, 32] —— 属性面板的一行落在了它的footprint 上。610 之前那个 y 区间是空的，所以点得下去。

追下去发现根因不在几何而在**层叠上下文**：时间轴 section 带 `backdrop-blur-xl`，而 **backdrop-filter 会创建层叠上下文**，于是导出面板的 `z-50` 被关在这个上下文里出不去；而时间轴自身 `z-index: auto`，又输给了属性面板列的 `z-30`。所以只要属性面板在该 y 区间有内容，导出面板就点不动。

修法：给时间轴 section 加 `z-40`。布局上时间轴与属性面板列各占一格、并不重叠，抬层级不改版面，只让面板/菜单类浮层能盖住右列。修完 `elementFromPoint` 命中回到导出面板自己的按钮，batch 40 一路走过了比例点击那一步（它后面挂在**已记录在案的既有 flake** `frameDifference > 1000` 上 —— 那条两侧都会，机制上也与 DOM 无关）。

这与 batch 604 修的是同一类问题：**看起来能点、其实点不动的控件**。

## 验收结果

`verify-liblib-batch611.py` **49/49 通过**，page error 0。覆盖：

- 未选中机位时**整块不存在**；
- section 280×168 / sticky / z-20 / `rgba(33,33,33,0.98)` / `border-b 1px white/8`（按 alpha 0.08 断言）/ pad 16 / `backdrop-blur` / 含 0.18 阴影；
- 盒 240×135 @x=1656 / `rounded-lg` 实算 12px / `overflow-hidden` / 1px 描边 / `rgba(8,8,16,0.95)`；
- canvas backing store 240×135，盒内起点 +1（即边框压在 canvas 上、由 overflow 裁掉，源站同款）；
- **是渲染不是填充**：亮度跨度 > 40、均值既不接近黑也不接近白、亮像素占比在 0.02–0.95、8×6 亮度网格至少 3 个不同区域；
- `FOV n°` 角标 absolute / `left-3 top-3`（相对 padding box 精确 12px）/ 13px/13px / `text-white/55`（alpha 0.55）/ `pointer-events-none` / 文案跟随 store；
- 放大钮 24×24 / `right-3 bottom-3` 精确 / `rounded-lg` / `bg-white/10`（alpha 0.10）/ `text-white/85` / 14×14 图标 / 可访问名「切换到机位视角」；
- **WebGL 上下文数前后不变（2 → 2 → 2）**，主画布仍非空（1 202 080 px）；
- **活的**：把机位 X 挪到 9.5，缩略图像素指纹改变；把 FOV 改成 70，角标变 `FOV 70°`；
- 放大钮：导演视角 → 点它 → `viewMode` 变 `camera` 且 `activeCameraId` 就是这台机位 → 可逆回导演视角；
- 取消选中 → 整块消失，上下文回到基线。

诊断过滤：除已知的 `TransformControls` 瞬态与 HMR 噪声外，本轮还按**路径**归因过滤了 `src/components/jimeng/nodes/JimengTextNode.tsx` —— 另一位开发者正在这个共享工作区里编辑该文件，半写的块注释会经 HMR 变成 page/console error，与本批无关；按路径匹配而不是整条忽略，我们自己文件里的真错误仍会失败。

## 不声称（not claimed）

- 放大钮的源站点击行为；
- 缩略图与源站**像素级一致** —— 是同一份场景、同一套相机数学、240×135 的缓冲，不是逐字节相同；
- 下面的「相机截图」网格：源站那格实测**高 0**（该工程没有截图），缩略图条目的形态无从量测。

回归：`610`（97）、`609`（73）、`611`（49）、`581`（31）、`36`、`607`（21）、`596`（10）、`47`、`86`、`93` 全绿；`40` 的吞点击已解除，现仅剩既有的 `frameDifference` flake。
门禁：`tsc` clean；`eslint src/components/director/` 0 error（1 条 warning 是他人 `DirectorCameraMotionTab.tsx` 未用 `RefreshCw`）；`npm run build` 通过；`verify-docs` 1249 文件 / 5437 目标全过。
