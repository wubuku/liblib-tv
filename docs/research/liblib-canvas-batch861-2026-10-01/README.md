# batch 861 — 导演台「全景图」三行**不再是死按钮**

## 0. 一句话结论

★ batch 859 把「全景图」面板化之后，那三行（**本地上传**／**历史记录**／**AI生成**）
**仍然完全没有 `onClick`** ⟹ ⟹ 点了什么也不会发生。

★ 本批用**源站逐字 ＋ 源站运行时实测**钉死了三行各自在源站的行为，
并把 clone 的三行**接上真实行为**：
**本地上传**真的弹出文件选择器；**历史记录**与**AI生成**真的打开一个选择器对话框
（AI 那行多「生成」「上传图片」两个入口，与源站逐条一致）。

---

## 1. ★ 靶子：clone 的三行是死按钮（改之前的实测）

`src/components/director/DirectorPanoramaPanel.tsx`（batch 859 建的那版）里，
三枚行按钮长这样：

```tsx
<button key={item.id} type="button"
        data-director-panorama-option={item.id}
        className={ROW_CLASS}>
  <Icon size={14} className="shrink-0" aria-hidden="true" />
  <span className="truncate">{item.label}</span>
</button>
```

⟹ ⟹ **没有 `onClick`** ⟹ ⟹ 三行都是**死按钮**。

★ 而源站逐字（chunk `aU` 的 panorama 段）**每一行都有 `onClick`**：

```js
(0,i.jsxs)("button",{type:"button",className:eu,
  onClick:()=>{I?.(),et.current?.click()},…})     // ① 本地上传
(0,i.jsxs)("button",{type:"button",className:eu,onClick:T,…})            // ② 历史记录
(0,i.jsxs)("button",{type:"button",disabled:E,className:eu,onClick:P,…}) // ③ AI生成
```

★ ★★ 源站那三行的行为**不是**猜的，是**点出来的**（见 §2）。

---

## 2. ★ 源站实测：三行各自在做什么

### 2.1 逐字：三个回调的实现

| 行 | 回调 | 逐字实现 | 真正行为 |
|---|---|---|---|
| 本地上传 | `I` ＝ `oY` | `useCallback(()=>{let{hasPanorama:e}=n3(); 埋点("libtv.canvas.director.panorama.local_upload.click",{…})},[n3])` | ★ **纯埋点**；真正的动作是面板那一行的 `et.current?.click()` |
| 历史记录 | `T` ＝ `oB` | `useCallback(()=>{eu?.((e,t)=>{e&&(nS.current={source:t?.panoramaSource??"generation_history",uuid:t?.panoramaUuid},r6({panoramaUrl:e}))})},[eu,r6])` | 打开**资产库选择器**，选中后 `r6({panoramaUrl})` ＝ 应用为全景图 |
| AI生成 | `P` ＝ `oX` | `useCallback(()=>td(!0),[])` | 打开一个对话框（`tc` 状态，`escape` 关闭） |

★ 源站逐字：`et` ＝ 一个**隐藏的 file input** 的 ref ⟹ ⟹ 「本地上传」的真实动作
就是**触发那个隐藏 input**（选中之后的回调是 `onUploadPanoramaFile` ＝ `oz`，
它会**上传**并把结果落成 `panoramaUrl`）。

### 2.2 ★★ 运行时实测（`probes/source861_panorama_rows.py` ＋ `probes/source861_panorama_diff.py`）

| 读数 | 值 | 出处 |
|---|---|---|
| 点「本地上传」 | **弹出了文件选择器**（Playwright `filechooser` 事件 ＝ `True`） | `raw/source-861-panorama-rows.json` |
| 点「历史记录」 | 按钮数 **86 → 95**；新增 `生成历史`／`我保存的`／`我上传的`／`本项目`／`全部项目`／`图片0`／`取消`／`确认选择` | `raw/source-861-panorama-diff.json` |
| 点「AI生成」 | 按钮数 **86 → 98**；在上一批之外**再多** `上传图片`／`生成`／`关闭` | 同上 |
| 三行的 `disabled` | **全为 `false`**（`opacity:1`／`cursor:pointer`） | `raw/source-861-panorama-rows.json` |
| 那个对话框 | **全屏**（rect 1920×1080），文本「资产库 生成历史 我保存的 我上传的 本项目 全部项目 图片 0 暂无历史记录 取消 确认选择」 | 同上 |

