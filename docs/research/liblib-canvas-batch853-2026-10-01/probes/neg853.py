#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法（沿用 851／852 的形态）

★ 门禁 S1–S11 读的是四类东西：**clone 源码文本** ＋ **clone 读数 JSON**
＋ **源站读数 JSON** ＋ **契约 JSON**。
⟹ ⟹ 所以阴性就改「该判据**独占读取**的字段」⟹ ⟹ 改完跑一次门禁 ⟹ ⟹
断言「**恰好**只有目标判据翻红」⟹ ⟹ 全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 源码 rules：`if (!modifier) return null` ⟹ `if (modifier) return null` | S4 |
| N2 | 源码 desk：`else ungroupSelectedCharacters()` ⟹ `else groupSelectedCharacters()` | S1 |
| N3 | 源码 rules：`d` 的返回值改成恒为 `"ungroup"`（⟹ ⌘D 也解组） | S4 |
| N4 | clone 读数：`③⌘D` 的「按后.DOM组数」（假装它解了组） | S5 |
| N5 | clone 读数：`④⌘⇧D` 的「按后.store选中组」（假装没清空） | S6 |
| N6 | clone 读数：`⑦⌘G` 的「按后.DOM组数」（假装没建组） | S7 |
| N7 | clone 读数：`⑧裸G` 的「按后.DOM组数」 | S8 |
| N8 | 契约：`sg` 片段里去掉 `"camera"===e`（⟹ 源站不许装机位） | S2 |
| N9 | 契约：修饰键条件里 `d` 段去掉 `||e.metaKey`（⟹ 矩阵变了） | S3 |
| N10 | clone 读数：`⑩⌘⇧G` 的「按后.DOM组数」（假装没解组） | S9 |
| N11 | 源站读数：`③行数变化`（⟹ 假装源站 ⌘G 没建组） | S10 |
| N12 | clone 面板源码：`group-key` 的字母 G ⟹ H | S11 |

★ ★★ **字段互不重叠**是这套阴性能成立的前提 ⟹ ⟹ 所以：
  - S2 只断言**除两段 keydown 原文之外**的片段 ⟹ ⟹ N9 改的正是那两段 ⟹ ⟹ 只翻 S3；
  - S5–S9 各自读 clone raw 里**不同的键**（③／④／⑦／⑧⑨／⑩）⟹ ⟹ 互不影响；
  - S1 只断言「某几个字符串在不在」⟹ ⟹ N2 改的是**另一个**字符串 ⟹ ⟹ 只翻 S1；
  - S4 只读**纯函数的运行结果** ⟹ ⟹ N1／N3 改的是函数体 ⟹ ⟹ 不影响别的判据。

★ ★ N8／N9 改的是**契约 JSON** ⟹ ⟹ 它们证明 S2／S3 **真的在读那两段**，
  ⟹ ⟹ 也就是说：那份契约必须是**机器提取**的，手抄的会骗人。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"
SRC_RULES = ROOT / "src/components/director/directorShortcutRules.ts"
SRC_DESK = ROOT / "src/components/director/DirectorDesk.tsx"
SRC_DIALOG = ROOT / "src/components/director/DirectorShortcutsDialog.tsx"
CLONE_RAW = RAW / "clone-853-groupkeys.json"
SRC_RAW = RAW / "source-853-groupkeys.json"
CONTRACT_RAW = RAW / "source-853-contract.json"
GATE = ROOT / "scripts/verify-liblib-batch853.py"

