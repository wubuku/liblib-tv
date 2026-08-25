# LibTV 画布 Batch 9 实施记录

> 状态：已完成
> 最后更新：2026-08-25

## 1. 规划与证据

- 复核图片选中态的节点、工具条与编辑面板原站矩形；
- 复核失败视频与 Seedance 生成面板原站矩形；
- 明确顶部 `NodeToolbar` 使用屏幕像素间距；
- 明确底部节点内面板使用 `16 * zoom` 屏幕间距；
- 把 Batch 8 的真实 parent-child 纳入浮层跟随验证；
- 定义“现状满足则只加测试，不强行改视觉”的退出条件。

规划已提交并推送：

```text
466333f docs: plan LibTV floating UI anchor batch
```

## 2. Clone 基线测量

在修改前的 `929x874` 整理态：

```text
image:
  node center = panel center
  toolbar = 900x49
  panel = 660x274
  panel gap = 4.257px

video:
  child center = panel center
  panel = 660x274
  panel gap = 4.256px

zoom inferred from 622px world width = 0.283816
16 * zoom = 4.541px
```

现有中心锚定、反缩放、自然裁切和 parented child 跟随模型都是正确的。唯一可重复的几何偏差是底部面板间距只有 `15 * zoom`。

原因不是 Tailwind translate 被覆盖。Tailwind v4 使用独立 `translate` 属性，inline `transform: scale(...)` 可以与其共存。真实原因是面板直接挂在有 `1px` border 的节点壳中：绝对定位包含块的 padding edge 比节点外边界少 `1` flow unit。

## 3. 实施

### 底部面板间距

以下节点内面板从 `-bottom-4` 改为 `-bottom-[17px]`：

- `ImageEditPanel`
- `VideoGenerationPanel`
- `SegmentReshootPanel`

在当前 bordered node shell 中，这会得到原站的 `16` flow-unit 外部间距。z-index 同时从 clone 旧值 `30` 对齐到原站 class 的 `20`。

### 图片顶部工具条

`ImageToolbar`：

- 固定屏幕宽从 `900px` 校准为原站实测 `900.5px`；
- 继续使用 React Flow `NodeToolbar(position=Top, align=center, offset=16)`；
- 不添加浏览器视口夹取。

### 稳定验证接口

新增：

```text
data-image-toolbar
data-image-edit-panel
data-video-generation-panel
data-segment-reshoot-panel
```

这些 attribute 只用于自动化测量，不改变视觉或交互。

实现与专项验证已提交并推送：

```text
c0d7e72 fix: align LibTV selected node overlays
```

## 4. 专项验证

```bash
python3 scripts/verify-liblib-batch9.py
```

最终 `929x874` 整理态实测：

```text
image:
  node center = 393.120
  toolbar center = 393.120
  panel center = 393.120
  toolbar gap = 16.000px
  toolbar size = 900.5x49
  panel gap = 4.541px
  expected 16 * zoom = 4.541px
  panel size = 660x274

video:
  child center = 643.446
  panel center = 643.446
  panel gap = 4.541px
  expected 16 * zoom = 4.541px
  panel size = 660x274
```

专项脚本还验证：

- 靠左图片的工具条和面板均为负 x，没有视口夹取；
- textarea 输入和滚轮不会移动节点或 React Flow viewport；
- parent drag 时 child 获得同样位移，选择切到 parent 后面板卸载；
- 重新选择 child 后面板在新绝对位置重建；
- child drag 时 parent 不动，panel 与 child 获得相同位移；
- zoom 从约 `28%` 到 `38%` 后面板仍为 `660x274`，间距更新；
- wheel pan 后 child 与 panel 获得相同位移；
- 图片与视频多选时所有单节点大型浮层隐藏；
- 控制台 error 为 0。

截图：

- `docs/design-references/liblib-clone-batch9-image-anchor-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch9-video-anchor-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch9-video-parent-child-follow-2026-08-25.png`

本批已识别截图的详细视觉结果写入 `SCREENSHOT_ANALYSIS.md`。截图识别复用规则同时加入项目检查指南与 `clone-website` 技能，并同步到所有平台副本：

```text
ddc985b docs: persist screenshot recognition findings
```

## 5. 跨批与工程验证

以下全部通过：

```bash
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch8.py
python3 scripts/verify-liblib-batch9.py
npm run check
```

- lint：0 error，保留仓库既有 9 个 warning；
- TypeScript strict：通过；
- Next.js 16.2.1 production build：通过；
- Batch 4-Batch 9 的交互回归全部通过。

## 6. 接力边界

- 原站直接证据是矩形、class、控件与无夹取行为；
- `-bottom-[17px]` 是 clone 为补偿自身 node shell border 的实现值，不是对原站 CSS class 的改写；
- parent drag 会改变选中对象，面板卸载是当前 React Flow 生命周期，不应伪造“面板跨选择持续显示”；
- 多选隐藏是 clone 的画布可操作性规则，不描述为原站实测；
- 当前有头原站浏览器不在本工具会话中，Batch 9 使用的是同日已保存的登录态 DOM JSON 与截图；
- 后续若调整节点 border 或把面板移到无边框 wrapper，必须重新测量 `-17px` 补偿，不能机械保留。
