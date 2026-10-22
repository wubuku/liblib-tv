#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | **文案清单**（H3 文字／chip 文案）＋ 控件**条数** ＋ 有无空态 |
| S2 | **几何**（盒：H3／chip／色块／卡片／卡片名／媒体／子页签） |
| S3 | **计算样式**（chip／色块／卡片名／媒体区／H3／子页签）＋ nav 底边框线 |
| S4 | **初始选中态**（哪一枚 chip／哪一枚色块被选中） |
| S5 | **点完之后**的状态（选中态是否转移） |
| S6 | **结构事实**（子页签枚数／滚动区位置／滚动高／「智能调整」数／切到「服装」后的状态） |
| S7 | **README** 文本 |

## ★ 两条「为什么这条臂不写成更直觉的样子」

1. **N2 不是「整体下移 6px」**：整体下移会**连带**改掉这一段的**内容起点**
   ⟹ ⟹ 那会**同时翻 S6** ⟹ ⟹ 违反「每条臂只翻它自己那一条」。
   ⟹ ⟹ 所以这一条臂改成「**发型那 7 枚 chip** 下移 6px」
   ⟹ ⟹ 几何（S2）红，内容起点（S6）不动 ✓
2. **N4 不是「把口红的初值改成别的」**：改初值会**连带**改掉那一枚色块的
   **选中态**⟹ ⟹ 而 S4 与 S5 **都读**选中态 ⟹ ⟹ 那样会**两条一起红**。
   ⟹ ⟹ 所以这一条臂改成「**发色**那一段的初值从 0 改成 10」
   ⟹ ⟹ 只翻 S4（初始态），S5（点完之后）读到的是**转移后的**那一枚 ⟹ ⟹ 不受影响

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「民族」改名成「民疾」 | S1 | ★ **同字数** ⟹ chip 盒 50px 不变 ⟹ S2 不红；★ 特意**不**改「古风」⟹ ⟹ S5 要点的那一枚不动 ⟹ ⟹ 不连累 S5 |
| N2 | **发型那 7 枚** chip 下移 6px | S2 | 只动**发型 chip** 的 y ⟹ 内容起点（H3）不动 ⟹ S6 不红 |
| N3 | chip 的**选中态底色**改成白 8% | S3 | 只动**颜色** ⟹ 盒不变 ⟹ S2 不红 |
| N4 | **发色**那一段的初值改成 10 | S4 | 只动**初始**选中 ⟹ S5 读的是**转移后**的那一枚 ⟹ 不红 |
| N5 | chip 的 onClick **不改选中态** | S5 | 只动**赋值** ⟹ S1–S4／S6–S7 读的是初始态，不受影响 |
| N6 | 让「智能调整」在**这一段**也出现 | S6 | 只动**生成行** ⟹ 内容与几何都不变 ⟹ S1–S5 不红 |
| N7 | README 里的 **iconify** 全部替换 | S7 | 只动**文档**（★ 门禁 S7 查的正是这个词） |
| N8 | 子页签行容器去掉那条**底边框线** | S3 | 只动**边框** ⟹ 盒不变 ⟹ S2 不红 |

## ★★ 两例「变异没生效」（★ 不是判据没牙）

- **N6 第一版**：`(A ? null : (true)) && (B)` ⟹ ⟹ 在 outfit 段得 `null && (B)` ＝ **null**
  ⟹ ⟹ **那枚按钮根本不渲染** ⟹ ⟹ 变异等于没发生 ⟹ ⟹ 门禁当然不红
  ⟹ ⟹ 改成 `(A ? (true) : (true)) && (B)`（**恒真**）⟹ ⟹ 才是真缺陷
- **N7 第一版**：删 README 里的「mock」⟹ ⟹ 但门禁 S7 **一条都不查 mock**
  ⟹ ⟹ 变异等于没发生 ⟹ ⟹ 改成删「iconify」（★ 那**正是** S7 查的词）

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
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch846.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CSS = ROOT / "src/components/character-studio.css"
README = BATCH / "README.md"

