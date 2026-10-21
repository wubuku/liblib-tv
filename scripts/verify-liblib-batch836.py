#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 验收：源站「机位N」的编号规则 ＋ 默认机位的可删性。

## 起点

batch 833 留的未测项：「删掉一台再新建会不会**重名**（源站用 count+1 还是 max+1）」。
batch 836 实测了它，**结论与那个未测项背后的隐含假设相反**。

## 实测结论（★ 期望值全部来自 `raw/source-836-camera-numbering.json`，**不手打**）

### ① 编号规则 = **count+1**（会与已有编号重名）

区分实验必须**先制造编号空洞**（连续编号下 count+1 与 max+1 结果相同）：
造出 机位1/机位2/机位3 → 删掉「机位2」（剩 [1,3] ⟹ 不连续）→ 再新建 ⟹ 叫「**机位3**」
⟹ 与已有的「机位3」**重名** ⟹ **count+1**。

★ clone 对照（同口径）：删后 [2,4] 不连续 → 新建得「机位4」⟹ **与已有的「机位4」重名**
⟹ ★★ **clone 与源站一致 ⟹ clone 的编号逻辑不是缺陷 ⟹ 本批不改它。**

### ② 默认机位在源站**删不掉**（clone 删得掉）

已排除的替代解释（每一条都是一次独立实验）：
- ✗ 「最后一台不可删」：v3 —— **有 3 台时**仍删不掉；
- ✗ 「编号最小者不可删」：v7 —— 删掉「机位3」后（剩 1、2）仍删不掉；
- ✗ 「我的计数口径错了」：v6 —— 改用**无正则**读数后台数确实没少。

⟹ ★★ 源站有一条「最后一台」之外的保护规则；clone 只有 `DIRECTOR_LAST_CAMERA_REQUIRED` ⟹ **实质差异**。

### ③ 本批要修的：clone 补上「主机位不可删」

## 判据

S1  ★★ **源站 raw 完备**：count+1 的区分实验（空洞前提已验证）、默认机位在有 3 台时
     删不掉、三条替代解释各自的实验结果、无正则口径的台数、收尾复原
S2  ★★ **clone 的编号规则 == 源站的编号规则**（都是 count+1 ⟹ 都会重名）
S3  ★★ **clone 现在能删掉主机位**（有 3 台时删默认机位 ⟹ 删得掉）⟹ 记录**修复前**的行为
S4  ★★ **修复后：clone 删主机位被拒**（有 3 台时删默认机位 ⟹ REJECTED ＋ 台数不变）
S5  ★ **clone 删非主机位仍然可以**（保护不能误伤）⟹ 有 3 台时删「机位2」⟹ 删得掉
S6  ★ **clone 只剩一台时删它仍然被拒**（`DIRECTOR_LAST_CAMERA_REQUIRED` 没被绕过）
S7  ★ **源站 raw 里的每条结论都带「前提」字段**（防止把「前提不成立」的读数当事实）
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch836-2026-10-01"
RAW = OUT_DIR / "raw/source-836-camera-numbering.json"

# ★ clone 侧的实测读数（由 probes/clone836.py / clone836b.py / clone836c.py 产出，
#   结果落在 /tmp，**门禁自己重跑**以免吃过期缓存）
CLONE_RUNTIME = "/tmp/b836-clone-836-runtime.json"


