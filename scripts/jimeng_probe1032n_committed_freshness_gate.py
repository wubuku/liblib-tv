#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②n：**提交的那本 == 探针现在会写的那本**（全量新鲜度门）。

⭐⭐⭐⭐⭐ **这道门为什么存在**：1032-②m 笔4·五 实测到「第一轮就漂移」的那 8 本
⇒ ⇒ ⇒ 那 8 本 = **提交的那本 != 探针现在会写出来的那本**
⇒ ⇒ ⇒ 而**全仓没有任何一道门抓得到它**：
⇒ ⇒ ⇒⇒ 1014 的表核的是「表里记的字节 vs 盘上的字节」
⇒ ⇒ ⇒⇒ 1032l 核的是「表 vs 盘上／提交态」
⇒ ⇒ ⇒⇒ **⇒ 二者都不问「盘上那本是不是【现在】的产物」**

⇒ ⇒ ⇒⇒ **⇒ 而「新鲜度」不等于「可复现性」** ⇒ ⇒ ⇒⇒
  1015 的四态答「**可复现吗**」（跑前 vs 跑后）
  ⇒ ⇒ ⇒⇒ **⇒ 本门答「**还新鲜吗**」（提交的那本 vs 这一轮跑出来的那本）**

⭐⭐⭐⭐⭐ **三个量各记各的**（本门自己的口径，不许混）：
  ① **提交态的字节**（`git show HEAD:<path>`）
  ② **盘上的字节**（工作区）
  ③ **这一轮跑出来的字节**（1015 发布的 `fresh_sha12`）
⇒ ⇒ ⇒⇒ **⇒ 「字节数相同」不是「字节相同」⇒ ⇒ 数字骗人、指纹不骗人**

⭐⭐⭐⭐⭐ **「排除」的效力必须按口径分**：
  1015 把**自己**排除在「可复现性比较」之外（不拿自己证明自己）
⇒ ⇒ ⇒⇒ **⇒ 但它【不许】被排除在「新鲜度比较」之外** ⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 本门必须把 1015 自己算进去**
⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 而本门自己的产物也必须在册**（它是那 30+1 本之一）⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ ⇒ 不许自己例外**

⭐⭐⭐⭐⭐ **宇宙是【实测得出】的、不许手列**：
  册子（1015 那本书）的 `books` 行给出「有哪些本、各自由谁生成」
⇒ ⇒ ⇒⇒ **⇒ 而被排除的那些（1027 的产物）由册子自己公布理由** ⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 本门核那份理由非空**
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
BOOK_REL = "docs/research/jimeng-canvas/rerun-reproducibility-1015.json"
BOOK_NAME = "rerun-reproducibility-1015.json"
GOLDEN = GDIR / "committed-freshness-1032n.json"
SELF = Path(__file__).name
PROBE_1015_REL = "scripts/jimeng_probe1015_rerun_reproducibility.py"

# ── 口径：kind 三档（与全册一致）────────────────────────────────────────
KINDS = ("failure", "conclusion", "precondition")
CRITERION_KINDS = {
    "P1_committed_bytes_equal_the_bytes_the_probe_wrote_1032n": "failure",
    "P2_this_book_itself_is_what_the_current_script_would_write_1032n": "failure",
    "P3_books_that_change_every_round_must_declare_themselves_1032n": "failure",
    "P4_every_excluded_book_must_publish_a_reason_1032n": "failure",
    "P5_this_gate_can_actually_go_red_1032n": "failure",
    "P6_two_implementations_of_the_committed_bytes_must_agree_1032n": "failure",
}


def _sha12(raw):
    if raw is None:
        return None
    return hashlib.sha256(raw).hexdigest()[:12]


def _read_worktree(rel):
    try:
        return (ROOT / rel).read_bytes()
    except Exception:
        return None


def _read_head(rel):
    try:
        r = subprocess.run(["git", "show", "HEAD:" + rel], cwd=str(ROOT),
                           capture_output=True, timeout=120)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def _book_rows(book):
    rows = book.get("books")
    if not isinstance(rows, list) or not rows:
        return []
    out = []
    for r in rows:
        if isinstance(r, dict) and r.get("golden"):
            out.append(r)
    return out


