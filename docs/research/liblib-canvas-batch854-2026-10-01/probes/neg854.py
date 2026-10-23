#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法（沿用 851／852／853 的形态）

★ 门禁 S1–S11 读的是五类东西：**clone 源码文本** ＋ **clone 读数 JSON**
＋ **源站读数 JSON** ＋ **契约 JSON** ＋ **可达性 JSON**。
⟹ ⟹ 所以阴性就改「该判据**独占读取**的字段」⟹ ⟹ 改完跑一次门禁 ⟹ ⟹
断言「**恰好**只有目标判据翻红」⟹ ⟹ 全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 源码 tree：成员行的 kind 属性改名（DOM 上就读不到类别了） | S1 |
| N2 | 契约：`sg` 片段里去掉 `"camera"===e`（⟹ 源站不许装机位） | S2 |
| N3 | clone 读数：`④打组后.DOM组员[0].文本x`（假装缩进不是 16） | S3 |
| N4 | clone 读数：`④打组后.store组员[0].kind`（假装组员的类别错了） | S4 |
| N5 | clone 读数：`④打组后.展开容器数` ＝ 0（假装组默认折叠） | S5 |
| N6 | clone 读数：`④打组后.DOM对象行` 少一行（假装成员还在类别分区） | S6 |
| N7 | clone 读数：`⑤解组后.DOM组数` ＝ 1（假装没解组） | S7 |
| N8 | clone 读数：`⑥shift加选道具后.store选中对象` 少一个（假装 ⇧ 加选失效） | S8 |
| N9 | 源站读数：`⑤⌘G后类别`（假装源站的组不含机位） | S9 |
| N10 | 源码 document：把 members／characterIds 的**先后顺序**反过来 | S10 |
| N11 | 可达性读数：`③导演台有树` ＝ False | S11 |
| N12 | 源站读数：`⑤⌘G后行[1].rowX`（假装源站的行元素缩进不是 0） | S3 |

★ ★★ **字段互不重叠**是这套阴性能成立的前提 ⟹ ⟹ 所以：
  - S1 只断言**符号存在** ⟹ ⟹ N1 改的是**属性名** ⟹ ⟹ 别的判据都不读它；
  - S2 只读契约 ⟹ ⟹ N2 改契约 ⟹ ⟹ 别的判据不读契约里那一段；
  - S3 读**源站与 clone 的缩进量** ⟹ ⟹ N3 改 clone 侧、N12 改源站侧 ⟹ ⟹ 互不影响；
  - S4–S8 各读 clone raw 里**不同的键／不同的字段** ⟹ ⟹ 互不影响；
  - S9 只读源站 raw 的**类别／标签／基线** ⟹ ⟹ N9 不碰 S3 读的那几行；
  - S10 读**两个纯函数的运行结果** ⟹ ⟹ N10 改函数体 ⟹ ⟹ 不影响别的判据；
  - S11 只读可达性 raw。

★ ★ N2／N3／N9／N12 改的是**入库的读数／契约** ⟹ ⟹ 它们证明 S2／S3／S9
★   **真的在读那几处** ⟹ ⟹ 也就是说：那些 JSON 必须是**机器提取／实测**的，
★   手抄的会骗人。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"
SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_TREE = ROOT / "src/components/director/DirectorObjectTree.tsx"
SRC_DOC = ROOT / "src/lib/directorProjectDocument.ts"
CLONE_RAW = RAW / "clone-854-groupmembers.json"
SRC_RAW = RAW / "source-854-groupmembers.json"
CONTRACT_RAW = RAW / "source-854-contract.json"
REACH_RAW = RAW / "clone-854-reachability.json"
GATE = ROOT / "scripts/verify-liblib-batch854.py"

