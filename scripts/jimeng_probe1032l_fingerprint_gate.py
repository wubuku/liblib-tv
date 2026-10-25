#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1032-②l —— **指纹表核对门**：1014 那张表必须与盘上的字节逐本对得上

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **1032-②j 收尾时我手工核过一遍「指纹表 30/30 自洽」。**
**⇒ ⇒ ⇒ ⇒ ⇒ 那次核验只活在对话里 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 没有任何人、没有任何门能复查它。**

⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以 ②l 把它变成一道门：**表里每一行的 sha256 与字节数，
必须与盘上那一本书的字节对得上；表必须覆盖盘上的每一本书（不缺、不多）。**

⭐⭐⭐⭐⭐ **两道基线、两个问题**：
  ① **提交态**（`HEAD`）：别人 clone 到的东西自洽吗？
  ② **工作区**：我手头这一版自洽吗？（抓「改了产物却没刷 1014」）

⭐⭐⭐⭐⭐ **为什么不能拿「刚跑完 1014 的状态」当基线**：
门禁清单里 1014 **后面**还有十几个会重写自己产物的探针
⇒ ⇒ ⇒⇒ 「跑完一遍门禁就绿」是**恒真**的假门
⇒ ⇒ ⇒⇒ ⇒ 所以这道门比的是**上一次落盘的那张表**与**盘上的字节**。

⭐⭐⭐⭐⭐ **规则从 1014 的源码里读**（`_EXCLUDED_GENERATORS` / `VOLATILE_INPUTS`）
⇒ ⇒ ⇒⇒ 不在门里另抄一份 ⇒ ⇒ ⇒⇒ ⇒ 两处不会漂移
⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ 一道门必须判「被测对象真的在做什么」。

⭐⭐⭐⭐⭐ `--selftest` 是**注入式反证**：把盘上的东西弄坏六种，
⇒ ⇒ ⇒⇒ ⇒ 每一种都必须让判决翻红 —— 而「抓不住」与「没坏」
⇒ ⇒ ⇒⇒ ⇒ ⇒ 在退出码上长得一模一样 ⇒ ⇒ ⇒⇒ ⇒ ⇒ 所以逐条断言「它红了」。