def _judge(book, read):
    """⭐ 纯函数：册子（事实）＋ 一个读取器 ⇒ 判决。

    ⇒ ⇒⇒⇒ **六件事**：
      ① 逐本：读到的字节 == 册子发布的 `fresh_sha12`
      ② 1015 自己：册子记的脚本指纹 == 现在脚本的指纹（脚本没变）
      ③ 跨轮不稳定的书必须**自己声明**「我的产物每次都变」
      ④ 被排除的那些必须在册子里**公布理由**、且不许混进被判集合
      ⑤ 两份实现（门自己算的 vs 册子发布的 `committed_sha12`）必须逐本相等
    """
    why = []
    rows = _book_rows(book)
    if not rows:
        return {"ok": False, "why": ["book_has_no_rows"], "n_rows": 0}

    # ── ① 逐本：读到的字节 == 这一轮跑出来的字节 ──────────────────────
    mismatch = []
    unreadable = []
    no_fact = []
    for r in rows:
        rel = "docs/research/jimeng-canvas/" + r["golden"]
        raw = read(rel)
        if raw is None:
            unreadable.append(r["golden"])
            continue
        fact = r.get("fresh_sha12")
        if not fact:
            no_fact.append(r["golden"])
            continue
        got = _sha12(raw)
        if got != fact:
            mismatch.append({"golden": r["golden"], "state": r.get("state"),
                             "sha12_read": got, "fresh_sha12_in_book": fact})
    if mismatch:
        why.append("committed_bytes_differ_from_the_bytes_the_probe_wrote:%d"
                   % len(mismatch))
    if no_fact:
        why.append("book_publishes_no_fresh_sha12_for:%d" % len(no_fact))

    # ── ② 1015 自己：脚本没变 ＋ 输入没变 ⇒ 输出必然没变 ──────────────
    script_now = _sha12(_read_worktree(PROBE_1015_REL))
    script_in_book = book.get("generator_sha12_1015")
    script_same = bool(script_now) and bool(script_in_book) and \
        script_now == script_in_book
    inputs_changed = []
    for r in rows:
        raw = read("docs/research/jimeng-canvas/" + r["golden"])
        if raw is None:
            continue
        fact = r.get("fresh_sha12")
        if fact and _sha12(raw) != fact:
            inputs_changed.append(r["golden"])
    if not script_same:
        why.append("the_script_that_wrote_the_book_is_not_the_current_one")
    if inputs_changed:
        why.append("inputs_changed_since_the_run:%d" % len(inputs_changed))

    # ── ③ 跨轮不稳定的书必须自己声明 ────────────────────────────────
    unstable = [r["golden"] for r in rows
                if r.get("stable_across_rounds") is False]
    undeclared = []
    for g in unstable:
        raw = read("docs/research/jimeng-canvas/" + g)
        doc = None
        try:
            doc = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:
            doc = None
        if not isinstance(doc, dict):
            undeclared.append(g)
            continue
        if doc.get("volatile") is not True or not str(doc.get("volatile_why") or "").strip():
            undeclared.append(g)
    if undeclared:
        why.append("books_that_change_every_round_but_did_not_declare:%d"
                   % len(undeclared))

    # ── ④ 被排除的那些必须公布理由、且不许混进被判集合 ──────────────
    disc = book.get("discovery")
    excluded = disc.get("excluded") if isinstance(disc, dict) else None
    excluded = excluded if isinstance(excluded, list) else []
    judged = {r["golden"] for r in rows}
    judged.add(BOOK_NAME)
    bad_exclusion = [e.get("golden") for e in excluded
                     if isinstance(e, dict)
                     and (not str(e.get("why") or "").strip()
                          or e.get("golden") in judged)]
    if bad_exclusion:
        why.append("exclusion_without_a_reason_or_inside_the_judged_set:%d"
                   % len(bad_exclusion))
    # 本门自己：**它的产物记着【提交态的判决】** ⇒ ⇒ 提交态一变它就变
    # ⇒ ⇒ ⇒ ⇒ 而它自己进「被排除」名单 ⇒ ⇒ 理由必须写在**源码里**、不许只在散文里
    own = [{"golden": GOLDEN.name, "generated_by": SELF,
            "why": "⭐⭐⭐⭐⭐ **本门的产物记着【提交态的判决】** ⇒ ⇒ 提交态一变它就变 "
                   "⇒ ⇒ ⇒ ⇒ 而它被 1014 的表排除、也是同一个理由 ⇒ ⇒ ⇒⇒ "
                   "⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 而「排除」的效力按口径分：不参加可复现性比较 ≠ 不参加新鲜度比较**"}]
    for e in own:
        if e["golden"] in judged:
            bad_exclusion.append(e["golden"])
    excluded = excluded + own

    # ── ⑤ 两份实现必须互核 ─────────────────────────────────────────
    disagree = []
    for r in rows:
        rel = "docs/research/jimeng-canvas/" + r["golden"]
        raw = read(rel)
        mine = _sha12(raw) if raw is not None else None
        theirs = r.get("committed_sha12")
        if theirs is None:
            continue
        if mine != theirs:
            disagree.append(r["golden"])
    if disagree:
        why.append("the_two_implementations_of_committed_bytes_disagree:%d"
                   % len(disagree))

    return {
        "ok": not why,
        "why": why,
        "n_rows": len(rows),
        "n_mismatch": len(mismatch),
        "mismatch": mismatch,
        "n_unreadable": len(unreadable),
        "unreadable": unreadable,
        "n_no_fact": len(no_fact),
        "no_fact": no_fact,
        "script_sha12_now": script_now,
        "script_sha12_in_book": script_in_book,
        "script_unchanged": script_same,
        "n_inputs_changed": len(inputs_changed),
        "inputs_changed": inputs_changed,
        "n_unstable": len(unstable),
        "unstable": unstable,
        "n_undeclared": len(undeclared),
        "undeclared": undeclared,
        "n_excluded": len(excluded),
        "n_bad_exclusion": len(bad_exclusion),
        "bad_exclusion": bad_exclusion,
        "n_disagree": len(disagree),
        "disagree": disagree,
    }


