# Batch 364 — 一个从未被任何门禁发现的死控件

## 立项依据: 画布本体全绿之后, 去哪找问题?

Batch 361 的 runner 首次跑出可信全局图: **297 passed / 14 failed**, 而 14 个
全部属导演台并行 session。**画布本体 100% 全绿** —— 已经没有可查的红了。

于是转向另一个问题: **还有哪些面从没被验证过?**

## 判据先被自己否决了一次

写 `probe_liblib_batch364_coverage.py`, 取每个画布组件源码里的 `data-*` 标记,
看有没有 liblib 门禁引用过。

**第一版判据是「组件名在门禁里出现过没有」, 报出 30 个未覆盖** —— 里面赫然
包括 `ImageEditPanel`, 而它明明被 batch359 的节点面普查**完整扫过**。

> **判据错了, 结论就全错。** 门禁靠 `data-*` 定位元素, 不靠组件名。
> 改用标记覆盖率后真相才出来: UNCOVERED = 0, PARTIAL = 10。
> 那个 30 的数字是**纯噪声**, 如果照它开工, 会去普查一堆早已验证过的面。

UNCOVERED = 0 这个零也做了双向自检: 造一个带 `data-*` 的假组件
(`ZzProbeTmp`), 普查立刻报 `UNCOVERED: 1`; 删掉后归零。**是真的干净, 不是测不到。**

## 真发现: PictureEditPanel 漏了 4 个标记

PARTIAL 里 `PictureEditPanel` 最可疑 —— 漏了 `picture-edit-mark-selected` /
`picture-edit-mark-time`, 那是一整块**有状态的交互**(标记帧的选中态与时间显示)。

于是写探针去打开它。**打开它花了四步, 每一步都是可达性事实**:

1. `evaluate("(el)=>el.click()")` 选节点 → **React Flow 收不到选中态**
   (它的 onClick 依赖 pointer 事件链), 工具条不出现。改真实鼠标点击。
2. 节点确实选中了(store: `nodeIds: ["v-UGQZzZOpbv"]`), 但 `NodeToolbar` 仍 0
   —— fixture 里那个视频节点 **`status: "failed"`**, 工具条要求 `"ready"`。
3. 置 ready 还不够: 菜单点「主体消除」后面板不开 —— `selectPictureEdit` 有
   **时长守卫**, 源视频必须 3~15 秒(`VideoNode.tsx:338-347`)。
4. 前两步用 Playwright 的 `click()` 会**移动鼠标**触发菜单容器的
   `onMouseLeave` → 菜单先被关掉, 点了个寂寞。改 `evaluate(el=>el.click())`。

> **这四步本身就是结论**: 这段编辑面在默认 fixture 上**根本走不到**。
> 不是「懒得测」, 是「走不到, 所以任何门禁都碰不到它」。
> 探针全程**如实报「跳过」而不是「0 问题」** —— 选择器写错那一次也是这么报的,
> 所以错误可见, 没变成假零。

## 抓到的缺陷

`src/components/nodes/VideoNode.tsx:490`:

```tsx
<button type="button" aria-label="播放视频"
  className="... size-14 ... hover:bg-black/70">
  <Play size={22} />
</button>
```

**无 onClick、无 disabled, 却带 `hover:bg-black/70`** —— 用户悬停看到它变亮,
点下去什么都不发生。它是视频节点封面上最大的圆形播放钮(56px), 视觉上最像
「点了会播视频」。

**决定性对照 —— 同一功能两处实现, 只接了一半**:

| 位置 | 标记 | onClick |
|---|---|---|
| `StoryboardBoard.tsx:78` | `data-storyboard-play` | **有** —— `onPlay?.()` 打开灯箱 |
| `VideoNode.tsx:490` | 无 | **无** |

连 `grep -rl '播放视频' scripts/verify-liblib-*.py` 都是**空** ——
这个控件从未被任何门禁提及过。

## 修法: 与 358/359/360 同策, 不发明

源站行为未采样(人机验证仍阻塞), 播放已有视频不涉及付费/生成, 但**仍不擅自
接线** —— 按既定处置让 UI 停止撒谎: 去掉 `hover:bg-black/70` + `cursor: default`
+ `title="播放功能暂不可用，请使用分镜板预览"` + `data-inert="true"` 自证惰性。

**几何与文案一律不动**(batch612 钉住的尺寸)。不用 `aria-disabled` ——
Playwright `is_disabled()` 会把它算作禁用, 与既有门禁冲突(见 batch358)。

## 门禁 11 项 + 变异全红

1. 防假零: 视频节点**真的**置为 ready + 合法时长, 工具条**真的**出现;
2. 播放按钮**真的存在**;
3. 惰性必须**自证**: `data-inert` + 非空 `title` + `cursor: default`;
4. **不误伤** `StoryboardBoard` 那个有 handler 的同名按钮;
5. `picture-edit` 面板**必须真的打开**(打不开直接红, 不许报 0 问题);
6. 面板无静默丢弃 / 无死控件 / 无交互谎言;
7. 覆盖下界: 至少扫到 30 个控件(实测 49)。

变异两轮, **红在对的地方**:

| 变异 | 结果 |
|---|---|
| 把 `hover:bg-black/70` 加回去 | exit=1, 红在 `picture-edit:no-lying-affordance` |
| 拿掉 `title` | exit=1, 红在 `video-play:has-explanatory-title` + `no-dead-control` |

> 第二项变异同时触发两条, 说明判据之间有交叉覆盖, 不是各管一摊。
> 两轮都**不是**被 TypeError 之类副作用抓住的 —— 那才算真正验证到了断言。

## 顺带记下(只记录不修)

- `CameraConfigDialog`(10 控件) / `CameraMovementDialog`(7 控件) 是普查里
  唯一两个「既无 `data-*` 标记、又无人渲染」的组件 —— **真盲区**。
  但它们属导演台跨线范围(batch360 已记), 不动。
- 其余 4 个无标记组件(`ChromeIcons` / `ImageElementEditMode` /
  `PlusIndicator` / `ScriptHeader`)**零可交互控件**, 不可测但无害, 不报。
