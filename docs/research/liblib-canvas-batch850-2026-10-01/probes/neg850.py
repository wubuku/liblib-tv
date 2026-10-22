#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段尽量**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | **结构与层级**：图区是不是四层、遮罩是不是三层、按钮是不是两枚、分隔线在不在 |
| S2 | **几何**：full 态（identity transform）的**全部盒** |
| S3 | **变换**：两态的 transform 矩阵 ＋ transform-origin ＋ transition 串 |
| S4 | **外观**：渐变（逐字符）＋ backdrop-filter ＋ 遮罩透明度 ＋ 按钮圆角／底色／文字色 ＋ 分隔线底色 ＋ 工具行底色 |
| S5 | **交互**：默认态／点全身后／点回半身后这**三刻**的矩阵 ＋ 遮罩透明度 ＋ blur |
| S6 | **间隙与分隔线**：工具行三个孩子的盒 ＋ 分隔线两侧的间隙 |
| S7 | **连带没坏 ＋ 如实标注**：左下三工具 ＋ 取景容器与两枚按钮的位置 ＋ 底部生成行 ＋ 预览区文字 |

## ★ 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 删掉 `.ce-figure-inner` 这层**纯包裹** | S1 | ★ 父级从 `.ce-figure-inner` 变成 `.ce-figure` ⟹ ⟹ 两者都是 467×550 ⟹ ⟹ **几何一模一样** ⟹ ⟹ S2 不红 |
| N2 | 图盒宽 425 → 420 | S2 | 只动**盒宽** ⟹ ⟹ S1 只看有没有 ⟹ ⟹ 不红；★ S4／S6／S7 不读图盒 |
| N3 | 半身态的 transition 去掉 `rotate` | S3 | ★ S4／S5 都不读变换层的 transition ⟹ ⟹ 不红 |
| N4 | 渐变里一个 alpha 0.075 → 0.08 | S4 | 只动**背景** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红 |
| N5 | 选中态按钮文字色 #fff → #feffff | S4 | ★ 与 N4 读的是**不同**的字段（渐变 vs 文字色）⟹ ⟹ 不重叠 |
| N6 | 工具行 gap 4 → 9 | S2／S6 | ★ ★ **联锁**：工具行盒宽 73 → 81 ⟹ ⟹ S2 的「工具行盒」也红 ⟹ ⟹ 如实标注 |
| N7 | 左下工具的 aria「撤销」→「撤銷」 | S7 | ★ 只改**aria** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ S1／S4 不读它 |
| N8 | 全身态遮罩 opacity 0 → 1 | S4／S5 | ★ ★ **联锁**：S4 也比「遮罩透明度·全身」⟹ ⟹ 如实标注 |
| N9 | 删掉渐变层那一整块 | S1／S2／S4 | ★ ★ **联锁对照**：★ 它的价值**不是**「证明某条断言有牙」⟹ ⟹ 而是**实证**「★ 删块会同时翻多条」⟹ ⟹ 必须如实写成「期望多条」 |

## ★ 变异的手法（★ 全部**行数中性**）

★ TSX 的变异都在**同一行内**完成（改值／加属性）⟹ ⟹ 文件行数不变；
★ 需要「删一层」的臂（N1／N9）⟹ ⟹ 把那一行**换成注释** ⟹ ⟹ 仍是**行数中性**；
★ 每个臂还要在某个元素上**加一个 `data-neg850` 标记** ⟹ ⟹ 好让 harness
等 dev server **真的重建完**（★ 只改 TSX 时，服务端 chunk 里会带上这个标记）。
★ CSS 的臂则等 **CSS chunk** 里出现标记（★ 见 `wait_for_marker`）。

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
BATCH = ROOT / "docs/research/liblib-canvas-batch850-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch850.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CSS = ROOT / "src/components/character-studio.css"

# ★ 标记锚点（★ 各自**唯一**）
M_ZOOM = '                  data-character-editor-figure-zoom'
M_FADE = '                data-character-editor-preview-mask-fade'


