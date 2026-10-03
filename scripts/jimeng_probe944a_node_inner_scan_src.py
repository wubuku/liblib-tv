#!/usr/bin/env python3
r"""batch 944 **发现探针**（源站，**纯读、零点击**）：节点**内部**到底有什么，
以及哪些**内部落点**可以安全地点。

## 为什么先做纯读发现

944 要测 943 标为「未测」的两条轴之一：**落点角色**（点节点**本体** vs 点节点
**内部的控件**）。⚠️ 但**点内部控件可能是有破坏性的** ——
节点工具条上很可能有「删除 / 移除」这类动作，一击就把画布改了，
后面所有读数全部作废（而且是在源站上真的删掉了别人的东西）。

⇒ 所以**先花一个纯读探针**把「节点里有什么、哪些落点安全」摸清楚，
再决定点哪个。**纯诊断必须纯读**（不劫持 `prototype`、不装 `MutationObserver`、
**不 reload**）。

## 本探针要回答的（全部纯读）

1. 节点内部的**元素标签直方图**（各多少个）
2. 每个节点**可点的内部落点**在哪、落点是什么标签、`aria-label` 是什么
3. ⭐ **哪些内部落点带破坏性语义**（`aria-label` / 文本里含
   删除 / 移除 / 清理 / delete / remove）⇒ **这一批永远不点**
4. 节点的 `data-testid` 清单（给复刻侧用）

## 判据纪律

- **零点击、零按键**（本探针只读 DOM）
- 落盘排在所有后处理之前（935）
- 派生键不许与原始键重叠（935）
- **重复 2 轮**（DOM 逐轮会变，节点数是易变量 74→77）

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe944a_node_inner_scan_src.py
"""

import json

OUT = "/tmp/b944a-node-inner-scan.json"
REPS = 2

NODE_SEL = ".react-flow__node"

RAW_KEYS = frozenset({
    # `SCAN_JS` 的原始键
    "n_nodes", "tag_hist", "per_node", "tid", "al", "cls", "n_inner", "tags",
    # ⭐ `INNER_JS` 每行的原始键（⚠️ 第一版漏登记，**当场被免疫针抓红** ——
    #   这就是 935 那道门存在的理由：漏登记的键会让「按原始键取值」那一步
    #   KeyError，读数整轮丢掉）
    "i", "x", "y", "tag", "destructive",
    # Python 侧汇总键
    "n_landable", "landable", "n_destructive", "destructive", "safe",
    "safe_tag_hist", "node_identity_hist",
})
DERIVED_KEYS = frozenset({"n_nodes_sum", "n_landable_sum", "n_destructive_sum"})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"

# ⛔ 带这些语义的元素**一律不点**（944 的选择依据）
DESTRUCTIVE = ("删除", "移除", "清理", "清空", "delete", "remove", "trash")

# ── JS：节点内部元素清单（**纯读**）──────────────────────────────
SCAN_JS = """([nodeSel]) => {
  const nodes = Array.from(document.querySelectorAll(nodeSel));
  const hist = {};
  const per_node = {};
  nodes.forEach((el, i) => {
    const inner = Array.from(el.querySelectorAll('*'));
    const tags = {};
    inner.forEach(c => {
      const t = (c.tagName || '').toUpperCase();
      tags[t] = (tags[t] || 0) + 1;
    });
    for (const t of Object.keys(tags)) {
      hist[t] = (hist[t] || 0) + tags[t];
    }
    per_node[i] = {tid: el.getAttribute('data-testid') || null,
                   al: el.getAttribute('aria-label') || null,
                   cls: String(el.className || ''), n_inner: inner.length,
                   tags: tags};
  });
  return {n_nodes: nodes.length, tag_hist: hist, per_node: per_node};
}"""

