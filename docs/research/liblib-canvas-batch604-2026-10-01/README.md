# Batch 604 — 视口底部浮动条：两枚并列胶囊

- 日期：2026-10-01
- 源站：<https://www.liblib.tv/canvas?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429>，CDP `http://127.0.0.1:9222`，视口 1920×1150 @DPR2
- 取证脚本：`/tmp/src593/probe51.py`（底栏全量扫描）、`probe52.py`（工具条行 + 容器栈）、`probe54.py`（整条底栏 DOM 树 + 控件全集）、`/tmp/src593/clone604.py`（clone 侧同口径实测）
- 验证器：`scripts/verify-liblib-batch604.py`（34 项）
- 参考图：`docs/design-references/liblib-bottom-bar-604-1920.png`

## 一句话

源站视口底部不是一条扁工具条，而是**两枚并列的胶囊**（工具胶囊 + prompt 胶囊）躺在同一个居中行里；clone 此前是一条扁条，且与自己的 prompt 栏**几乎完全重叠**——这正是 batch 35/43/44 长期失败的根因。

## 一、源站实测结构

```
div.z-(--z-sticky).pointer-events-none.absolute.inset-x-0.bottom-0
    .flex.flex-col.items-center.gap-1                 1920×182 @(0,968)  z=200
  div.pointer-events-auto.flex.items-center.gap-2        360×48  @(780,968)
    div.nodrag.nopan.nowheel.relative.flex.items-end.gap-2  360×48 @(780,968)
      nav.relative.flex.h-12.shrink-0.items-center.gap-2.rounded-full
          .border.border-white/10.bg-[rgba(33,33,33,0.94)].text-white
          .shadow-[0_1px_2px_rgba(0,0,0,0.18)].backdrop-blur-xl.w-32.p-2
                                                       128×48  @(780,968)
        div.relative              → button 移动        32×32 @(789,976)
        span.flex.shrink-0        → button 截图        32×32 @(829,976)
        button 动画时间轴（直接子节点）                   32×32 @(869,976)
      div.relative.shrink-0.transition-[width].duration-200.ease-out
                                                       224×48  @(916,968)
        div.nodrag.nopan.nowheel.relative.z-10.grid.min-h-12.w-full
            .border.border-white/10.bg-[rgba(33,33,33,0.94)].p-2.text-white
            .shadow-[0_16px_24px_rgba(0,0,0,0.18),0_4px_8px_rgba(0,0,0,0.16),
                    0_1px_1px_rgba(0,0,0,0.12)]
                                                       224×48  cols 32/142/32
          button 上传图片  col-1  32×32 @(925,977)  rounded-full text-white/60
                                                      icon size-4，hover:text-white
          input（1×1 隐藏）
          button 发送      col-3  32×32 @(1103,977) rounded-full ml-1
                                                      bg-white text-[#171717]
                                                      disabled:bg-white/8 text-white/28
  div.pointer-events-auto…border-t.border-white/10.bg-[#1f1f1f]
      .shadow-[0_-18px_48px_rgba(0,0,0,0.24)].backdrop-blur-xl  1920×130 @(0,1020)
```

底栏总高 182 = 48（胶囊行）+ 4（`gap-1`）+ 130（导演台面板）。胶囊落在 182 的**顶部**，因为下面被导演台占满。

### 两段视觉语言不一致（照抄不修正）

| | 工具胶囊 `nav` | prompt 胶囊 `grid` |
|---|---|---|
| 圆角 | `rounded-full` | `rounded-full` |
| 底色 | `rgba(33,33,33,0.94)` | `rgba(33,33,33,0.94)` |
| 阴影 | `0 1px 2px rgba(0,0,0,0.18)` | `0 16px 24px / 0 4px 8px / 0 1px 1px` 三段 |
| 按钮圆角 | **`rounded-lg`（8px）** | **`rounded-full`（9999px）** |
| 图标 | **20px（`size-5`）** | **16px（`size-4`）** |
| 底色按钮 | 无 | 发送是 `bg-white text-[#171717]` |

源站自己就不统一，clone 照抄。

## 二、clone 改动前的实测（问题所在）

