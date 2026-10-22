#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 阴性对照 ＋ 真实注入自检。

★ 两条纪律：
  1. **阴性每条只翻它自己那一条** ⟹ 读的字段必须**互不重叠** ⟹
     ★ 为此把「源站差分」**同时**写进两份**独立**的 raw：
       `source-839-assets.json`（S1 读）与 `source-839-voice-noop.json`（S7 读）
       ⟹ 注入其中一份**不会**波及另一条判据。
  2. **注入没打上 ⟹ 负控看起来是「绿的」**（两者一模一样）⟹ 注入必须**先证明打上了**，
     打不上就**中止**（别把「没打上」当成「通过」）。

★ ★★ **必须轮询，不能只跑一次**：dev server 的**重建是异步的** ⟹ 改完源码立刻跑门禁，
  量的可能还是**上一版**的 chunk ⟹ ⟹ 正解是**轮询门禁，直到它真的翻红**（带超时）。
  ★ 这条是本批实测出来的（见 README §五）。

★ 每次注入后**按字节复原**（不是 `git checkout` ⟹ 那会碰到别人的改动）。
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch839.py"
CSS = ROOT / "src/components/character-studio.css"
PANEL = ROOT / "src/components/CharacterLibraryPanel.tsx"
CTX = ROOT / "src/lib/libtvSelectionCommandContext.ts"
RAWDIR = ROOT / "docs/research/liblib-canvas-batch839-2026-10-01/raw"
RAW_ASSETS = RAWDIR / "source-839-assets.json"
RAW_EDITOR = RAWDIR / "source-839-editor.json"
RAW_NOOP = RAWDIR / "source-839-voice-noop.json"
README = ROOT / "docs/research/liblib-canvas-batch839-2026-10-01/README.md"

PY = sys.executable


class PreflightFailed(RuntimeError):
    """门禁的**前置检查**没过 ⟹ ⟹ 本条负控**作废**（不是「没翻红」，是**读数不可信**）。"""


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> tuple:
    r = subprocess.run([PY, str(GATE)], capture_output=True, text=True, timeout=1200)
    # ★ 门禁的前置检查没过 ⟹ **立刻**作废 ⟹ 不能当成「没翻红」再等 300 秒。
    if "PREFLIGHT-FAIL" in r.stdout:
        print("★ 门禁前置检查没过（服务端 CSS chunk 没追平磁盘）⟹ 本条负控作废")
        print(r.stdout[-1500:])
        raise PreflightFailed("preflight")
    fails = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAIL"):
            parts = line.split()
            fails.append(parts[1] if len(parts) > 1 else line)
    passed_line = [l for l in r.stdout.splitlines() if "通过" in l and "/" in l]
    return r.returncode, fails, (passed_line[-1] if passed_line else "?")


def run_gate_expect(expected: set, timeout_s: int = 300) -> tuple:
    """★ 轮询门禁，直到它**真的**翻成期望的那一组红。

    ⟹ 必须轮询：dev server 的重建是异步的（README §五）。
    ⟹ 超时**如实**报告最后一次读数 ⟹ **不**把「没翻红」算成通过。
    """
    deadline = time.time() + timeout_s
    last = ([], "?")
    while time.time() < deadline:
        _, fails, verdict = run_gate()
        last = (fails, verdict)
        if set(fails) == expected:
            return True, fails, verdict
        time.sleep(6)
    return False, last[0], last[1]