def _once(src: str, old: str, new: str) -> str:
    """★ 精确替换**唯一**一处（⟹ ⟹ 源串没匹配上就**报错**，⟹ ⟹ 不许默默没生效）。"""
    if src.count(old) != 1:
        raise SystemExit("锚点命中 %d 处（应为 1）：%r" % (src.count(old), old[:60]))
    return src.replace(old, new, 1)


def _mark(src: str, anchor: str, mark: str) -> str:
    """★ 在**同一行**上插一个标记属性 ⟹ ⟹ 变异**行数中性** ⟹ ⟹ 标记可被服务端 chunk 看到。"""
    line = anchor + "\n"
    if src.count(line) != 1:
        raise SystemExit("标记锚点命中 %d 处（应为 1）：%r" % (src.count(line), anchor[:60]))
    return src.replace(line, anchor + ' data-neg850="%s"\n' % mark, 1)


ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 把 `.ce-figure-inner` 这层**纯包裹**的类名改掉 ⟹ ⟹ 探针读不到它
        #   ⟹ ⟹ ★ **行数中性**（同一行内改类名）
        #   ⟹ ⟹ ★ 而且 inner 失去 `absolute inset-0` 之后 ⟹ ⟹ 变换层（absolute inset:0）
        #   ⟹ ⟹   的包含块变成 `.ce-figure`（也是 467×550）⟹ ⟹ **几何一模一样** ⟹ ⟹ S2 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '              <div className="ce-figure-inner">',
            '              <div className="ce-figure-inner-gone">'),
            M_ZOOM, "n1")),
        "marker": "neg850",
        "note": "把 `.ce-figure-inner` 这层纯包裹的类名改掉 ⟹ 「结构与层级」这条红"
                "（★ 变换层的包含块换成同样是 467×550 的 `.ce-figure` ⟹ ⟹ 几何不变 ⟹ ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [CSS],
        # ★ 只动**盒宽** ⟹ ⟹ S1 只看有没有 ⟹ ⟹ 不红；★ S4／S6／S7 不读图盒
        "mutate": (lambda s: _once(
            s,
            ".ce-figure-img {\n  position: absolute;\n  left: 50%;\n  top: 0;\n"
            "  width: 425px;\n  height: 542px;",
            ".ce-figure-img {\n  position: absolute;\n  left: 50%;\n  top: 0;\n"
            "  width: 420px;\n  height: 542px;")),
        "marker": "ce-figure-img",
        "note": "图盒宽 425 → 420 ⟹ 「几何」这条红（★ 只动盒宽 ⟹ ⟹ 其他判据不红）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [CSS],
        # ★ 只动**过渡串**（去掉 rotate）⟹ ⟹ 矩阵与原点不变 ⟹ ⟹ S4／S5 不读它
        "mutate": (lambda s: _once(
            s,
            "    scale 0.5s cubic-bezier(0.33, 0.68, 0, 1),\n"
            "    rotate 0.5s cubic-bezier(0.33, 0.68, 0, 1);",
            "    scale 0.5s cubic-bezier(0.33, 0.68, 0, 1);")),
        "marker": "ce-figure-zoom",
        "note": "半身态的过渡串少一个 rotate ⟹ 「变换」这条红"
                "（★ S4／S5 都不读变换层的过渡 ⟹ ⟹ 单条）",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [CSS],
        # ★ 只动**渐变里一个 alpha** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红
        "mutate": (lambda s: _once(
            s,
            "    rgba(36, 36, 36, 0.075) 9.904%,",
            "    rgba(36, 36, 36, 0.08) 9.904%,")),
        "marker": "ce-preview-mask-fade",
        "note": "渐变里一个 alpha 0.075 → 0.08 ⟹ 「外观」这条红（★ 逐字符比 ⟹ ⟹ 必红）",
    },
    {
        "id": "N5",
        "expect": "S4",
        "files": [CSS],
        # ★ 只动**选中态按钮的文字色** ⟹ ⟹ ★ 与 N4 读的是**不同**的字段
        "mutate": (lambda s: _once(
            s,
            ".ce-preview-tools .ce-tool.is-on { color: rgb(255, 255, 255); }",
            ".ce-preview-tools .ce-tool.is-on { color: rgb(254, 255, 255); }")),
        "marker": "ce-preview-tools",
        "note": "选中态按钮文字色 #fff → #feffff ⟹ 「外观」这条红"
                "（★ 与 N4 的字段不重叠 ⟹ ⟹ 两条臂互不干扰）",
    },
    {
        "id": "N6",
        "expect": "S2/S4/S6/S7",
        "files": [CSS],
        # ★ ★★ **联锁对照** ⟹ ⟹ **不是**严格单条 ⟹ ⟹ 如实标注
        #   ⟹ ⟹ 工具行的 gap 4 → 9 ⟹ ⟹ 容器实宽 73 → 81
        #   ⟹ ⟹ ⟹ **会同时**翻四条（★ 每一条读的字段都受影响）：
        #     · S2（工具行盒的宽 73 → 81、且两枚按钮的 x 跟着挪）
        #     · S4（S4 也比「工具行间隙」）
        #     · S6（间隙不再是 4）
        #     · S7（取景容器与两枚按钮的位置与 840 基线不同）
        "mutate": (lambda s: _once(
            s,
            "  gap: 4px;\n  height: 32px;\n  padding: 0;\n  z-index: 20;",
            "  gap: 9px;\n  height: 32px;\n  padding: 0;\n  z-index: 20;")),
        "marker": "ce-preview-tools",
        "note": "工具行 gap 4 → 9 ⟹ 「联锁对照」：S2／S4／S6／S7 **一起红**"
                "（★ 容器实宽、间隙值、间隙本身、以及与 840 基线的位置比"
                "⟹ ⟹ **四条判据都读它** ⟹ ⟹ 如实标注）",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [PANEL],
        # ★ 只改左下三工具里一枚的 **aria** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ S1／S4 不读它
        "mutate": (lambda s: _mark(_once(
            s,
            '              aria-label="撤销"\n'
            '              onClick={() => flash("clone mock：撤销未接真实历史栈")}',
            '              aria-label="撤銷"\n'
            '              onClick={() => flash("clone mock：撤销未接真实历史栈")}'),
            '              aria-label="撤銷"\n'
            '              onClick={() => flash("clone mock：撤销未接真实历史栈")}', "n7")),
        "marker": "neg850",
        "note": "左下三工具里「撤销」的 aria 改成「撤銷」 ⟹ 「连带没坏」这条红"
                "（★ 与 840 基线逐项比 ⟹ ⟹ 只有它会红）",
    },
    {
        "id": "N8",
        "expect": "S4/S5",
        "files": [CSS],
        # ★ ★★ **联锁对照** ⟹ ⟹ 如实标注
        #   ⟹ ⟹ 全身态的遮罩 opacity 0 → 1 ⟹ ⟹ S5 的「点全身后遮罩要变 0」红
        #   ⟹ ⟹ ⟹ S4 的「遮罩透明度·全身」也红（★ 两条读的是同一个字段）
        "mutate": (lambda s: _once(
            s,
            ".ce-preview-mask.is-full {\n  opacity: 0;",
            ".ce-preview-mask.is-full {\n  opacity: 1;")),
        "marker": "ce-preview-mask",
        "note": "全身态的遮罩 opacity 0 → 1 ⟹ 「联锁对照」：S4／S5 **一起红**"
                "（★ 两条判据读的是**同一个** opacity 字段 ⟹ ⟹ 如实标注）",
    },
    {
        "id": "N9",
        "expect": "S1/S2/S4",
        "files": [PANEL],
        # ★ ★★ **联锁对照** ⟹ ⟹ **不是**严格单条 ⟹ ⟹ 如实标注
        #   ⟹ ⟹ 把渐变层那个块的 **data 属性名**改掉 ⟹ ⟹ 探针读不到它
        #   ⟹ ⟹ ⟹ **效果等同删块** ⟹ ⟹ 但仍然**行数中性**（同一行内改）
        #   ⟹ ⟹ ⟹ **会同时**翻：S1（遮罩不是三层）＋ S2（渐变层盒没了）＋ S4（渐变没了）
        #   ⟹ ⟹ ★ 它的价值**不是**「证明某条断言有牙」⟹ ⟹ 而是
        #   ⟹ ⟹ ★ **实证**「★ 删块会同时翻多条」这条纪律
        #   ⟹ ⟹ ★ 标记用**改后的属性名**（★ 不用 `_mark` ⟹ ⟹ 那一行的缩进容易写错）
        "mutate": (lambda s: _once(
            s,
            '                data-character-editor-preview-mask-fade\n',
            '                data-character-editor-preview-mask-fade-gone\n')),
        "marker": "mask-fade-gone",
        "note": "把渐变层那个块的 data 属性名改掉 ⟹ 「联锁对照」：S1／S2／S4 **一起红**"
                "（★ 门禁**要**比遮罩的层级／盒／渐变 ⟹ ⟹ 「少一块」必然连带多条"
                "⟹ ⟹ ★ 这条实证的正是「★ 臂里不用删块」这条纪律）",
    },
]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def served_chunks() -> tuple:
    """返回 (全部 chunk 文本, CSS chunk 文本)。"""
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.(?:js|css)', html)))
    js, css = [], []
    for u in urls:
        try:
            body = urllib.request.urlopen(DEV_ORIGIN + u, timeout=60) \
                .read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        (css if u.endswith(".css") else js).append(body)
    return "\n".join(js), "\n".join(css)


