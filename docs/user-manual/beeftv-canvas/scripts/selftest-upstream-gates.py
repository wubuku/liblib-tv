#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 45「痕迹清单有没有漏」的反向验证（Batch 331）。

**为什么这四支要成对**：只测「能抓」的话，一次「恒 rc=2」也能通过——
而 rc=2 是**未能核对**，它什么都证明不了。所以必须同时测：

| # | 场景 | 期望 | 钉的是什么 |
|---|---|---|---|
| 1 | 夹具矩阵（覆盖恰好 = 工具说的那批、两遍都 rc=0） | **rc=0** | 正常时不误报 |
| 2 | 矩阵里多一道「实测会读」、而痕迹清单里没有它 | **rc=1** | **能抓漏**（而且必须是 1，不是 2） |
| 3 | 某道闸的指纹与矩阵记录不符 | **rc=2** | **退化必须报「未能核对」**（纪律 101） |
| 4 | 矩阵里有一行标着「红基线上量的」 | **rc=2** | **证据不完整 ≠ 没发现问题**（纪律 367②） |

**第 3 支尤其重要，而且它的成因是一次实测**：
第一次试图用「把某道闸的 `module_ref()` 藏起来」来制造第 2 支的场景，
**结果 rc=2 而不是 rc=1**——因为**任何导致清单漏掉的改动都会先让指纹过期**。
**这不是闸坏了，是三态设计在正确工作**：
真实流程里「清单漏了」只会在**重测之后**才成立（闸被改 → rc=2 → 重测 → 新的实测 vs 旧的清单）。
**所以第 2 支该篡改的是矩阵，不是闸**——
**而这件事只有先撞上第 3 支才想得到。**

**第 4 支是给「第一批实测量出来的东西」补的**：
本工具第一版是在**有他人未提交 WIP 的工作区**里跑的，
四道闸的正常那一遍已经是 rc=1，量出 `1 → 1`——
**而「rc 没变」本来就有两种成因**（真不读 / 读了但静默降级），
**红基线把两种搅成一种，那种行连「证明不了什么」都算不上，它会被下游当成证据。**
**只加判据不验它，等于新加了一条没人走过的分支**（纪律 265 的老形态）。

## 为什么反验用**夹具矩阵**、而不是树上那份落盘矩阵（纪律 367⑧，一个死循环）

闸 18 会**在构建里真跑每一份非慢反验**，于是它会跑到本文件。
而如果本反验的基线用的是「树上那份落盘矩阵」，就形成首尾相接的死循环：

    重测需要「全绿基线」 → 全绿基线包含闸 18 →
    闸 18 跑本反验 → 本反验要落盘矩阵新鲜 → 落盘矩阵新鲜只能靠重测完成

**它的表现极像「工具坏了」**：闸 18 被拖成 rc=1，矩阵里它那一行被标成「红基线上量的」，
**整份实测作废，而谁也说不清是哪一环先坏**（实测就是这样撞上的）。

**处置不是「把基线那一支改成不核」**（那就没有基线了），
也不是「把闸 18 排除出测量」（那要在工具里加一条例外，而例外会过期），
**而是让每个克隆体带一份自造的夹具矩阵**：
每个被测闸一行、两遍都记 rc=0、指纹按克隆体现算、覆盖恰好等于工具说的那批。
**这样四个用例验的仍是「判据的判断」，而不再验「落盘数据新不新鲜」**——
**后者是闸 45 自己在构建里的活**（纪律 356 的分工：工具产出、闸做比对）。
**换句话说：判断与数据分开验，分不开就会死锁。**
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(ROOT, "scripts")
GATE = os.path.join(SD, "verify-upstream-gates.py")
MATRIX = os.path.join(SD, "upstream-gates-sentinel.json")
SELF = os.path.basename(__file__)


