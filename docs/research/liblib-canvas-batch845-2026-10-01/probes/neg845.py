#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | 滑杆**文案**（名字清单） ＋ 有无空态 |
| S2 | **几何**（盒：名字／输入／数值／圆心点／「i」） |
| S3 | **计算样式**（名字／数值／「i」／圆心点底色） |
| S4 | **量程属性**（min／max／step／初值） ＋ 分布条数 |
| S5 | **点完之后**的状态（控件值／渲染数字／圆心点位置） |
| S6 | **结构事实**（内容起点／滚动高／这一段与切回后的页签数） |
| S7 | **README** 文本 |

## ★ 两条「为什么这条臂不写成更直觉的样子」

1. **N2 不是「整体下移 6px」**：整体下移会**连带**改掉这一段的**内容起点**
   ⟹ ⟹ 那会**同时翻 S6** ⟹ ⟹ 违反「每条臂只翻它自己那一条」。
   ⟹ ⟹ 所以这一条臂改成「第 2～18 条下移 6px（第一条不动）」
   ⟹ ⟹ 几何（S2）红，内容起点（S6）不动 ✓
2. **N4 不是「把 min 改成 0」**：改 min/max 会**连带**改变圆心点的初始位置
   ⟹ ⟹ 圆心点的盒（S2）也会红 ⟹ ⟹ 同样违反分工。
   ⟹ ⟹ 所以这一条臂改 **`step`**（初始比例不变 ⟹ ⟹ 几何不动）⟹ ⟹ 只翻 S4 ✓

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「美臀」改名成「翘臀」 | S1 | ★ **同字数** ⟹ 名字盒 28px 不变 ⟹ S2 不红；S4 只比量程 ⟹ 不红 |
| N2 | 第 2～18 条滑杆下移 6px（第一条不动） | S2 | 只动几何 ⟹ S1（文案）／S3（样式）／S4（量程）不读它；★ 内容起点不动 ⟹ S6 不红 |
| N3 | 名字颜色改成 `#ededed` | S3 | 只动**颜色** ⟹ 盒与其它样式不变 ⟹ S2 不受影响 |
| N4 | 「丰胸」的 `step` 改成 2 | S4 | 只动**步进** ⟹ 初值与比例不变 ⟹ 几何不动 ⟹ S2 不红 |
| N5 | 滑杆的 onChange 把值**写死成 0** | S5 | 只动**赋值** ⟹ S1–S4／S6–S7 读的是初始态，不受影响 |
| N6 | 让页签行在**这一段**也出现 | S6 | 只动**页签行** ⟹ 内容与几何都不变 ⟹ S1–S5 不红 |
| N7 | README 里的 **mock** 标注全部删掉 | S7 | 只动**文档** |
| N8 | 圆心点底色改成 `#ededed` | S3 | 只动**底色** ⟹ 盒不变 ⟹ S2 不红 |

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
BATCH = ROOT / "docs/research/liblib-canvas-batch845-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch845.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
README = BATCH / "README.md"

# ★ 标记位（JSX **属性位置** ⟹ 同行插入 ⟹ 变异**行数中性**）
_MARK = (
    '          data-character-editor-slider-dot={item.id}\n',
    '          data-character-editor-slider-dot={item.id} data-neg845="__MARK__"\n',
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
        "mutate": (lambda s: with_mark(s.replace(
            '  { id: "body-hip", label: "美臀", info: false, min: -100, max: 100, step: 1 },',
            '  { id: "body-hip", label: "翘臀", info: false, min: -100, max: 100, step: 1 },', 1),
            "neg845n1")),
        "marker": "neg845n1",
        "note": "「美臀」改名成「翘臀」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        # ★ 只动**第 2～18 条**（第一条不动 ⟹ ⟹ 内容起点不变 ⟹ ⟹ S6 不红）
        "mutate": (lambda s: with_mark(s.replace(
            '          renderSlider(item, i, BODY_SLIDERS_TOP + i * SLIDER_STEP),',
            '          renderSlider(item, i, BODY_SLIDERS_TOP + (i === 0 ? 0 : 6) + i * SLIDER_STEP),', 1),
            "neg845n2")),
        "marker": "neg845n2",
        "note": "第 2～18 条滑杆下移 6px（第一条不动）⟹ 几何与源站差 6px",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★★ **并进已有的 style 属性**：JSX 里同名 `style` 属性**后者胜**
        #   ⟹ ⟹ 再加一个 style 属性 ⇒ 前面那个**整段失效** ⟹ ⟹ 变异等于没发生
        "mutate": (lambda s: with_mark(s.replace(
            '          style={{ top: `${top}px` }}',
            '          style={{ top: `${top}px`, color: "#ededed" }}', 1),
            "neg845n3")),
        "marker": "neg845n3",
        "note": "滑杆名字的颜色改成 #ededed（源站实测是纯白）⟹ 「外观」这条红",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 改 **step**（★ 不改 min/max ⟹ ⟹ 初值比例不变 ⟹ ⟹ 几何不动 ⟹ ⟹ 只翻 S4）
        "mutate": (lambda s: with_mark(s.replace(
            '  { id: "body-breast", label: "丰胸", info: false, min: -100, max: 100, step: 1 },',
            '  { id: "body-breast", label: "丰胸", info: false, min: -100, max: 100, step: 2 },', 1),
            "neg845n4")),
        "marker": "neg845n4",
        "note": "「丰胸」的 step 改成 2（源站实测是 1）⟹ 「量程」这条红",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        # ★ onChange 把值**写死成 0** ⟹ ⟹ 点轨道两端都不动 ⟹ ⟹ 「真交互」这条红
        "mutate": (lambda s: with_mark(s.replace(
            '              [item.id]: Number(event.target.value),',
            '              [item.id]: 0,', 1),
            "neg845n5")),
        "marker": "neg845n5",
        "note": "滑杆的 onChange 把值写死成 0 ⟹ 点最左/最右都不变",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★★ 「页签行在不该出现的段也出现」——★ 这正是 clone 843 之前的**老毛病**
        "mutate": (lambda s: with_mark(s.replace(
            '            {segment === "face" ? renderTabs() : null}',
            '            {segment === "face" || segment === "body" ? renderTabs() : null}', 1),
            "neg845n6")),
        "marker": "neg845n6",
        "note": "页签行在「身材塑形」段也出现 ⟹ 「这一段没有标题行」这条红",
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
        "expect": "S3",
        "files": [PANEL],
        # ★ 圆心点的**底色**（★ 像素实测 ＝ 70 ＝ #464646）⟹ ⟹ 只动底色 ⟹ ⟹ 盒不变
        "mutate": (lambda s: with_mark(s.replace(
            '          style={{ left: `${24 + thumbX - 1}px`, top: `${top + 41.4}px` }}',
            '          style={{ left: `${24 + thumbX - 1}px`, top: `${top + 41.4}px`, background: "#ededed" }}', 1),
            "neg845n8")),
        "marker": "neg845n8",
        "note": "圆心点底色改成 #ededed ⟹ 「外观」这条红（盒不变 ⟹ S2 不红）",
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
        "batch": 845,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）；"
                "★ N2 只移第 2～18 条、N4 改 step ⟹ 都是为了**不连累** S6／S2",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
