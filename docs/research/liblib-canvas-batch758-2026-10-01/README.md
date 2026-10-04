# batch 758 — 节点类型的 DOM 契约普查：查出**高严重度缺陷**「双击空白画布开面板」从未触发

## 起点

757 普查了 `storyboard-group` 一种节点。而 `page.tsx:145-157` 注册了
**13 种**节点类型，种子上只出现过 5 种 —— 另外 8 种（含 `video-clip` /
`shot-breakdown` / `audio` / `script`）**从未在这台机器的屏幕上被量过**。

本批把面板能提供的类型全部建出来，逐个量 DOM 契约，并对 13 个组件做静态普查。

入口先做普查：「添加节点」面板共 **9 个条目**（左栏 32×32 按钮
`aria-label=添加节点` 可开），其中 `script` / `material` 两项带箭头、走子菜单。
先把入口钉住，否则「某类型建不出来」会分不清是入口坏了还是类型不支持。

## 一、缺陷：双击空白画布开面板 —— 入口从未触发

`page.tsx:421-430` 在画布容器上注册了一个 dblclick 监听器：

```tsx
const handleDoubleClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null;
  if (!target?.closest(".react-flow__pane")) return;
  const state = useUIStore.getState();
  if (!state.isAddNodePanelOpen) state.toggleAddNodePanel();
};
container.addEventListener("dblclick", handleDoubleClick);
```

**实测：连打两次双击，面板条目数始终是 0。**

这是个否定结论，所以必须配阳性对照，否则无法区分「入口坏了」与「我的双击没送到」：

| 对照 | 读数 |
|---|---|
| 双击点是否真在 `.react-flow__pane` 上 | `pointIsPane=**true**` |
| 原生 `dblclick` 是否到达页面（window **捕获**计数器） | **+1** |
| 原生 `mousedown` 计数 | **+2** |
| 面板条目数 | **0** |
| 再打一次双击 | 计数器 +1，条目仍 **0** |
| **阳性对照**：同浏览器对左栏按钮双击 | 计数器 **+1** 且开出 **9** 个条目 |

所以 Playwright 的 `dblclick` 在这台机器上确实能产生原生事件，**不是探针不行**。

### 机制：事件进了 pane 就被掐断

在三个位置各挂一个计数器（容器挂捕获+冒泡两个）：

| 计数器 | 值 |
|---|---|
| 容器**捕获** | **1** |
| pane **冒泡** | **1** |
| 容器**冒泡** | **0** |
| window **冒泡** | **0** |

事件路径是：**容器捕获 → pane 冒泡 → 断**。

React Flow 在 pane 处 `stopPropagation` 掉了 `dblclick`，
而 app 的监听器恰恰挂在**容器上等冒泡阶段** —— 所以它**永远收不到**。

修复方向有三个（都没验证过）：把监听器挂到 `.react-flow__pane` 上、
改用捕获阶段、或直接用 React Flow 的 `onPaneDoubleClick` prop。

## 二、8 种类型全部建出，几何与 handle 契约

各建出 **+1** 节点，**0 失败**。`script` 走子菜单 `script-new`。
⚠ zoom 在同一批里变了两次：757 是 **0.375**、758a 读到 **1.501**、758c 读到 **0.751**。
所以凡读 DOM 几何都必须**当轮现取 zoom 换算**，不能沿用上一批或上一个探针的值。
判据 5 把两个探针各自的 zoom 都记了下来。

zoom 换算后，8 种类型的未缩放宽高与 store **逐项相等**。
运行时 handle 数**全部是 2**（target + source）。

## 三、★ `ShotBreakdownResultNode` 是 13 个组件里唯一只有 1 个 handle 的

