#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 843 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 三条纪律

1. **每条臂只翻它自己那一条** ⟹ 读的字段**互不重叠**；
2. **改完必须字节级复原**（SHA-256 对拍）；
3. **等 dev server 真的重建完**再跑门禁 ⟹ 否则读到的是旧 chunk。

★★ **第三条在 CSS 臂上尤其要紧**：843 门禁的前置检查盯的是**JS chunk**
   （找「妆容素材」）⟹ ⟹ 改了 **CSS** 时那个标记**不会变** ⟹ ⟹ 门禁可能在
   **旧 CSS** 上跑 ⟹ ⟹ 阴性会「没翻红」⟹ ⟹ 而那不是「断言没牙」，是「环境没跟上」。
   ⟹ ⟹ 正解是把缺陷打在 **TSX** 上（内联样式 ＋ 字符串标记）⟹ ⟹ 标记一定出现在
   **下发的 JS chunk** 里 ⟹ ⟹ 等得到。

## ★★ 字段分工（★ 这是本批**第一次**把「字段不重叠」当硬约束设计）

| 判据 | 读什么 | 归谁 |
| --- | --- | --- |
| S1 | 卡片**文案**（aria ＋ 名字）＋ chip **文案顺序** | 843 门禁 |
| S2 | **几何**（盒） | 843 门禁 |
| S3 | **计算样式** | 843 门禁 |
| S4 | **数量**（每个分类几张卡）＋ **选中态**（选中的 chip／选中的卡） | 843 门禁 |
| S5 | **点卡之后**的状态转移 | 843 门禁 |
| S6 | **分段结构**（页签行在不在） | 843 门禁 |
| S7 | **README** 文本 | 843 门禁 |

★ S4 原先还比「清单逐条相等」⟹ ⟹ 那与 S1 **读同一批文案** ⟹ ⟹ 「改名」这种缺陷
  会**同时**翻 S1 与 S4 ⟹ ⟹ 阴性臂就**证明不了**哪一条有牙
  ⟹ ⟹ 本批把 S4 改成比**数量**（★ 文案那一条**没有删** ⟹ ⟹ 它在 S1 里，更严）。

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 把「卧蚕」分类里一张卡**改名**（「自然」→「天生」） | S1 | 只改**文案**；★ **同字数** ⟹ 名字盒 22px 不变 ⟹ S2 不红；★ S4 只比**数量** ⟹ 不红 |
| N2 | 妆造块的**卡片**整体下移 6px（> ±1px 容差） | S2 | 只动几何 ⟹ S1（文案）／S3（样式）不读它 |
| N3 | 选中 chip 的底色改成**半透明黑**（源站是**纯白**） | S3 | 只动**颜色** ⟹ 盒与其它样式不变 ⟹ S2 不受影响 |
| N4 | 让**第一枚** chip 永远呈选中态 ⟹ ⟹ 每个分类**两个** chip 同时选中 | S4 | 只动**选中态** ⟹ 文案／几何／样式／数量都不变 |
| N5 | 卡片的 `onClick` 不再切换选中态 | S5 | 只动**点击** ⟹ S1–S4／S6–S7 不读卡片选中态 |
| N6 | 分段切换失效（**页签行在第二段仍然显示**） | S6 | 只动**结构** ⟹ S1–S5／S7 不读页签行 |
| N7 | README 里的 **mock** 标注全部删掉 | S7 | 只动**文档** |
| N8 | 「卧蚕」分类的**默认选中卡**不是「无」 | S4 | 只动**默认选中态** ⟹ 文案／几何／数量不变；★ S5 点的是**美瞳** ⟹ 不受影响 |

★ N4 与 N8 都翻 S4 ⟹ ⟹ 它们分别钉住 S4 的**两条子判据**
（**恰好一个**选中的 chip ／ **选中卡**与源站一致）⟹ ⟹ S4 两条都有牙。

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
BATCH = ROOT / "docs/research/liblib-canvas-batch843-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch843.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
README = BATCH / "README.md"

# ★ chip 元素上的标记位（JSX **属性位置** ⟹ 放进函数体会变成无效 JSX）
# ★★ **同行插入** ⟹ ⟹ 变异**行数中性** ⟹ ⟹ 不会让任何「按行号断言」的门禁漂移
_MARK_CHIP = (
    '              data-character-editor-chip={item.id}\n',
    '              data-character-editor-chip={item.id} data-neg843="__MARK__"\n',
)

