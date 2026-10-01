# Batch 350 — 裁剪表单静默丢弃用户输入；以及 batch333「偶发失败」的真因（门禁缺陷）

日期：2026-10-01
范围：`src/components/frameos/FrameosNodeFloatingToolbar.tsx`（缺陷修复）
性质：**CLONE_DECISION**（克隆侧；源站人机验证仍被拦，裁剪的**提交语义**未采样）

---

## 缺陷一：裁剪是一条「接受输入并静默丢弃」的表单

### 现象

`FrameosNodeFloatingToolbar` 的裁剪态（Batch 279 源站采样的 UI 外观）里：

- `裁剪宽度` / `裁剪高度` 是 `<input defaultValue={480}>` 的**非受控**输入，
  全仓没有任何代码**读过**它们；那个 480 与节点实际尺寸也毫无关系；
- 「✓ 确认裁剪」只做 `window.alert("已确认裁剪 (mock)")` + 退出裁剪态；
- 裁剪框（参考线 + 8 手柄）**恒等于节点当前矩形**，8 个手柄全是
  `pointerEvents: "none"` —— 框根本拖不动、改不大。

结果：用户认真填的数字被整个丢弃，**节点一点没变**，而 UI 弹了确认。

> 这比普通 mock 更坏：mock 是「本来就没做」，而这里是**收了输入、给了确认、
> 然后把输入扔掉**。用户无法从界面上分辨自己填的数字到底有没有生效。

### 修复（不新增 store API，不发明裁剪语义）

1. 宽高改**受控**，进入裁剪态时用**节点当前尺寸**初始化（而不是写死的 480）；
2. 裁剪框跟随输入尺寸，锚在节点左上角（与「裁剪到 W×H」的直觉一致）；
3. 「确认裁剪」复用节点拖拽手柄用的**同一对** action：
   `beginResize`（入历史快照） + `resizeNode`（落尺寸）—— 不新增 store API，
   不发明裁剪语义，且**自动可撤销**，与全 app 其它结构变更的历史语义一致；
4. 最小值夹取沿用拖拽手柄的同一对下限 `200 × 120`；
5. 解析不出数字就**不落也不谎报成功**；
6. 屏幕坐标 ↔ 流坐标显式换算：`nodeRect` 是屏幕坐标，宽高是流坐标 ——
   与 Batch 342「屏幕坐标喂给要流坐标的函数」同源的陷阱。

### 实测

```
选中后      w=300 h=169 past=0
确认裁剪后  w=420 h=260 past=1   ← 裁剪真的落上了
Meta+Z 之后 w=300 h=169 past=0   ← 撤销精确还原
```

## 验证

`scripts/verify-frameos-batch350.py` —— **14 项检查，0 诊断**。

两处变异都确认验证器会红，且**报错数字就是缺陷原文**：

| 变异 | 验证器输出 | 对应缺陷原貌 |
|---|---|---|
| 移除 `resizeNode` 落尺寸 | `confirm:applies-size style=(300,169) expect=(420,260)` | 节点纹丝不动 |
| 宽高退回 `defaultValue={480}` | `input:initialized-from-node input=(480,480) style=(300,169)` | 输入框数字与实际无关 |

---

## 探针自身的坑（第五次「先看失败在哪一步」救下误改）

`undo:restores-size` 首次报 `style=(None,None)`，看起来像「撤销把节点删了」。

实测才发现撤销**精确还原了** 300×169，只是 `selectedNodeId` 变成了 `null` ——
而 `undo()` 里就明确写着 `selectedNodeId: null, selectedGroupId: null`
（快照恢复丢掉选中，是**有意的显式设计**，不是缺陷）。

探针原先按 `selectedNodeId` 取节点，撤销后就读不到了。改为**按 node id 读**
（稳定身份），并补一条 `undo:node-still-present` 把「还原尺寸」和「节点还在」
拆成两个断言。

> 本会话累计五次因「先看失败在哪一步」而避免误改应用代码：
> 346 探针坐标失效 / 348 探针复用已有节点 / Playwright `position` 笔误 /
> 349 监听器重复注册造出假缺陷 / 350 按选中态取节点。

---

## 顺带查清：batch333「反复偶发失败」的真因是**门禁缺陷**

### 现象

`verify-frameos-batch333.py` 的 `diagnostics:zero` 连续三轮在全量套件里失败、
重试也失败；但**隔离跑 5+ 次全过、6 路并发下 3 次全过、重编译扰动下 3 次全过**。

### 抓到的证据

前两次抓诊断都失败：runner 对失败输出做 `tail -5`，把诊断那行截掉了。
改成**写文件**（`/tmp/b333-diag.jsonl`）才抓到原文：

```
requestfailed:GET:.../_next/static/chunks/%5Bturbopack%5D_browser_dev_hmr-client_....js:net::ERR_ABORTED
requestfailed:GET:.../_next/static/chunks/Documents_wubuku_liblib-tv_src_....js:net::ERR_ABORTED
requestfailed:GET:http://localhost:4317/images/frameos/node-vid-cover-2.jpg:net::ERR_ABORTED
requestfailed:GET:http://localhost:4317/images/frameos/node-image-1.png:net::ERR_ABORTED
```

**全是 `net::ERR_ABORTED`** —— 浏览器**主动取消**的请求，不是服务器或应用失败。
两类来源：

1. **Turbopack HMR chunk**：别的 session 改源文件触发重编译，旧 hash 的 chunk 失效，
   飞行中的请求被中止；
2. **`/images/frameos/*.jpg|png`**：batch333 密集 `page.reload()`
   （它专门测跨刷新持久化），飞行中的图片请求随导航被取消。

`attach_errors` 把浏览器的 `requestfailed` 一律当成应用错误记下，
于是 `diagnostics:zero` 在长跑/并发下必然误报。

### 结论

**batch333 本身没有功能回归**（隔离/并发/扰动下共 11 次全过），
问题在门禁：**它分不清「应用抛错了」和「HMR chunk 被取消了」**。
这会持续误报，还可能把真实错误淹没在噪音里 —— 门禁必须零误报，所以要修。

> 修法与验证留待 Batch 351（改共享的 `attach_errors` 影响 86 个验证器，
> 需要配套的「门禁没被削弱」反向测试，故单独成批）。

---

## 保真度差距

- 裁剪的**提交语义**（源站裁剪是裁图像像素，本克隆落成节点尺寸）源站未采样，
  属 CLONE_DECISION，不冒充源站对齐声明。
- 裁剪框仍**不可拖拽**（8 手柄是 `pointerEvents: none`，沿用 Batch 279 的采样外观），
  本批只让「输入 → 尺寸」这条链真正生效，未发明拖拽交互。

## 源站阻塞

`frameos.cn` 人机验证仍不可通过（用户手动点击亦失败），本批全部结论均为
克隆侧运行时证据，无一条源站采样。