⇒ ⇒ **源站的「历史记录」与「AI生成」打开的是同一个资产库选择器**，
AI 那一行多一个「生成」入口。

---

## 3. ★★ 方法学：第四版探针说「没反应」是**漏读**，不是事实

★ 第四版探针（`source861_panorama_rows.py`）读「新出现的浮层」时，
用的是 **`z-index ≥ 30` 过滤** ⟹ ⟹ 源站那个对话框虽然**是全屏的**，
它的 z-index 没过线 ⟹ ⟹ **探针没读到** ⟹ ⟹ 我一度写下了
「历史记录／AI生成 在源站也点了没反应」的结论。

★ ★★ **第四版还报了一件更误导的事**：它读到的 `本地上传_浮层` 里**也没有任何新浮层**
⟹ ⟹ 差点连「本地上传会弹文件选择器」这条**真读数**一起丢掉。

⇒ ⇒ **第五版改用「点击前后的 DOM 差分」（按钮文本集合 ＋ 整页文本长度 ＋ 截图）**，
才拿到真相：两行**都**打开了对话框（按钮 86→95／86→98）。

⇒ ⇒ ★ **通式**：**「没读到」不等于「没发生」** ⟹ ⟹ 探针的**过滤器**本身
是一个待验证的部件 ⟹ ⟹ 当读数是「什么都没出现」时，
要先问「**我的过滤器会不会把它滤掉了**」，再下结论。

---

## 4. clone 整改（5 个源文件）

| 文件 | 改了什么 |
|---|---|
| `src/components/director/DirectorPanoramaPanel.tsx` | ★ 三行**接上 `onClick`**（按 `item.id` 显式三分支）；加**隐藏 file input**（`accept="image/*"`）＋ 点击即 `fileInputRef.current?.click()`（源站逐字 `et.current?.click()`）；选中文件后读尺寸并回调；面板底部加一行「当前全景图」（clone 自己的扩展） |
| `src/components/director/DirectorPanoramaPicker.tsx`（**新建**） | ★ 选择器对话框：标题条 ＋ 列表 ＋ 底部「取消」「确认选择」；AI 模式多「生成」「上传图片」 |
| `src/store/directorStore.ts` | ★ 新增 `localPanoramaAsset`（会话级 blob URL 资产）＋ `setLocalPanoramaAsset`（换资产时 revoke 旧 blob） |
| `src/lib/directorCanvasMediaIngress.ts` | ★ 新增 `mergeDirectorLocalPanoramaInput` ＋ `DirectorLocalPanoramaAsset` ＋ 前缀 `local-panorama:` |
| `src/components/director/DirectorDesk.tsx` | ★ 把本地资产**并进** `canvasMediaInputs`；给面板传 `panoramaInputs`／`currentPanoramaSourceId`／两个回调 |

★ ★★ **为什么要「并成同构的虚拟输入」**：
★ clone 的全景图来源是**画布图片节点的直接上游**（`sourceNodeId` ＝ 节点 id），
而**本地文件没有节点 id** ⟹ ⟹ 若另开一条「本地 URL」通路，
3D 层、检查器、选择器就要各写一遍 ⟹ ⟹
现在把本地图片包成**同一个结构**（`sourceNodeId` ＝ `local-panorama:<id>`、
`sourceKind` ＝ `"panorama"`、带 `imageUrl`）⟹ ⟹ **一条通路照常工作**，
不必新增渲染分支。

---

## 5. ★ clone 实测（改之后）

`raw/clone-861-panorama.json`（`probes/clone861_panorama.py`）：