# ★ 标记位（JSX **属性位置** ⟹ 同行插入 ⟹ 变异**行数中性**）
_MARK = (
    '          data-character-editor-outfit-title={t.title}\n',
    '          data-character-editor-outfit-title={t.title} data-neg846="__MARK__"\n',
)


def with_mark(src: str, mark: str) -> str:
    if src.count(_MARK[0]) != 1:
        raise SystemExit("标记位不唯一（%d 处）" % src.count(_MARK[0]))
    return src.replace(_MARK[0], _MARK[1].replace("__MARK__", mark), 1)


ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★★ 改的是「民族」⟹ ⟹ **不是** S5 要点的那枚「古风」
        #   ⟹ ⟹ 否则 S5 会因为「点不到古风」**连带**红 ⟹ ⟹ 那是**字段重叠**
        #   ⟹ ⟹ ★ 同字数 ⟹ ⟹ chip 盒 50px 不变 ⟹ ⟹ S2 不红
        "mutate": (lambda s: with_mark(s.replace(
            '  { label: "民族", x: 80, y: 78, w: 50, sel: false },',
            '  { label: "民疾", x: 80, y: 78, w: 50, sel: false },', 1),
            "neg846n1")),
        "marker": "neg846n1",
        "note": "「民族」改名成「民疾」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1；★ 特意**不**改"
                "「古风」⟹ ⟹ S5 要点的那一枚不动 ⟹ ⟹ 不连累 S5）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        # ★ 只动**发型那 7 枚 chip** 的 y（★ H3 与内容起点不动 ⟹ ⟹ S6 不红）
        # ★★ 用 chip **独有**的那行 style（★ 带 `width` ⟹ ⟹ 与色块/卡片的 style 行不同
        #   ⟹ ⟹ 不会「误伤」别的控件）
        "mutate": (lambda s: with_mark(s.replace(
            '              style={{ top: `${c.y}px`, left: `${c.x}px`, width: `${c.w}px` }}',
            '              style={{ top: `${c.y + 6}px`, left: `${c.x}px`, width: `${c.w}px` }}', 1),
            "neg846n2")),
        "marker": "neg846n2",
        "note": "发型那 7 枚 chip 下移 6px ⟹ 几何与源站差 6px（★ H3 不动 ⟹ S6 不红）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [CSS],
        # ★ chip 的**选中态底色**（★ 源站实测 ＝ 纯白）⟹ ⟹ 只动颜色 ⟹ ⟹ 盒不变
        "mutate": (lambda s: s.replace(
            ".ce-chip.is-on {\n  background: #fff;",
            ".ce-chip.is-on {\n  background: rgba(255, 255, 255, 0.08);", 1)),
        "note": "chip 选中态底色改成白 8% ⟹ 「外观」这条红（盒不变 ⟹ S2 不红）",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 只动**发色**那一段的初值（★ S5 读的是**点完之后**的那一枚 ⟹ ⟹ 不红）
        "mutate": (lambda s: with_mark(s.replace(
            '  const [outfitHairColor, setOutfitHairColor] = useState(0);',
            '  const [outfitHairColor, setOutfitHairColor] = useState(10);', 1),
            "neg846n4")),
        "marker": "neg846n4",
        "note": "发色的初始选中改成第 11 枚（源站实测是第一枚）⟹ 「初始选中态」这条红",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        # ★ chip 的 onClick **不改选中态** ⟹ ⟹ 点「古风」不动 ⟹ ⟹ 「真交互」这条红
        "mutate": (lambda s: with_mark(s.replace(
            '              onClick={() => setOutfitHairChip(c.label)}',
            '              onClick={() => void c.label}', 1),
            "neg846n5")),
        "marker": "neg846n5",
        "note": "发型 chip 的 onClick 不再改选中态 ⟹ 点「古风」不转移",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★★ 让「智能调整」在**这一段**也出现（★ 源站实测这一段**没有**它）
        # ★★ 改法：`{segment === "outfit" ? null : (B)}` ⟹ ⟹ 换成
        #   `{(segment === "outfit" ? (true) : (true)) && (B)}`
        #   ⟹ ⟹ 恒真 ⟹ ⟹ 「智能调整」在**所有**段都出现
        #   ⟹ ⟹ ★ **行数中性**（同行改写 ⟹ ⟹ 不动文件行数 ⟹ ⟹ 不影响别的）
        # ★★ ★ 第一版写的是 `(A ? null : (true)) && (B)` ⟹ ⟹ 那在 outfit 段得
        #   `null && (B)` ＝ **null** ⟹ ⟹ **变异等于没发生** ⟹ ⟹ 门禁当然不红
        #   ⟹ ⟹ ★ 这是「变异没生效」的一例（★ 不是判据没牙）
        "mutate": (lambda s: with_mark(s.replace(
            '              {segment === "outfit" ? null : (',
            '              {(segment === "outfit" ? (true) : (true)) && (', 1),
            "neg846n6")),
        "marker": "neg846n6",
        "note": "「智能调整」在「服装造型」段也出现 ⟹ 「结构事实」这条红",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        # ★★ 删掉「iconify」⟹ ⟹ 门禁 S7 里那条「★README写明图标字形是占位」
        #   （它查的是 `"iconify" in readme and "lucide" in readme`）就会红
        # ★★ ★ 第一版删的是「mock」⟹ ⟹ 但门禁 S7 **一条都不查 mock**
        #   ⟹ ⟹ 删 mock ⟹ ⟹ **变异等于没发生** ⟹ ⟹ 门禁当然不红
        #   ⟹ ⟹ ★ 这是「变异没生效」的第二例（★ 不是判据没牙）
        "mutate": (lambda s: re.sub(r"iconify", "某个图标库", s)),
        "note": "README 里的「iconify」全部替换 ⟹ 「如实标注」这条红",
    },
    {
        "id": "N8",
        "expect": "S3",
        "files": [CSS],
        # ★ nav 的那条**底边框线**（★ 源站实测 ＝ 1px 白 8%）⟹ ⟹ 只动边框 ⟹ ⟹ 盒不变
        "mutate": (lambda s: s.replace(
            "  /* ★ 源站 nav 实测：`border-bottom: 1px solid rgba(255,255,255,0.08)` */\n"
            "  border-bottom: 1px solid rgba(255, 255, 255, 0.08);",
            "  /* ★ 源站 nav 实测：`border-bottom: 1px solid rgba(255,255,255,0.08)` */\n"
            "  border-bottom: 0 solid rgba(255, 255, 255, 0.08);", 1)),
        "note": "子页签行容器去掉那条底边框线 ⟹ 「外观」这条红（盒不变 ⟹ S2 不红）",
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
    """★ 门禁 846 的 audit 结构是 `检查: [{名, ok, 详情}]` ⟹ ⟹ 取每条名前缀。"""
    out = []
    for c in audit.get("检查", []):
        if not c.get("ok"):
            out.append(str(c.get("名") or "").split(" ")[0])
    return out


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
                time.sleep(8)
            out = run_gate()
            reds = failed_checks(out["audit"])
            ok = (reds == [arm["expect"]])
            print("%s %s ⟹ 红的是 %s（期望 %s）%s"
                  % ("PASS" if ok else "FAIL", aid, reds or "无",
                     arm["expect"], "" if ok else "  ★ 不符合预期"))
            if not ok:
                print("   判据明细：", json.dumps(out["audit"].get("检查"),
                                             ensure_ascii=False)[:3000])
            results.append({"臂": aid, "红": reds, "期望": arm["expect"],
                            "通过": ok, "说明": arm["note"]})
        finally:
            for f, data in backups.items():
                f.write_bytes(data)
            for f in arm["files"]:
                if sha(f) != before_sha[f]:
                    raise SystemExit("复原失败：%s 的 SHA-256 对不上" % (aid, f))
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
        "batch": 846,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）；"
                "★ N2 只移发型 chip、N4 改发色初值 ⟹ 都是为了**不连累** S6／S5",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
