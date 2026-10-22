#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 842 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

★ 三条纪律：
  1. **每条臂只翻它自己那一条** ⟹ 读的字段**互不重叠**；
  2. **改完必须字节级复原**（SHA-256 对拍）；
  3. **等 dev server 真的重建完**再跑门禁 ⟹ 否则读到的是旧 chunk。

★★ **第三条在 CSS 臂上尤其要紧**：842 门禁的前置检查盯的是**JS chunk**
   （找「眼神光」）⟹ ⟹ 改了 **CSS** 时那个标记**不会变**⟹ ⟹ 门禁可能在
   **旧 CSS** 上跑 ⟹ ⟹ 阴性会「没翻红」⟹ ⟹ 而那不是「断言没牙」，是「环境没跟上」。
   ⟹ ⟹ **CSS 臂自带一个 CSS 注释标记**，等它在**下发的 CSS chunk** 里出现。

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 把「亮眼（左）」与「亮眼（右）」的文案**对调**（**同宽度** ⟹ 盒宽不变） | S1 | 只改**文案** ⟹ S2 比的是几何（同字宽 ⟹ 不变）⟹ S3–S7 不读滑杆文案 |
| N2 | 眼睛段那 19 条滑杆整体下移 6px（> ±1px 容差） | S2 | 只动几何 ⟹ S1（文案）／S3（样式）不读它 |
| N3 | 「i」标记的底色改回**填充**（源站是**描边圆**、无填充） | S3 | 只动 `.ce-info` 的 background ⟹ 盒与其它样式不变 ⟹ S2 不受影响 |
| N4 | 眼型卡的 `onClick` 不再切换选中态 | S4 | 只动**点击** ⟹ S1–S3／S5–S7 不读选中态 |
| N5 | 滑杆更新量 `Number(...) % 1` ⟹ 拖动后永远是 0 | S5 | 只动**状态更新** ⟹ S1／S2／S3 是读 DOM 几何与样式 ⟹ 不受影响 |
| N6 | 妆造页的空态文案改回说「未实测」 | S6 | 只动**文案** ⟹ S1–S5／S7 不读它（S7 读的是 **README**） |
| N7 | README 里的 **mock** 标注全部删掉 | S7 | 只动**文档** |

## 产物

`negative-audit.json`
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]  # probes→batch→research→docs→仓库根
BATCH = ROOT / "docs/research/liblib-canvas-batch842-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch842.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CSS = ROOT / "src/components/character-studio.css"
README = BATCH / "README.md"

# ★ 滑杆标签元素上的标记位（JSX **属性位置** ⟹ 放进函数体会变成无效 JSX）
_MARK_LABEL = (
    '          data-character-editor-slider-label={item.id}\n',
    '          data-character-editor-slider-label={item.id}\n'
    '          data-neg842="__MARK__"\n',
)

ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '  { id: "eye-bright-l", label: "亮眼（左）", info: false },\n'
            '  { id: "eye-bright-r", label: "亮眼（右）", info: false },',
            '  { id: "eye-bright-l", label: "亮眼（右）", info: false },\n'
            '  { id: "eye-bright-r", label: "亮眼（左）", info: false },', 1)
            .replace(_MARK_LABEL[0], _MARK_LABEL[1].replace("__MARK__", "neg842n1"), 1)),
        "marker": "neg842n1",
        "note": "「亮眼（左）」与「亮眼（右）」文案对调（同宽度 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '    { kind: "sliders", top: 60, items: BROW_EYE_EYE_SLIDERS },',
            '    { kind: "sliders", top: 66, items: BROW_EYE_EYE_SLIDERS },', 1)
            .replace(_MARK_LABEL[0], _MARK_LABEL[1].replace("__MARK__", "neg842n2"), 1)),
        "marker": "neg842n2",
        "note": "眼睛段那 19 条滑杆整体下移 6px ⟹ 几何与源站差 6px",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★★ **为什么不是改 CSS**：dev 的 CSS 管线会**剥掉注释**（下发的 CSS 里
        #   只剩 5 处 `/*`）⟹ ⟹ CSS 注释当标记**永远等不到**；而且声明值还会被
        #   压缩（`background: transparent` ⟹ `background: none`）⟹ ⟹ 也不可靠。
        #   ⟹ ⟹ 正解：**把缺陷打在 TSX 上**（内联样式）⟹ ⟹ 标记是字符串字面量
        #   ⟹ ⟹ 一定出现在下发的 JS chunk 里 ⟹ ⟹ 等得到。
        "mutate": (lambda s: s.replace(
            '              className="ce-info"\n'
            '              role="img"',
            '              className="ce-info"\n'
            '              style={{ background: "rgba(255, 255, 255, 0.12)" }}\n'
            '              data-neg842="neg842n3"\n'
            '              role="img"', 1)),
        "marker": "neg842n3",
        "note": "「i」标记的底色改回**填充** ⟹ 「描边圆、无填充」这条红",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '        data-character-editor-card={name}\n'
            '        onClick={() => setCardSel((prev) => (prev === name ? "" : name))}',
            '        data-character-editor-card={name}\n'
            '        data-neg842="neg842n4"\n'
            '        onClick={() => undefined}', 1)),
        "marker": "neg842n4",
        "note": "眼型卡的 onClick 不再切换选中态",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "              [item.id]: Number(event.target.value),",
            "              [item.id]: Number(event.target.value) % 1,", 1)
            .replace(_MARK_LABEL[0], _MARK_LABEL[1].replace("__MARK__", "neg842n5"), 1)),
        "marker": "neg842n5",
        "note": "滑杆更新量取模 ⟹ 拖动后 state 永远是 0 ⟹ 控件成了摆设",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '    "「妆造」这一页签的控件 **已实测**（源站 raw 入库在 batch 841／842），" +',
            '    "「妆造」这一页签的控件 本批未实测（源站那趟没采妆造页），" +', 1)
            .replace(
            '                <p className="ce-empty" data-character-editor-empty>',
            '                <p className="ce-empty" data-character-editor-empty\n'
            '                   data-neg842="neg842n6">', 1)),
        "marker": "neg842n6",
        "note": "妆造页的空态文案改回说「未实测」",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        "mutate": (lambda s: re.sub(r"[Mm][Oo][Cc][Kk]", "占位", s)),
        "note": "README 里的 mock 标注全部删掉 ⟹ 「mock 出现次数 >= 3」这条红",
    },
]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def served_chunks() -> str:
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.(?:js|css)', html)))
    out = []
    for u in urls:
        try:
            out.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                       .read().decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001
            pass
    return "\n".join(out)


