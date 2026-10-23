#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 855 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法（沿用 851／852／853／854 的形态）

★ 门禁 S1–S13 读的是六类东西：**clone 源码文本** ＋ **clone 读数 JSON**
＋ **契约 JSON** ＋ **可达性 JSON** ⟹ ⟹ 所以阴性就改「该判据**独占读取**的
字段」⟹ ⟹ 改完跑一次门禁 ⟹ ⟹ 断言「**恰好**只有目标判据翻红」⟹ ⟹
全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 源码 store：组轨道 rig 的调用点改名 | S1 |
| N2 | 契约：锚点片段的逐字被改 | S2 |
| N3 | clone 读数：`④判定.组characterIds` 混进了机位（不再是派生量） | S3 |
| N4 | clone 读数：`⑤判定.组轨道memberOffsets键` 少了机位 | S4 |
| N5 | clone 读数：受控检查里**角色**的后位置不是纯平移期望 | S5 |
| N6 | clone 读数：受控检查里**机位**的后位置变了 | S6 |
| N7 | clone 读数：`⑩判定.★成员x位移` 里道具的位移与角色不同 | S7 |
| N8 | clone 读数：`⑨判定.★选中态＝全部成员` ＝ false | S8 |
| N9 | 源码 math：把 rig 的纯平移改成「偏移 ×2」 | S9 |
| N10 | 源码 document：组轨道键集退回「只按角色」 | S10 |
| N11 | 源码 planner：轨道 closure 退回「只按角色」 | S11 |
| N12 | 源码 store：把锁定守卫退回「只认角色」的旧写法 | S12 |
| N13 | 可达性读数：`路径A_导演台.有场景树` ＝ false | S13 |
| N14 | 源码 store：建组路径的选中态退回「只认角色」 | S14 |
| N15 | **老门禁 `87.mjs`**：把迁移后的判据改回旧写法 | S15 |

★ ★★ **字段互不重叠**是这套阴性能成立的前提 ⟹ ⟹ 所以：
  - S1 只断言**符号存在**（store 里的 rig 调用点／两个解析器）⟹ ⟹
    N1 改的是 **store 的调用点**，N10／N11 改的是 **document／planner 的函数体**
    ⟹ ⟹ 互不影响；
  - S2 只读契约 ⟹ ⟹ N2 改契约 ⟹ ⟹ 别的判据不读契约里那一段；
  - S3 读 `④判定` ⟹ ⟹ N3 改 `组characterIds` ⟹ ⟹ S4 读的是 `⑤判定` ＋
    `④判定.组成员`（**成员列表**）⟹ ⟹ 改 `characterIds` 不影响 S4；
  - S4–S8 各读 clone raw 里**不同的键** ⟹ ⟹ 互不影响；
  - S9 只读 `math` 源 ⟹ ⟹ N9 改 `math` 的 rig 公式 ⟹ ⟹ S1 读的是
    **符号存在性**（函数名还在）⟹ ⟹ 不受影响；
  - S10 只读 document 的**具体用法** ⟹ ⟹ S11 只读 planner 的**具体用法**；
  - S12 只读 store 的锁定守卫形状；
  - S13 只读可达性 raw。

★ ★ **N2／N3／N4／N5／N6／N7／N8／N13 改的是「入库的读数／契约」**
  ⟹ ⟹ 它们证明 S2／S3–S8／S13 **真的在读那几处** ⟹ ⟹ 也就是说：那些 JSON
  必须是**机器提取／实测**的，手抄的会骗人。

★ ★★ **行数中性**：所有源码变异都是**同一行内**的等长替换 ⟹ ⟹ 文件行数
   不变 ⟹ ⟹ 复原时能**字节级**校验。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch855-2026-10-01"
RAW = BATCH / "raw"
SRC_MATH = ROOT / "src/components/director/directorGroupMath.ts"
SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_DOC = ROOT / "src/lib/directorProjectDocument.ts"
SRC_PLANNER = ROOT / "src/lib/directorDeletePlanner.ts"
CLONE_RAW = RAW / "clone-855-grouprig.json"
CONTRACT_RAW = RAW / "source-855-contract.json"
REACH_RAW = RAW / "reachability-855.json"
GATE = ROOT / "scripts/verify-liblib-batch855.py"
# ★ 老门禁 87.mjs（★ 本批把它的判据迁移了 ⟹ ⟹ S15 要盯住这件事）
GATE_87 = ROOT / "scripts/verify-liblib-batch87.mjs"

