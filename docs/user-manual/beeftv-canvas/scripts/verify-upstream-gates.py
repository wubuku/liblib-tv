#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十五道闸：`verify-upgrade-drift.py` 的「会读上游的闸」这份清单，本身有没有过期。

## 这道闸治什么（纪律 364 的直接后果）

`verify-upgrade-drift.py` 靠 `UPSTREAM_MARKERS` 一张**手工痕迹清单**扫出「会读上游的闸」，
而 `20-reference.md` 把那个数当事实写给了读者。实测它错过两次：

- **Batch 329**：漏了 `module_ref(`（Batch 197 把 ref 解析改成模块级缓存）→ **少扫 4 道**；
- **Batch 331**：**多算 4 道**——`verify-meta`（闸 9）与 `verify-baseline`（闸 14）
  **自己不读上游 ref**（闸 9 的源码里甚至写着「本闸不读上游、没有基线可读」），
  `verify-upstream-gates`（**本闸自己**）**被源码里那句 `print()` 算进来**，
  而 `verify-baseline-landmark`（闸 40）**确实读上游、但走 `origin/main^{commit}`、
  结构上不受 `BEEFTV_REF` 控制**。
- **而闸 18 那一道，本身就是「红基线上量出来的数据会骗人」的一个实例**：
  第一遍实测是在有他人未提交改动的工作区里跑的，闸 18 那一遍本来就是红的，
  量出 `1 → 1`，于是它被算进「多算」；**在一棵全绿的树里重测，它是 `0 → 1`——它真读那个 ref**。
  **同一个方法、同一份代码，两次结论相反，而错的那一次看不出任何异常**。

**而「一道闸读不读上游」是运行时的事实，不是源码里有什么字面量**——
所以清单旁边必须有一份**实测**，由 `scripts/remeasure-upstream-gates.py` 用哨兵 ref 跑出来。

## 本闸只判红一类，因为另一类判红会误伤（纪律 248）

- **哨兵实测会读、而痕迹清单没扫到 → 判红**。
  **这是确定的漏**：实测说「它在哨兵 ref 下 rc 变了」，而清单说「它没有读上游的痕迹」，
  **两边不可能都对**，而实测那一侧是运行时事实。
- **痕迹清单说会读、而哨兵实测 rc 没变 → 只列出来，不判红**。
  **实测已证明这一侧是混合的**：Batch 331 量到 4 道里——
  **闸 40 是正当例外**（读上游走 `^{commit}` 那条路、哨兵天然抓不到），
  **闸 9 / 闸 14 是真的不读**，**剩下 1 道是本闸自己**
  （工具刻意不量它的消费者，所以它那一行不在矩阵里）。
  **把正当例外和真不读一起判红，就是陪绑**。

## 「不作数」那一侧现在有数了（纪律 370）

工具对**哨兵下 rc 未变**的那些闸**再跑一遍真实漂移 ref**，于是那一侧被拆成三类：
- **A**：哨兵下 rc 变 → **真读，且读不到时会响**；
- **B**：哨兵下 rc 未变、而漂移 ref 下 rc 变 → **读到了真实漂移，却在「读不到」时沉默**
  ——**本闸对这一类判红**，它是本项目最坏的一类（平时绿、真上游坏了也绿）；
- **C**：两边都无反应 → **而这一句推不出「它不读」**（纪律 365⑦：
  也可能读了、只是比的东西与那个 ref 无关），所以它**只列不判红**。
**而第三遍要有一个存在性守卫**：漂移参照不存在时那一列会整列 rc=2，
**那会被误读成「全部都在沉默」——那是最坏的一种假红**（纪律 330 的同款处置）。

## 三态退出码（纪律 101）

- **0**：清单没漏，实测矩阵也是新鲜的；
- **1**：清单**漏了**实测会读的闸（处置是补 `UPSTREAM_MARKERS`，**不是删实测**）；
- **2**：**未能核对**——实测矩阵不在 / 指纹对不上（**闸被改过、矩阵已过期**）/
  解析不出汇总 / **矩阵里有行是在红基线上量的** / **矩阵没盖住当前全部闸**。
  **这一侧绝不报「不一致」**：一次工具故障不是一次不一致。

## 两条「证据不完整」也算 rc=2（纪律 367②④）

- **红基线**：矩阵里若有行标着 `unusable`（正常那一遍不是 rc=0），
  **那种行证明不了任何事**——「rc 没变」本来就有两种成因（真不读 / 读了但静默降级），
  **而红基线把两种搅成一种**。所以它不是「没发现问题」，是**证据不完整**。