J_S1 = "S1 结构：成员类型／可分组类别／两个解析器／树侧接线都在"
J_S2 = "S2 契约：17 个片段唯一命中 ＋ 源站原文逐字对得上"
J_S3 = "S3 几何：**同粒度**的缩进量，源站与 clone 逐层相等（文本 +16 ／ 行元素 0）"
J_S4 = "S4 clone：组的成员 ＝ 被选中的那两个对象（跨类别，id＋kind 逐个相等）"
J_S5 = "S5 clone：组**默认展开**（成员子行直接可见）"
J_S6 = "S6 clone：入组后成员**从自己的类别分区里消失**"
J_S7 = "S7 clone：解组后**逐字回到基线**（组没了 ＋ 对象行逐个回来）"
J_S8 = "S8 clone：**⇧+点击**也能加选（第二个修饰键）"
J_S9 = "S9 源站实测：⌘G 建出**跨类别**的组（机位＋角色）＋ 解组回到基线"
J_S10 = "S10 文档层：members 优先／characterIds 兜底／去重（两套实现交叉验证）"
J_S11 = "S11 可达性：**从根地址无参**进入 ⟹ 打开导演台 ⟹ 树／对象行／rail／可交互元素都在"


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
    targets = [SRC_STORE, SRC_TREE, SRC_DOC, CLONE_RAW, SRC_RAW, CONTRACT_RAW,
               REACH_RAW]
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

    # ══ N1：成员行的 kind 属性改名 ⟹ DOM 上读不到类别 ⟹ S1
    def n1():
        patch_text(SRC_TREE,
                   "data-director-group-member-kind={member.kind}",
                   "data-director-group-member-type={member.kind}")
    run_case("N1", J_S1, n1)
    _restore(SRC_TREE, backups[SRC_TREE])

    # ══ N2：契约里的 sg 去掉 camera ⟹ S2
    def n2():
        def m(d):
            key = "可分组类别 sg(e)"
            d["片段"][key]["原文"] = d["片段"][key]["原文"].replace(
                '||"camera"===e', "")
        patch_json(CONTRACT_RAW, m)
    run_case("N2", J_S2, n2)
    _restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ N3：假装 clone 的成员缩进不是 16 ⟹ S3
    def n3():
        def m(d):
            d["④打组后"]["DOM组员"][0]["文本x"] = \
                d["④打组后"]["DOM组员"][0]["文本x"] - 1
        patch_json(CLONE_RAW, m)
    run_case("N3", J_S3, n3)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N4：假装组员的类别错了 ⟹ S4
    def n4():
        def m(d):
            d["④打组后"]["store组员"][0]["kind"] = "character"
        patch_json(CLONE_RAW, m)
    run_case("N4", J_S4, n4)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N5：假装组默认折叠 ⟹ S5
    def n5():
        def m(d):
            d["④打组后"]["展开容器数"] = 0
        patch_json(CLONE_RAW, m)
    run_case("N5", J_S5, n5)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N6：假装成员还在类别分区里 ⟹ S6
    def n6():
        def m(d):
            d["④打组后"]["DOM对象行"] = d["④打组后"]["DOM对象行"][:-1]
        patch_json(CLONE_RAW, m)
    run_case("N6", J_S6, n6)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N7：假装没解组 ⟹ S7
    def n7():
        def m(d):
            d["⑤解组后"]["DOM组数"] = 1
        patch_json(CLONE_RAW, m)
    run_case("N7", J_S7, n7)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N8：假装 ⇧ 加选失效 ⟹ S8
    def n8():
        def m(d):
            d["⑥shift加选道具后"]["store选中对象"] = \
                d["⑥shift加选道具后"]["store选中对象"][:1]
        patch_json(CLONE_RAW, m)
    run_case("N8", J_S8, n8)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N9：假装源站的组里没有机位 ⟹ S9
    def n9():
        def m(d):
            d["⑤⌘G后类别"] = ["other" if k == "camera" else k
                              for k in d["⑤⌘G后类别"]]
        patch_json(SRC_RAW, m)
    run_case("N9", J_S9, n9)
    _restore(SRC_RAW, backups[SRC_RAW])

    # ══ N10：把 document 层 members／characterIds 的先后反过来 ⟹ S10
    def n10():
        patch_text(
            SRC_DOC,
            '  (group.members ?? []).forEach((member) => push(member.kind, member.id));\n'
            '  group.characterIds.forEach((id) => push("character", id));',
            '  group.characterIds.forEach((id) => push("character", id));\n'
            '  (group.members ?? []).forEach((member) => push(member.kind, member.id));',
        )
    run_case("N10", J_S10, n10)
    _restore(SRC_DOC, backups[SRC_DOC])

    # ══ N11：假装导演台没有树 ⟹ S11
    def n11():
        def m(d):
            d["③导演台有树"] = False
        patch_json(REACH_RAW, m)
    run_case("N11", J_S11, n11)
    _restore(REACH_RAW, backups[REACH_RAW])

    # ══ N12：假装源站的行元素缩进不是 0 ⟹ S3
    def n12():
        def m(d):
            d["⑤⌘G后行"][1]["rowX"] = d["⑤⌘G后行"][1]["rowX"] + 4
        patch_json(SRC_RAW, m)
    run_case("N12", J_S3, n12)
    _restore(SRC_RAW, backups[SRC_RAW])

    # ══ 复原验证（★ 字节级）
    restore_ok = all(p.read_bytes() == backups[p] for p in targets)
    print("\n复原（字节级）：%s" % ("OK" if restore_ok else "★ 失败"))
    ok_count = sum(1 for c in cases if c["通过"])
    print("== batch 854 阴性对照：%d/%d 通过 ==" % (ok_count, len(cases)))

    audit = {
        "批次": 854,
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