| 组件 | Handle | data 钩子 | aria | aria-label | 框外标题 |
|---|---|---|---|---|---|
| VideoNode | 2 | **53** | 2 | ✓ | ✓ |
| ImageNode | 2 | **23** | 1 | ✗ | ✓ |
| LongVideoProcessNode | 2 | 15 | **0** | ✗ | ✓ |
| ScriptGeneratorNode | 2 | 5 | 3 | ✓ | ✓ |
| **ScriptNode** | 2 | **0** | 1 | ✓ | ✓ |
| ScriptV2Node | 2 | 1 | 1 | ✗ | ✓ |
| ScriptExecutionNode | 2 | 3 | **0** | ✗ | ✓ |
| ShotBreakdownNode | 2 | 5 | 1 | ✗ | ✓ |
| **ShotBreakdownResultNode** | **1** | 6 | 2 | ✓ | ✓ |
| **StoryboardGroupNode** | 2 | **0** | **0** | ✗ | ✓ |
| TextNode | 2 | 2 | 1 | ✗ | ✓ |
| VideoClipNode | 2 | 3 | 1 | ✗ | **✗** |
| AudioNode | 2 | 6 | 1 | ✓ | ✓ |

`ShotBreakdownResultNode.tsx:177` 只有
`<Handle type="target" position={Position.Left} id="target" />`，
其余 12 个组件都是 target+source 各一（例如 `ShotBreakdownNode.tsx:97-98`）。

含义：逐帧拉片的结果卡（754 验过，3 维→5 结果）是**死端** ——
可以接收连线，但**拖不出**任何连线。

⚠ 这一格**只在静态侧验到**：该类型不在种子上、也不从面板直接建。

## 四、更正：「`video-clip` 没有框外标题」是**我的探针缺陷**

初版（758c）结论是「`video-clip` 是 8 种类型里唯一框外没有标题的」。
**这条已作废。**

回去看源码，`VideoClipNode.tsx:65-68` 的标题行是：

```tsx
<div className="pointer-events-none absolute -top-8 left-0 flex items-center gap-2 text-sm text-[#858585]">
  <Scissors size={14} />
  {data.title ?? "智能剪辑 1"}     ← 裸文本节点，没有包在元素里
</div>
```

而 758c 的扫描写了 `if(x.children.length) return;`（**只取叶子元素**）——
标题 div 因为含那个 `<Scissors>` 子元素被整块跳过，里面的裸文本又没有任何元素
包裹 ⟹ 一个叶子都扫不到。

758d 改回**元素级**判定（只要包围盒底边在节点顶边之上就算），重测：

| 类型 | 框外标题 | 候选元素数 | 标题是裸文本 |
|---|---|---|---|
| text | 「文本节点」 | 4 | ✓ |
| image | 「新图片」、「512 × 512」 | 5 | ✓ |
| video | 「视频节点 5-片段重拍」、「1280 × 720」 | 5 | ✓ |
| **video-clip** | **「智能剪辑 1」** | 3 | ✓ |
| script-execution | 「第一集：咖啡馆对峙」 | 1 | ✓ |
| shot-breakdown | 「逐帧拉片」 | 4 | ✓ |
| audio | 「新音频」 | 3 | ✓ |

**7 种类型全部有框外标题，产品没问题。**

更普遍的一点：**7 种类型的标题全是「图标 + 裸文本」结构**（`hasBareTextNode`
全为 true），所以任何靠「读叶子元素文案」的工具都会把它们的标题**全部漏掉**。
758a 用的**不要求叶子**的启发式本来是对的，是我在 758c 收窄了扫法才出的问题。

顺带查清静态普查的第二个坑：框外标题在代码里有**两种写法** ——
`-top-8`（`VideoClipNode` / `ShotBreakdownNode` / …）与
`top-[-28px]`（`TextNode` / `ScriptV2Node` / …），只匹配一种会误判。

## 五、★ 种子 image 节点把原始流水线文件名显示成标题

同一个 `image` 类型，两种实例给出两种标题：

| 实例 | 框外标题 |
|---|---|
| 种子 image 节点 | **`image_2026-06-15T11-22-00`** |
| 面板新建的 image 节点 | 「新图片」 |

根因在 `AudioNode.tsx:21`（image/video 同构）：

```tsx
const filename = data.filename ?? "新音频";
```