| | 改动前 | 改动后 |
|---|---|---|
| 工具条 | `absolute bottom-5 left-1/2` 595×44 @(651.5,904) z-10，`h-11 rounded-md bg-[#222]/95 px-1.5` | 671×48 @(497,919)，源站 `nav` 外壳 |
| prompt 栏 | `absolute inset-x-0 bottom-4` **1366×44 @(266,908)** z-20 | 225×48，与工具胶囊同排，间隙 8px |
| 关系 | **几乎完全重叠**：工具条 904–948，prompt 栏 908–952 | 同一行，工具条 919–967 / prompt 918–968 |
| 按钮 | 15px 图标、`rounded`(4px)、idle `#8d8d8d`、选中 `bg-white/10 text-[#5ddcff]` | 20px 图标、`rounded-lg`(8px)、idle `text-white`、选中 `bg-white/8` |
| prompt 胶囊 | `+` 字形 + input + 发送 | `grid-cols-[32px_1fr_32px]`，**上传图片** / input / 发送 |
| 模式段 | 光标 / 相机 / 手 三枚模式钮 | 已删除（源站没有） |

**重叠是真实缺陷**，不是观感问题。基线对照（`git checkout --` 回到 HEAD 后重跑 batch35）直接抓到证据：

```
- <input value="" aria-label="描述想搭建的场景" … data-director-scene-prompt-input="true"
  class="min-w-0 flex-1 …"/> from <div data-director-scene-prompt-bar="true"
  class="pointer-events-none absolute inset-x-0 bottom-4 z-20 flex items-center justify-center gap-2">
  subtree intercepts pointer events
```

prompt 栏 z-20 高于工具条 z-10，其 `pointer-events-auto` 的胶囊正好压住工具条按钮，点击被吞。

## 三、改了什么

1. **共享底栏行**：`DirectorViewport` 新增 `data-director-bottom-bar`，外壳逐字取源站
   `pointer-events-none absolute inset-x-0 bottom-0 z-[200] flex flex-col items-center gap-1`。
   内层 `pointer-events-auto flex w-full overflow-x-auto` + `mx-auto flex shrink-0 items-center gap-2`
   ——源站把这两层合成一层，clone 多一层滚动壳做窄屏保护（batch 41 断言 390 宽下工具条
   `x >= 12` 且右缘 `<= 378`；batch 86 的 `mobileContextGeometry` /
   `contextWithinToolbar` / `noHorizontalOverflow` 也依赖它）。`mx-auto` + `shrink-0`
   保证内容超宽时 auto 外边距解析为 0，左侧不会被 `justify-center` 顶出裁切区。
2. **prompt 胶囊进同一行**：`DirectorDesk` 不再单独渲染 `<DirectorScenePromptBar />`，
   改经 `bottomBarExtra` 插槽交给 `DirectorViewport` 摆在工具胶囊右侧。组件实例与
   内部 state 仍归 `DirectorDesk`，没有把 `DirectorViewport` 的一大堆状态上提。
3. **工具胶囊换源站外壳**：`h-12 rounded-full border-white/10 bg-[rgba(33,33,33,0.94)]
   p-2 gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.18)] backdrop-blur-xl`，按钮
   `size-8 rounded-lg text-white hover:bg-white/8`，`aria-pressed` 选中追加 `bg-white/8`，
   图标 15px → 20px。
4. **删掉幻觉的模式段**：`光标 / 相机 / 手` 三枚模式钮来自 batch 535 对历史截图
   `18-director-console-opened.png` 的转录，源站实时 DOM 里根本没有。已删除，
   batch 535 迁移为断言「不存在」。
5. **`+` 字形换成真实「上传图片」**：32×32 `rounded-full`、`text-white/60 hover:text-white`、
   16px 图标、可及名逐字「上传图片」。点开本地文件选择器，选中后把文件名回填到状态行
   （**本地 mock，不发任何网络请求、不触发生成**）。这兑现「复刻用户体验、可用 mock
   数据支撑交互」。

### 唯一一处有意偏离源站类名

源站 prompt 胶囊写的是 `min-h-12`，但它实测 224×48，而它自己的算术是
8(`p-2`) + 32(按钮) + 8 + 1 + 1(border) = **50**——`min-h-12` 只设下限，内容照样把盒子
撑到 50，源站却实测 48（且 col-1 按钮实测落在 +9 处、底部留 7px，确实被压过）。
按既定「以实测为准」，clone 用 `h-12` 把 48 钉死，让 32px 按钮上下各溢出 1px。

