# batch 865 —— 取景框结构改成源站同构（D25 结案）＋ 修 batch 864 的后遗症（开关挡住坐标控件）

> ★ **一句话**：本批把 clone 的取景框从「三层嵌套」改成源站逐字的
> 「**遮罩层／空框／三分线层／开关**四者平级」（D25 结案），
> 顺带整改了 batch 864 引入的一个**真缺陷**
> （那枚开关反过来盖住了 clone 自有的坐标控件两枚按钮）。

---

## 1. 靶子与结论（★ 先说结论）

| # | 靶子 | 结论 |
| --- | --- | --- |
| ① | **D25**（batch 864 登记：「源站取景框那三层是四者平级，clone 把三分线与开关塞进了框里」） | ★ **结案并已对齐** ⟹ ⟹ clone 改成源站逐字结构 ⟹ ⟹ ★ **视觉零差别**（像素对照 846,630 像素 **0 个不同**）⟹ ⟹ 这是**纯结构对齐**，**不是视觉改进** |
| ② | batch 864 把坐标控件降到 `z-10` 之后 ⟹ ⟹ 框上那枚开关（`z-20`）**反过来盖住**坐标控件的「X 反向」「Z 正向」 | ★ **真缺陷，已整改** ⟹ ⟹ 坐标控件挪到**视口左侧**（水平分离）⟹ ⟹ 六枚按钮**全部命中自己** |
| ③ | 源站的框**没写** `pointer-events` ⟹ ⟹ clone 写了 `pointer-events-none` ⟹ ⟹ 是偏差吗 | ★ **不是偏差（D26 结案）** ⟹ ⟹ `pointer-events` **可继承** ⟹ ⟹ 源站那个框**继承**了容器的 `pointer-events-none` ⟹ ⟹ 源站运行时实测框的 `pointerEvents` ＝ `"none"` ⟹ ⟹ 两者**完全等价** |
| ④ | 老门禁 `77`／`788` 的「旧前提」（它们**不在** batch 864 的回归清单里 ⟹ ⟹ 那些红从来没人看见） | ★ **已整改** ⟹ ⟹ `77` 写死的个数改成**结构性判据**；`788` 写死的行号改成**锚点式** ⟹ ⟹ 并**补进回归清单** |
| ⑤ | 本批自己踩的坑 | ★ 负控 N2 **打空**（`aria-hidden="true"` 全文 11 处 ⟹ ⟹ 静态判据是**假绿**的）⟹ ⟹ 已修；★ 负控会**污染门禁产物** ⟹ ⟹ 已加「还原后重跑门禁」 |

---

## 2. D25：源站的取景框是「四者平级」

### 2.1 源站逐字（已入库）

`raw/source-865-mp-verbatim.txt` —— chunk `0fmehki05gkzw.js.js` 的 `mP` 组件
（文件头记 chunk 路径／字符偏移／chunk 与摘录的**两个 sha256**）。

```jsx
<div ref={l} className:"pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10">
  {u && <>
    {/* ① 遮罩层 */}
    <div className:"absolute inset-0 bg-black/20 backdrop-blur-md" style={{…mask…}} />
    {/* ② 空框（★ 框里没有任何 children） */}
    <div className:"outline-white/18 absolute rounded-xl outline -outline-offset-1"
         style={{left:u.left,top:u.top,width:u.width,height:u.height}} />
    {/* ③ 三分线层（条件渲染，`aria-hidden`） */}
    {n ? <div className:"pointer-events-none absolute overflow-hidden rounded-xl"
             style={{left:u.left,top:u.top,width:u.width,height:u.height}}
             aria-hidden>
            <div className:"bg-(--color-white-alpha-50) absolute left-[33.333%] top-0 h-full w-px" />
            <div className:"bg-(--color-white-alpha-50) absolute left-[66.667%] top-0 h-full w-px" />
            <div className="bg-(--color-white-alpha-50) absolute left-0 top-[33.333%] h-px w-full" />
            <div className="bg-(--color-white-alpha-50) absolute left-0 top-[66.667%] h-px w-full" />
          </div> : null}
    {/* ④ 开关（条件渲染，容器坐标） */}
    {a ? <button type="button" title={…}
            className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 …`}
            style={{left:u.left+u.width-40, top:u.top+8}} onClick={a}>…</button> : null}
  </>}