J_S1 = "S1 结构：打组/解组纯函数 ＋ DirectorDesk 接线 ＋ 依赖数组都在"
J_S2 = "S2 契约：16 个片段唯一命中 ＋ 源站原文逐字对得上"
J_S3 = "S3 矩阵：提取器与门禁两套独立实现给出同一张表"
J_S4 = "S4 纯函数：16 格动作表（node 实跑，期望值取自契约矩阵）"
J_S5 = "S5 clone 按 ⌘D ⟹ **什么都不做**（逐字段比对按前/按后）"
J_S6 = "S6 clone 按 ⌘⇧D ⟹ 解组（DOM 组数 1→0 ＋ store 选中组清空 ＋ DELETE_GROUP）"
J_S7 = "S7 clone 按 ⌘G ⟹ 打组（DOM 组数 0→1 ＋ 选中组指向新组 ＋ GROUP_CHARACTERS）"
J_S8 = "S8 clone 裸 G ／ 裸 D ⟹ **什么都不做**（两组各逐字段比对）"
J_S9 = "S9 clone 按 ⌘⇧G ⟹ 解组（★ 源站面板没列这个别名，但逐字行为成立）"
J_S10 = "S10 源站实测：⌘G 建组（只有成员被缩进）＋ ⌘D 无 ＋ ⌘⇧D 解组回到基线"
J_S11 = "S11 面板：打组 ⌘G ／ 解组 ⌘⇧D 两行与源站逐字一致"


def run_gate():
    r = subprocess.run(
        [sys.executable, str(GATE)], capture_output=True, text=True, cwd=str(ROOT)
    )
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {}
    # ★ 兼容两种键名（门禁写「判据」，早期写法是「结果」）⟹ ⟹ 免得读空集合却报「没翻红」
    items = report.get("判据") or report.get("结果") or []
    failed = [x["判据"] for x in items if not x["通过"]]
    return failed, report, r.stdout