**标题就是 `filename` 本身**。而种子的 filename 写死在
`canvasStore.ts:825/843`（`image_2026-06-15T11-22-00`、
`image_2026-06-15T11-22-15`）—— 流水线命名直接漏进了用户可见的标题。
另两个种子视频节点的 filename 是「分镜 #2」「分镜视频-#9」，属于半正常。

## 六、aria 与测试钩子：两处分布极不均

- **aria 属性为 0** 的组件：`LongVideoProcessNode`、`ScriptExecutionNode`、
  `StoryboardGroupNode`
- **无 `aria-label`** 的组件：13 个里有 7 个
- **data-\* 钩子为 0** 的组件：`ScriptNode`、`StoryboardGroupNode`
- **data-\* 最多**：`VideoNode` 53 个、`ImageNode` 23 个

测试钩子的投入差了 53 倍。后两者（`ScriptNode` / `StoryboardGroupNode`）
正是 756/757 要靠 store 读数才能测的类型 —— 本批能给出 8 种类型的 DOM 读数，
靠的是**通用选择器**，不是各家自己的钩子。

## 七、判据

14 条。757 那种「两轮一致性」在本批不适用 —— 这是**普查型**单轮，
每种类型只建一个实例；涉及可变状态的三格（双击机制、面板开关、节点数变化）
都在同一轮内做了阳性/阴性对照。

1. 「添加节点」面板 9 个条目普查（左栏 32×32 按钮可开）
2. **★ 双击空白画布开面板 = 高严重度缺陷**（事件到达但面板条目恒为 0）
3. **★ 机制钉死**：容器捕获=1 / pane 冒泡=1 / 容器冒泡=0 / window 冒泡=0
4. 8 种类型各建出 +1 节点，**0 失败**（`script` 走子菜单 `script-new`）
5. zoom 换算后 DOM 尺寸 == store 尺寸（8 种全对）
6. 8 种类型运行时全部 2 个 handle
7. **★ `ShotBreakdownResultNode` 唯一只有 1 个 handle**（target，只进不出）
8. **更正**：8 种类型**全都**遵守框外标题约定（758d 元素级重测）；
   758c 的「video-clip 无标题」是探针缺陷，已作废
9. **★ 种子 image 节点把原始流水线文件名当标题显示**
10. 标题文案横向对照表
11. aria 覆盖不均：静态 3 个组件为 0，运行时 1–4 个不等
12. `aria-label` 只出现在 6/13 个组件里
13. **★ data-\* 钩子分布差 53 倍**（VideoNode 53 vs ScriptNode/StoryboardGroupNode 0）
14. 本批两处诚实边界（见下）

## 八、返工五处（全是探针问题，不是产品问题）

| id | 现象 | 教训 |
|---|---|---|
| R24 | 用「空白画布双击」开面板，8 种类型全部 entry-hit missing | **「入口打不开」第一嫌疑是探针**；同一个动作至少准备两条独立入口（双击 vs 左栏按钮），两条都失败才有资格说入口坏了 |
| R25 | 否定结论缺阳性对照，差点把探针限制当成产品缺陷 | **说「某入口坏了」之前必须有一条能证明事件送达的阳性对照**；「事件没送达」和「送达了但被掐断」是两个完全不同的结论 |
| R26 | 标题启发式太窄，把「标题在框内」误报成「没有标题」 | **启发式筛选会把「不同」误报成「没有」**；宁可多列原始读数让方位自己说话，也不要让窄条件直接下「不存在」的结论 |
| R27 | 758b 报了 4 个 `missing`，差点读成「这 4 种没标题」 | **探针的 `missing` 必须区分「目标不存在」与「特征不存在」**；普查型批次里前者往往说明量错了范围 |
| R28 | 758c 的「叶子元素」扫描把 `video-clip` 的框外标题漏掉，导致判据 8 一度写成「唯一框外无标题的类型」 | **判据写「某物不存在」之前，必须用至少两种不同口径各查一次**；同一口径内部自洽不构成证据 |

R25 与 R28 是本批最关键的两条：