# ── JS：找**内部**可点落点（在节点矩形内扫网格，落点**不是**节点本体）
INNER_JS = """([nodeSel, destructive, grid]) => {
  const out = [];
  const nodes = Array.from(document.querySelectorAll(nodeSel));
  for (let i = 0; i < nodes.length; i += 1) {
    const el = nodes[i];
    const r = el.getBoundingClientRect();
    const seen = new Set();
    for (let gy = 0; gy < grid.length; gy += 1) {
      for (let gx = 0; gx < grid.length; gx += 1) {
        const x = Math.round(r.left + r.width * grid[gx]);
        const y = Math.round(r.top + r.height * grid[gy]);
        if (x < 0 || y < 0) continue;
        const at = document.elementFromPoint(x, y);
        if (!at) continue;
        if (at === el) continue;                 // 只要**内部**的
        if (!el.contains(at)) continue;
        // ⚠️⚠️ SVG 元素的 `className` 是 **SVGAnimatedString 对象**、不是字符串
        //    ⇒ 直接 `.slice()` 会抛 `is not a function`（第一版就栽在这：
        //    节点里有 156 个 `G` + 237 个 `SVG`，一碰到就炸）
        const cls = String(at.className && at.className.baseVal !== undefined
                           ? at.className.baseVal : (at.className || ''));
        const key = (at.tagName || '') + '|' + cls;
        if (seen.has(key)) continue;
        seen.add(key);
        const al = at.getAttribute('aria-label')
          || (at.innerText || at.textContent || '').slice(0, 30);
        const low = al.toLowerCase();
        let bad = false;
        for (const d of destructive) {
          if (low.indexOf(d) >= 0) { bad = true; break; }
        }
        out.push({i: i, x: x, y: y,
                  tag: (at.tagName || '').toUpperCase(),
                  cls: cls.slice(0, 60),
                  al: al, destructive: bad});
      }
    }
  }
  return out;
}"""


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

GRID = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]
out = {"node_sel": NODE_SEL, "destructive": list(DESTRUCTIVE),
       "grid": GRID, "void_runs": ["本探针是**纯读发现**探针，无作废跑"],
       "runs": []}

for rep in range(1, REPS + 1):
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n_audio = page.locator('button[aria-label="音频"]').count()
    if n_audio == 0:
        page.wait_for_timeout(8000)
        n_audio = page.locator('button[aria-label="音频"]').count()
    print(f"===== rep {rep} ===== 登录态={'命中' if n_audio else '未命中'}",
          flush=True)
    rec = {"rep": rep, "n_audio_rail_button": n_audio}
    out["runs"].append(rec)
    dump(out)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        continue

    scan = ev(SCAN_JS, [NODE_SEL])
    unknown = set(scan) - RAW_KEYS - DERIVED_KEYS
    assert not unknown, f"SCAN_JS 冒出未登记的键: {unknown}"
    rec["n_nodes"] = scan["n_nodes"]
    rec["tag_hist"] = scan["tag_hist"]
    print(f"  节点={scan['n_nodes']} 内部标签直方图："
          f"{dict(sorted(scan['tag_hist'].items(), key=lambda kv: -kv[1])[:12])}",
          flush=True)

    inner = ev(INNER_JS, [NODE_SEL, list(DESTRUCTIVE), GRID])
    unknown = {k for row in inner for k in row} - RAW_KEYS - DERIVED_KEYS
    assert not unknown, f"INNER_JS 冒出未登记的键: {unknown}"
    rec["n_landable"] = len(inner)
    rec["landable"] = inner
    rec["destructive"] = [row for row in inner if row["destructive"]]
    rec["safe"] = [row for row in inner if not row["destructive"]]
    rec["safe_tag_hist"] = {}
    for row in rec["safe"]:
        rec["safe_tag_hist"][row["tag"]] = rec["safe_tag_hist"].get(
            row["tag"], 0) + 1
    print(f"  内部可点落点 {len(inner)} 个（**破坏性** {len(rec['destructive'])} 个）"
          f"｜安全标签分布 {rec['safe_tag_hist']}", flush=True)
    for row in rec["destructive"][:6]:
        print(f"    ⚠️ 破坏性落点：i={row['i']} {row['tag']} "
              f"al={row['al']!r}", flush=True)
    for row in rec["safe"][:6]:
        print(f"    安全落点：i={row['i']} {row['tag']} al={row['al']!r}",
              flush=True)

    # 节点身份清单（给复刻侧）
    tids = {}
    for i, info in scan["per_node"].items():
        key = (info["tid"] or "") + "|" + (info["al"] or "")
        tids[key] = tids.get(key, 0) + 1
    rec["node_identity_hist"] = dict(sorted(tids.items(),
                                            key=lambda kv: -kv[1])[:20])
    print(f"  节点身份 top：{list(rec['node_identity_hist'].items())[:6]}",
          flush=True)
    dump(out)

print("\n读数已写入", OUT, flush=True)