def patch_text(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit("★ 变异目标没找到：%s ⟹ %r" % (path.name, old))
    if text.count(old) != 1:
        raise SystemExit(
            "★ 变异目标出现 %d 次（必须唯一）：%r" % (text.count(old), old)
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_json(path, mutate):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    targets = [SRC_RULES, SRC_DESK, SRC_DIALOG, CLONE_RAW, SRC_RAW, CONTRACT_RAW]
    backups = {p: p.read_bytes() for p in targets}

    baseline_failed, baseline_report, _ = run_gate()
    print("基线：%d/%d 通过，失败=%s"
          % (baseline_report.get("通过数", 0), baseline_report.get("判据总数", 0),
             baseline_failed))
    if baseline_failed:
        print("★ 基线不绿，先修门禁")
        return 1

    cases = []

    def run_case(name, target_judge, apply_fn):
        apply_fn()
        failed, report, _ = run_gate()
        only = set(failed) == {target_judge}
        cases.append({"阴性": name, "目标判据": target_judge,
                      "实际翻红": failed, "恰好一条": only,
                      "通过": only and len(failed) == 1})
        print("  %-4s %-6s 目标=%s 实际=%s %s"
              % (name, "OK" if only else "BAD", target_judge[:14], failed,
                 "" if only else "★★ 不是恰好一条"))

    # ══ N1：把「没按修饰键就什么都不做」反过来 ⟹ 裸 G 也会打组 ⟹ S4
    def n1():
        patch_text(SRC_RULES, "  if (!modifier) return null;",
                   "  if (modifier) return null;")
    run_case("N1", J_S4, n1)
    _restore(SRC_RULES, backups[SRC_RULES])

    # ══ N2：把「解组」接成「打组」⟹ 接线不再匹配 ⟹ S1
    def n2():
        patch_text(SRC_DESK, "        else ungroupSelectedCharacters();",
                   "        else groupSelectedCharacters();")
    run_case("N2", J_S1, n2)
    _restore(SRC_DESK, backups[SRC_DESK])

    # ══ N3：`d` 恒返回 ungroup ⟹ ⌘D 也会解组 ⟹ S4
    def n3():
        patch_text(SRC_RULES, '  if (key === "d") return shift ? "ungroup" : null;',
                   '  if (key === "d") return "ungroup";')
    run_case("N3", J_S4, n3)
    _restore(SRC_RULES, backups[SRC_RULES])

    # ══ N4：假装 ⌘D 解了组 ⟹ S5
    def n4():
        def m(d):
            d["③⌘D 不做"]["按后"]["DOM组数"] = 0
        patch_json(CLONE_RAW, m)
    run_case("N4", J_S5, n4)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N5：假装 ⌘⇧D 没清空选中组 ⟹ S6
    def n5():
        def m(d):
            d["④⌘⇧D 解组"]["按后"]["store选中组"] = "director-character-group-x"
        patch_json(CLONE_RAW, m)
    run_case("N5", J_S6, n5)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N6：假装 ⌘G 没建组 ⟹ S7
    def n6():
        def m(d):
            d["⑦⌘G 打组"]["按后"]["DOM组数"] = 0
        patch_json(CLONE_RAW, m)
    run_case("N6", J_S7, n6)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N7：假装裸 G 建了组 ⟹ S8
    def n7():
        def m(d):
            d["⑧裸G 不做"]["按后"]["DOM组数"] = 0
        patch_json(CLONE_RAW, m)
    run_case("N7", J_S8, n7)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N8：契约里的 sg 去掉 camera ⟹ S2
    def n8():
        def m(d):
            key = "可分组类别 sg(e)（character/prop/emptyObject/camera）"
            d["片段"][key]["原文"] = d["片段"][key]["原文"].replace(
                '||"camera"===e', "")
        patch_json(CONTRACT_RAW, m)
    run_case("N8", J_S2, n8)
    _restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ N9：契约里的修饰键条件改 `d` 段 ⟹ 矩阵变了 ⟹ S3
    def n9():
        def m(d):
            key = "keydown 里 hY 块的修饰键条件（g / d 两段）"
            d["片段"][key]["原文"] = d["片段"][key]["原文"].replace(
                'e.shiftKey&&(e.ctrlKey||e.metaKey)', 'e.shiftKey&&e.ctrlKey')
        patch_json(CONTRACT_RAW, m)
    run_case("N9", J_S3, n9)
    _restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ N10：假装 ⌘⇧G 没解组 ⟹ S9
    def n10():
        def m(d):
            d["⑩⌘⇧G 解组"]["按后"]["DOM组数"] = 1
        patch_json(CLONE_RAW, m)
    run_case("N10", J_S9, n10)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N11：假装源站 ⌘G 没建组 ⟹ S10
    def n11():
        def m(d):
            d["③行数变化"] = 0
        patch_json(SRC_RAW, m)
    run_case("N11", J_S10, n11)
    _restore(SRC_RAW, backups[SRC_RAW])

    # ══ N12：clone 面板的「打组」字母改成 H ⟹ S11
    def n12():
        patch_text(SRC_DIALOG, '{ id: "group-key", label: "G" },',
                   '{ id: "group-key", label: "H" },')
    run_case("N12", J_S11, n12)
    _restore(SRC_DIALOG, backups[SRC_DIALOG])

    # ══ 复原验证（★ 字节级）
    restore_ok = all(p.read_bytes() == backups[p] for p in targets)
    print("\n复原（字节级）：%s" % ("OK" if restore_ok else "★ 失败"))
    ok_count = sum(1 for c in cases if c["通过"])
    print("== batch 853 阴性对照：%d/%d 通过 ==" % (ok_count, len(cases)))

    audit = {
        "批次": 853,
        "阴性总数": len(cases),
        "通过数": ok_count,
        "复原字节级一致": restore_ok,
        "结果": cases,
    }
    (BATCH / "negative-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")

    if ok_count != len(cases) or not restore_ok:
        return 1
    # ★ 复原后必须把门禁跑回绿（★ runtime-audit.json 也要留下**绿**的那份）
    failed, report, _ = run_gate()
    print("复原后门禁：%d/%d 通过，失败=%s"
          % (report.get("通过数", 0), report.get("判据总数", 0), failed))
    return 1 if failed else 0


def _restore(path, data: bytes):
    path.write_bytes(data)


if __name__ == "__main__":
    sys.exit(main())