| 读数 | 值 |
|---|---|
| 三行逐字文本 | `本地上传`／`历史记录`／`AI生成` ✔ |
| 隐藏 file input | `type="file"` ＋ `accept="image/*"` ✔ |
| 点「本地上传」 | **`filechooser` 事件 1 次**（与源站同款） ✔ |
| 点「历史记录」 | 选择器在场、`mode=history`、**无**「生成」按钮、有「取消」「确认选择」 ✔ |
| 点「AI生成」 | 选择器在场、`mode=ai`、**有**「生成」「上传图片」 ✔ |
| 点「取消」 | 选择器消失 ✔ |
| 喂一张真 PNG | store 里出现 `localPanoramaAsset`（`blob:` URL、8×8） ✔ |
| ★ 喂完之后 | **「当前全景图」从画布那张 `i-1FQ9tErTcC` 变成 `local-panorama:local-…`** ✔ |
| 选择器列表 | 4 张画布图片 ＋ **本地那张** ✔ |
| 诊断错误 | 无 ✔ |

★ ★★ 顺带发现并修掉的一个**体验缺口**：
★ clone 的**检查器默认不展开** ⟹ ⟹ 选完全景图**什么反馈都没有**（用户视角仍是「点了没反应」）
⟹ ⟹ 所以面板底部补了一行「当前全景图：<文件名>」
（★ **clone 自己的扩展**，源站面板里没有这一行；源站是**3D 场景**里变了所以用户看得见）。

---

## 6. 判据（`scripts/verify-liblib-batch861.py`，**29/29**）

| 段 | 内容 | 条数 |
|---|---|---|
| S1 | 源码契约（静态、**剥注释后**比、**精确定位到声明处**） | 9 |
| S2 | 源站实测产物必须存在 ＋ 复核源站的三个读数 | 5 |
| S3 | clone 实测（live DOM ＋ `filechooser` 事件） | 15 |
| | **合计** | **29** |

### 6.1 ★★ 判据写的过程中撞到的**两个真 bug**（都是**判据错、不是产品错**）

★ **第一个**：`strip_comments()` 用 `/\*.*?\*/` 剥块注释
⟹ ⟹ ★ **JSX 属性值里的 `image/*` 含 `/*`** ⟹ ⟹ 被当成**块注释起点**、
把后面整段删掉 ⟹ ⟹ `accept="image/*"` 被删成 `accept="image/` ⟹ ⟹ **假红**。
⇒ ⇒ 修法：**先把引号字符串换成占位符、再剥注释、再还原**。

★ **第二个**：静态判据用 `in` **全文匹配** ⟹ ⟹
同一个名字在**别处**出现时，变异测不出来 ⟹ ⟹ **假绿**（★ 阴性 N1／N4／N6 各撞一次）：
- `"local-upload"`：常量表 `panoramaItems` 里也有一份 ⟹ ⟹ 改坏 `onClick` 的分派仍绿；
- 「生成」二字：选择器的**提示文案**里也有一份 ⟹ ⟹ 删掉「生成」按钮仍绿；
- `localPanoramaAsset`：store 里有**声明＋初始值＋action** 好几处 ⟹ ⟹ 改声明仍绿。

⇒ ⇒ ★ **通式**：静态判据必须**定位到那一处声明/那一段代码**
（本批改成：匹配 `item.id === "…"` 的**分派语句**、
匹配 `data-director-panorama-*` 的**属性名**、
匹配 `localPanoramaAsset: DirectorLocalPanoramaAsset | null;` 的**完整声明行**）。

★ ★★ 顺带：这条判据还**逼出了源码的一个真弱点** ⟹ ⟹
第三行原本写的是裸 `else`（隐含「AI生成」）⟹ ⟹ 已改成**显式三分支**
（将来加第四行时不会误落到 `else`）。

---

## 7. 阴性对照（`probes/neg861.py` ⟹ `negative-audit.json`）