## 四、保留的 clone-only 部分

源站那枚胶囊只有三项（移动/截图/动画时间轴），clone 的控件集大得多，全部保留：

- 变换上下文条（`data-director-transform-context`）
- 移动 / 旋转 / 缩放（`data-director-transform-mode`，源站的「移动」≡ clone 的 translate 档）
- 画幅比 16:9 / 9:16 / 1:1（源站在左侧 rail 的「选择画幅比例」里）
- 九宫格辅助线、虚拟相机、添加群众阵列、模型库
- 保存构图（`data-director-capture`，12 个 verifier 依赖该属性，**属性名未动**）

「保存构图」按钮顺带从 `rounded`(4px) 调到 `rounded-lg`，与胶囊语言一致。

## 五、本批不声称

- **源站「截图」的点击行为未取证**——点它可能触发真实截图并写入用户真实项目，
  按约定不点。clone 侧只对齐外观与 `aria-pressed`，不接一个会真的去截源站图的 handler。
- **源站「动画时间轴」的点击行为未取证**，`aria-pressed=true` 只说明它当前是开态。
  clone 的时间轴常驻可见，接这个开关需要把 `DirectorTimeline` 内部的 `timelineCollapsed`
  上提到 store（且该字段属视图态，按 batch 599 的结论不进持久化 schema），留给后续批次。
- **源站「移动」的点击行为未取证**（无 `aria-pressed`，可能是开菜单而非切档）。
- **源站 prompt 的 Enter 语义未取证**（可能触发付费生成）；上传后的去向、发送的实际行为同理。
- **源站关闭再打开导演台是否保留 zoom 未观测**（batch 599 遗留）。
- clone 的底栏行不含导演台面板（源站那一层还挂着 130px 的导演台），故 clone 的胶囊
  绝对 y 值（919）与源站（976）不同；两者的**相对关系**一致：胶囊行紧贴时间轴面板上方。

## 六、连带修好的既有失败

修掉重叠后，三个长期失败的批次直接转绿（此前记录的根因正是「prompt 栏
`pointer-events-none` 容器内 input/button 重新开启 pointer-events 吞点击」）：

| 批次 | 之前 | 之后 |
|---|---|---|
| batch 35 | 失败（input 拦截截帧按钮点击） | **通过** |
| batch 43 | 失败（同源） | **通过** |
| batch 44 | 失败（同源） | **通过** |
| batch 46 | 失败（`TransformControls` 瞬态） | **通过**（补了与 batch 37 一致的瞬态过滤） |

batch 35 / 46 的过滤是**最小解除**：先做基线对照确认在 HEAD 上同样失败，再照 batch 37
的既有写法过滤 `TransformControls: The attached 3D object must be a part of the scene graph.`
并在结果里留计数。

## 七、门禁与回归

- `verify-liblib-batch604.py`：**34/34**
- 回归：604 / 603 / 602 / 601 / 598 / 596 / 592 / 586 / 535 / 86 / 82 / 47 / 41 / 39 / 38 / 37 / 35 / 36 —— 全过
- `tsc --noEmit`：clean
- `eslint src/`：0 error / 13 warning（与基线一致，无新增）
- `npm run build`：通过
- `python3 scripts/verify-docs.py`：通过

### batch 40 是既有 flake，不是本批回归

batch 40 的 `frameDifference > 1_000` 会间歇失败。采样：

- 改动后 4 次：2 过 2 败
- 基线（HEAD 源文件）4 次：3 过 1 败

两侧都会失败，且机制上不可能相关——导出走 `output.captureStream(30)` 的 **canvas 流**
（`src/components/director/directorVideoExport.ts:194`），DOM 外壳根本不在视频里。
判定为既有抖动，记录在案，不改该断言。

## 八、下一批候选（batch 605）

- 源站有而 clone 无的「退出跟随」（64×16 @(970,9)）
- 「收起」按钮位置：源站在 280px 左列 header 右缘 40×40 @(240,·)，clone 在顶栏 32×32 @(155,·)
- 「导演视角 / 机位视角」：源站 81×32，clone 68×28
- 动画时间轴开关（需把 `timelineCollapsed` 上提到 store，属视图态不进持久化 schema）