# ★ 卡片元素上的标记位
_MARK_CARD = (
    '              data-character-editor-makeup-name={name}\n',
    '              data-character-editor-makeup-name={name} data-neg843="__MARK__"\n',
)

ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 只改**文案**（★ **同字数** ⟹ 名字盒 22px 不变 ⟹ S2 的几何不受影响；
        #   ★ S4 只比**数量** ⟹ 不受影响 ⟹ ⟹ 只翻 S1）
        "mutate": (lambda s: s.replace(
            '  { id: "wochan", label: "卧蚕", cards: ["素颜", "自然", "妈生感", "可爱", "无辜", "月牙", "减龄", "亮片"] },',
            '  { id: "wochan", label: "卧蚕", cards: ["素颜", "天生", "妈生感", "可爱", "无辜", "月牙", "减龄", "亮片"] },', 1)
            .replace(_MARK_CHIP[0], _MARK_CHIP[1].replace("__MARK__", "neg843n1"), 1)),
        "marker": "neg843n1",
        "note": "「卧蚕」分类里「自然」改成「天生」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '    { kind: "makeup", h4Top: 20, chipTop: 50, cardTop: 152 },',
            '    { kind: "makeup", h4Top: 20, chipTop: 50, cardTop: 158 },', 1)
            .replace(_MARK_CHIP[0], _MARK_CHIP[1].replace("__MARK__", "neg843n2"), 1)),
        "marker": "neg843n2",
        "note": "妆造块的卡片整体下移 6px ⟹ 几何与源站差 6px",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★★ **为什么不是改 CSS**：dev 的 CSS 管线会**剥掉注释** ⟹ ⟹ 注释当标记
        #   **永远等不到**；而且声明值还会被压缩 ⟹ ⟹ 也不可靠。
        #   ⟹ ⟹ 正解：**把缺陷打在 TSX 上**（内联样式）⟹ ⟹ 标记是字符串字面量
        #   ⟹ ⟹ 一定出现在下发的 JS chunk 里 ⟹ ⟹ 等得到。
        # ★★ **为什么必须并进已有的 `style` prop**：另加一个 `style` 属性 ⟹ ⟹
        #   **后者覆盖前者**（JSX 同名属性后者胜）⟹ ⟹ `top/left` 会把背景**顶掉**
        #   ⟹ ⟹ 注入**根本没生效** ⟹ ⟹ 阴性会「没翻红」⟹ ⟹ 而那不是「断言没牙」。
        "mutate": (lambda s: s.replace(
            '                left: `${24 + (ci % 4) * 56}px`,\n'
            '              }}',
            '                left: `${24 + (ci % 4) * 56}px`, background: on ? "rgba(0, 0, 0, 0.4)" : undefined,\n'
            '              }}', 1)
            .replace(_MARK_CHIP[0], _MARK_CHIP[1].replace("__MARK__", "neg843n3"), 1)),
        "marker": "neg843n3",
        "note": "选中 chip 的底色改成半透明黑 ⟹ 「白底黑字」这条红",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 第一枚 chip **永远**呈选中态 ⟹ ⟹ 切到别的分类时**两个** chip 同时选中
        #   ⟹ ⟹ 只翻 S4 的「**恰好一个**选中的 chip」那一条
        "mutate": (lambda s: s.replace(
            '          const on = item.id === makeupCat;',
            '          const on = item.id === makeupCat || item.id === MAKEUP_CATEGORIES[0].id;', 1)
            .replace(_MARK_CHIP[0], _MARK_CHIP[1].replace("__MARK__", "neg843n4"), 1)),
        "marker": "neg843n4",
        "note": "第一枚 chip 永远选中 ⟹ 每个分类有两个选中的 chip ⟹ 只翻 S4",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '              onClick={() =>\n'
            '                setMakeupSel((prev) => ({ ...prev, [cat.id]: name }))\n'
            '              }',
            '              onClick={() => undefined}\n'
            '              data-neg843="neg843n5"\n'
            '              aria-disabled={false}', 1)),
        "marker": "neg843n5",
        "note": "卡片的 onClick 不再切换选中态 ⟹ 点「美瞳 琥珀」后 aria-pressed 不变 true",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★ 分段切换失效：让页签行在**任何段**都显示
        #   ⟹ ⟹ 「页签行只在「脸部精修」段存在」这条结构事实就红
        "mutate": (lambda s: s.replace(
            '            {segment === "face" ? (',
            '            {true ? (', 1)
            .replace(_MARK_CHIP[0], _MARK_CHIP[1].replace("__MARK__", "neg843n6"), 1)),
        "marker": "neg843n6",
        "note": "分段切换失效（页签行在第二段仍然显示）⟹ 「页签行只在脸部精修段存在」这条红",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        "mutate": (lambda s: re.sub(r"[Mm][Oo][Cc][Kk]", "占位", s)),
        "note": "README 里的 mock 标注全部删掉 ⟹ 「mock 出现次数 >= 3」这条红",
    },
    {
        "id": "N8",
        "expect": "S4",
        "files": [PANEL],
        # ★ 「卧蚕」分类的**默认选中卡**不是「无」 ⟹ ⟹ 只翻 S4 的「选中卡与源站一致」
        #   ⟹ ⟹ ★ S5 点的是**美瞳**的卡 ⟹ ⟹ S5 不受影响
        "mutate": (lambda s: s.replace(
            '          const on = (makeupSel[cat.id] ?? "无") === name;',
            '          const on = (makeupSel[cat.id] ?? (cat.id === "wochan" ? cat.cards[0] : "无")) === name;', 1)
            .replace(_MARK_CARD[0], _MARK_CARD[1].replace("__MARK__", "neg843n8"), 1)),
        "marker": "neg843n8",
        "note": "「卧蚕」默认选中卡不是「无」 ⟹ 只翻 S4 的「选中卡」那一条",
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
        "batch": 843,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）；"
                "★ S4 与 S1 的**字段已拆开**（S1 比文案、S4 比数量）⟹ ⟹ 「改名」只翻 S1",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