J = {
    "S1": "S1 源码结构：权威列表／rig／守卫／文档层／规划器",
    "S2": "S2 契约：8 个片段唯一命中 ＋ 4 条关键逐字 ＋ 任意值自检",
    "S3": "S3 组成员含机位 ＋ characterIds 只是派生量",
    "S4": "S4 组轨道 memberOffsets 键集 ＝ 全部成员（含机位）",
    "S5": "S5 rig 是纯平移：位置＝关键帧位置＋成员偏移，rotation／scale 不变",
    "S6": "S6 机位入组后不被组轨道带动（源站 rig 无 camera 分支）",
    "S7": "S7 道具也跟组动，且与角色的位移相同（纯平移）",
    "S8": "S8 解组：组／组轨道都没了、成员都在、选中态＝全部成员、selectedGroupId 空",
    "S9": "S9 独立实现（抽成 JS 跑 node）：锚点／偏移／rig 逐字",
    "S10": "S10 文档层：组轨道 memberOffsets 键集按全部成员校验",
    "S11": "S11 删除规划器：轨道 closure 按全部成员保留偏移",
    "S12": "S12 锁定守卫：组关键帧按全部成员判锁（旧的「只认角色」写法清零）",
    "S13": "S13 可达性：根地址无参可达 ＋ 导演台可交互",
    "S14": "S14 选中态：按全部成员算（旧写法清零 ＋ 建组按权威成员列表）",
    "S15": "S15 旧门禁 87.mjs：判据已迁移（旧写法清零 ＋ 有负向断言）",
}


def run_gate():
    r = subprocess.run(
        [sys.executable, str(GATE)], capture_output=True, text=True, cwd=str(ROOT)
    )
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {}
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
    before_lines = text.count("\n")
    blob = path.read_bytes()
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    after_lines = path.read_text(encoding="utf-8").count("\n")
    if before_lines != after_lines:
        # ★★ **当场回滚** ⟹ ⟹ 变异不是行数中性时，**不能把变异留在仓库里**
        #   （本批踩过一次：`SystemExit` 把文件留在变异态 ⟹ ⟹ 文档层被改回旧写法
        #    却没人发现 ⟹ ⟹ 门禁 S10 变红才暴露出来）
        path.write_bytes(blob)
        raise SystemExit(
            "★ 变异不是行数中性（已回滚）：%d → %d 行" % (before_lines, after_lines)
        )


def patch_json(path, mutate):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def restore(path, blob):
    path.write_bytes(blob)
    if path.read_bytes() != blob:
        raise SystemExit("★ 复原失败（字节级校验没过）：%s" % path.name)