def _load_book(read):
    raw = read(BOOK_REL)
    if raw is None:
        return None
    try:
        doc = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def _selftest(book):
    """⭐⭐⭐⭐⭐ **注入式反证**：改原始字段 ⇒ 必须翻红。

    ⇒ ⇒⇒⇒ 而反证必须**改原始字段**（册子里的 sha / 脚本指纹 / 排除理由），
    ⇒ ⇒⇒⇒ **不许改上游的 ok 标志** ⇒ ⇒⇒⇒ 否则那道判决会变成恒真。
    """
    import copy
    base = _judge(book, _read_worktree)
    cases = []

    def _mutate(name, fn):
        b = copy.deepcopy(book)
        rows = _book_rows(b)
        if not rows:
            return
        fn(b, rows)
        cases.append((name, not _judge(b, _read_worktree)["ok"]))

    _mutate("改掉一行的 fresh_sha12", lambda b, rows: rows[0].__setitem__(
        "fresh_sha12", "deadbeefcafe"))
    _mutate("改掉书级 generator_sha12_1015", lambda b, rows: b.__setitem__(
        "generator_sha12_1015", "deadbeefcafe"))
    _mutate("清空排除项的理由", lambda b, rows: b["discovery"]["excluded"][0].__setitem__(
        "why", ""))
    _mutate("把一行改成跨轮不稳定且没声明", lambda b, rows: rows[0].__setitem__(
        "stable_across_rounds", False))
    _mutate("改掉一行的 committed_sha12", lambda b, rows: rows[0].__setitem__(
        "committed_sha12", "deadbeefcafe"))
    ok = bool(cases) and all(c[1] for c in cases)
    return {"n_cases": len(cases), "cases": [{"name": c[0], "went_red": c[1]}
                                               for c in cases], "ok": ok}