**8/8 条负控有效**，字节级复原自检 True。

| 变异 | 改坏什么 | 期望翻红的判据 |
|---|---|---|
| N1 | 三行的 `onClick` 分派失效 | `source:every-row-has-an-onclick` ＋ 三条 clone 行为判据 |
| N2 | 不触发隐藏 file input | `source:panel-clicks-the-file-input` ＋ `clone:local-upload-opens-a-file-chooser` |
| N3 | `accept` 改成 `video/*` | `source:panel-has-a-hidden-file-input` ＋ `clone:there-is-a-hidden-image-file-input` |
| N4 | 选择器里没有「生成」入口 | `source:the-picker-has-the-source-actions` ＋ `clone:the-ai-picker-adds-generate-and-upload` |
| N5 | ★ 选择器里偷偷加一个 `fetch`（真实生成） | `source:the-generate-button-makes-no-network-call` |
| N6 | store 里没有 `localPanoramaAsset` | `source:store-has-the-local-panorama-asset` |
| N7 | 虚拟输入的前缀写错 | `source:ingress-merges-the-local-input` |
| N8 | 「当前全景图」不写来源 | `clone:the-current-panorama-becomes-the-local-one` |

★ ★★ **N5 是本批的一条「底线门禁」**：clone **绝不**接真实全景图生成
（真实生图**会产生费用**）⟹ ⟹ 选择器源码里**不许出现任何网络调用**。
它同时是**将来**有人想偷偷接真生成时的**第一道闸**。

★ 纪律：每条变异先断言文件**真的被改了**（SHA-256）⟹ ⟹ 不会出现
「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」；变异**行数中性**；
每条变异后**字节级复原**；收尾再复核一遍全部文件 == 基线。

---

## 8. ★ 登记的差异（如实登记，不假装一致）

★ **D12（新建）· 选择器的形态不同**：
源站那个对话框是**资产库**（五个筛选标签：生成历史／我保存的／我上传的／本项目／全部项目；
实测该账号下内容是「图片 0 ／ 暂无历史记录」）；
clone 的是**当前可作全景图的图片输入**（画布图片 ＋ 本地上传的那张）。
⟹ ⟹ **界面形态不同、内容语义等价**（都是「挑一张已有图片当全景图」）。
★ 源站是**全屏**对话框，clone 是**居中 880px** 卡片。

★ **D13（新建）· 本地上传的落地方式不同**：
源站把文件**上传**，拿回 `panoramaUrl`；clone 用**会话级 blob URL**（**不上传任何东西**）
⟹ ⟹ 刷新页面即失效。★ 这是**有意的**（测试帐号、避免副作用）。

★ **D14（新建）· 「AI生成」的「生成」不接真实生成**：
clone 点「生成」只给一句明确说明（真实生图会产生费用）⟹ ⟹ **不假装能生成**。

★ **D15（新建）· clone 的面板多一行「当前全景图」**：
源站面板里没有这一行（源站是 3D 场景里变）⟹ ⟹ 这是 **clone 自己的扩展**。

★ **D16（新建）· 源站的 `disabled:!hasCameras` 未对齐**：
★ 源站逐字：`hasCameras: rL.cameras.length > 0` ＋ aspect 段 `disabled:!a`
（⟹ ⟹ **没有机位时，七档画幅比例全部禁用**）。
★ 运行时只取到「**有机位时**七格 `disabled:false`」这一半：
★ **源站的机位在本项目里删不掉**（机位行只有「隐藏」「锁定」两个按钮，
`Delete`／`Backspace` 都无效）⟹ ⟹ 「无机位」这个状态**在源站未能实测**
⟹ ⟹ clone 侧**本批未改**（登记待查）。

---

## 9. ★ 用户可达（用户硬要求：**从根可达 ＋ 写清怎么测**）

根地址：**`http://localhost:4317/`**（**无参数**）。