def wait_for_marker(marker: str, want_css: bool, timeout: int = 240) -> bool:
    """等 dev server **真的重建完**。

    ★ TSX 的标记等 **JS chunk**；★ CSS 的改动等 **CSS chunk**
    ⟹ ⟹ 否则「CSS 改了但没重建」⟹ ⟹ 变异**没生效**⟹ ⟹ 门禁当然不会红
    ⟹ ⟹ 那会得到一个**假阴性**。
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            js, css = served_chunks()
            if want_css:
                if marker in css:
                    return True
            else:
                if marker in js:
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
    out = []
    for c in audit.get("checks", []):
        if not c.get("通过"):
            out.append(str(c.get("判据") or "").split(" ")[0])
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
            ready = True
            if arm.get("marker"):
                ready = wait_for_marker(arm["marker"],
                                       want_css=(CSS in arm["files"]))
            if not ready:
                reds = ["<未重建>"]
                print("%s %s ⟹ %s（期望 %s）  ★ **变异没被重建**（★ 多半是变异把代码改坏了）"
                      % ("FAIL", aid, reds, arm["expect"]))
                results.append({"臂": aid, "红": reds, "期望": arm["expect"],
                                "通过": False,
                                "说明": arm["note"] + " ★★ 变异未被重建（多半是语法错）"})
                continue
            out = run_gate()
            reds = failed_checks(out["audit"])
            # ★ ★ 单条臂要求**恰好**红那一条；★ 联锁臂要求**恰好**红它列的那几条
            expect_set = set(arm["expect"].split("/"))
            ok = (set(reds) == expect_set)
            print("%s %s ⟹ 红的是 %s（期望 %s）%s"
                  % ("PASS" if ok else "FAIL", aid, reds or "无",
                     arm["expect"], "" if ok else "  ★ 不符合预期"))
            if not ok:
                print("   判据明细：", json.dumps(out["audit"].get("checks"),
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
        "batch": 850,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "★ 变异全部**行数中性**（同一行内改值／加属性；★ 需要删层的臂改成注释行）；"
                "★ 标记等的是**下发的 chunk**（★ TSX 等 JS chunk、CSS 等 CSS chunk）；"
                "★ S1 只看「有没有」、S2 看「长什么样」⟹ ⟹ 所以臂里**尽量不用删块**"
                "（★ N1 删的是**纯包裹** ⟹ ⟹ 几何不变 ⟹ ⟹ 仍是单条）；"
                "★ N6／N8／N9 是**如实标注的联锁对照**⟹ ⟹ 不可当单条证据",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
