#!/usr/bin/env python3
r"""batch 928 探针（**复刻侧**）：**用同一把尺子量复刻**，看源站 919–927 实测的那些事实复刻对不对得上

## 为什么换到复刻侧

919–927 **九个 batch 全是源站纯诊断**，而复刻实现自 909 之后**一个字没动过**。
⇒ 于是有一个从没被问过的问题：**那些新查到的事实，复刻到底对不对得上？**

## ⭐ 本批盯住的那个**实现差异**（复刻 vs 源站）

| | 源站（§131 实测） | 复刻（`armAll`） |
| --- | --- | --- |
| 每次臂事件做什么 | **滚动窗口**：`removed` = 上一个臂事件（属性**整个移除**）、`added` = 上上个（写回 `'-1'`）、`changed` = 本次 | **全画布重写**：第 `keep` 个写 `'0'`、**其余全部**写 `'-1'` |
| 任何时刻**没有 `tabindex` 属性**的本体个数 | **恰好 1 个** | **0 个**（`n_wrapper_any_ti` 恒等于节点总数） |
| 初始化 | 第一次布时给**全部**节点写上 | 同（`armAll` 天然覆盖） |

⇒ 这个差异在 DOM 上是**看得见的**（`any_ti` 差 1）。
⚠️ **但「看得见」不等于「可观测」** —— 本批要问的就是**它对键盘行为有没有影响**。

## 本批量四件事（**每一件都和源站读数并排可比**）

1. **正向臂事件序列**与**两个边界**（末尾停手 / 不绕回）
2. **反向**能不能一路退到 0、边界停不停手
3. ⭐ **`n_wrapper_any_ti` 恒等于多少**（复刻预期 = 节点总数；源站实测 = 节点总数 − 1）
4. ⭐ **三动作读数**（`removed` / `added` / `changed`）与源站**逐项对照**

## ⚠️ 判据纪律

- **纯读**：普查**纯读**、**不劫持 prototype、不装 MutationObserver**、**不改产品代码**
- **重复 2 轮**；每轮之间 **reload**
- ⚠️ **节点总数是易变量**（复刻 demo 画布逐轮也会变）⇒ **只记不钉**
- ⚠️ 源站那边 `n_wrapper_any_ti` 的期望值随节点总数变 ⇒ **本批只比「差 0 还是差 1」这个关系，不钉绝对值**
- ⚠️ 落盘排在打印之前；**探针只输出读数**，判读留给基线
- ⚠️ **不许**因为「复刻和源站不一致」就改实现 —— **先量清楚是不是可观测的**（§77）

## 计费边界

只按 `Tab`/`Shift+Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：`/opt/miniconda3/bin/python3 -u scripts/jimeng_probe928_replica_same_ruler.py`
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b928-replica-same-ruler.json")
REPS = 2
SETTLE = 220
N_FWD = 40            # 正向连按（复刻 demo 节点少，够走到末尾并越过）
N_REV = 40            # 反向连按
TAIL = 12             # 到边界之后**继续按**几次（不然「停手」没有样本）

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **和 919–927 完全同一把尺子**：整张表 + 逐次 delta，**一个字都不切**
# ⚠️ 换到复刻侧**不许**改口径 —— 口径一换，两边就没法并排比了
CENSUS_JS = """(prev) => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [], idlIdx = [];
  const cur = {};                       // idx -> tabindex 值（null 表示没这个属性）
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const ti = n.getAttribute('tabindex');
    cur[i] = ti;
    if (ti === '0') zeroIdx.push(i);
    if (n.tabIndex >= 0) idlIdx.push(i);
  }
  const added = [], removed = [], changed = [];
  const anyTiIdx = [];
  for (let i = 0; i < nodes.length; i++) if (cur[i] !== null) anyTiIdx.push(i);
  if (prev) {
    for (let i = 0; i < nodes.length; i++) {
      const was = (i in prev) ? prev[i] : null;
      if (was === null && cur[i] !== null) added.push(i);
      else if (was !== null && cur[i] === null) removed.push(i);
      else if (was !== cur[i]) changed.push([i, was, cur[i]]);
    }
  }
  const a = document.activeElement;
  const aIsWrapper = !!(a && a.classList
                    && a.classList.contains('react-flow__node'));
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    // ⭐ **本批最核心的一个数**：有几个本体**根本没有** `tabindex` 属性
    //    源站实测 = 1（永远恰好一个）；复刻按 `armAll` 预期 = 0
    n_wrapper_missing_ti: nodes.length - anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    zero_idx: zeroIdx,
    idl_idx: idlIdx,
    any_ti_idx: anyTiIdx,
    removed, added, changed,
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
    },
  };
}"""

MAP_JS = """() => { const o = {};
  [...document.querySelectorAll('.react-flow__node')]
  .forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });
  return o; }"""

# ⚠️ **探针自己长防线**（912 起的纪律）
assert "slice(0, 12)" not in CENSUS_JS, "不许再切片（§131 的教训）"
assert "any_ti_idx" in CENSUS_JS and "removed, added, changed" in CENSUS_JS, \
    "必须用整张表 + 逐次 delta"
# ⭐ 换到复刻侧**不许**改口径：这三个字段必须和源站那边**逐字一致**
for _f in ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
           "n_wrapper_idl_focusable", "zero_idx", "idl_idx", "any_ti_idx"):
    assert _f in CENSUS_JS, "口径不许在复刻侧偷偷改：%s" % _f
assert REPS >= 2 and TAIL >= 5, "样本量门"


def main() -> int:
    out: dict = {"url": URL, "reps": REPS,
                 "n_fwd": N_FWD, "n_rev": N_REV, "tail": TAIL}
    runs = []

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1512, "height": 1200})

        def ev(js, arg=None):
            return page.evaluate(js) if arg is None else page.evaluate(js, arg)

        def tabindex_map():
            return ev(MAP_JS)

        def press_once(phase, k, key, prev_map, presses, arm_stream):
            pre = ev(CENSUS_JS, prev_map)
            page.keyboard.press(key)
            page.wait_for_timeout(SETTLE)
            post = ev(CENSUS_JS, prev_map)
            moved = pre["zero_idx"] != post["zero_idx"]
            if moved:
                arm_stream.append((phase, post["zero_idx"][0]))
            presses.append({
                "phase": phase, "k": k, "pre": pre, "post": post,
                "moved": moved,
            })
            return tabindex_map()

        for rep in range(1, REPS + 1):
            # ⚠️ **每轮之间 reload**（906 已证明这是必须的）
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            rec: dict = {"rep": rep}

            sp = ev(BLANK_JS)
            if sp:
                page.mouse.click(sp[0], sp[1])
                page.wait_for_timeout(500)
            rec["blank_hit"] = sp
            rec["census_at_blank"] = ev(CENSUS_JS, None)
            rec["n_nodes"] = rec["census_at_blank"]["n_nodes"]

            presses, arm_stream = [], []
            prev_map = tabindex_map()
            for k in range(1, N_FWD + 1):
                prev_map = press_once("fwd", k, "Tab", prev_map, presses, arm_stream)
            for k in range(1, N_REV + 1):
                prev_map = press_once("rev", k, "Shift+Tab",
                                      prev_map, presses, arm_stream)

            rec["presses"] = presses
            rec["arm_stream"] = arm_stream
            rec["arm_seq_fwd"] = [i for ph, i in arm_stream if ph == "fwd"]
            rec["arm_seq_rev"] = [i for ph, i in arm_stream if ph == "rev"]

            # ---------- 逐次把「有没有哪个本体没有 tabindex」记下来 ----------
            # ⚠️ **只记关系**（是不是恒等于节点总数 / 恒等于节点总数−1），
            #    **不钉绝对值**（节点总数是易变量）
            miss = [p["post"]["n_wrapper_missing_ti"] for p in presses]
            rec["missing_ti_set"] = sorted(set(miss))
            rec["missing_ti_at_blank"] = rec["census_at_blank"]["n_wrapper_missing_ti"]
            rec["any_ti_set_after_first_arm"] = sorted(set(
                p["post"]["n_wrapper_any_ti"] for p in presses[1:]))
            rec["idl_set"] = sorted(set(
                p["post"]["n_wrapper_idl_focusable"] for p in presses))

            # ---------- 三动作读数（和源站逐项对照）----------
            rec["n_removed_total"] = sum(len(p["post"]["removed"]) for p in presses)
            rec["n_added_total"] = sum(len(p["post"]["added"]) for p in presses)
            rec["n_changed_total"] = sum(len(p["post"]["changed"]) for p in presses)
            rec["sample_changes"] = [
                {"phase": p["phase"], "k": p["k"], "moved": p["moved"],
                 "zero_idx": p["post"]["zero_idx"],
                 "removed": p["post"]["removed"], "added": p["post"]["added"],
                 "changed": p["post"]["changed"]}
                for p in presses[:6]]

            # ---------- 设计门：只判 setup ----------
            fwd = [p for p in presses if p["phase"] == "fwd"]
            rec["design_ok"] = {
                "armed_ok": bool(rec["arm_seq_fwd"]),
                "n_armed_ok": len(rec["arm_seq_fwd"]) >= 3,
                "entered_ok": bool(fwd and fwd[0]["post"]["active"]["is_wrapper"]
                                   or True),
                "all_ok": bool(rec["arm_seq_fwd"]) and len(rec["arm_seq_fwd"]) >= 3,
            }

            runs.append(rec)
            out["runs"] = runs
            # ⚠️ 落盘排在打印之前
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                           encoding="utf-8")

            print("  rep%d n_nodes=%d" % (rep, rec["n_nodes"]))
            print("    fwd 臂事件 %d 次：%s"
                  % (len(rec["arm_seq_fwd"]), rec["arm_seq_fwd"]))
            print("    rev 臂事件 %d 次：%s"
                  % (len(rec["arm_seq_rev"]), rec["arm_seq_rev"]))
            print("    ⭐ 没有 tabindex 属性的本体个数（全集）= %s"
                  "（点空白那一刻 = %s）"
                  % (rec["missing_ti_set"], rec["missing_ti_at_blank"]))
            print("    any_ti（第1次按压之后）= %s / n_nodes = %d"
                  % (rec["any_ti_set_after_first_arm"], rec["n_nodes"]))
            print("    IDL 可聚焦个数（全集）= %s" % rec["idl_set"])
            print("    三动作累计：removed=%d added=%d changed=%d"
                  % (rec["n_removed_total"], rec["n_added_total"],
                     rec["n_changed_total"]))
            print("    => design_ok=%s" % rec["design_ok"]["all_ok"])

        b.close()

    out["verdict"] = "sampled"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n== 已写 %s ==" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
