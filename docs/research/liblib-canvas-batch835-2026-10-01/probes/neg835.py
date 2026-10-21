#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 835：门禁的**阴性对照** —— 逐条证明每个判据**能红**。

★ 为什么必须有这一步：门禁报 7/7 可能只是**恒真**（判据压根没接上事实）。
⟹ 对每条判据做一次**只翻它自己那一条**的注入 ⟹ 期望：只有那一条翻红。

★★ **注入必须自己校验「打上了没打上」** —— 这是本脚本第一版的真坑：
  N3 的注入把 Python 语法写坏了 ⟹ 门禁**崩了** ⟹ 解析出来是 `{}`（全红）
  ⟹ 看起来像「注入有效果」，其实是**脚本根本没跑起来**；
  N6 的替换串没匹配上 ⟹ 748 压根没被改 ⟹ S7 当然还绿。
  ⟹ **「打不上」与「打上了但没效果」必须分开**：打不上 ⟹ **中止**，不当成阴性通过。
  ⟹ 所以每条注入后都做：① 语法可解析；② 锚点确实被替换；③ 脚本能跑出判据行。

★ 注入方式（每条都**行数中性**，且**按字节复原**）：
  N1 篡改 S1 的静态恒等式 ② ⟹ 只有 S1 翻红
  N2 从 S2 的期望清单删掉一个属性名 ⟹ 只有 S2 翻红
  N3 把一个属性名安到错误的批次上 ⟹ 只有 S2 翻红
  N4 把 help 也说成零新增 ⟹ 只有 S4 翻红
  N5 把机位预设的属性名写错 ⟹ 只有 S5 翻红
  N6 把 748 的期望改成新的快照数字 ⟹ 748 转绿 ⟹ S7（故意保留的红）翻红
  N7 反例实验：过期缓存 + 「吃缓存」的旧写法 ⟹ 证明旧写法会照单全收地报绿