def main() -> int:
    results = []
    backups = {}

    def backup(path: pathlib.Path):
        if path not in backups:
            backups[path] = path.read_bytes()

    def restore_all():
        for path, data in backups.items():
            path.write_bytes(data)

    # ── N1：改 clone 的资产图条几何 ⟹ S2 红 ───────────────────────────
    #    ★ 证明 S2 的几何比对**真的**在读运行时盒子，不是写死的期望。
    backup(CSS)
    o = CSS.read_text(encoding="utf-8")
    m = o.replace("  left: 139px;\n  top: 114px;", "  left: 100px;\n  top: 114px;", 1)
    if m == o:
        print("★ 注入没打上（.cs-asset-strip 的 left 那两行没找到）⟹ 中止")
        restore_all()
        return 2
    CSS.write_text(m, encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S2"})
        results.append({"id": "N1", "注入": "clone 的资产图条 left 139→100（行数中性）",
                        "★注入是否真打上": True, "预期红": ["S2"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N2：把源站的差分读数清空 ⟹ S1 红（只红 S1） ──────────────────
    #    ★ S7 读的是**另一份** raw ⟹ 不会被波及 ⟹ 这正是「互不串门」的证明。
    backup(RAW_ASSETS)
    d = json.loads(RAW_ASSETS.read_text(encoding="utf-8"))
    if "D_★新增的可见文本" not in d:
        print("★ 注入没打上（raw 里没有 D_★新增的可见文本）⟹ 中止")
        restore_all()
        return 2
    d["D_★新增的可见文本"] = []
    RAW_ASSETS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S1"})
        results.append({"id": "N2", "注入": "★源站 raw 的「点前/点后差分」清空 ⟹ S1 应翻红"
                                     "（★ S7 读的是**另一份** raw ⟹ 不该跟着红）",
                        "★注入是否真打上": True, "预期红": ["S1"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N3：删掉前台阻塞面的分支 ⟹ S4/S5 红 ──────────────────────────
    #    ★ S4 与 S5 读的是**同一件事的两面**（Esc 关的是哪一层）⟹ 它们**本该**一起翻
    #    ⟹ 这不是「串门」，是**耦合是真实的** ⟹ 归因靠「只有它们翻、其它没翻」。
    backup(CTX)
    o = CTX.read_text(encoding="utf-8")
    m = o.replace('  if (snapshot.characterAssetsId) return "character-assets";\n', "", 1)
    if m == o:
        print("★ 注入没打上（阻塞面那一行没找到）⟹ 中止")
        restore_all()
        return 2
    CTX.write_text(m, encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S4", "S5"})
        results.append({"id": "N3", "注入": "★删掉 `character-assets` 阻塞面分支 ⟹ "
                                     "Esc 会把**整个面板**一起关掉 ⟹ S4／S5 应翻红"
                                     "（★ 这两条**本就耦合**于「Esc 关哪一层」）",
                        "★注入是否真打上": True, "预期红": ["S4", "S5"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N4：把详情图的文件名改坏 ⟹ S3 红 ─────────────────────────────
    backup(PANEL)
    o = PANEL.read_text(encoding="utf-8")
    m = o.replace("character-detail-${n}.webp", "character-detailX-${n}.webp", 1)
    if m == o:
        print("★ 注入没打上（详情图路径那行没找到）⟹ 中止")
        restore_all()
        return 2
    PANEL.write_text(m, encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S3"})
        results.append({"id": "N4", "注入": "★详情图文件名改坏（character-detail→detailX）⟹ "
                                     "资源不存在 ⟹ S3 应翻红",
                        "★注入是否真打上": True, "预期红": ["S3"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N5：改源站 raw 里的一张图的盒 ⟹ S2 红 ────────────────────────
    #    ★ 证明 S2 的**期望值**是从 raw 读的（不是手打的常量）。
    #    ★★ **要改的是 `source-839-editor.json`** —— 门禁 S2 的期望值从**那份** raw 的
    #    `A_资产视图_imgs` 里提取（第一版误改了 `source-839-assets.json` 的差分图片 ⟹
    #    ★ 门禁根本不读那个字段 ⟹ ⟹ 注入**打上了却什么都没测** ⟹ 负控看起来「通过」实则**空转**）。
    backup(RAW_EDITOR)
    d = json.loads(RAW_EDITOR.read_text(encoding="utf-8"))
    imgs = d.get("A_资产视图_imgs") or []
    target = next((i for i in imgs
                   if (i.get("cls") or "").strip() in ("size-full object-contain",
                                                      "size-full object-cover")), None)
    if not target:
        print("★ 注入没打上（editor raw 里没有那 4 张详情图）⟹ 中止")
        restore_all()
        return 2
    before_x = (target.get("box") or {}).get("x")
    target["box"]["x"] = (before_x or 0) + 100
    d["A_资产视图_imgs"] = imgs
    RAW_EDITOR.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S2"})
        results.append({"id": "N5", "注入": "★源站 raw（editor 那份）里第一张详情图的 x 改大 100 ⟹ "
                                     "S2 应翻红（★ 证明期望值确实是从 raw 提取的，不是手打常量）",
                        "★注入是否真打上": before_x != target["box"]["x"],
                        "预期红": ["S2"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N6：把「源站音色点击无可见变化」改成有变化 ⟹ S7 红 ─────────────
    backup(RAW_NOOP)
    d = json.loads(RAW_NOOP.read_text(encoding="utf-8"))
    if "B_音色_新增文本条数" not in d:
        print("★ 注入没打上（voice-noop raw 里没有 B_音色_新增文本条数）⟹ 中止")
        restore_all()
        return 2
    d["B_音色_新增文本条数"] = 5
    RAW_NOOP.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S7"})
        results.append({"id": "N6", "注入": "★把「源站点音色**无**可见变化」改成「有 5 条新文本」⟹ "
                                     "「clone 的音色按钮是 mock」这条前提被推翻 ⟹ S7 应翻红",
                        "★注入是否真打上": True, "预期红": ["S7"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── N7：把 README 里的 mock 标注删掉 ⟹ S7 红 ──────────────────────
    #    ★★ **第一版只替换了一处**「**只能**是 **mock**」⟹ ⟹ README 里**还有两处** mock
    #    ⟹ ⟹ 判据照样绿 ⟹ ⟹ **负控自己暴露了「全文弱存在式」这个缺陷**
    #    ⟹ ⟹ 现在**全部**改掉 ⟹ 并且门禁那条判据也**定位到 §2.4 那一节**（见门禁 S7）。
    backup(README)
    o = README.read_text(encoding="utf-8")
    m, n_mock = re.subn("mock", "mkbd", o, flags=re.IGNORECASE)
    if n_mock == 0:
        print("★ 注入没打上（README 里一处 mock 都没有）⟹ 中止")
        restore_all()
        return 2
    README.write_text(m, encoding="utf-8")
    try:
        ok, fails, verdict = run_gate_expect({"S7"})
        results.append({"id": "N7", "注入": "★把 README 里**全部** %d 处 mock 标注改掉 ⟹ "
                                     "S7 的「必须如实标注」那条应翻红"
                                     "（★ 第一版只改一处 ⟹ 全文弱存在式判据照样绿 ⟹ 真发现）"
                                     % n_mock,
                        "★注入是否真打上": n_mock > 0,
                        "★改掉了几处": n_mock,
                        "预期红": ["S7"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 复原核验 ──────────────────────────────────────────────────────
    restore_all()
    intact = {}
    for path, data in backups.items():
        intact[str(path.relative_to(ROOT))] = sha(path) == hashlib.sha256(data).hexdigest()
    results.append({"id": "复原", "注入": "★所有被注入文件按字节复原",
                    "逐文件字节一致": intact, "是否全部复原": all(intact.values())})

    ok_all = all(r.get("是否只红预期那些", True) for r in results) and \
        all(r.get("是否全部复原", True) for r in results)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    n = sum(1 for r in results if r.get("是否只红预期那些", True) or r.get("是否全部复原"))
    print("阴性对照：%d/%d 通过" % (n, len(results)))
    out = RAWDIR / "negative-839.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out)
    return 0 if ok_all else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PreflightFailed:
        # ★ 注入文件已由各条臂的 `finally` 复原 ⟹ 这里只是**如实报告**「这轮不算数」。
        print("★ 负控因**环境问题**中止（门禁前置检查没过）⟹ ⟹ 本轮读数**不算**通过")
        sys.exit(3)