</div>
```

★ **期望值全部只从这份逐字解析**（连 `33.333%` 都是用正则从源站类名里抽出来的）。

### 2.2 源站运行时取证（★ 比逐字更强：运行时不会骗人）

`raw/source-865-frame-structure.json` —— 探针 `probes/source865_frame_structure.py`
（带 cookie，点「选择画幅比例」→「16:9」→ 再点框上「构图参考线」）：

| 读数 | 值 |
| --- | --- |
| 遮罩容器的**直接子元素数** | **4** |
| **四者都直属容器** | **True** |
| 那个**框**的**子元素数** | **0**（★ 空框） |
| 那个**框**的 `pointerEvents` | **`"none"`** |

★ 源站逐字 ＋ 运行时读数**双重证实** D25。

### 2.3 clone 的实施（`src/components/director/DirectorViewport.tsx`）

改成与源站**逐字同构**：

1. **框变成空框**（自闭合，**零 children**）；
2. **三分线层**从框里**提出来**，成为框的**兄弟**；
   - 类名照抄源站：`pointer-events-none absolute overflow-hidden rounded-xl`；
   - 加 `aria-hidden="true"`（源站逐字 `"aria-hidden":!0`）；
   - 四条线改用 **inline 百分比** `33.333%`／`66.667%`
     （源站那些任意值类 `left-[33.333%]` 在 4317 的**冻结 Tailwind 扫描**下不生成）；
3. **开关**从框里**提出来**，成为框的**兄弟**，
   位置改用源站逐字的**容器坐标** `left: frameLeft + frameWidth - 40` / `top: frameTop + 8`
   （源站逐字是 `left: u.left + u.width - 40` / `top: u.top + 8`）。

---

## 3. D25 是「纯结构对齐」—— 像素对照为证

`probes/clone865_pixels.py`（产物 `raw/clone-865-pixels.json` ＋ 两张 PNG）：

- **同一页面 A/B**：把 3D canvas 隐藏 ＋ 铺纯色底（`FREEZE`），
  再用 DOM 手术把结构**还原成旧版**（`SURGERY`）⟹ ⟹ 两次截图**确定性可比**；
- **逐像素比对**：**846,630** 个像素 ⟹ ⟹ **不同像素 0 个**、**最大通道差 0**。

★ ⇒ **D25 是纯结构对齐，视觉无差别**。

★ ★ 顺带**推翻**了我自己先前的错推：
先前据「加了 `overflow-hidden rounded-xl` 之后线会溢出圆角」而担心视觉回归
—— **像素对照证明这个担心不成立**（那四条线在 `33.333%`／`66.667%` 处
⟹ ⟹ **永远碰不到四角** ⟹ ⟹ 圆角裁剪**对线没有可见影响**）。

---

## 4. D26：框的 `pointer-events` **不是**偏差

- 源站的框**没有**写 `pointer-events` ⟹ ⟹ 但 `pointer-events` **是可继承属性**
  ⟹ ⟹ 源站那个框**继承**了容器的 `pointer-events-none`
  ⟹ ⟹ **源站运行时实测框的 `pointerEvents` 就是 `"none"`**；
- clone **显式**写出 `pointer-events-none` ⟹ ⟹ 与源站**完全等价**。

★ ⇒ **不登记偏差**。门禁 `clone:the-frame-pierces-no-pointer-like-the-source`
把**clone 读数**与**源站运行时读数**并排断言。

★ ★ **为什么当初会以为照抄源站会出事**：
源站视口是 **1920** 宽 ⟹ ⟹ 框右沿与右上角控件**不重叠**；
clone 视口只有 **1358** 宽 ⟹ ⟹ 框右沿 1574 与坐标控件 1539–1619 **重叠 35px**
⟹ ⟹ 若照抄成 `pointer-events:auto` ⟹ ⟹ **clone 自有的**坐标控件会被框吞掉
⟹ ⟹ 那是**用源站的写法换一个 clone 独有的功能损坏** ⟹ ⟹ 保留 `none`。
★ 但**根本解**是本批第 5 节：**把坐标控件挪开** ⟹ ⟹ 于是连这个隐患也一并消失。

---

## 5. 整改 batch 864 的后遗症：开关挡住了坐标控件

### 5.1 症状与根因

batch 864 把 clone 自有坐标控件容器从 `z-20` 降到 `z-10`（为了不让它盖住框上那枚开关）
⟹ ⟹ **反过来**让那枚 `z-20` 的开关盖住了坐标控件的
「X 反向」@(1557,142) 与「Z 正向」@(1560,155) **两枚按钮**
⟹ ⟹ 它们**点不到**。

★ ★ 864 门禁只测了「**开关能不能点**」⟹ ⟹ **没测「它挡了谁」** ⟹ ⟹ 漏掉了。

### 5.2 为什么不能只靠 z 序

竖直方向**不可能**稳：开关的 x **固定**（框右沿 − 40）、y **随画幅比例动**
⟹ ⟹ 任何一档比例下都会跟视口右上角那块区域**竖直相交**。

### 5.3 修法：水平分离（把坐标控件挪到视口左侧）

- clone 自有的坐标控件容器：`className="absolute left-3 z-10 h-20 w-20"`
  ＋ `style={{ top: 56 }}`（原来是 `right-5 top-5`）；
- ★ **可挪的依据**：★ 源站 chunk 里 15 处「Gizmo」**全是 three.js `TransformControls`**
  ⟹ ⟹ **源站的 3D 视口根本没有这枚六轴坐标控件**
  ⟹ ⟹ 它是 **clone 自有扩展**（batch 49）⟹ ⟹ **位置没有源站约束**。

★ 结果：六枚按钮**全部命中自己**（门禁 `clone:every-gizmo-button-is-hittable-while-the-frame-exists`）。

---

## 6. 验收

| 项 | 结果 |
| --- | --- |
| 门禁 `scripts/verify-liblib-batch865.py` | ★ **22 判据、0 失败** |
| 复验 `scripts/verify-liblib-batch862.py` | ★ **58 判据、0 失败** |
| 复验 `scripts/verify-liblib-batch863.py` | ★ **113 判据、0 失败** |
| 像素对照 `probes/clone865_pixels.py` | ★ **846,630** 像素 ⟹ ⟹ **0 个不同**、最大通道差 **0** |
| 阴性对照 `probes/neg865.py` | ★ **7/7**（每条行数中性 ＋ 变异已落地 ＋ **具名**命中预期判据 ＋ 字节级还原） |
| 回归 `probes/regress865.py` | ★ 见 `raw/regression.json` |
| 受控对照 `probes/attrib865.py` | ★ 见 `controlled-comparison.json` |

### 6.1 门禁的判据构成（`verify-liblib-batch865.py`）

- **S1 静态**：期望值**只从入库的源站逐字解析**
  ⟹ ⟹ 缺证据文件 ⟹ ⟹ **直接判失败**（不崩、不放行）；
- **S2 运行时结构读数**：四者的**父子关系**与**顺序**、框是**空框**、
  三分线层的**裁剪／圆角／aria**、四条线的**相对位置百分比**、
  开关的**容器坐标**；
- **S3 偏差取证**：D26（框的 `pointer-events` 与源站运行时读数并排断言）、
  以及「坐标控件的每一枚按钮都命中自己」。

---

## 7. ★ 本批自己踩的坑（都已写成纪律）

### 7.1 ★★★★ 「同名在别处出现」⟹ ⟹ 静态判据假绿

阴性对照 **N2**（把三分线层的 `aria-hidden` 改成 `false`）**打空了**：
rc=0、**零红灯**。两个叠加的原因：

1. **负控锚点不唯一** ⟹ ⟹ `aria-hidden="true"` 在 `DirectorViewport.tsx` 里出现
   **11 处** ⟹ ⟹ `replace(…, 1)` 改到了**第 2570 行别处**那一处
   ⟹ ⟹ 三分线层**根本没被改**；
2. ★★ **门禁静态判据本身无效** ⟹ ⟹ 那条判据写的是
   `'aria-hidden="true"' in view_code` ⟹ ⟹ 其余 **10 处**还在 ⟹ ⟹ 照样绿。

★ ⇒ **两条都要修**（只修一条仍然是假绿）：

- **负控侧**：锚点扩到**唯一**（带上三分线层那一行的注释上下文）；
- **门禁侧**：★ 新增 `thirds_start_tag()` ⟹ ⟹ 判据**只读三分线层自己的开始标签**，
  并加一条 **`data-director-thirds` 锚点唯一性**判据
  （若它出现多次 ⟹ ⟹ 锚到的就未必是「那一个」⟹ ⟹ 先判红）。

★ ⇒ **通式：静态判据不能是「全文 contains」** ⟹ ⟹ 必须**锚到被断言的那一处**；
⟹ ⟹ 顺带：★ **同名在别处出现**这件事本身就该有判据（唯一性）。

### 7.2 ★★★ 负控会污染门禁产物

负控跑完 N7（把坐标控件挪回右上角）之后 ⟹ ⟹ 磁盘上的源码**已经还原**，
但 `runtime-audit.json` 里留下的是**变异态**的读数
（「坐标控件命中」写着「全命中 = False」）⟹ ⟹ **产物与源码对不上**
⟹ ⟹ 若直接提交 ⟹ ⟹ 提交的产物是**红的**、而门禁本身是**绿的** ⟹ ⟹ 自相矛盾。

★ ⇒ 修法：**还原之后重跑一遍门禁** ⟹ ⟹ 让产物回到基准态。
（`neg865.py` 末尾已加这一步。）

### 7.3 ★★★ 回归清单里漏掉的老门禁

本批把 `77` 与 `788` 补进回归清单 ⟹ ⟹ **当场发现它们早就红了**
（它们的「旧前提」过期很久了：写死的个数、写死的行号）
⟹ ⟹ ★ **因为不在清单里，那些红从来没人看见**。

★ ⇒ 两条门禁的旧前提都已整改：

- `77`：`count("object={transformTarget}") == 3` ⟹ ⟹ 改成**结构性判据**
  （剥注释后 `<TransformControls>` 数 == `object={transformTarget}` 数）；
  它的 4 处 `assert errors == []` ⟹ ⟹ 改成**窄口径**噪声过滤
  （只放行「TransformControls: … must be a part of the scene graph」）；
- `788`：写死行号 ⟹ ⟹ 改成**锚点式**（按内容唯一命中）。

★ ⇒ **通式：回归清单本身就是一份「旧前提普查表」** ⟹ ⟹
扩大清单后新出现的红**必须定点对照归因**（这次的红在扩之前就已经红了）。

### 7.4 ★★ 一次差点造成假因果的对照

MIX 态的变异最初设计成「把三分线层整块搬进框里」⟹ ⟹ 那会**改行数**
⟹ ⟹ 改成**两处各改一行**（框的 `/>` → `>`；三分线层末尾 `) : null}` → `) : null}</div>`）
⟹ ⟹ **行数中性**、位置偏移不变。
★ 且**闭合锚点必须唯一**：★ `        </div>\n      ) : null}` 全文出现 **3 处**
⟹ ⟹ 扩到「三分线层最后一条线」那段上下文才唯一命中。

---

## 8. 差异登记

| 编号 | 内容 |
| --- | --- |
| **D25** | ★ **结案**：源站取景框「四者平级」⟹ ⟹ clone 已改成同构 ⟹ ⟹ 视觉无差别（像素对照为证） |
| **D26** | ★ **核实为非差距**：框的 `pointer-events` ⟹ ⟹ 源站**继承**得到 `"none"` ⟹ ⟹ clone 显式写出 **完全等价** |
| **D18** | （batch 864 结案，本批未动）取景框的**像素几何**差异是**布局级** ⟹ ⟹ 源站视口 1920 vs clone 1358 ⟹ ⟹ 绝对像素**不可比** ⟹ ⟹ 不改 |

★ 本批**没有新登记**差异。

---

## 9. ★ 用户可达（怎么自己验）

> ★ **根地址**：**`http://localhost:4317/`**
> （★ 用 `localhost` 而**不是** `127.0.0.1` —— 后者在 dev 模式下**不 hydration**，
> 页面看着正常但**点不动**；见 batch 827 的教训。）