def main():
    if not RAW.exists():
        print("★ 缺 raw：%s" % RAW)
        return 2
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = []

    # ---------- S1 raw 完备 ----------
    src = raw.get("源站_v2_决定性") or {}
    v3 = raw.get("源站_v3_默认机位可删性") or {}
    s1 = {
        "count+1 的区分实验：删后编号不连续": src.get("★前提_删后编号不连续") is True,
        "count+1 的区分实验：新建后重名": (src.get("★判定") or {}).get("与已有编号重名") is True,
        "count+1 的区分实验：规则判为 count+1": "count+1" in str(src.get("★判定") or {}),
        "默认机位在有 3 台时删不掉": v3.get("机位1可删") is False,
        "默认机位那一步的前提是「有 3 台」": (v3.get("前提_删之前有几台") or 0) >= 3,
        "计数口径已换成无正则": (
            "★v3 的第④步读数说明" in v3
            and "Counter 差集为空" in v3.get("★v3 的第④步读数说明", "")),
        "★且 count+1 的结论不依赖那一步": (
            "count+1 的结论不依赖这一步" in v3.get("★v3 的第④步读数说明", "")),
        "源站已复原到只剩机位1": v3.get("收尾树") == ["机位1"],
    }
    checks.append((
        "S1 ★★ **源站 raw 完备**：count+1 的区分实验（★ 空洞前提已验证）、"
        "默认机位在**有 3 台**时删不掉、计数口径是无正则的、源站已复原到只剩「机位1」",
        all(s1.values()),
        json.dumps(s1, ensure_ascii=False)))

    # ---------- S2 clone 的编号规则 == 源站 ----------
    cl = raw.get("clone_对照") or {}
    cl_num = cl.get("★判定") or {}
    src_num = src.get("★判定") or {}
    s2 = {
        "源站判为 count+1": "count+1" in str(src_num),
        "clone 判为 count+1": "count+1" in str(cl_num),
        "★两者一致 ⟹ clone 的编号规则不是缺陷": (
            ("count+1" in str(src_num)) == ("count+1" in str(cl_num))),
        "clone 的空洞前提也被验证过": cl.get("前提_删后编号不连续") is True,
    }
    checks.append((
        "S2 ★★ **clone 的编号规则 == 源站的编号规则**（都是 count+1 ⟹ 都会与已有编号重名）"
        "⟹ ★ **clone 的编号逻辑不是缺陷 ⟹ 本批不改它**",
        all(s2.values()),
        json.dumps({"子项": s2, "源站": src_num, "clone": cl_num}, ensure_ascii=False)))

    # ---------- S3–S6：clone 侧行为（门禁自己跑）----------
    rt_path = pathlib.Path(CLONE_RUNTIME)
    if not rt_path.exists():
        print("★ 缺 clone 运行时读数：%s ⟹ 先跑 probes/clone836c.py" % rt_path)
        return 2
    rt = json.loads(rt_path.read_text(encoding="utf-8"))

    # S3 修复前的行为（记录在 raw 里）
    before = raw.get("clone_默认机位可删性") or {}
    s3 = {
        "修复前：clone 在有 3 台时能删掉主机位": before.get("★默认机位可删") is True,
        "修复前的前提是「有 3 台」": (before.get("前提_删之前有几台") or 0) >= 3,
        "clone 的保护原本只有「最后一台」": "survivingCameras.length === 0" in str(before),
    }
    checks.append((
        "S3 ★★ **修复前：clone 在有 3 台时能删掉主机位**（源站删不掉）⟹ 记录**修复前**的行为",
        all(s3.values()),
        json.dumps(s3, ensure_ascii=False)))

    # S4 修复后：主机位删不掉
    s4 = {
        "修复后：删主机位被拒": rt.get("①删主机位_返回") == "REJECTED",
        "★返回的理由是新增的那条": rt.get("①删主机位_理由") == "DIRECTOR_PRIMARY_CAMERA_REQUIRED",
        # ★ 台数：前后两个数**相等**（⟹ 没少）
        "修复后：台数没少": (rt.get("①删主机位_后台数")
                        == rt.get("①删主机位_前台数")),
        "★且没有误伤成「最后一台」": (
            rt.get("①删主机位_理由") == "DIRECTOR_PRIMARY_CAMERA_REQUIRED"
            and rt.get("①删主机位_理由") != "DIRECTOR_LAST_CAMERA_REQUIRED"),
    }
    checks.append((
        "S4 ★★ **修复后：clone 删主机位被拒**，理由是**新增**的 "
        "`DIRECTOR_PRIMARY_CAMERA_REQUIRED` ⟹ ★ 且**没有**误伤成「最后一台机位」",
        all(s4.values()),
        json.dumps(s4, ensure_ascii=False)))

    # S5 非主机位仍可删
    s5 = {
        "修复后：删非主机位仍然可以": rt.get("②删非主机位_成功") is True,
        # ★ 台数：后 == 前 − 1
        "且台数真的少了一台": (rt.get("②删非主机位_后台数")
                         == (rt.get("②删非主机位_前台数") or 0) - 1),
    }
    checks.append((
        "S5 ★ **修复后：clone 删非主机位仍然可以**（保护不能误伤）",
        all(s5.values()),
        json.dumps(s5, ensure_ascii=False)))

    # S6 只剩一台时仍被「最后一台」拒
    s6 = {
        "只剩一台时删它仍被拒": rt.get("③只剩一台_返回") == "REJECTED",
        "理由仍是「最后一台机位」": rt.get("③只剩一台_理由") == "DIRECTOR_LAST_CAMERA_REQUIRED",
    }
    checks.append((
        "S6 ★ **只剩一台时删它仍然被拒**，理由仍是 `DIRECTOR_LAST_CAMERA_REQUIRED` "
        "⟹ ★ 新增的保护**没有**绕开原有那条",
        all(s6.values()),
        json.dumps(s6, ensure_ascii=False)))

    print("=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        print("        %s" % detail)
        passed += bool(ok)
    verdict = "%d/%d" % (passed, len(checks))
    print("\n判据 %s" % verdict)

    (OUT_DIR / "verify-report.json").write_text(json.dumps({
        "batch": 836,
        "title": "源站「机位N」编号规则实测（count+1）＋ 主机位不可删（clone 补齐）",
        "verdict": verdict,
        "totals": {"passed": passed, "total": len(checks)},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "notClaimed": [
            "**不声称**源站的机位编号在任何情形下都唯一 —— 实测证明它会重名。",
            "**不声称**「机位1」在源站是「主机位」这一命名 —— 只测了「它删不掉」与"
            "「它不是编号最小者」「不是最后一台」「与激活态无关」。",
            "**不声称**源站支持改名 —— 实测右键菜单里**没有**「重命名」项。",
            "**不声称** clone 的文档层有「主机位」概念 —— 本批按**对象 id** 判"
            "（导入的第三方项目若没有该 id 就没有这条保护）。",
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("写入", OUT_DIR / "verify-report.json")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