def _measured_gates_in(sd):
    """被测闸的枚举**只从工具那里问**（纪律 355 / 367⑤）——
    **夹具的覆盖面必须与工具说的那批一致，否则它验的就不是判据的判断了。**"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rm_fixture", os.path.join(sd, "remeasure-upstream-gates.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.measured_gates(sd)


def clone(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    s = os.path.join(dst, "scripts")
    os.makedirs(s)
    for n in os.listdir(SD):
        if n.endswith(".py") or n.endswith(".json"):
            shutil.copy(os.path.join(SD, n), os.path.join(s, n))
    # **自造夹具矩阵**（理由见文件头，纪律 367⑧）：
    # 覆盖恰好等于工具说的那批、每行两遍都 rc=0、指纹按克隆体现算
    gates = _measured_gates_in(s)
    if not gates:
        return dst
    rows = [{"gate": g,
             "normal": {"rc": 0, "tail": ["夹具"], "sec": 0.0},
             "sentinel": {"rc": 0, "tail": ["夹具"], "sec": 0.0},
             "changed": False, "unusable": None} for g in gates]
    d = {"measured_at": "夹具（反验自造，不是落盘实测）",
         "sentinel": "zzz-not-a-real-ref-9f3a", "rows": rows,
         "fingerprints": {g: hashlib.sha256(open(os.path.join(s, g), "rb").read()).hexdigest()
                          for g in gates}}
    json.dump(d, open(os.path.join(s, os.path.basename(MATRIX)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return dst


def run(root):
    r = subprocess.run([sys.executable, os.path.join(root, "scripts", os.path.basename(GATE))],
                       cwd=root, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def case_baseline():
    """**基线用的是自造的夹具矩阵，不是树上那份落盘矩阵**（纪律 367⑧：
    用落盘矩阵会与「重测要绿基线」形成死循环）。
    **而落盘矩阵本身由闸 45 在构建里核**——两件事分开验。"""
    td = clone(os.path.join(tempfile.gettempdir(), "sug-selftest-base"))
    rc, out = run(td)
    shutil.rmtree(td, ignore_errors=True)
    if rc == 0:
        print("  ✓ 基线：夹具矩阵（覆盖恰好 / 两遍都 rc=0）→ rc=0")
        return True
    print("  ✗ 基线：夹具矩阵 → rc=%d，期望 0" % rc)
    print(out[-600:])
    return False


def case_missed():
    td = clone(os.path.join(tempfile.gettempdir(), "sug-selftest-miss"))
    p = os.path.join(td, "scripts", os.path.basename(MATRIX))
    d = json.load(open(p, encoding="utf-8"))
    # 挑一道痕迹清单里**没有**、而实测**没变**的闸，把它改成「实测会读」
    sys.path.insert(0, os.path.join(td, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ud", os.path.join(td, "scripts", "verify-upgrade-drift.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    marks = set(m.upstream_gates(td))
    target = None
    for r in d["rows"]:
        if r["gate"] not in marks and not r.get("unusable") \
                and r["normal"]["rc"] == r["sentinel"]["rc"]:
            target = r
            break
    if target is None:
        print("  ✗ 找不到「痕迹清单里没有、而实测没变」的闸 —— 夹具前提不成立，**作废**")
        shutil.rmtree(td, ignore_errors=True)
        return False
    target["normal"] = dict(target["normal"], rc=0)
    target["sentinel"] = dict(target["sentinel"], rc=2)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rc, out = run(td)
    shutil.rmtree(td, ignore_errors=True)
    if rc == 1 and target["gate"] in out:
        print("  ✓ 能抓：矩阵说 %s 实测会读、而痕迹清单没有它 → rc=1 并点名" % target["gate"])
        return True
    print("  ✗ 能抓：期望 rc=1 并点名 %s，实测 rc=%d" % (target["gate"], rc))
    print(out[-600:])
    return False


def case_stale():
    td = clone(os.path.join(tempfile.gettempdir(), "sug-selftest-stale"))
    p = os.path.join(td, "scripts", os.path.basename(MATRIX))
    d = json.load(open(p, encoding="utf-8"))
    g = sorted(d["fingerprints"])[0]
    d["fingerprints"][g] = "0" * 64
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rc, out = run(td)
    shutil.rmtree(td, ignore_errors=True)
    if rc == 2 and "已过期" in out:
        print("  ✓ 退化必报 rc=2：%s 的指纹对不上 → 「已过期」，**没有**报成 rc=1" % g)
        return True
    print("  ✗ 退化：期望 rc=2 且说「已过期」，实测 rc=%d" % rc)
    print(out[-600:])
    return False


def case_unusable():
    """把一行标成「红基线上量的」——闸 45 必须报 rc=2「证据不完整」，
    **而不是**照旧跑完那个「漏没漏」的核对并给出一个 rc=0 或 rc=1。"""
    td = clone(os.path.join(tempfile.gettempdir(), "sug-selftest-unusable"))
    p = os.path.join(td, "scripts", os.path.basename(MATRIX))
    d = json.load(open(p, encoding="utf-8"))
    # **注入锚点用 assert 钉死**（纪律 265 的老规矩）：没有 `unusable` 键就作废
    if not d["rows"] or "unusable" not in d["rows"][0]:
        print("  ✗ 矩阵里没有 `unusable` 键 —— 夹具前提不成立，**作废**")
        shutil.rmtree(td, ignore_errors=True)
        return False
    d["rows"][0]["unusable"] = "正常那一遍 rc=1（**反验注入**）"
    d["rows"][0]["changed"] = None
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rc, out = run(td)
    shutil.rmtree(td, ignore_errors=True)
    if rc == 2 and "红基线" in out and d["rows"][0]["gate"] in out:
        print("  ✓ 红基线行必报 rc=2：%s 被标成红基线量的 → "
              "「证据不完整」，**没有**照旧报成 rc=0/1" % d["rows"][0]["gate"])
        return True
    print("  ✗ 红基线：期望 rc=2 且点名该行，实测 rc=%d" % rc)
    print(out[-600:])
    return False


def main():
    print("闸 45 反向验证：4 例（1 基线 / 1 能抓 / 2 退化必报 rc=2）")
    results = [case_baseline(), case_missed(), case_stale(), case_unusable()]
    ok = sum(1 for r in results if r)
    bad = sum(1 for r in results if not r)
    # **末尾这一行的写法有硬要求（闸 18 方向十七实测）**：
    # 它要从反验输出的末尾**解析出合计**（`通过 N / 失败 N / 作废 N` 这个顺序），
    # 用来核对应关系表里「例数」那一列。
    # **第一版这里写的是「→ 通过 3 / 3；作废 0」，解析不出例数——**
    # 而那个形态的后果**不是构建变红，是那一列例数从此没人核**
    # （闸自己的报错原话：「别让『解析不到』变成一个没人知道的静默缺口」）。
    print("闸 45 反验：通过 %d / 失败 %d / 作废 0 = %d" % (ok, bad, ok + bad))
    if ok != 4:
        print("→ 有用例没过 —— 闸 45 上线前必须全过")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())