def main() -> int:
    targets = [SRC_MATH, SRC_STORE, SRC_DOC, SRC_PLANNER, CLONE_RAW,
               CONTRACT_RAW, REACH_RAW, GATE_87]
    backups = {p: p.read_bytes() for p in targets}

    baseline_failed, baseline_report, _ = run_gate()
    total = len(baseline_report.get("判据", []))
    print("基线：%d/%d 通过，失败=%s" % (total - len(baseline_failed), total,
                                       baseline_failed))
    if baseline_failed:
        print("★ 基线不绿，先修门禁")
        return 1

    cases = []

    def run_case(name, key, apply_fn):
        apply_fn()
        failed, _, _ = run_gate()
        target = J[key]
        only = set(failed) == {target}
        cases.append({"阴性": name, "目标判据": target, "实际翻红": failed,
                      "恰好一条": only, "通过": only and len(failed) == 1})
        print("  %-4s %-4s 目标=%s 实际=%s %s"
              % (name, "OK" if only else "BAD", key, failed,
                 "" if only else "★★ 不是恰好一条"))

    # ══ N1：store 里 rig 的调用点改名 ⟹ S1 ═════════════════════════════
    def n1():
        patch_text(SRC_STORE, "return applyDirectorGroupRig(",
                   "return applyDirectorGroupRigZ(")
    run_case("N1", "S1", n1)
    restore(SRC_STORE, backups[SRC_STORE])

    # ══ N2：契约里锚点片段的逐字被改 ⟹ S2 ═════════════════════════════
    def n2():
        def m(d):
            k = "组的锚点 H(e,t)（全部成员位置的平均值）"
            d["片段"][k]["原文"] = d["片段"][k]["原文"].replace(
                "n.x/r.length", "n.x/r.lengthX")
        patch_json(CONTRACT_RAW, m)
    run_case("N2", "S2", n2)
    restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ N3：characterIds 混进机位（不再是派生量）⟹ S3 ═════════════════
    def n3():
        def m(d):
            ids = d["④判定"]["组characterIds"]
            d["④判定"]["组characterIds"] = sorted(ids + ["director-camera-main"])
        patch_json(CLONE_RAW, m)
    run_case("N3", "S3", n3)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N4：组轨道偏移键集少了机位 ⟹ S4 ═══════════════════════════════
    def n4():
        def m(d):
            d["⑤判定"]["组轨道memberOffsets键"] = [
                k for k in d["⑤判定"]["组轨道memberOffsets键"]
                if k != "director-camera-main"
            ]
        patch_json(CLONE_RAW, m)
    run_case("N4", "S4", n4)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N5：角色的后位置不是纯平移期望 ⟹ S5 ══════════════════════════
    def n5():
        def m(d):
            rows = d["★数据级受控检查：rig 纯平移"]["成员"]
            for r in rows:
                if r.get("★rig驱动类别"):
                    r["后位置"] = [r["后位置"][0] + 0.5, r["后位置"][1],
                                   r["后位置"][2]]
        patch_json(CLONE_RAW, m)
    run_case("N5", "S5", n5)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N6：机位被 rig 带动了 ⟹ S6 ═══════════════════════════════════
    def n6():
        def m(d):
            rows = d["★数据级受控检查：rig 纯平移"]["成员"]
            for r in rows:
                if r.get("kind") == "camera":
                    r["后位置"] = [r["后位置"][0] + 2, r["后位置"][1],
                                   r["后位置"][2]]
        patch_json(CLONE_RAW, m)
    run_case("N6", "S6", n6)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N7：道具的位移与角色不同 ⟹ S7 ════════════════════════════════
    def n7():
        def m(d):
            shifts = d["⑩判定"]["★成员x位移"]
            for v in shifts.values():
                if v.get("类别") == "prop":
                    v["位移x"] = 0.0
        patch_json(CLONE_RAW, m)
    run_case("N7", "S7", n7)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N8：解组后选中态不是全部成员 ⟹ S8 ═════════════════════════════
    def n8():
        def m(d):
            d["⑨判定"]["★选中态＝全部成员"] = False
        patch_json(CLONE_RAW, m)
    run_case("N8", "S8", n8)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N9：rig 的纯平移被改成「偏移 ×2」⟹ S9 ════════════════════════
    def n9():
        patch_text(
            SRC_MATH,
            "sampledTransform.position[0] + offset[0],",
            "sampledTransform.position[0] + offset[0] * 2,",
        )
    run_case("N9", "S9", n9)
    restore(SRC_MATH, backups[SRC_MATH])

    # ══ N10：文档层退回「只按角色」⟹ S10 ═════════════════════════════
    def n10():
        patch_text(
            SRC_DOC,
            "const memberIds = new Set(\n"
            "        resolveDirectorGroupMembers(group).map((member) => member.id),\n"
            "      );",
            # ★ 行数中性：3 行 → 3 行
            "const memberIds = new Set(\n"
            "        group.characterIds,\n"
            "      );",
        )
    run_case("N10", "S10", n10)
    restore(SRC_DOC, backups[SRC_DOC])

    # ══ N11：删除规划器退回「只按角色」⟹ S11 ═════════════════════════
    def n11():
        patch_text(
            SRC_PLANNER,
            "resolveDirectorGroupMembers(group)\n"
            "          .map((member) => member.id)\n"
            "          .filter((memberId) => track.memberOffsets[memberId])",
            # ★ 行数中性：3 行 → 3 行
            "group.characterIds\n"
            "          .filter((memberId) => track.memberOffsets[memberId])\n"
            "          .map((memberId) => memberId)",
        )
    run_case("N11", "S11", n11)
    restore(SRC_PLANNER, backups[SRC_PLANNER])

    # ══ N12：锁定守卫退回「只认角色」⟹ S12 ═══════════════════════════
    def n12():
        # ★ 变异**守卫函数体**（而不是某个调用点）⟹ ⟹ 调用点那行有 3 处，
        #   字符串不唯一 ⟹ ⟹ 会误伤别处。
        # ★ 行数中性：3 行 → 3 行
        patch_text(
            SRC_STORE,
            "  return resolveGroupMemberRefs(group).some((member) =>\n"
            "    directorObjectIsLocked(state, member.id),\n"
            "  );",
            "  return group.characterIds.some((objectId) =>\n"
            "    directorObjectIsLocked(state, objectId),\n"
            "  );",
        )
    run_case("N12", "S12", n12)
    restore(SRC_STORE, backups[SRC_STORE])

    # ══ N13：可达性读数说导演台没有树 ⟹ S13 ═════════════════════════
    def n13():
        def m(d):
            d["路径A_导演台"]["有场景树"] = False
        patch_json(REACH_RAW, m)
    run_case("N13", "S13", n13)
    restore(REACH_RAW, backups[REACH_RAW])

    # ══ N14：选中态退回「只认角色」⟹ S14 ═════════════════════════════
    def n14():
        # ★ 变异**建组路径**的选中态（`members.map(...)` → `characterIds`）
        #   ⟹ ⟹ 命中 S14 的「建组按权威成员列表」那半 ⟹ ⟹
        #   同时 S1／S9／S10／S11／S12 都不读这几行 ⟹ ⟹ 恰好翻一条。
        # ★ ★ 变异目标必须**唯一** ⟹ ⟹ `members.map(...)` 这一行在 store 里
        #   出现了 **2 次**（一次在 `normalizeDirectorTimelineSelection` 里、
        #   一次在 `set({…})` 里）⟹ ⟹ 所以带上**上文**一起匹配。
        # ★ 行数中性：4 行 → 4 行
        patch_text(
            SRC_STORE,
            "        //   `lQ(r)` 的 `selectedSceneMembers` 一致。\n"
            "        selectedObjectIds: members.map((member) => member.id),\n"
            "        selectedGroupId: group.id,",
            "        //   `lQ(r)` 的 `selectedSceneMembers` 一致。\n"
            "        selectedObjectIds: [...group.characterIds],\n"
            "        selectedGroupId: group.id,",
        )
    run_case("N14", "S14", n14)
    restore(SRC_STORE, backups[SRC_STORE])

    # ══ N15：把老门禁 87.mjs 的判据改回旧写法 ⟹ S15 ═══════════════════
    def n15():
        # ★ 变异的是**老门禁脚本本身**（不是 clone 源码）⟹ ⟹
        #   证明 S15 真的在读 `scripts/verify-liblib-batch87.mjs`。
        # ★ ★ 变异要**整行换掉**那条正向正则 ⟹ ⟹ 只改前缀没用
        #   （`resolveGroupMemberRefs\(selectedGroup\)` 仍在 ⟹ ⟹ S15 还是绿的）。
        # ★ 行数中性：1 行 → 1 行
        patch_text(
            GATE_87,
            "    /resolveGroupMemberRefs\\(selectedGroup\\)\\s*\\.map\\(\\(member\\) =>\\s*member\\.id\\s*\\)\\s*\\.filter\\(\\(objectId\\) =>\\s*objectIds\\.has\\(objectId\\)/s,",
            "    /selectedGroup\\.characterIds\\.filter\\(\\(objectId\\) =>\\s*objectIds\\.has\\(objectId\\)/s,",
        )
    run_case("N15", "S15", n15)
    restore(GATE_87, backups[GATE_87])

    # ── 全部复原后必须回绿 ────────────────────────────────────────────
    for p in targets:
        restore(p, backups[p])
    final_failed, final_report, _ = run_gate()
    green = not final_failed
    passed = sum(1 for c in cases if c["通过"])
    print("\n阴性 %d/%d 条「恰好翻一条」" % (passed, len(cases)))
    print("复原后门禁：%s" % ("回绿" if green else "★ 没回绿 %s" % final_failed))
    if not green:
        return 1
    for p in targets:
        if p.read_bytes() != backups[p]:
            print("★ 字节级复原失败：%s" % p.name)
            return 1
    out = BATCH / "negative-audit.json"
    out.write_text(
        json.dumps({"批次": 855, "阴性": cases,
                    "复原后回绿": green,
                    "字节级复原": True},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print("已落盘：", out)
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