| 步骤 | 做什么 | 期望 |
| --- | --- | --- |
| ① | 打开根地址 ⟹ ⟹ hover「导演台」卡片 | 卡片浮起 |
| ② | 点「打开导演台 →」 | 导演台打开 |
| ③ | 点左侧 rail 的「选择画幅比例」⟹ ⟹ 点「16:9」 | ★ **取景框出现**（框外压暗 ＋ 化开，框内被 mask 挖空） |
| ④ | 点**取景框右上角**那枚 32×32 的圆钮（`[data-director-frame-thirds-toggle]`） | ★ **分线 0 → 4 条**（三等分线） |
| ⑤ | ★ **重点验本批的结构**：DevTools 控制台跑 | 见下 |

★ **验「四者平级」（本批的核心）**：

```js
// 在 DevTools 控制台跑这一段 ⟹ ⟹ 期望打印 ["遮罩层","空框","三分线层","开关"]
(() => {
  const c = document.querySelector('[data-director-aspect-mask-container]');
  const mark = el => el.hasAttribute('data-director-aspect-mask') ? '遮罩层'
    : el.hasAttribute('data-director-aspect-frame') ? '空框'
    : el.hasAttribute('data-director-thirds') ? '三分线层'
    : el.hasAttribute('data-director-frame-thirds-toggle') ? '开关' : '其他';
  return [...c.children].map(mark);
})()
```