1. 打开 `http://localhost:4317/`；
2. 找到标题为「**第一集：咖啡馆对峙**」的那张**导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）；
3. **鼠标悬停**在它上面 ⟹ ⟹ 出现「**打开导演台 →**」按钮 ⟹ ⟹ 点它 ⟹ ⟹
   **导演台**盖在画布上（等约 **6.5 秒**）；
4. 点左栏 rail 的「**全景图**」（第 4 枚，`[data-director-rail-entry='panorama']`）
   ⟹ ⟹ 左侧面板出现三行；
5. ★ 点「**本地上传**」⟹ ⟹ **系统文件选择器弹出**（这就是源站同款的行为）
   ⟹ ⟹ 选一张图 ⟹ ⟹ 面板底部那行变成「**当前全景图：<你选的文件名>**」，
   3D 场景里那张图成了环境全景；
6. ★ 点「**历史记录**」⟹ ⟹ 弹出一个**选择器**（列着你画布上的图片 ＋ 刚才那张本地的）
   ⟹ ⟹ 点一张 ⟹ ⟹ 「**确认选择**」⟹ ⟹ 底部那行跟着变；
7. ★ 点「**AI生成**」⟹ ⟹ 弹出**同一个选择器**，但顶部**多**「生成」「上传图片」两枚
   ⟹ ⟹ 点「生成」会得到一句明确说明（**本原型不接真实生成，不产生任何费用**）。

★ 三个选择器就够自己写探针：
`[data-director-panorama-option]`（三行）、
`[data-director-panorama-picker]`（选择器）、
`[data-director-panorama-current]`（当前全景图那行）。

★ 想在 Console 里自己查：
```js
window.__director_store.getState().localPanoramaAsset
// ⟹ { id, filename, imageUrl: "blob:…", width, height }
```

---

## 10. ★ 复现步骤

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"

# ① 源站实测（★ 只读；点这三行**只打开界面**、不生成、不上传）
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/source861_aspect_disabled.py
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/source861_cam_entry.py
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/source861_no_camera.py
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/source861_panorama_rows.py
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/source861_panorama_diff.py

# ② clone 实测
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/clone861_panorama.py

# ③ 门禁（29/29）
python3 scripts/verify-liblib-batch861.py

# ④ 阴性（会**改源码**做变异 ⟹ ⟹ 跑完必须确认文件已复原）
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/neg861.py

# ⑤ 回归（既有门禁清单）
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/regress861.py