"""
import ast
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch835.py"
GATE748 = ROOT / "scripts/verify-liblib-batch748.py"
BACKUP = pathlib.Path("/tmp/b835-neg-backup")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate():
    proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(("PASS ", "FAIL ")):
            key = line.split()[1]
            res[key] = line.startswith("PASS ")
    return res, proc.returncode, out


def expect(base, res, flip, name):
    diff = [k for k in base if base[k] != res.get(k)]
    ok = diff == [flip] and res.get(flip) is False
    print("  %s %s ⟹ 翻红的是 %s（期望只有 %s）" % ("✔" if ok else "✘", name, diff, flip))
    if not ok:
        print("      base:", base)
        print("      got :", res)
    return ok


def inject_gate(old, new, label):
    """注入到门禁；**先自校验注入真的打上了且语法没坏**，否则中止。"""
    txt = GATE.read_text(encoding="utf-8")
    if txt.count(old) != 1:
        raise SystemExit("★ %s：锚点出现 %d 次（应为 1）⟹ 注入没打上，**中止**（不当作阴性通过）"
                         % (label, txt.count(old)))
    cand = txt.replace(old, new)
    if cand == txt:
        raise SystemExit("★ %s：替换后文本没变 ⟹ 注入没打上，**中止**" % label)
    try:
        ast.parse(cand)
    except SyntaxError as exc:
        raise SystemExit("★ %s：注入后语法坏了（line %s %s）⟹ **中止**（脚本跑不起来不等于判据翻红）"
                         % (label, exc.lineno, exc.msg))
    GATE.write_text(cand, encoding="utf-8")
    # 注入确实落进文件了吗？—— 读回验证
    back = GATE.read_text(encoding="utf-8")
    if new not in back or old in back:
        raise SystemExit("★ %s：读回验证失败 ⟹ 注入没真正落盘，**中止**" % label)


def restore():
    GATE.write_bytes((BACKUP / "verify-liblib-batch835.py").read_bytes())
    if sha(GATE) != sha(BACKUP / "verify-liblib-batch835.py"):
        raise SystemExit("★ 复原后 sha256 不一致")


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GATE, BACKUP / "verify-liblib-batch835.py")
    shutil.copy2(GATE748, BACKUP / "verify-liblib-batch748.py")
    if sha(BACKUP / "verify-liblib-batch835.py") != sha(GATE):
        raise SystemExit("★ 备份校验失败")

    print("=== 基线 ===")
    base, _, _ = run_gate()
    print("  ", base)
    if len(base) != 7:
        raise SystemExit("★ 基线不是 7 条判据（拿到 %r）⟹ 中止" % base)
    results = []

    cases = [
        ("N1", "篡改静态恒等式 ②（有效并集 == 字面量并集 + 派生名增量）", "S1",
         '"② 有效并集 == 字面量并集 + dataset 派生名增量": len(eff) == len(union) + len(ds - union),',
         '"② 有效并集 == 字面量并集 + dataset 派生名增量": len(eff) == len(union) + len(ds),'),
        ("N2", "从期望清单删一个属性名（增量账对不上）", "S2",
         '"data-director-camera-preset", "data-director-camera-preset-glyph"],',
         '"data-director-camera-preset-glyph"],'),
        ("N3", "把一个属性名安到错误的批次上（逐条反查对不上）", "S2",
         '"data-director-camera-preset", "data-director-camera-preset-glyph"],',
         '"data-director-camera-preset", "data-director-camera-preset-glyph",\n'
         '        "data-director-follow-hint"],'),
        ("N4", "把 help 也说成零新增（S4 对不上）", "S4",
         '"零新增的入口恰好是 scene 一枚": zero == ["scene"],',
         '"零新增的入口恰好是 scene 一枚": zero == ["scene", "help"],'),
        ("N5", "把机位预设的属性名写错（S5 对不上）", "S5",
         '{"data-director-camera-preset", "data-director-camera-preset-glyph"} <= cam_gained,',
         '{"data-director-camera-preset", "data-director-camera-preset-WRONG"} <= cam_gained,'),
    ]

    for cid, desc, flip, old, new in cases:
        try:
            inject_gate(old, new, cid)
            res, code, out = run_gate()
            if not res:
                print("  ✘ %s：门禁没跑出判据行（exit=%s）⟹ 注入破坏了脚本，**不算阴性通过**"
                      % (cid, code))
                print(out[-1500:])
                results.append(False)
            else:
                results.append(expect(base, res, flip, "%s %s" % (cid, desc)))
        finally:
            restore()

    # ---------- N6：把 748 的 C1／C3／C4 改成绿 ⟹ S7 应翻红 ----------
    # ★ 第一版 N6 的做法是「改几个数字」⟹ 失败：748 的每条判据有**十几个 and 条件**，
    #   只改三处数字 ⟹ 其余条件（fileCount==13／每个文件的 count／firstPaintCount==200／
    #   afterRailWalkCount==250／gains 字典…）仍不满足 ⟹ 748 **压根没转绿** ⟹ S7 当然还绿。
    # ★ 教训：**注入要针对「判据整体」，不是「判据里的某个数字」**。
    # ⟹ 改成把三条判据的**条件表达式整体**换成 True（detail 保持原样）。
    print()
    before = GATE748.read_bytes()
    try:
        txt = before.decode("utf-8")
        # C1 的条件块：从 `st["fileCount"] == 13` 到 `{"data-director-gizmo-webgl-canvas", "data-director-webgl-canvas"},`
        c1_old = '''         st["fileCount"] == 13
         and st["sumByFile"] == 460 and st["unionCount"] == 446
         and st["sharedAcrossFiles"] == 14 and len(st["sharedNames"]) == 13
         and sum(len(v) - 1 for v in st["sharedNameOwners"].values()) == 14
         and st["sharedNameOwners"]["data-director-bottom-bar"] ==
             ["DirectorDesk.tsx", "DirectorTimeline.tsx", "DirectorViewport.tsx"]
         and st["files"]["DirectorMannequin.tsx"]["count"] == 0
         and st["files"]["DirectorInspector.tsx"]["count"] == 142
         and st["files"]["DirectorViewport.tsx"]["count"] == 86
         and st["files"]["DirectorTimeline.tsx"]["count"] == 79
         and {d["attr"] for d in st["datasetAssignments"]} ==
             {"data-director-gizmo-webgl-canvas", "data-director-webgl-canvas"},'''
        c1_new = '''         True,   # ★ N6 注入：整条判据改成绿'''
        c3_old = '''         c3["firstPaintCount"] == 200 and c3["afterRailWalkCount"] == 250
         and c3["staticLiteralUnion"] == 446 and c3["staticEffectiveUnion"] == 447
         and c3["staticSumByFile"] == 460
         and c3["directorKindsSeen"] + c3["extraOnPage"] == c3["afterRailWalkCount"]
         and c3["directorKindsSeen"] + c3["residueAfterWalk"] == c3["staticEffectiveUnion"]
         and c3["extraDatasetBlindSpot"] == []          # 补进有效并集后已不再是"额外项"
         and c3["extraCanvasLeftover"] and
              "data-open-director" in c3["extraCanvasLeftover"]
         and "data-inert" in c3["extraCanvasLeftover"]
         and "data-director-webgl-canvas" not in c3["extraCanvasLeftover"]
         and c3["extraUnprefixedDirector"] == ["data-director-node", "data-director-node-id"]
         and len(c3["perRail"]) == 7,'''
        c3_new = '''         True,   # ★ N6 注入：整条判据改成绿'''
        c4_old = '''         c4["zeroGainCount"] == 2
         and {z["key"] for z in c4["zeroGain"]} == {"scene", "help"}
         and c4["biggest"]["key"] == "add-camera" and c4["biggest"]["gainedCount"] == 34
         and {g["key"]: g["n"] for g in c4["gains"]} ==
             {"scene": 0, "add-character": 3, "add-camera": 34, "panorama": 2,
              "aspect-ratio": 4, "ai-import": 7, "help": 0},'''
        c4_new = '''         True,   # ★ N6 注入：整条判据改成绿'''
        for o, n, name in ((c1_old, c1_new, "C1"), (c3_old, c3_new, "C3"), (c4_old, c4_new, "C4")):
            if txt.count(o) != 1:
                raise SystemExit("★ N6：%s 的条件块出现 %d 次 ⟹ 注入没打上，**中止**"
                                 % (name, txt.count(o)))
            txt = txt.replace(o, n)
        GATE748.write_text(txt, encoding="utf-8")
        # ★ 自校验：748 真的被改绿了吗？（先跑 748 本身看 C1/C3/C4 是不是都 PASS）
        p748 = subprocess.run([sys.executable, str(GATE748)], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=1800)
        out748 = (p748.stdout or "") + (p748.stderr or "")
        green = [ln.strip() for ln in out748.splitlines()
                 if ln.strip().startswith("PASS ") and ln.strip().split()[1] in ("C1", "C3", "C4")]
        print("  748 被注入后，C1/C3/C4 里变绿的有：%s" % ([g.split()[1] for g in green],))
        if len(green) != 3:
            print("  ✘ N6：748 没被改成绿的 ⟹ 注入没生效，**不算阴性通过**")
            print("  ", [ln.strip()[:120] for ln in out748.splitlines()
                          if ln.strip().startswith(("PASS", "FAIL"))][:8])
            results.append(False)
        else:
            res, _, _ = run_gate()
            ok = res.get("S7") is False
            print("  %s N6 把 748 的 C1/C3/C4 整条改成绿 ⟹ S7（故意保留的红）应翻红 ⟹ 实际 S7=%s"
                  % ("✔" if ok else "✘", res.get("S7")))
            if not ok:
                print("      got:", res)
            results.append(ok)
    finally:
        GATE748.write_bytes(before)
        if sha(GATE748) != sha(BACKUP / "verify-liblib-batch748.py"):
            raise SystemExit("★ 748 复原后 sha256 不一致")

    # ---------- N7：反例实验 ----------
    print("\n=== N7 反例实验：门禁若吃外部缓存会怎样 ===")
    cache = pathlib.Path("/tmp/b835-runtime.json")
    stale = cache.exists()
    stale_bytes = cache.read_bytes() if stale else None
    try:
        cache.write_text(json.dumps({
            "关系式不变量": {"累计 = 首屏 + 各枚 rail 新增之和": True,
                        "累计 = 导演台属性 + 非并集": True,
                        "有效并集 = 见过 + 残留": True,
                        "非并集 = 画布残留 + dataset 盲区 + 无前缀导演台": True,
                        "dataset 盲区已不在并集外": True,
                        "首屏 ⊆ 累计": True,
                        "求和 - 并集 == 跨文件重复数": True,
                        "有效并集 == 字面量并集 + 派生名增量": True,
                        "每枚 rail 的新增都是首次出现": True},
            "rail": {"zeroGain": ["scene"], "gains": {"scene": 0, "help": 0},
                     "perRail": []}}, ensure_ascii=False), encoding="utf-8")
        d = json.loads(cache.read_text(encoding="utf-8"))
        old_would_pass = all(d["关系式不变量"].values())
        print("  过期缓存里所有不变量都是 true ⟹ 「吃缓存」的旧写法会报绿：", old_would_pass)
        print("  ⟹ ★ 这就是「吃缓存」的危险：缓存内容若是**旧的真值**，判据**察觉不到**")
        print("  ⟹ 所以门禁必须**自己跑**运行时读数（本批已改）")
        results.append(old_would_pass)
    finally:
        if stale_bytes is not None:
            cache.write_bytes(stale_bytes)
        elif cache.exists():
            cache.unlink()

    print("\n阴性对照 %d/%d" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
