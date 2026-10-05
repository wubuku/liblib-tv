#!/usr/bin/env python3
"""批次 165-i —— 纯静态：从 165-h 留下的读数里**算出**每个二级页签的
「点得中 / 点不着」宽度带，而不是再跑一次浏览器。

🔑 为什么要单独一个脚本：165-h 那个循环跑完 15 档之后，我在**收尾的算门槛那一步**
   写错了一个变量名（`第一个坏` vs `第一个坏的`）⇒ 中途抛异常。
   ⇒ 结论只能从**已落盘的读数**里算，而不是「再跑一遍直到它不报错」——
   后者会让我为了拿绿灯而反复重跑，掩盖「脚本本身有 bug」这件事。
   （这正是立规 29 的变体：**别把「重跑一次就绿了」当成「原来就对」。**）

用法：python3 scripts/jimeng-b165i-bands.py
"""
import json
import pathlib

SRC = pathlib.Path(__file__).parent / "_tmp-b165h.json"
rec = json.loads(SRC.read_text())
rows = rec["读数"]
names = [t["逐字"] for t in rows[0]["读数"]["二级页签"]]

print(f"读数来源：{SRC.name}（{len(rows)} 档）\n")
header = f"{'窗口宽':>7} {'模态宽':>7} {'搜索框宽':>9}  " + "  ".join(f"{n:>6}" for n in names)
print(header)
print("-" * len(header))
per = {n: [] for n in names}
for r in rows:
    d = r["读数"]
    if not d or not d.get("有"):
        continue
    inp = d["输入盒"][2] if d["输入盒"] else None
    cells = []
    for n, t in zip(names, d["二级页签"]):
        per[n].append((r["视口宽"], t["点得中"], t.get("被输入抢走", False)))
        cells.append("  ✅  " if t["点得中"] else "  ⛔  ")
    print(f"{r['视口宽']:>7} {d['对话框盒'][2]:>7} {inp:>9}  " + "  ".join(f"{c:>6}" for c in cells))

print("\n=== 每个二级页签的「点不着」宽度带（连续区间）===")
bands = {}
for n in names:
    seq = sorted(per[n])
    bad = [w for w, ok, _ in seq if not ok]
    ok = [w for w, ok, _ in seq if ok]
    # 把 bad 压成连续区间
    runs, cur = [], []
    for w in bad:
        if cur and w - cur[-1] > 60:      # 相邻档间隔 >60 视为断开（我扫的档距最大 20）
            runs.append(cur); cur = []
        cur.append(w)
    if cur:
        runs.append(cur)
    bands[n] = {
        "点不着_宽度": bad,
        "点不着_区间": [f"{r[0]}–{r[-1]}" for r in runs],
        "点得着_宽度": ok,
        "抢走它的元素": sorted({('搜索输入框' if steal else '未知') for _, ok, steal in seq if not ok}),
    }
    print(f"  {n:>3}：点不着 {bands[n]['点不着_宽度']} → 区间 {bands[n]['点不着_区间']}；"
          f"仍可点的最大宽度 {max(ok) if ok else None}")

print("\n=== 非单调检查（同一个页签在更窄的窗口里反而又能点了？）===")
# 🔴 批次 165-i 自身失误：这道检查**方向搞反了**。按宽度升序扫，
#    「先窄(点不着) 后宽(点得着)」是**理所当然**的，会把每一页签都报成「非单调」。
#    正解：要问的是「**已经点不着之后，再变窄反而又点得着了**」⇒ 必须**降序**扫。
nonmono = []
for n in names:
    seq = sorted(per[n], key=lambda t: -t[0])          # 宽 → 窄
    seen_bad = False
    for w, ok, _ in seq:
        if not ok:
            seen_bad = True
        elif seen_bad:
            nonmono.append((n, w))
if nonmono:
    print("  ⚠️ 存在非单调：" + "；".join(f"**{n}** 在 {w} 宽时又恢复可点（比它开始点不着的窗口更窄）" for n, w in nonmono))
else:
    print("  无：每个页签一旦点不着，再变窄也一直点不着")

out = {"产物": "b165i", "读数来源": SRC.name, "档数": len(rows), "页签": names,
       "带": bands, "非单调": nonmono,
       "结论": "资产库二级页签在窄窗口下会被顶部搜索输入框盖住并点不中；"
               "各页签的「点不着」宽度带不同，且极窄时搜索框自身收缩会让部分页签恢复可点"}
pathlib.Path(__file__).parent.joinpath("_tmp-b165i.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1))
print("\n已落盘 _tmp-b165i.json")