★ **验「框是空框」**：

```js
document.querySelector('[data-director-aspect-frame]').childElementCount   // ⇒ 0
```

★ **验「本批整改的后遗症」（坐标控件不再被挡）**：

```js
// 期望：6 枚按钮，每一枚 elementFromPoint 都命中自己
[...document.querySelectorAll('[data-director-viewport-gizmo-button]')].map(b => {
  const r = b.getBoundingClientRect();
  const top = document.elementFromPoint(Math.round(r.x + r.width/2), Math.round(r.y + r.height/2));
  return [b.getAttribute('aria-label'), top?.closest('[data-director-viewport-gizmo-button]') === b];
})
```

★ **选择器清单**：`[data-director-aspect-mask-container]`／`[data-director-aspect-mask]`／
`[data-director-aspect-frame]`／`[data-director-thirds]`／`[data-director-frame-thirds-toggle]`／
`[data-director-aspect-option]`／`[data-director-viewport-gizmo]`／`[data-director-viewport-gizmo-button]`。

★ **本批改动对用户的可见影响**：**几乎没有** —— ★ 结构变了，**像素没变**
（846,630 像素 0 差异）⟹ ⟹ 用户能感觉到的只有一件事：
★ **框右上角那枚开关不再挡住视口左侧的坐标控件**（batch 864 之后坐标控件还在右上角，
现在挪到了**左上角偏下**的位置 ⟹ ⟹ 那里**空着**，不挡任何东西）。

---

## 10. 产物索引

| 路径 | 内容 |
| --- | --- |
| `raw/source-865-mp-verbatim.txt` | ★ **源站逐字**（chunk 路径／偏移／两个 sha256） |
| `raw/source-865-frame-structure.json` | ★ **源站运行时**：四者平级、框子元素数 0、框 `pointerEvents="none"` |
| `raw/clone-865-pixels.json` ＋ `raw/clone-865-pixels-{old,new}.png` | ★ **像素对照**：846,630 像素、0 差异、最大通道差 0 |
| `raw/negative-audit.json` | ★ **阴性对照** 7/7 |
| `raw/regression.json` | ★ **回归**结果 |
| `runtime-audit.json` | ★ 门禁产物（22 判据、0 失败） |
| `controlled-comparison.json` | ★ **受控对照**五态 |
| `probes/source865_frame_structure.py` | 源站运行时探针 |
| `probes/clone865_pixels.py` | 像素对照探针 |
| `probes/neg865.py` | 阴性对照（7 条变异） |
| `probes/regress865.py` | 回归清单（**111 条**） |
| `probes/attrib865.py` | 受控对照（HEAD／MIX／WORK 五态） |
