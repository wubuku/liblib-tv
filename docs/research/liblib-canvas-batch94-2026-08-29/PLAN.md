# Batch 94 计划：Director 焦点与键盘边界

> 状态：`IMPLEMENTED` / `FOCUSED_RUNTIME_RECORDED_PASS`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`29f14b8`（Batch 93 最终回归）。

## 1. 背景与目标

Batch 93 已确认 Director 桌面/移动端的可见 shell、R3F 工作区、对象树、
Inspector、Timeline、抽屉和关闭/重开流程在当前 clone 上没有发现结构性回归。
但既有成熟度审计仍将 focus trap、focus return 和 target-scoped keyboard
ownership 列为未闭环的 UI/UX 缺口。

本批目标是让 Director 作为前景工作区具备完整、可复现的焦点边界：

1. 打开时保存调用入口并把焦点送入工作区；
2. `Tab` / `Shift+Tab` 只在当前 Director 对话框内循环；
3. 关闭时将焦点返回原调用入口，调用入口已不存在时回退到安全工作区；
4. 移动端打开的对象树/Inspector 抽屉获得局部焦点边界，关闭后返回对应触发按钮；
5. 不可见或折叠的抽屉不进入键盘遍历；
6. 现有 Escape 优先级、输入框编辑、导出/截图/项目 IO 和 Director 命令快捷键
   行为保持不变。

## 2. 证据分层

| 标签 | 本批使用方式 |
|---|---|
| `CLONE_FACT` | 当前 `DirectorDesk` 已有 `role=dialog`、`aria-modal=true`、工作区初始 focus；没有 Tab containment/focus return，移动抽屉主要靠 transform 隐藏 |
| `SOURCE_FACT` | 当前已认证 LibTV Director 的 DOM/CSS/runtime 证据不足；本批不新增 source-exact 结论 |
| `STORYAI_FACT` | 上游仅作为 authoring-workspace 结构和交互边界的借鉴背景，不把其具体焦点实现升级为 LibTV 事实 |
| `DECISION` | 将焦点 containment、回焦和 inert 隐藏抽屉作为 clone-owned accessibility/UI reliability 合同实现 |

## 3. 范围排序

| 优先级 | Slice | 交付 | 停止条件 |
|---|---|---|---|
| P0 | Director dialog trap | 可计算 tabbable 集合、首尾循环、DOM 动态变化可处理 | fresh desktop 场景 `Tab` 和 `Shift+Tab` 不离开 Director |
| P0 | Close focus return | 记录入口、关闭后回焦、入口删除时安全回退 | close button / Escape / mobile close 均不把焦点丢到 document body |
| P1 | Mobile drawer containment | 抽屉打开时局部 trap，关闭按钮和第一控件可达 | tree/Inspector 关闭态不出现在 tabbable 集合，打开后局部循环 |
| P1 | Keyboard ownership regression | 输入框不触发命令快捷键；Escape 仍按 overlay、drawer、workspace 顺序处理 | Batch 50/62/75 与本批专项均通过 |
| P1 | Documentation and gate | spec、runtime audit、ledger、manifest、Harness 可发现 | docs check、quality gate、current regression 通过 |

## 4. 交互合同

### 4.1 Director 对话框

- 工作区是唯一顶层 `role=dialog`；打开后焦点进入工作区内第一个可操作控件。
- `Tab` 在工作区当前可见、未禁用的 tabbable 元素之间循环。
- `Shift+Tab` 反向循环。
- 当动态面板打开或关闭时，下一次 Tab 使用最新集合，不使用过期快照。
- `aria-modal=true` 只作为语义声明；实际 containment 由键盘处理实现。

### 4.2 移动端抽屉

- 对象树和 Inspector 仍是同一个 Director 工作区的局部 surface，不增加第二个
  顶层 dialog。
- 未打开的抽屉设置 `inert`，并提供对应 `aria-hidden`；CSS transform 不能单独
  代表“不可聚焦”。
- 打开抽屉后焦点进入抽屉的关闭按钮或第一个可操作元素。
- 点击遮罩、Escape 或抽屉关闭按钮后，焦点返回原触发按钮。

### 4.3 关闭与异常回退

