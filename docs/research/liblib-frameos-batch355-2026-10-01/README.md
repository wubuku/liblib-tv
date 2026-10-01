# Batch 355 — 「启用着、收下输入、什么都不做」的表单控件：普查 + 清零 + 门禁

日期：2026-10-01
范围：`src/components/frameos/FrameosProjectAssetsPanel.tsx`
性质：**CLONE_DECISION**（克隆侧缺陷；不改任何源站已采样的文案与外观）

---

## 缺陷

`FrameosProjectAssetsPanel` 的搜索框是一个**启用着、无 `value` 绑定、无 `onChange`**
的裸 `<input placeholder="搜索资产名称...">`。用户在里面打字，控件收下输入，
然后**什么都不发生**。

实测（修复前）：

```
搜索框 disabled = False
搜索框 有 value 绑定 = False
输入 '角色' 后面板文本变化 = False     ← 一字不变
输入框当前值 = '角色'                  ← 收下了, 留着, 没被用
面板文本: '项目资产\n×\n角色\n物品\n环境\n暂无已生成的资产图'
console errors: []                     ← 不是报错, 是纯惰性
```

零 console 错误这一点很关键：它不是「坏了」，是**安静地什么都不做**，
所以任何「页面有没有报错」类的检查都发现不了它。

与 Batch 350 的裁剪宽高同族（**看起来能用的表单，静默丢弃用户输入**），
区别是裁剪那条还会弹一条确认（更恶劣），这条连反馈都没有。

## 普查：这一类在全 app 还剩多少

写了普查探针 `scripts/probe-frameos-batch355-input-census.py`，
在 4 种 UI 态下枚举所有 `input/textarea`，用 React 挂在 DOM 上的
`__reactProps$*` 读 `onChange`（判据是「**这个控件有没有被 React 接上事件处理**」，
而不是看源码里有没有写）：

| UI 态 | 输入控件 | 静默丢弃输入 |
|---|---|---|
| default | 0 | 0 |
| **assets_panel** | 1 | **1** |
| crop | 2 | 0（Batch 350 已修） |
| generative_panel | 1 | 0 |

**全 frameos 只剩这 1 个。**

## 修复：不是「让它能用」，是「别假装它能用」

两条路可选：

1. 给面板接上真实的资产列表，让搜索真的能过滤；
2. 没有资产可搜时，**禁用它并说明原因**。

选 2，理由是不发明：面板内容是硬编码空态「暂无已生成的资产图」——
克隆侧**没有资产数据**；而「把节点设为资产图」的源站点击效果**未采样**
（Batch 226），所以「一个图片节点该归到角色/物品/环境哪一类」**没有依据**。
凭空虚构一套分类学，比留一个诚实的禁用态更糟。

于是：加 `disabled` + `title="暂无资产可搜索"` + 视觉区分（`opacity: 0.45`、
`cursor: not-allowed`），并保留空态文案不动。

> 这与 Batch 344「分组删除」的处理同构：没有真 action 可接时，
> **选择让 UI 停止撒谎，而不是发明一个假 action**。

## 变成门禁

`scripts/verify-frameos-batch355.py`（**13 项检查，0 诊断**）在 4 种 UI 态下
重跑同一套普查，任一「启用 + 无 onChange + 非 readonly」的控件就让验证器失败
并指名是哪个。每个非空态都带 `scan:not-empty:<态>` 防假绿自检，
另加一条「全部态加起来控件数 ≥ 4」防止普查整体失效。

另外钉住本次修复的三条性质：搜索框确实 `disabled`、确实带说明、空态没被误删。

### 变异测试

去掉 `disabled`（恢复成静默丢弃输入的假控件）→ 红：

```
no-silent-discard:assets_panel 静默丢弃输入的控件:
[{'tag': 'input', 'ph': '搜索资产名称...', 'data': ['data-frameos-assets-search']}]
```

## 保真度差距

- 「设为资产图」→ `showToast("已设置为资产图 (mock)", "success")`（Batch 226，
  源站点击效果未采样）与资产面板恒为空，**两者互不连通**：用户点了会看到成功提示，
  打开面板却什么都没有。这条**未改**（要连通就得先有资产数据与分类学，属产品决定）。
  本批只消除了「搜索框假装能用」这一处更硬的谎言。

## 顺带记一个自伤

普查探针第一版我在 Python 里写了 `hasattr(window.__frameos_store...)` ——
`window` 是 JS 名字，Python 里直接 `NameError`。**这类错误 `py_compile` 抓不到**，
必须实跑才发现（与 Batch 354 的 `import sys` 同类）。