- **R25**：如果没有那两条阳性对照，我大概率会把「Playwright 的 dblclick 在这个
  环境里没生效」写成「产品的双击入口坏了」—— 一个关于**探针**的错误结论。
- **R28**：R26 与 R28 是**同一类错误的两次重演**，而且第二次就发生在
  我把 R26 的教训写进产物之后的**同一个批次里**。R26 说「宁可多列原始读数、
  不要让窄条件直接下不存在的结论」，我下一批就把扫法收窄到只取叶子，
  于是又造了一个假结论。教训要落到**具体动作**上：多口径交叉。

## 九、待拍板（需改 `src/`，等授权）

1. **双击入口怎么修**（本批新，最高优先）：监听器挂到 `.react-flow__pane` 上 /
   改捕获阶段 / 用 `onPaneDoubleClick` prop —— 三个方向都没验证过。
   另外 `if (!state.isAddNodePanelOpen)` 让它**只能开不能关**，双击已开的面板
   不会有任何反应，要不要改成 toggle。
2. **`ShotBreakdownResultNode` 补 source handle**（补齐后结果卡才不是死端），
   还是它本来就该是只收不发的终点。
3. **种子节点的 filename 当标题**：要在数据层给出可读标题
   （`分镜视频-#9` 那种），还是在渲染层做一次清洗。
4. **aria / aria-label 补齐**：`LongVideoProcessNode` / `ScriptExecutionNode` /
   `StoryboardGroupNode` 一个 aria 都没有；13 个里 7 个无 aria-label。
5. **测试钩子补齐**：`ScriptNode` / `StoryboardGroupNode` 一个 `data-*` 都没有；
   顺带考虑是否给 758 这类普查定一条「每种节点至少一个 data-* 钩子」的约定。
6. 沿用 757 拍板项：分组框跟随成员、空组可见性、标题选中反馈对比度、
   `groupKind` 接还是删。
7. 沿用 756 拍板项：组合跨组多选的成员保护（本会话至今的头号缺陷）。

## 十、不声称

- 本批是**普查型单轮**，没有做两轮一致性判定（每种类型只建一个实例）
- **未在运行时验证** `ShotBreakdownResultNode` 的单 handle 结论 ——
  该类型不在种子上也不从面板直接建；「结果卡拖不出连线」这个后果
  也没做运行时点击验证
- `script-generator` / `script-v2` / `long-video-process` 三种
  **既不在种子上、也不能从面板直接建**，只有静态读数，没有 DOM 读数
- 未测：节点缩放、节点内的可交互控件、节点的键盘可达性、
  节点被复制/删除后的 DOM 回收
- aria 普查只统计属性**名**，没逐个核对 `aria-label` 的**内容**
- 标题方位用的是叶子元素包围盒粗判，没区分「真标题」与「恰好在框外上方的别的文字」
- 视频节点框外标题在不同实例间不同（种子「分镜视频-#9」vs 新建
  「视频节点 5-片段重拍」），**没有追这个命名逻辑的来源**
- **没有与源站对照**：源站的节点标题 / handle / aria 契约未知
- 双击入口的修复方案只列了三个方向，**没有验证任何一个可行**

## 产物

| 文件 | 说明 |
|---|---|
| `runtime-audit.json` | 14 条判据（含 1 条更正）+ 面板普查 + 13 组件静态普查 + 5 处返工 + 不声称清单 |
| `README.md` | 本文件 |
| `scripts/verify-liblib-batch758.py` | 验收器：静态 `src/` 复核 / 产物层 / 原始读数叶子级交叉核对 |

探针：`/tmp/dbg758{a,b,c,d}.py` ⟹ 原始读数 `/tmp/vb758{a,b,c,d}.json`
（汇编器 `/tmp/mk758audit.py` 从原始读数现算产物，13 组件的静态普查由汇编器
自己扫 `src/components/nodes/*.tsx`，本文件不手抄任何计数）。

未改 `src/`（自 batch 740 起 0 行改动）⟹ 跳过 build，绿构建记录停在 Batch 255。
