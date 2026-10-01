# 回走审计

> 本文件记录两件事：**已经做过什么验证**，以及**还欠着什么**。
> 按 SKILL §7 的两道交付闸门组织；Gate B（真实浏览器回走）在本轮尚未完整执行，
> 因此任务状态里凡标 ⚠️ 的都留在下面的「待回走清单」里，没有伪装成 verified。

## 证据分级

| 级别 | 含义 |
|---|---|
| `RUNTIME` | 在真实运行界面点过，DOM / 网络 / 截图三者对得上 |
| `RUNTIME-READONLY` | 只读了界面结构与文案，没有触发有副作用的动作 |
| `PANEL-CLAIM` | 键位、参数这类**面板自称**的内容，未逐条实按/实跑 |
| `INFERRED` | 按界面措辞推断，正文已标 📖 |

---

## Gate A：覆盖率与机械完整性

### 任务覆盖

| 任务 | 页面 | 状态 |
|---|---|---|
| create-project | 00-quickstart / enter-canvas | ✅ RUNTIME |
| manage-canvases | manage-canvases | ✅ RUNTIME（含 POST /api/canvas/project/update） |
| navigate-canvas | organize-canvas / 20-reference | ✅ RUNTIME |
| organize-canvas | organize-canvas | ✅ RUNTIME |
| storyboard-mode | storyboard-mode | ✅ RUNTIME |
| share-canvas | share-canvas | ⚠️ RUNTIME-READONLY（未点发布） |
| create-nodes | create-nodes | ✅ RUNTIME（九类全部建出） |
| connect-nodes | connect-nodes | ✅ RUNTIME（edgeCount=1 多次确认） |
| select-and-edit-nodes | create-nodes / shortcuts | ⚠️ PANEL-CLAIM（成组/解组/复制未实跑） |
| generate-media | generate-media | ⚠️ RUNTIME-READONLY（未提交） |
| asset-library | asset-library | ✅ RUNTIME-READONLY |
| character-studio | character-studio | ✅ RUNTIME-READONLY |
| assets-page | 20-reference | ✅ RUNTIME-READONLY |
| agent-director | agent-director | ⚠️ RUNTIME-READONLY（未提交任务） |
| shortcuts | shortcuts / 20-reference | ⚠️ PANEL-CLAIM（部分实按） |

### 本轮否证过的说法

这些是取证过程中被实测推翻的，保留下来免得下一位重犯：

| 曾经的判断 | 实测结论 |
|---|---|
| 底部「教程」按钮打开教程中心 | 实现是 `data-sidebar-btn="contact"`，点击无面板/无跳转/无新窗口 |
| 选中节点按 `Delete` 就能删 | 不生效；必须先点空白让焦点回画布，再 `⌘A` + `⌫` |
| 「复制画布」会把副本插到列表最前 | 插在**源画布正下方**，与「新建画布」规则不同 |
| 快捷键面板是「成组 G / 合并 ⌥G」（无 ⌘） | 面板上有 ⌘ 前缀，是**图形键帽没有文本**；只读 innerText 会整列丢失 |
| `⌘0` 是「重置缩放」 | 它是「适合屏幕」，节点少时会放大到 100% 以上 |
| 从「+」建节点可以自己选位置 | 一律落在同一锚点；要定位得用**双击画布**（面板锚在双击点） |
| 「项目」和「画布」是同一个东西 | 两层；且**一张画布 = 一个 projectId**，切换画布 URL 会变 |

### 已知误读风险（留给 Gate B）

| 风险 | 说明 |
|---|---|
| 下拉列表动画期读数 | 打开画布下拉后立刻读行列表，会读到**过渡中的瞬态**（曾把 2 行读成 1 行，误判成「画布被删了」）。必须等读数连续两次一致 |
| 清理画布不可靠 | 焦点在节点输入框里时 `⌘A` 选的是文字，连点四次都没清干净；一度让截图堆着上一轮残留节点 |
| `hasText` 子串误匹配 | `filter({hasText:'视频节点'})` 会命中「请连接**视频节点**后操作」的智能剪辑节点。必须按标题前缀精确匹配 |
| `input[type="text"]` 选不中 | React 只设了 `type` **属性**没设 attribute，得用 `aria-label="画布名称"` |

---

## Gate B：真实浏览器回走 —— 本轮执行情况

**状态：部分执行。** 已按手册复现并确认的：

- 从项目页「新建项目」进入画布（无对话框）；
- 添加节点面板九项逐项打开；
- 文本 / 图片 / 视频三类节点建出并展开；
- 图片节点输出 → 视频节点输入连线成立；
- 画布下拉：新建、重命名（回车提交，`POST /api/canvas/project/update`）、复制（命名 `副本1`、自动切换）、删除（二次确认、活动画布回落）；
- 缩放菜单六项；
- 工作流 / 故事板切换；
- 整理画布 `⌥⇧F` 触发「是否保留此次整理结果？」；
- 快捷键面板四列逐列读数。

**未回走的项目**（见下表）。

---

## 待回走清单

| # | 项目 | 页面 | 级别 | 阻塞原因 |
|---|---|---|---|---|
| 1 | 逐条实按快捷键（成组/解组/连线/复制/新建节点/节点搜索/Space/V/H） | shortcuts | PANEL-CLAIM | 多数需要先框选多节点，框选入口本轮未取得可靠读数 |
| 2 | 真正提交一次生成，取耗时/进度/产物落位 | generate-media | — | **会扣积分**，需用户单独授权 |
| 3 | TV Director 发一条指令，观察它改了什么 | agent-director | — | 会动画布且可能触发生成 |
| 4 | 发布与分享的实际效果与撤回路径 | share-canvas | — | **对外不可逆**，需用户单独授权 |
| 5 | 导演台三维工作区内部 | create-nodes | — | 本轮只建了节点卡，列为下一批首要任务 |
| 6 | 角色创建流程 | character-studio | — | 会写入账户数据 |
| 7 | 上传素材的格式与体积上限 | asset-library | — | 会写入账户数据 |
| 8 | 框选（空白 Shift 拖拽）与成组 | create-nodes | — | 与 #1 同源 |

> 清单 #2 #3 #4 需要**用户单独许可**才能执行 —— 它们分别触及费用、外部可见性、账户写入。
> 在拿到许可前，手册对应页面一律保持 `partial`，不做任何「已验证」的表述。

---

## 严重性分级

本轮**没有 Blocker，也没有 Major**。

发现的两处「名不副实」定为 **Minor**，且都已在正文如实写明，不影响操作正确性：

| 级别 | 发现 | 处理 |
|---|---|---|
| Minor | 底部 `教程` 按钮实为联系入口 | 正文 shortcuts.md / troubleshooting.md 明确写出 |
| Minor | 底部 `教程` 之外，画布内**没有教程中心入口** | 已在 troubleshooting 里作为结论写明 |

---

## 机械审计

见 `PROGRESS.md` 的提交记录。Gate A 机械审计命令：

```bash
python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py docs/user-manual/libtv-canvas --phase gate-a
```