def _prune(obj):
    """⭐⭐⭐⭐⭐ **产物里不许留空列表**（1014 的普查：空列表与「没算过」长得一模一样）
    ⇒ ⇒⇒⇒ ⇒ ⇒ **⇒ 所以空的整条删掉、只留计数** ⇒ ⇒⇒⇒ ⇒ ⇒ **⇒ 「没有这个量」由「键不存在」自证**
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            pv = _prune(v)
            if isinstance(pv, list) and not pv:
                continue
            if pv is None:
                continue
            out[k] = pv
        return out
    if isinstance(obj, list):
        return [_prune(v) for v in obj]
    return obj


def main():
    selftest_mode = "--selftest" in sys.argv
    book_head = _load_book(_read_head)
    book_work = _load_book(_read_worktree)
    out = {"generated_by": SELF,
           "what_this_gate_asks": "**提交的那本 == 探针现在会写的那本**",
           "what_it_is_not": "⇒ ⇒ **这不是「可复现性」** ⇒ ⇒ 1015 的四态答的是「跑两遍会不会变」"
                              "⇒ ⇒ ⇒ ⇒ 而本门答的是「提交的那本是不是【现在】的产物」"
                              "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 两个口径不许合并**"}
    P = {}
    if book_head is None or book_work is None:
        P["P1_committed_bytes_equal_the_bytes_the_probe_wrote_1032n"] = False
        P["P2_this_book_itself_is_what_the_current_script_would_write_1032n"] = False
        P["P3_books_that_change_every_round_must_declare_themselves_1032n"] = False
        P["P4_every_excluded_book_must_publish_a_reason_1032n"] = False
        P["P6_two_implementations_of_the_committed_bytes_must_agree_1032n"] = False
        out["why"] = ["the_book_could_not_be_read"]
    else:
        head = _judge(book_head, _read_head)
        work = _judge(book_work, _read_worktree)
        P["P1_committed_bytes_equal_the_bytes_the_probe_wrote_1032n"] = bool(
            head["ok"] and work["ok"] and head["n_rows"] > 0
            and head["n_unreadable"] == 0 and work["n_unreadable"] == 0)
        P["P2_this_book_itself_is_what_the_current_script_would_write_1032n"] = bool(
            head["script_unchanged"] and work["script_unchanged"]
            and head["n_inputs_changed"] == 0 and work["n_inputs_changed"] == 0)
        P["P3_books_that_change_every_round_must_declare_themselves_1032n"] = bool(
            head["n_undeclared"] == 0 and work["n_undeclared"] == 0)
        P["P4_every_excluded_book_must_publish_a_reason_1032n"] = bool(
            head["n_bad_exclusion"] == 0 and work["n_bad_exclusion"] == 0)
        P["P6_two_implementations_of_the_committed_bytes_must_agree_1032n"] = bool(
            head["n_disagree"] == 0 and work["n_disagree"] == 0)
        st = _selftest(book_work)
        P["P5_this_gate_can_actually_go_red_1032n"] = bool(st["ok"])
        out["head"] = head
        out["worktree"] = work
        out["selftest"] = st
    out["criteria_1032n"] = P
    out["criterion_kinds_1032n"] = CRITERION_KINDS
    out["criterion_kinds_complete_1032n"] = (set(out["criterion_kinds_1032n"])
                                              == set(out["criteria_1032n"]))
    out["n_criteria_1032n"] = len(out["criteria_1032n"])
    out["rule"] = ("⇒ ⇒ **三个量各记各的**：提交态的字节／盘上的字节／这一轮跑出来的字节"
                    "⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 「提交态 == 现在跑出来的那本」＝ 前两者与第三者相等**")
    out = _prune(out)
    GOLDEN.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    bad = [k for k, v in P.items() if v is False]
    print("判据逐条 =", " | ".join("%s=%s" % (k, P[k]) for k in sorted(P)))
    if bad:
        print("P 为假的：", ", ".join(bad))
        return 1
    print("P 为假的： 无 | 共 %d 条 P 判据" % len(P))
    return 0


if __name__ == "__main__":
    sys.exit(main())