- 正常 close、Escape close、返回画布按钮都使用同一条回焦路径。
- 如果入口已被卸载、不可见或不可聚焦，尝试把焦点放回 document 中仍存在的
  LibTV canvas focus root；再失败则聚焦 Director workspace 的安全节点。
- 忙碌状态下现有 close guard 保持不变。

## 5. 稳定选择器与运行时证据

本批新增或使用以下 clone-owned selectors：

| Selector | 用途 |
|---|---|
| `[data-director-focus-scope="workspace"]` | 顶层 Director focus scope |
| `[data-director-focus-scope="tree"]` | 移动对象树局部 scope |
| `[data-director-focus-scope="inspector"]` | 移动 Inspector 局部 scope |
| `[data-director-focus-return]` | 记录/诊断回焦目标 |
| `[data-director-focus-state]` | 当前 focus scope 状态 |
| `[data-director-focus-scope]` descendants | 专项 verifier 计算 tabbable 集合 |

不生成截图。本批只记录 DOM、`activeElement`、`inert`、ARIA、viewport、console/
page/request diagnostics；无需截图识别。

## 6. 专项 verifier 设计

新增 `scripts/verify-liblib-batch94.py`，使用 fresh BrowserContext，覆盖：

1. 打开 Director 后焦点在 workspace 内；
2. 连续 `Tab` 及 `Shift+Tab` 循环不离开 workspace；
3. 打开 mobile tree/Inspector 后焦点进入对应 scope，关闭态抽屉不含 tabbable；
4. drawer `Escape` / backdrop close 返回原触发按钮；
5. workspace close button、Escape close 返回 `[data-open-director]`；
6. 删除或失效的入口触发安全回退，不抛 page/console/request error；
7. editable input 中的字符输入、`Tab`、Escape 不触发 Director command shortcut；
8. desktop `1440x900`、mobile `390x844` 均无横向溢出。

## 7. 回归与文档交付

实施后按顺序运行：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch94.py

python3 scripts/verify-liblib-batch50.py
python3 scripts/verify-liblib-batch62.py
python3 scripts/verify-liblib-batch75.py

npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

更新：

- 本批 `README.md`、`IMPLEMENTATION.md`、`runtime-audit.json`；
- `docs/research/VERIFICATION_LEDGER.md`；
- `docs/research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`；
- `docs/HARNESS.md`；
- `docs/research/README.md`；
- 必要时更新 `docs/BIG_PICTURE.md` 或 `docs/AGENT_TASK_MAP.md`。

## 8. 不在本批范围

- 不声称 LibTV 原站已采用本批具体 focus trap DOM/CSS；
- 不改变 Director project/schema/history/resource 合同；
- 不新增 Three.js 场景能力、panorama 或多机位产品语义；
- 不重写普通画布的全局焦点系统；
- 不生成或重新识别截图。

## 9. 完成条件

1. 专项 focus verifier 通过，桌面/移动端 diagnostics 为 `0/0/0`；
2. Batch 50、62、75 相关键盘/焦点回归通过；
3. `npm run check`、文档检查和 diff 检查通过；
4. 实施结果和证据边界落档，稳定索引可发现；
5. commit/push 后 `master == origin/master` 且工作区干净。

## 10. 当前执行记录

2026-08-29 已完成本批代码实施和专项验证：

- `scripts/verify-liblib-batch94.py` 通过；
- Director Batch 59、67-93 current gates 在固定
  `http://localhost:4317` 上串行通过；
- Batch 94 桌面 `1440x900`、移动端 `390x844` 的 console/page/request
  diagnostics 均为 `0/0/0`；
- 没有生成截图，也没有重复执行截图识别；
- 本批只描述 clone-owned Director 焦点边界，不升级为 LibTV 原站
  source-exact DOM/CSS 或焦点实现证据。

普通画布跨批回归的完整序列已经由 Batch 93 记录并通过。本次为验证
Batch 94 影响边界而进行的额外 spot check 中，Batch 57、60 和隔离重试的
Batch 64 通过；后续重复执行在用户要求“Batch 93 后不要再自动循环”后停止，
Batch 61 处于被中断状态。因此本批不把这次未完成的重复序列写成新的普通画布
全量通过，详见 [`current-gate-regression.json`](current-gate-regression.json)
和 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)。
