# Batch 21 Screenshot Analysis

## 1. 原站 Seedance 菜单状态

### 文件

- `docs/design-references/liblib-original-seedance-model-menu-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-mode-menu-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-params-menu-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-long-params-2026-08-25.png`
- 来源：LibTV 登录态画布
- 采样日期：2026-08-25
- viewport：`929x874`
- 识图方式：四图缩放后合并为一次性临时 contact sheet
- 识图次数：1

### Source fact：共同层级

- 四个 popover 都从视频生成 panel footer 向上展开。
- popover 叠在画布和节点之上，但 footer trigger 仍保持可见。
- 原站使用较大的深灰实体面板和低对比 border，不是紧贴文字的 compact menu。
- 视频节点、panel 和画布构图不随菜单切换重排。

### Source fact：普通参数

- 比例区是 7 个带 outline glyph 的卡片：
  - 第一行 `Auto / 16:9 / 4:3 / 1:1 / 3:4`
  - 第二行 `9:16 / 21:9`
- `16:9` active card 有更亮 border 和 surface。
- 清晰度为 `480P / 720P / 1080P` 三段整宽 control，`720P` active。
- 视频时长标题右侧有当前值框 `6 s`，下方为 slider。
- 生成音频是 `开启 / 关闭` 两段整宽 control。
- 生成数量是 `1个 / 2个 / 4个` 三段整宽 control。
- DOM rect：`341x445`，`x=541.320, y=90.961`。

### Source fact：超长参数

- 比例和清晰度结构与普通态相同。
- 视频时长当前值为 `30 s`，范围为 `30-300s`。
- slider 下有一行灰色时长设计说明。
- 生成音频仍为整宽两段 control。
- 不显示生成数量。
- DOM rect：`341x397`，`x=549.305, y=138.961`。

### Source fact：模式与模型上下文

- 模式菜单中：
  - disabled：文生视频、图生视频、首尾帧、视频编辑
  - enabled：全能参考、图片参考、超长视频 Beta
- 模型截图可见 Seedance 2.5、Seedance 2.0 VIP、Minimax H3、Seedance 2.0 Fast VIP、Seedance 2.0 Mini、Wan 3.0 Prime、Wan 3.0。
- 模型列表底部可能还有被裁切内容，因此本批不把可见列表当作完整模型清单。

### Unknown

- 没有提取 ratio glyph 的原始 SVG path。
- 没有参数 dialog 的 hover/enter transition。
- 模型和模式 popover 的精确 DOM rect 未进入 `live-audit.json`。

## 2. 当前 clone DOM 审计

### Normal

- generation panel：`x=453.939, y=304.897, w=660, h=274`
- params dialog：`x=603.767, y=231.068, w=341, h=299.328`
- 相对 panel：`left +149.828`, `top -73.828`

### Long

- params dialog：`x=603.767, y=263.068, w=341, h=267.328`
- 相对 panel：`left +149.828`, `top -41.828`

### Gap conclusion

- normal 高度少约 `145.7px`，top 比原站相对位置低约 `137.9px`。
- long 高度少约 `129.7px`，top 比原站相对位置低约 `121.9px`。
- compact pills、无当前值框和无超长说明与截图结构不符。

### Re-inspection rule

本批实现前不再打开这四张原站截图。后续优先使用本文和 `live-audit.json`；只有 glyph path、动画或模型/模式精确 rect 成为新范围时才重新采样。

## 3. Clone verification

### 文件

- `docs/design-references/liblib-clone-batch21-video-params-normal-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch21-video-params-long-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch21-video-params-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch21-video-params-contact-sheet-2026-08-25.png`
- 生成日期：2026-08-25
- 识图方式：normal、long、mobile 合并为一次性 contact sheet
- 识图次数：1

### Verified clone fact

- normal 与 long dialog 都从 footer trigger 向上展开，footer model/mode/settings 仍可见。
- 两种 dialog 的 ratio cards 都保持 5+2 排列，active `16:9` 使用更亮 border。
- resolution 是整宽三段 control，active `720P` 清晰可辨。
- duration label、value box、slider 和 min/max 没有相互遮挡。
- normal 的 audio/count controls 都落在固定 `445px` 高度内。
- long 的 helper 与 audio control 都落在固定 `397px` 高度内，count 不存在。
- 390px 下 dialog 与 generation panel 按节点上下文自然裁切；底部两条画布工具条仍在页面层可见。
- 页面没有横向滚动，也没有 console/page error。

### DOM-backed geometry

| State | Dialog | Relative to generation panel |
|---|---:|---:|
| normal | `x=535.767, y=93.397, w=341, h=445` | `left +81.828, top -211.500` |
| long | `x=543.767, y=141.397, w=341, h=397` | `left +89.828, top -163.500` |

Source target：

| State | Source relative geometry |
|---|---:|
| normal | `left +82.016, top -211.710` |
| long | `left +90.000, top -163.710` |

### Clone-only detail

- ratio glyph 使用 CSS outline，不声称复用了原站 SVG path。
- long helper `围绕视频画面设计，支持更长时长的连续场景` 是对截图可见语义的保守改写，不是逐字 DOM extraction。
- 参数和积分继续是本地 state，不发送模型任务或计费请求。

### Re-inspection rule

除非 Batch 21 实现或截图发生变化，不再打开本批 clone 截图；几何和行为问题优先运行 `scripts/verify-liblib-batch21.py`。