# ⑥ 受控对照（★ 会把源码换回 HEAD ⟹ ⟹ 跑完确认已复原）
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/attrib861.py
python3 docs/research/liblib-canvas-batch861-2026-10-01/probes/attrib861_mix.py
```

---

## 11. ★ 回归（`probes/regress861.py`）

**98 条，红 14 条 ⟹ 全部是已知旧账、零新红。**

★ 与 batch 860 的 **97 条 / 红 14 条**相比：**条数多 1**（多了本批自己的 861 门禁）
而 **红的集合逐条相同** ⟹ ⟹ **本批零新红**。

| 门禁 | 红因 | 性质 |
|---|---|---|
| 门禁 831 | S14／S15／S16／S17 | 旧账 |
| 门禁 835 | 判据 6/7 | 旧账 |
| 门禁 741 | 判据 11/13 | 旧账 |
| 门禁 91 | TransformControls 瞬态 | 旧账 |
| 门禁 736 | 判据 6/10 | 旧账 |
| 门禁 748 | 判据 4/7 | 旧账 |
| 门禁 749 | 判据 7/9 | 旧账 |
| 门禁 782 | 不通过 | 旧账 |
| 门禁 626 | **只剩** `live-controls-reachable/1280x720/crowd-dialog`（**D7**） | 旧账（源站同款） |
| 门禁 546／542 | fixture `/private/tmp/batch542-fixture/hero-character.fbx` 缺失 | 旧账 |
| 门禁 738 | 判据 8/9 | 旧账 |
| 门禁 656 | 2 条 | 旧账 |
| 门禁 648 | 2 条 | 旧账 |

★ 本批两道门禁在回归里全绿：
`861 → 29 判据，0 失败`／`860 → 59 判据，0 失败`。

---

## 12. ★ 受控对照与 MIX 半回退态

### 12.1 四态：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分

| 态 | 源码 | 新门禁 861 | 老门禁 | 结论 |
|---|---|---|---|---|
| HEAD-1 | 五个文件全换回 HEAD | rc=1，**19 条红** | 860 绿／859 绿／626 红 1（D7 旧账）／625／590／589 绿 | — |
| HEAD-2 | 同上（第二遍） | rc=1，**19 条红** | 同上 | ★ **两遍读数一致** ⟹ 稳定 |
| WORK-1 | 本批工作副本 | rc=0，**0 条红** | 同上 | — |
| WORK-2 | 同上（第二遍） | rc=0，**0 条红** | 同上 | ★ **两遍读数一致** |

★ `稳定=True`／`新门禁有牙=True`／`复原=True`（SHA-256 逐字节），
★ **各迁移门禁的失败集合差异为空**（`diffs: {}`）⟹ ⟹ **本批没有引入任何新问题**，
★ **HEAD 态零 CRASH**（19 条红**全是具名**）。

### 12.2 MIX 半回退态：只回退 `DirectorPanoramaPanel.tsx`

★ **只**把面板文件换回 HEAD（⟹ ⟹ 回到「三行没有 `onClick`」的老写法），
**保留** store / lib / picker / desk 的**新**代码
⟹ ⟹ 正好**隔离出「三行没接行为」这一条**。

| 门禁 | MIX 态读数 |
|---|---|
| 门禁 861 | rc=1，**15 条红**（两遍一致 ⟹ 稳定） |
| 门禁 860 | rc=0，0 红 |
| 门禁 590 | rc=0，0 红 |

★ 15 条红的**构成**（读原始输出原文，不按「我以为的落点」写）：
- **静态 3 条**：`source:every-row-has-an-onclick`／
  `source:panel-has-a-hidden-file-input`／`source:panel-clicks-the-file-input`
  （三条**全部指向面板**）；
- **运行时 12 条**：隐藏 file input 不在场／`filechooser` 次数 0／
  两种选择器都不在场／本地资产取不到／「当前全景图」读数为空／选择器不列本地那张。

★ ★★ **store / lib / picker / desk 那几条静态判据在 MIX 态是绿的**
（`store-has-the-local-panorama-asset`／`ingress-merges-the-local-input`／
`desk-wires-the-local-asset`／`the-picker-has-the-source-actions`／
`the-generate-button-makes-no-network-call`）
⟹ ⟹ 说明**隔离干净**：红的确实只是「面板没接行为」这一处。

★ ★★ **门禁里那条 `clone:the-local-file-becomes-a-local-asset` 出现两次**
（一条 `CRASH: TimeoutError: 面板没有那个 file input` ＋ 一条状态红条 `None`）
⟹ ⟹ 这是**提前修掉的假牙**：MIX 态下面板没有那个 file input，
`set_input_files` 会**超时抛错**、把整条门禁**崩掉**
⟹ ⟹ 改成「等不到就报一条**具名**红条并继续往下走」，
⟹ ⟹ 于是 MIX 态的红**条条具名、零 Traceback**。

⇒ ⇒ **MIX 态红得「不多不少」** ⟹ ⟹ 证明**判据层**有牙，
而不是「整个功能都没了所以一片红」。

---

## 13. ★ 遗留

★ 源站**截图／导出**的比例档位仍未取证（batch 860 遗留，本批未碰）。
★ 源站 aspect 七格的 `disabled:!hasCameras` 分支**未能实测**（D16）。
★ 源站的「历史记录」打开的是**资产库**（含「生成历史」等真实历史），
clone 的等价物是画布图片输入 ⟹ ⟹ 若要完全对齐，需接真实的资产库/历史接口（D12）。
★ 源站的「本地上传」走**上传**、clone 走 blob（D13）。