**纯离线**（只读仓里的文件 ＋ 只读 `git show`）。
"""
import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
RELDIR = "docs/research/jimeng-canvas"
PROBE1014 = ROOT / "scripts/jimeng_probe1014_empty_ambiguity.py"
TABLE_NAME = "empty-ambiguity-1014.json"
GOLDEN = GDIR / "fingerprint-gate-1032l.json"
# ⇒ **本门自己的产物名**（由 GOLDEN 派生 ⇒ 不会与文件名漂移）
SELF_ARTIFACT_NAME = GOLDEN.name

# ⭐⭐⭐⭐⭐ kind 三档（沿用 ②k 的口径）：本门六条**全是 `failure`** ——
#   ⇒ 红了的含义都是「仪器/数据自检没过 ⇒ 要修」
#   ⇒ ⇒⇒ 而没有一条是 `conclusion`（结论被推翻 ⇒ 要重读）
#   ⇒ ⇒⇒ ⇒ 也没有 `precondition`（前提不成立 ⇒ 本次测量不适用）
KINDS_1032L = {
    "P1_every_row_of_the_table_matches_the_bytes_on_disk_1032l": "failure",
    "P2_the_table_covers_every_book_on_disk_1032l": "failure",
    "P3_volatile_is_declared_and_kept_out_of_the_table_1032l": "failure",
    "P4_the_committed_state_is_self_consistent_1032l": "failure",
    "P5_the_working_tree_is_self_consistent_1032l": "failure",
    "P6_this_gate_can_actually_go_red_1032l": "failure",
    "P7_the_table_declares_the_gate_that_checks_it_1032l": "failure",
}


def _sha12(raw):
    return hashlib.sha256(raw).hexdigest()[:12]


def _fp(raw):
    return {"sha256_12": _sha12(raw), "bytes": len(raw)}


# ── 规则：只从 1014 的源码里读，不在本文件里另抄一份 ──────────────────────
def _load_markers(src_text):
    """⭐ 从 1014 的源码 AST 里读出三样规则。

    ⇒ ⇒⇒⇒ **为什么不在门里另抄一份**：另抄 ⇒ 两处会漂移
    ⇒ ⇒⇒⇒ ⇒ 漂移之后这道门拿「过期的排除表」去判
    ⇒ ⇒⇒⇒ ⇒ ⇒ 那它判的就不是 1014 的行为了
    """
    tree = ast.parse(src_text)
    found = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            name = node.targets[0].id
            if name in ("_SELF_MARK", "_EXCLUDED_GENERATORS", "VOLATILE_INPUTS"):
                try:
                    found[name] = ast.literal_eval(node.value)
                except Exception as exc:  # noqa: BLE001
                    raise AssertionError(
                        "⭐ 1014 的 %s 不是字面量（%r）⇒ 门读不到规则" % (name, exc))
    for need in ("_SELF_MARK", "_EXCLUDED_GENERATORS", "VOLATILE_INPUTS"):
        if need not in found:
            raise AssertionError("⭐ 1014 里找不到 %s ⇒ 门读不到规则" % need)
    return {
        "self_mark": found["_SELF_MARK"],
        "excluded": set(found["_EXCLUDED_GENERATORS"]),
        "volatile": set(found["VOLATILE_INPUTS"]),
    }


def _table_of(raw):
    """⭐ 1014 的产物里，那张可核对的表 + 它声明的 volatile。"""
    doc = json.loads(raw.decode("utf-8"))
    ci = doc["census_inputs_2029"]
    table = ci["fingerprints"]
    volatile = set(ci.get("volatile_inputs") or {})
    return table, volatile, ci


# ── 两套「取名 + 取字节」的读取器：工作区与提交态共用同一套扫描 ──────────
class _DirReader:
    def __init__(self, gdir):
        self.gdir = Path(gdir)

    def names(self):
        return sorted(f.name for f in self.gdir.glob("*.json"))

    def read(self, name):
        try:
            return (self.gdir / name).read_bytes()
        except Exception:  # noqa: BLE001
            return None


class _GitReader:
    def __init__(self, sha):
        self.sha = sha

    def names(self):
        # ⭐ `-r` 必须加：不加的话 `ls-tree` 只列出**目录这一项**、扫到 0 本
        #   ⇒ ⇒⇒ ⇒ 而「扫到 0 本」会让表的每一行都变成「幽灵行」
        #   ⇒ ⇒⇒ ⇒ ⇒ 那道门会红，而红的原因与被测对象无关（门自己坏了）
        out = _git("ls-tree", "-r", "--name-only", self.sha, "--", RELDIR)
        names = []
        for line in out.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line.endswith(".json"):
                continue
            # ⭐ 只要**直接**躺在这一层的产品（`inputs/`、`contracts/` 不算）
            if line.rsplit("/", 1)[0] != RELDIR:
                continue
            names.append(line.rsplit("/", 1)[1])
        return sorted(set(names))

    def read(self, name):
        return _git_show(self.sha, RELDIR + "/" + name)


def _git(*args):
    return subprocess.run(["git", "-C", str(ROOT)] + list(args),
                          capture_output=True).stdout


def _git_show(sha, relpath):
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", "%s:%s" % (sha, relpath)],
        capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def _scan(reader):
    """⭐ 扫一遍：每本书的指纹 ＋ 它的 `generated_by`（用来认「被排除的产物」）。"""
    actual, generators = {}, {}
    for name in reader.names():
        raw = reader.read(name)
        if raw is None:
            continue
        actual[name] = _fp(raw)
        gen = None
        try:
            doc = json.loads(raw.decode("utf-8"))
            if isinstance(doc, dict):
                gen = doc.get("generated_by")
        except Exception:  # noqa: BLE001
            gen = None
        generators[name] = gen
    return actual, generators


# ── 判决：纯函数（表、volatile、盘上的字节 ⇒ 对不对得上） ─────────────────
def _judge(table, volatile, actual, generators, excluded_markers):
    """⭐⭐⭐⭐⭐ **纯函数**：一张指纹表与盘上的一堆字节，对不对得上。

    ⇒ ⇒⇒⇒ 六个方向：① 逐行对得上 ② 不缺 ③ 不多
    ⇒ ⇒⇒⇒ ⇒ ④ volatile 必须在盘上 ⑤ volatile 不许进表 ⑥ 被排除的不许进表
    """
    excluded = {n for n, g in generators.items() if g in excluded_markers}
    expected = set(actual) - set(volatile) - excluded
    got = set(table)
    why = []
    missing = sorted(expected - got)
    phantom = sorted(got - expected)
    stale = []
    for name in sorted(got & set(actual)):
        if table[name] != actual[name]:
            stale.append(name)
    gone = sorted(set(volatile) - set(actual))
    leak_vol = sorted(set(volatile) & got)
    leak_exc = sorted(excluded & got)
    if missing:
        why.append("missing_from_the_table:" + ",".join(missing))
    if phantom:
        why.append("phantom_in_the_table:" + ",".join(phantom))
    if stale:
        why.append("row_mismatch:" + ",".join(stale))
    if gone:
        why.append("volatile_not_on_disk:" + ",".join(gone))
    if leak_vol:
        why.append("volatile_leaked_into_the_table:" + ",".join(leak_vol))
    if leak_exc:
        why.append("excluded_leaked_into_the_table:" + ",".join(leak_exc))
    return {
        "ok": not why,
        "why": why,
        "n_table_rows": len(table),
        "n_files_on_disk": len(actual),
        "n_excluded": len(excluded),
        "n_volatile": len(volatile),
        "n_matched": len(got & set(actual)) - len(stale),
        "stale_books": stale,
        "missing_books": missing,
        "phantom_books": phantom,
    }


def _declared_checkers(raw):
    """⇒ **1014 的产物里，它自己声明「谁在查我」**⇒ ⇒ ⇒ ⇒ **⇒ 读不到就当「没声明」**（不猜）。"""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return []
    blk = doc.get("snapshot_and_who_checks_it") or {}
    names = blk.get("who_checks_it") or []
    return [str(x) for x in names]


def _judge_dir(gdir, markers):
    """⭐ 工作区那一侧：读表 → 扫盘 → 判。"""
    reader = _DirReader(gdir)
    raw = reader.read(TABLE_NAME)
    if raw is None:
        return {"ok": False, "why": ["table_artifact_missing"],
                "n_table_rows": 0, "n_files_on_disk": 0, "n_excluded": 0,
                "n_volatile": 0, "n_matched": 0, "stale_books": [],
                "missing_books": [], "phantom_books": []}
    table, volatile, _ci = _table_of(raw)
    actual, generators = _scan(reader)
    verdict = _judge(table, volatile, actual, generators, markers["excluded"])
    verdict["declared_volatile"] = sorted(volatile)
    verdict["source_volatile"] = sorted(markers["volatile"])
    # ⇒ ⇒ ⇒ ⇒ **1032-②m：核「表声明谁在查它」**
    #   ⇒ ⇒ ⇒ ⇒ **⇒ 而这一步在 `_judge` 之后**⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ 免得改掉 `_judge` 的签名（verifier 有锚点钉着）**
    _decl = _declared_checkers(raw)
    verdict["declared_checkers"] = _decl
    verdict["declares_me"] = bool(SELF_ARTIFACT_NAME in _decl)
    if not verdict["declares_me"]:
        verdict["why"].append("table_does_not_declare_this_gate_as_its_checker")
        verdict["ok"] = False
    # ⭐⭐⭐⭐⭐ **「产物里声明的 volatile」与「源码里声明的 volatile」是不是同一批**
    #   ⇒ 这一条**不进 `_judge`** ⇒ ⇒⇒ 因为自检造的那个小世界里
    #   ⇒ ⇒⇒⇒ 它的 volatile 是假的（`v.json`）⇒ ⇒⇒⇒ ⇒ 若塞进判决里
    #   ⇒ ⇒⇒⇒ ⇒ ⇒ 阳性对照会被自己的工具判红 ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ 那就不是「能失败」的证明
    #   ⇒ ⇒⇒⇒ ⇒ 而是「连对的都对不了」
    return verdict


def _judge_head(markers):
    """⭐ 提交态那一侧：`git show HEAD:<path>`（钉在 HEAD 上，不靠工作区）。"""
    sha = _git("rev-parse", "HEAD").decode("utf-8", "replace").strip()
    if not sha:
        return {"ok": False, "why": ["no_head"],
                "n_table_rows": 0, "n_files_on_disk": 0, "n_excluded": 0,
                "n_volatile": 0, "n_matched": 0, "stale_books": [],
                "missing_books": [], "phantom_books": []}
    reader = _GitReader(sha)
    raw = reader.read(TABLE_NAME)
    if raw is None:
        return {"ok": False, "why": ["head_has_no_table_artifact"],
                "n_table_rows": 0, "n_files_on_disk": 0, "n_excluded": 0,
                "n_volatile": 0, "n_matched": 0, "stale_books": [],
                "missing_books": [], "phantom_books": []}
    table, volatile, _ci = _table_of(raw)
    actual, generators = _scan(reader)
    verdict = _judge(table, volatile, actual, generators, markers["excluded"])
    verdict["declared_volatile"] = sorted(volatile)
    _decl = _declared_checkers(raw)
    verdict["declared_checkers"] = _decl
    verdict["declares_me"] = bool(SELF_ARTIFACT_NAME in _decl)
    if not verdict["declares_me"]:
        verdict["why"].append("table_does_not_declare_this_gate_as_its_checker")
        verdict["ok"] = False
    return verdict


# ── 注入式反证：这道门必须**能红** ────────────────────────────────────────
def _write_table(gdir, table, volatile, self_mark):
    """在临时目录里造一张「表」（内容自洽 ⇒ 判决应当是绿的）。"""
    doc = {
        "generated_by": self_mark,
        "census_inputs_2029": {
            "fingerprints": table,
            "volatile_inputs": {k: {"sha256_12": "x", "bytes": 0, "why": "selftest"}
                                for k in sorted(volatile)},
        },
        "snapshot_and_who_checks_it": {"who_checks_it": [SELF_ARTIFACT_NAME]},
    }
    (gdir / TABLE_NAME).write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def _selftest(markers):
    """⭐⭐⭐⭐⭐ **注入式反证**：把盘上的东西弄坏 ⇒ 这道门必须翻红。

    ⇒ ⇒⇒⇒ 六种破坏，每一种都必须被抓住 —— 而「抓不住」和「没坏」
    ⇒ ⇒⇒⇒ 在退出码上长得一模一样 ⇒ ⇒⇒⇒ ⇒ 所以逐条断言「它红了」。
    """
    tmp = Path(tempfile.mkdtemp(prefix="b1032l-selftest-"))
    cases = []
    try:
        # ── 造一个自洽的小世界 ──
        base = tmp / "base"
        base.mkdir()
        (base / "a.json").write_text('{"generated_by": "x.py", "v": 1}\n',
                                     encoding="utf-8")
        (base / "b.json").write_text('{"generated_by": "x.py", "v": 2}\n',
                                     encoding="utf-8")
        (base / "v.json").write_text('{"generated_by": "x.py", "v": 3}\n',
                                     encoding="utf-8")
        table = {}
        for nm in ("a.json", "b.json"):
            table[nm] = _fp((base / nm).read_bytes())
        _write_table(base, table, {"v.json"}, markers["self_mark"])

        pos = _judge_dir(base, markers)
        cases.append({"case": "positive_control_unbroken_world",
                      "want": "green", "ok": bool(pos["ok"]),
                      "why": pos["why"]})

        def _mutate(name, fn):
            d = tmp / name
            shutil.copytree(base, d)
            fn(d)
            v = _judge_dir(d, markers)
            cases.append({"case": name, "want": "red", "ok": (not v["ok"]),
                          "why": v["why"]})

        def _mutate_artifact(d):
            p = d / "a.json"
            p.write_bytes(p.read_bytes() + b"\n")

        def _mutate_row(d):
            doc = json.loads((d / TABLE_NAME).read_text(encoding="utf-8"))
            doc["census_inputs_2029"]["fingerprints"]["a.json"]["sha256_12"] = "000000000000"
            (d / TABLE_NAME).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

        def _drop_row(d):
            doc = json.loads((d / TABLE_NAME).read_text(encoding="utf-8"))
            del doc["census_inputs_2029"]["fingerprints"]["a.json"]
            (d / TABLE_NAME).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

        def _add_phantom(d):
            doc = json.loads((d / TABLE_NAME).read_text(encoding="utf-8"))
            doc["census_inputs_2029"]["fingerprints"]["ghost.json"] = {
                "sha256_12": "abcdefabcdef", "bytes": 7}
            (d / TABLE_NAME).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

        def _volatile_into_table(d):
            doc = json.loads((d / TABLE_NAME).read_text(encoding="utf-8"))
            doc["census_inputs_2029"]["fingerprints"]["v.json"] = _fp(
                (d / "v.json").read_bytes())
            (d / TABLE_NAME).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

        def _delete_artifact(d):
            (d / "b.json").unlink()

        def _declaration_points_at_someone_else(d):
            doc = json.loads((d / TABLE_NAME).read_text(encoding="utf-8"))
            doc["snapshot_and_who_checks_it"]["who_checks_it"] = ["someone_else.py"]
            (d / TABLE_NAME).write_text(json.dumps(doc, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

        _mutate("mutate_one_artifact_on_disk", _mutate_artifact)
        _mutate("declaration_points_at_someone_else",
                _declaration_points_at_someone_else)
        _mutate("mutate_one_row_of_the_table", _mutate_row)
        _mutate("drop_one_row_of_the_table", _drop_row)
        _mutate("add_one_phantom_row", _add_phantom)
        _mutate("put_the_volatile_book_into_the_table", _volatile_into_table)
        _mutate("delete_one_artifact_from_disk", _delete_artifact)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = bool(cases) and all(c["ok"] for c in cases)
    return {"ok": ok, "n_cases": len(cases), "cases": cases}


def _criteria(work, head, st, vol_matches_source):
    """⭐ 六条判据（全部关系式，不钉绝对数）。"""
    wt_rows_ok = (not work["stale_books"])
    hd_rows_ok = (not head["stale_books"])
    wt_cover_ok = (not work["missing_books"]) and (not work["phantom_books"])
    hd_cover_ok = (not head["missing_books"]) and (not head["phantom_books"])
    vol_ok = (
        bool(vol_matches_source)
        and not any(w.startswith("volatile_") for w in work["why"])
        and not any(w.startswith("volatile_") for w in head["why"]))
    return {
        "P1_every_row_of_the_table_matches_the_bytes_on_disk_1032l":
            bool(wt_rows_ok and hd_rows_ok),
        "P2_the_table_covers_every_book_on_disk_1032l":
            bool(wt_cover_ok and hd_cover_ok),
        "P3_volatile_is_declared_and_kept_out_of_the_table_1032l":
            bool(vol_ok),
        "P4_the_committed_state_is_self_consistent_1032l":
            bool(head["ok"]),
        "P5_the_working_tree_is_self_consistent_1032l":
            bool(work["ok"]),
        "P6_this_gate_can_actually_go_red_1032l":
            bool(st["ok"]),
        # ⇒ ⇒ ⇒ ⇒ **1032-②m：**表必须声明「谁在查它」**
        #   ⇒ ⇒ ⇒ ⇒ **⇒ 而「声明」若没人核、它就退化成散文**
        #   ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ 而「散文说明」与「没算过」在产物里长得一模一样**
        "P7_the_table_declares_the_gate_that_checks_it_1032l":
            bool(work.get("declares_me") and head.get("declares_me")),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true",
                        help="只跑注入式反证（不写产物）")
    parser.add_argument("--dir", default=str(GDIR),
                        help="换掉被检查的目录（注入用）")
    # 1015 会带着 `--write-golden` 跑每一本 ⇒ 这个门必须**认**它（而不是报错）
    parser.add_argument("--write-golden", action="store_true",
                        help="兼容 1015 的统一调用（本门永远写仓内产物）")
    args = parser.parse_args(argv)

    markers = _load_markers(PROBE1014.read_text(encoding="utf-8"))
    gdir = Path(args.dir)
    work = _judge_dir(gdir, markers)
    head = _judge_head(markers)
    st = _selftest(markers)
    vol_matches_source = (set(work.get("declared_volatile") or [])
                           == set(markers["volatile"]))
    crit = _criteria(work, head, st, vol_matches_source)

    print("— 1032-②l 指纹表核对门")
    print("   表：%s（%d 行）  盘上 %d 本  被排除 %d 本  volatile %d 本"
          % (TABLE_NAME, work["n_table_rows"], work["n_files_on_disk"],
             work["n_excluded"], work["n_volatile"]))
    print("   工作区：%s%s" % ("绿" if work["ok"] else "红",
                              "" if work["ok"] else "  " + "; ".join(work["why"])))
    print("   提交态：%s%s" % ("绿" if head["ok"] else "红",
                              "" if head["ok"] else "  " + "; ".join(head["why"])))
    if work["stale_books"]:
        print("   ⭐ 过期（表里记的那一版已经不是盘上那一版了）：%d 本 %s"
              % (len(work["stale_books"]), ", ".join(work["stale_books"])))
    print("   反证：%d 例，%s" % (st["n_cases"], "全过" if st["ok"] else "有漏网的"))

    if args.selftest:
        for c in st["cases"]:
            print("     [%s] %s" % ("OK" if c["ok"] else "FAIL", c["case"]))
        print("PROBE_1032L_SELFTEST_OK" if st["ok"] else "PROBE_1032L_SELFTEST_FAIL")
        return 0 if st["ok"] else 1

    payload = {
        "generated_by": "jimeng_probe1032l_fingerprint_gate.py",
        "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **指纹表核对门**：1014 那张表"
                "必须与盘上的字节逐本对得上",
        "rule": "⭐⭐⭐⭐⭐ **表里每一行的 sha256_12 与 bytes 必须等于盘上那一本的"
                "实际字节；表必须覆盖盘上的每一本书（不缺、不多）；"
                "volatile 必须在盘上、且被挡在表外**",
        "table_artifact": RELDIR + "/" + TABLE_NAME,
        "n_table_rows": work["n_table_rows"],
        "n_files_on_disk": work["n_files_on_disk"],
        "n_excluded_from_the_table": work["n_excluded"],
        "n_volatile": work["n_volatile"],
        # ⭐⭐⭐⭐⭐ 2026-10-25：**本产物每轮都会变** ⇒ ⇒ 必须自己声明（1032n 判据③）
        "volatile": True,
        "volatile_why": "⭐⭐⭐⭐⭐ 本产物记的是**全目录的文件指纹表**"
                        "⇒ ⇒ ⇒⇒ 目录里任何一本书变了 ⇒ ⇒ ⇒⇒ 指纹表就变 "
                        "⇒ ⇒ ⇒⇒ ⇒ ⇒ **⇒ 而它自己写盘也会改到别人的指纹** "
                        "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ **所以它必然每轮都变** ⇒ ⇒ ⇒⇒ ⇒ ⇒ "
                        "⇒ ⇒ ⇒ **必须自己声明**，否则跨轮稳定性的账"
                        "会把「面变了」记成「出问题了」。",
        "worktree": {
            "ok": work["ok"],
            "n_matched": work["n_matched"],
            "n_stale": len(work["stale_books"]),
            "stale_books": work["stale_books"],
            "missing_books": work["missing_books"],
            "phantom_books": work["phantom_books"],
            "why": work["why"],
        },
        "head": {
            "ok": head["ok"],
            "n_matched": head["n_matched"],
            "n_stale": len(head["stale_books"]),
            "stale_books": head["stale_books"],
            "missing_books": head["missing_books"],
            "phantom_books": head["phantom_books"],
            "why": head["why"],
        },
        "selftest": {
            "ok": st["ok"],
            "n_cases": st["n_cases"],
            "cases": [{"case": c["case"], "want": c["want"], "ok": c["ok"]}
                      for c in st["cases"]],
        },
        "P": crit,
        "criterion_kinds_1032l": KINDS_1032L,
        "criterion_kinds_complete_1032l": True,
    }
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("判据逐条 = " + " | ".join("%s=%s" % (k, crit[k])
                                     for k in sorted(crit)))
    print("PROBE_1032L_FINGERPRINT_GATE_DONE ->", GOLDEN)
    all_ok = all(crit.values())
    print("PROBE_1032L_FINGERPRINT_GATE_OK" if all_ok
          else "PROBE_1032L_FINGERPRINT_GATE_RED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