def wait_for_marker(marker: str, timeout: int = 180) -> bool:
    """等 dev server **真的重建完**（在服务端下发的 chunk 里看到标记）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if marker in served_chunks():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    return False


def run_gate() -> dict:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, timeout=1800)
    if not AUDIT.exists():
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit("门禁没有产出 runtime-audit.json")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    return {"rc": r.returncode, "audit": audit}


def failed_checks(audit: dict) -> list:
    return [c["label"].split(" ")[0] for c in audit.get("checks", [])
            if not c.get("pass")]


def main() -> int:
    results = []
    for arm in ARMS:
        aid = arm["id"]
        backups = {}
        before_sha = {}
        for f in arm["files"]:
            backups[f] = f.read_bytes()
            before_sha[f] = sha(f)
        try:
            for f in arm["files"]:
                src = f.read_text(encoding="utf-8")
                dst = arm["mutate"](src)
                if dst == src:
                    raise SystemExit("%s 变异没有生效（源串没匹配上）" % aid)
                f.write_text(dst, encoding="utf-8")
            if arm.get("marker"):
                if not wait_for_marker(arm["marker"]):
                    raise SystemExit("%s 等不到标记 %r" % (aid, arm["marker"]))
            else:
                time.sleep(6)
            out = run_gate()
            reds = failed_checks(out["audit"])
            ok = (reds == [arm["expect"]])
            print("%s %s ⟹ 红的是 %s（期望 %s）%s"
                  % ("PASS" if ok else "FAIL", aid, reds or "无",
                     arm["expect"], "" if ok else "  ★ 不符合预期"))
            if not ok:
                print("   判据明细：", json.dumps(out["audit"].get("checks"),
                                             ensure_ascii=False)[:2000])
            results.append({"臂": aid, "红": reds, "期望": arm["expect"],
                            "通过": ok, "说明": arm["note"]})
        finally:
            for f, data in backups.items():
                f.write_bytes(data)
            for f in arm["files"]:
                if sha(f) != before_sha[f]:
                    raise SystemExit("%s 复原失败：%s 的 SHA-256 对不上" % (aid, f))
            time.sleep(4)

    print("\n=== 阴性对照汇总 ===")
    for r in results:
        print("  %s  %s ⟹ %s" % ("PASS" if r["通过"] else "FAIL", r["臂"], r["说明"]))
    passed = sum(1 for r in results if r["通过"])

    print("\n复原后再跑一次门禁（必须回到 7/7）……")
    out = run_gate()
    reds = failed_checks(out["audit"])
    back_green = (not reds) and out["rc"] == 0
    print("  %s 复原后门禁：%s（红的是 %s）"
          % ("PASS" if back_green else "FAIL", out["audit"].get("verdict"), reds or "无"))

    print("\n%d/%d 通过" % (passed, len(results)))
    out_path = BATCH / "negative-audit.json"
    out_path.write_text(json.dumps({
        "batch": 842,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "CSS 臂等的是**下发的 CSS chunk** 里的标记（★ 否则会「假阴性」）",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