- **两类摘要**（纪律 368）：`tree_digest`（手册内容）与 `shared_digest`
  （`scripts/` 下除闸自己与这份矩阵之外的一切）必须与现场重算的一致。
  **只核闸自己的 sha256 是不够的**——**改一行手册正文就可能改掉某道闸的 rc，
  而那个闸的文件一个字节没动**；而 `scripts/` 下改一份反验，**闸 18 的 rc 就变**
  （它在构建里真跑每一份）。
- **覆盖**：矩阵必须**恰好**盖住 `remeasure-upstream-gates.py` 说的那批闸。
  **少盖**是「新加的闸没量」（新闸到底读不读上游，没人知道），
  **多盖**是「矩阵里有已经不存在的闸」（这份实测描述的不是这棵树）。
  **枚举只写一份**——本闸用 importlib 调工具自己的 `measured_gates()`，不重刻。

## 边界（不建人工登记表，纪律 242）

「正当例外」这一类**不登记**，**只每次列出来**。
理由是：**一份「谁可以例外」的名单，就是纪律 364 那张会过期的清单的另一个版本**——
而这一版的过期形态更难发现（它看起来像一份权威的豁免清单）。
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(ROOT, "scripts")
DRIFT = os.path.join(SD, "verify-upgrade-drift.py")
MEASURE = os.path.join(SD, "remeasure-upstream-gates.py")
MATRIX = os.path.join(SD, "upstream-gates-sentinel.json")
SELF = os.path.basename(__file__)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def marker_gates():
    """按 `verify-upgrade-drift.py` 自己的判据现场扫一遍——**不重刻它的实现**
    （纪律 355：同一个概念只能有一份实现）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ud_drift", DRIFT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return set(m.upstream_gates(ROOT)), tuple(sorted(m.UPSTREAM_MARKERS))


def expected_gates():
    """「该测哪些闸」问的是**工具自己**——**枚举只写一份**（纪律 367⑤）。
    各写一遍的后果很具体：工具排除了三个、闸排除了两个，
    **差出来的那一道在两边都"不是例外"，于是谁都不报**。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("rm_measure", MEASURE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return set(m.measured_gates(SD))


def digests_now():
    """现场重算两类摘要——**「过期了没有」要按「变化能从哪些地方传进来」列全**（纪律 368）：
    只核闸自己的源码是不够的，**改一行手册正文就可能改掉某道闸的 rc，
    而它自己的文件一个字节没动**。
    **实测代价 0.07 + 0.02 秒，所以闸每次跑都算得起**——而算不起的 freshness
    就等于没有 freshness（那是纪律 265 的老形态：只有真出现时才炸的洞没人守）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("rm_digest", MEASURE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.tree_digest(ROOT), m.shared_digest(SD)[0]


def main():
    if not os.path.exists(MATRIX):
        print("[skip] 还没有实测矩阵 %s" % MATRIX)
        print("       跑 `python3 scripts/remeasure-upstream-gates.py` 生成它")
        print("→ 实测矩阵不在，**本闸本轮没有核对任何东西**（这既不是「一致」也不是「不一致」）")
        return 2
    try:
        data = json.load(open(MATRIX, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("[skip] 实测矩阵读不出来：%s" % e)
        print("→ 解析不出来就是**未能核对**，不是「没有不一致」")
        return 2

    rows = data.get("rows")
    fps = data.get("fingerprints")
    if not isinstance(rows, list) or not isinstance(fps, dict):
        print("[skip] 实测矩阵缺 `rows` 或 `fingerprints`")
        return 2

    # ① 指纹：闸被改过而矩阵没重测 ⇒ 矩阵已过期 ⇒ rc=2（不是 rc=1）
    stale = []
    for gate, fp in sorted(fps.items()):
        p = os.path.join(SD, gate)
        if not os.path.exists(p):
            stale.append("%s（文件不在了）" % gate)
        elif sha256_of(p) != fp:
            stale.append(gate)
    if stale:
        print("[skip] 实测矩阵已过期：以下闸在实测之后被改过（%d 道）" % len(stale))
        for g in stale:
            print("         %s" % g)
        print("→ 处置是**重测**（`python3 scripts/remeasure-upstream-gates.py`），"
              "不是把指纹改回去——改回去等于让过期值继续冒充实测值")
        return 2

    # ①之二 两类摘要：手册内容 / scripts 里的共享实现与反验（纪律 368）
    try:
        td_now, sh_now = digests_now()
    except Exception as e:  # noqa: BLE001
        print("[skip] 算不出两类摘要：%s" % e)
        return 2
    if data.get("tree_digest") is None or data.get("shared_digest") is None:
        # **缺键与「值对不上」要分开说**：缺键是**格式旧**，而对不上是**内容变了**，
        # **混在一张单子里，读者会去查「我改了什么」，而他真正该做的是重测**
        print("[skip] 矩阵里**没有** `tree_digest` / `shared_digest`（那是上一版的格式）")
        print("→ 处置是**重测**（`python3 scripts/remeasure-upstream-gates.py`）")
        return 2
    drift = []
    if data.get("tree_digest") != td_now:
        drift.append("**手册内容**变了（`tree_digest` 对不上）")
    if data.get("shared_digest") != sh_now:
        drift.append("**`scripts/` 下有文件变了**（共享实现 / 反验 / 夹具 / 其它工具，`shared_digest` 对不上）")
    if drift:
        print("[skip] 实测矩阵与这棵树已经对不上：%d 处" % len(drift))
        for d in drift:
            print("         · %s" % d)
        print("→ **改手册正文与改反验都会改掉某道闸的 rc，而闸自己的文件一个字节没动**——")
        print("  所以处置是**重测**（`python3 scripts/remeasure-upstream-gates.py`），")
        print("  **不是把摘要改回去**——改回去就是让过期值继续冒充实测值")
        return 2

    # ② 形状不对的行：读不出来不等于 0
    for r in rows:
        if not isinstance(r, dict) or "normal" not in r or "sentinel" not in r:
            print("[skip] 实测矩阵里有认不出的行 —— 读不出来不等于 0")
            return 2

    # ③ 红基线：那种行证明不了任何事（纪律 367②）
    bad = [r for r in rows if r.get("unusable")]
    if bad:
        print("[skip] 实测矩阵里有 %d 行是在**红基线**上量的，它们不是证据：" % len(bad))
        for r in bad:
            print("         %s —— %s" % (r["gate"], r["unusable"]))
        print("→ 处置是**在一棵全绿的树里重测**"
              "（`python3 scripts/remeasure-upstream-gates.py`），")
        print("  **不是把那些行删掉**——删掉就是在假装那几道量过了")
        print("→ **证据不完整 ≠ 没发现问题**")
        return 2

    # ④ 覆盖：矩阵必须**恰好**盖住该测的那批闸（纪律 367④）
    try:
        want = expected_gates()
    except Exception as e:  # noqa: BLE001
        print("[skip] 问不出「该测哪些闸」：%s" % e)
        return 2
    got = {r.get("gate") for r in rows}
    uncovered = sorted(want - got)
    ghost = sorted(g for g in got - want if g)
    # **指纹表的键也必须等于同一批**——「行在、指纹不在」意味着那行没有新鲜度锚点，
    # **而那正是本闸第一版实测里真实发生过的形态**（工具没写 fingerprints）
    fps_set = set(fps)
    fp_uncovered = sorted(want - fps_set)
    fp_ghost = sorted(fps_set - want)
    if uncovered or ghost or fp_uncovered or fp_ghost:
        print("[skip] 实测矩阵的覆盖对不上当前这棵树（纪律 367④）")
        if uncovered:
            print("       **没量到**（新加的闸？还是它不被测？——不猜）：%d 道" % len(uncovered))
            for g in uncovered:
                print("         · %s" % g)
        if ghost:
            print("       **量了但树里已经没有它**：%d 道" % len(ghost))
            for g in ghost:
                print("         · %s" % g)
        if fp_uncovered:
            print("       **没有指纹的行**（那行没有新鲜度锚点，纪律 367①）：%d 道" % len(fp_uncovered))
            for g in fp_uncovered:
                print("         · %s" % g)
        if fp_ghost:
            print("       **指纹指向树里没有的闸**：%d 道" % len(fp_ghost))
            for g in fp_ghost:
                print("         · %s" % g)
        print("→ 处置是**重测**，不是改矩阵里的行数")
        return 2

    # ⑤ 哨兵实测「真读了那个 ref」= 两次 rc 不同
    measured = set()
    for r in rows:
        if r["normal"].get("rc") != r["sentinel"].get("rc"):
            measured.add(r["gate"])

    marks, markers = marker_gates()

    missed = sorted(measured - marks)
    extra = sorted(marks - measured)

    print("实测矩阵：%s（哨兵 %s）"
          % (data.get("measured_at", "?"), data.get("sentinel", "?")))
    print("痕迹清单（%s）：%d 道；哨兵实测会读：%d 道"
          % (markers, len(marks), len(measured)))
    if SELF not in got:
        # **明说，但不判红**（纪律 367③）：「没量自己」不是「清单漏了」——
        # 量自己等于让本闸读一份**写到一半**的矩阵，那一行是坏行（实测 rc=2）。
        print("[note] 本闸**不在**实测矩阵里（工具刻意不量它的消费者）——"
              "**这一条不判红**：它既不证明本闸会读上游，也不证明它不会。")

    if extra:
        print("→ 痕迹清单说会读、而哨兵 rc 没变的 %d 道（**不判红，须逐条定性**）：" % len(extra))
        # **Batch 331：下面这两行说明为什么本闸要放在 docstring 里而不是这里**——
        # 它们提到上游那个浮动 ref 的**字面量**，而闸 14 方向四核的是
        # 「**代码里**（剥掉 docstring 与注释之后）有没有写死它」，
        # **它剥不掉字符串字面量**。
        # **所以「解释别人为什么合规」的文字，写在代码里会被判成「自己不合规」**
        # ——本闸上线首跑就被方向四报了一次，这是实测。
        # **处置不是把判据放宽，而是把说明搬回 docstring**（纪律 329 的那一条同款）。
        print("   **其中闸 40 读上游走的是「浮动 ref + ^{commit}」那条路、")
        print("   结构上不受 `BEEFTV_REF` 控制，所以哨兵天然抓不到它——这是正当例外。**")
        print("   **而本闸自己也在这一列里**：它代码里有一句 `print()` 提到了那个变量名，")
        print("   **所以任何基于源码字面量的清单都会把它算进去——这正是这道闸存在的理由。**")
        for g in extra:
            mark = "　← **本闸自己**" if g == SELF else ""
            print("     · %s%s" % (g, mark))

    # ⑥ 三分类里唯一判红的一类：B（哨兵下没变、而真实漂移 ref 下变了）
    # **它是「读到了却在「读不到」时沉默」**——平时绿、真上游坏了也绿（纪律 365⑦）
    silent = []
    for r in rows:
        d = r.get("drift")
        if r.get("changed") or r.get("unusable") or not isinstance(d, dict):
            continue
        if d.get("rc") not in (0, None):
            silent.append((r["gate"], d.get("rc")))
    buckets = {"A": 0, "B": 0, "C": 0, "未测": 0}
    for r in rows:
        if r.get("unusable"):
            continue
        if r.get("changed"):
            buckets["A"] += 1
        elif isinstance(r.get("drift"), dict):
            buckets["B" if r["drift"].get("rc") not in (0, None) else "C"] += 1
        else:
            buckets["未测"] += 1
    print("三分类：A 真读且响 %d 道 / B 未变但对真实漂移有反应 %d 道 / C 两边都无反应 %d 道"
          % (buckets["A"], buckets["B"], buckets["C"]))
    if buckets["未测"]:
        print("     另有 %d 道**没跑第三遍**（漂移参照不存在）——**这一类不作数**" % buckets["未测"])
    print("     **而 C 类那一句「两边都无反应」推不出「它不读」**（纪律 365⑦）")

    if missed:
        print("→ ✗ 痕迹清单**漏了 %d 道实测会读的闸**：" % len(missed))
        for g in missed:
            print("     · %s" % g)
        print("   处置是给 `UPSTREAM_MARKERS` 补标记并重测，"
              "**不是删掉实测**——实测那一侧是运行时事实")
        print("痕迹清单核对：1 处不一致")
        return 1

    if silent:
        print("→ ✗ **%d 道闸「读到了却在『读不到』时沉默」**（B 类）：" % len(silent))
        for g, rc in silent:
            print("     · %s —— 哨兵下 rc 不变，而真实漂移 ref 下 rc=%s" % (g, rc))
        print("   **这类闸平时绿、真上游坏了也绿**，是本项目最坏的一类（纪律 365⑦）；")
        print("   处置是**把那道闸改成读不到时 rc=2**，**不是把它从清单里去掉**")
        print("痕迹清单核对：1 处不一致")
        return 1

    print("痕迹清单核对通过：没漏（%d 道痕迹 / %d 道实测，会读的那 %d 道全在清单里）"
          % (len(marks), len(measured), len(measured)))
    return 0


if __name__ == "__main__":
    sys.exit(main())