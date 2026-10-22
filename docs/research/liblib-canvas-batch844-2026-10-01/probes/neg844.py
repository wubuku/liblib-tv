#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 844 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | 卡片**文案**（名字清单）＋ H3 文案 ＋ 有无空态 ＋ 页签数 |
| S2 | **几何**（盒） |
| S3 | **计算样式** |
| S4 | **初始选中态**（每张卡的 `aria-pressed` 有无与取值）＋ 有图/无图 |
| S5 | **点卡之后**的状态转移 |
| S6 | **结构事实**（这一段的页签数 ＋ 切回后的页签数） |
| S7 | **README** 文本 |

★ N6 之所以能只翻 S6：★ batch 844 把页签行**抽成了 `renderTabs()`**
  ⟹ ⟹ 阴性臂可以注入「页签行在**不该**出现的段也出现」这条**真实**缺陷
  ⟹ ⟹ 而不必塞一个假的标记元素（★ 假标记测的是「标记在不在」，不是「结构对不对」）。

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 把「疤痕_浅」改名成「疤痕_浓」 | S1 | ★ **同字数** ⟹ 名字盒 47px 不变 ⟹ S2 不红；★ S4 只比 `aria-pressed` 不比名字 ⟹ 不红 |
| N2 | 6 张卡整体下移 6px | S2 | 只动几何 ⟹ S1（文案）／S3（样式）不读它 |
| N3 | 缩略图的圆角从 `9999px` 改成 `16px` | S3 | 只动**圆角** ⟹ 盒与其它样式不变 ⟹ S2 不受影响 |
| N4 | 初始就把「痣」设成选中态 | S4 | ★ 源站实测**初始一个都没选中** ⟹ ⟹ 只翻 S4；★ S5 点完仍是「痣」选中 ⟹ 不红 |
| N5 | 卡片的 `onClick` 不再切换选中态 | S5 | 只动**点击** ⟹ S1–S4／S6–S7 不读卡片选中态 |
| N6 | 让页签行在**这一段**也出现 | S6 | 只动**页签行** ⟹ 内容与几何都不变 ⟹ S1–S5 不红 |
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
BATCH = ROOT / "docs/research/liblib-canvas-batch844-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch844.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
README = BATCH / "README.md"

# ★ 卡片按钮上的标记位（JSX **属性位置** ⟹ 同行插入 ⟹ 变异**行数中性**）
_MARK_CARD = (
    '              data-character-editor-trait={card.name}\n',
    '              data-character-editor-trait={card.name} data-neg844="__MARK__"\n',
)
# ★ 页签行容器上的标记位
_MARK_TABS = (
    '    <div className="ce-tabs" role="tablist">\n',
    '    <div className="ce-tabs" role="tablist" data-neg844="__MARK__">\n',
)

ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 只改**文案**（★ **同字数** ⟹ 名字盒 47px 不变 ⟹ S2 的几何不受影响）
        "mutate": (lambda s: s.replace(
            '    name: "疤痕_浅",', '    name: "疤痕_浓",', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg844n1"), 1)),
        "marker": "neg844n1",
        "note": "「疤痕_浅」改名成「疤痕_浓」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '                top: `${42 + Math.floor(i / 3) * 62}px`,',
            '                top: `${48 + Math.floor(i / 3) * 62}px`,', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg844n2"), 1)),
        "marker": "neg844n2",
        "note": "6 张卡整体下移 6px ⟹ 几何与源站差 6px",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★★ **为什么不改 CSS**：dev 的 CSS 管线会**剥掉注释** ⟹ ⟹ 注释当标记
        #   **永远等不到**；而且声明值还会被压缩 ⟹ ⟹ 也不可靠。
        #   ⟹ ⟹ 正解：**把缺陷打在 TSX 上**（内联样式）⟹ ⟹ 标记是字符串字面量
        #   ⟹ ⟹ 一定出现在下发的 JS chunk 里 ⟹ ⟹ 等得到。
        "mutate": (lambda s: s.replace(
            '                className={`ce-trait-thumb${card.img ? "" : " ce-trait-thumb--custom"}`}\n',
            '                className={`ce-trait-thumb${card.img ? "" : " ce-trait-thumb--custom"}`} '
            'style={{ borderRadius: "16px" }}\n', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg844n3"), 1)),
        "marker": "neg844n3",
        "note": "缩略图的圆角从 9999px 改成 16px ⟹ 「圆形」这条红",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 初始就把「痣」设成选中态 ⟹ ⟹ 与源站实测（「初始一个都没选中」）不符
        "mutate": (lambda s: s.replace(
            '  const [traitSel, setTraitSel] = useState<string | null>(null);',
            '  const [traitSel, setTraitSel] = useState<string | null>("痣");', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg844n4"), 1)),
        "marker": "neg844n4",
        "note": "初始就把「痣」设成选中态 ⟹ 「初始一个都没选中」这条红",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '              onClick={() =>\n'
            '                card.img\n'
            '                  ? setTraitSel(card.name)\n'
            '                  : flash("clone mock：自定义贴纸未接上传")\n'
            '              }',
            '              onClick={() =>\n'
            '                card.img\n'
            '                  ? undefined\n'
            '                  : undefined\n'
            '              }', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg844n5"), 1)),
        "marker": "neg844n5",
        "note": "卡片的 onClick 不再切换选中态 ⟹ 点「痣」后 aria-pressed 不变 true",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★★ 「页签行在不该出现的段也出现」——★ 这正是 clone 843 之前的**老毛病**
        #   ⟹ ⟹ 用它当阴性臂 ⟹ ⟹ 判据若没牙 ⟹ ⟹ 这个老毛病就抓不住
        "mutate": (lambda s: s.replace(
            '            {segment === "face" ? renderTabs() : null}',
            '            {segment === "face" || segment === "traits" ? renderTabs() : null}', 1)
            .replace(_MARK_TABS[0], _MARK_TABS[1].replace("__MARK__", "neg844n6"), 1)),
        "marker": "neg844n6",
        "note": "页签行在「脸部 & 身体特征」段也出现 ⟹ 「这一段没有标题行」这条红",
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
                                             ensure_ascii=False)[:2500])
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
        "batch": 844,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
