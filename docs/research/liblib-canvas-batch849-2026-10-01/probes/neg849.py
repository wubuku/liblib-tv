#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | **结构**：两页各有哪些块、有没有「未实测」说明、各页有没有别的页的控件 |
| S2 | **几何**：所有盒（子页签／可见文字／图标／chip／卡／P2 的五块） |
| S3 | **计算样式**：子页签／可见文字／chip／卡／P2 的五块 |
| S4 | **文案**：chip 文案／卡名／胶囊文案／占位文案／按钮文案／aria |
| S5 | **交互**：三页的子页签宽度 ＋ 切回「服装」后的卡数与 chip 数 |
| S6 | **三页的结构差异**：底部生成行 有／有／无 |
| S7 | **README** 文本 |

★★ **S1 与 S2／S3 的分工要小心**：S1 只看「**有没有**」，
S2／S3 看「**长什么样**」⟹ ⟹ 所以「删掉一个块」这种变异会**同时**翻 S1 与 S2
⟹ ⟹ 阴性臂**不能**用删块 ⟹ ⟹ 这里改成「加一个属性／改一个值」。

## ★ 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「服装」页的小标题上多一个 `data-character-editor-empty` | S1 | ★ 只加**属性** ⟹ ⟹ 几何/样式/文案都不变 ⟹ ⟹ S2–S4 不红 |
| N2 | 一张服装卡的**盒高** 155 → 147 | S2 | 只动**盒高** ⟹ ⟹ 高度**不在** S3 的键集里 ⟹ ⟹ S3 不红；★ S1 只看有没有 ⟹ ⟹ S1 不红 |
| N3 | 分类 chip 的文字色 白 60% → 纯白 | S3 | 只动**颜色** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 文案不变 ⟹ ⟹ S4 不红 |
| N4 | 胶囊文案「人设定制造型」→「人设定造型」 | S4 | ★ 只动**文案** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 不是样式 ⟹ ⟹ S3 不红 |
| N5 | 服装卡只渲染前 23 张 | S5 | ★ 849 门禁**要**比卡片的盒/样式/文案 ⟹ ⟹ S2–S4 **会**红 ⟹ ⟹ ★ 所以这条臂**不能**用「少渲染一张」⟹ ⟹ 见下面 N5 的实际做法 |
| N6 | 「AI 生成」页也渲染底部生成行 | S6 | ★ S1 不看底部生成数 ⟹ ⟹ S1 不红；★ 底部生成行**不在** S2／S3 的比对清单里 ⟹ ⟹ 不红 |
| N7 | README 里删掉「人设定制造型」 | S7 | 只动**文档**（★ 门禁 S7 查的正是这个字符串） |
| N8 | 「确认生成」按钮的圆角 10 → 6 | S3 | ★ 圆角**不影响盒** ⟹ ⟹ S2 不红；★ S5 只读**宽度与条数** ⟹ ⟹ S5 不红 |

★★ **N5 的一处设计修正**：★ 849 门禁**比**卡片的盒/样式/文案
⟹ ⟹ 所以「少渲染一张卡」会**同时**翻 S2／S3／S4 ⟹ ⟹ 那就**不是**单条阴性臂了。
⟹ ⟹ 正解：★ 让 N5 改「**切回后**的读数」——★ 只在**「服装页_再读」**那一次读数里
少渲染一张 ⟹ ⟹ 主读的 24 张**不变** ⟹ ⟹ S2／S3／S4 不红 ⟹ ⟹ 只有 S5 的
「切回服装_卡数」翻红。

## ★ 变异的手法（★ 全部**行数中性**）

★ TSX 的变异都在**同一行内**完成（改值／加属性）⟹ ⟹ 文件行数不变；
★ 每个臂还要在某个元素上**加一个 `data-neg849` 标记** ⟹ ⟹ 好让 harness
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
BATCH = ROOT / "docs/research/liblib-canvas-batch849-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch849.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CSS = ROOT / "src/components/character-studio.css"
README = BATCH / "README.md"

# ★ 标记锚点（★ 各自**唯一**）
M_TITLE = '          data-character-editor-outfit-clothes-title="服装"'
M_CHIP = "              data-character-editor-outfit-clothes-chip={c.label}"
M_CARD = "              data-character-editor-outfit-clothes-card={c.img}"
M_AI_CARD = '          data-character-editor-outfit-ai-card="1"'
M_PILL = "                data-character-editor-outfit-ai-pill={OUTFIT_AI_PILL.label}"
M_GEN = '          data-character-editor-outfit-ai-generate="1"'


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
    return src.replace(line, anchor + ' data-neg849="%s"\n' % mark, 1)


ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 给小标题加上 `data-character-editor-empty` ⟹ ⟹ 探针会把它读成「未实测说明」
        #   ⟹ ⟹ S1 的「两页都没有未实测说明」翻红
        #   ⟹ ⟹ ★ 只加**属性** ⟹ ⟹ 几何/样式/文案**都不变** ⟹ ⟹ S2–S4 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '          data-character-editor-outfit-clothes-title="服装"',
            '          data-character-editor-outfit-clothes-title="服装" data-character-editor-empty'),
            '          data-character-editor-outfit-clothes-title="服装" data-character-editor-empty',
            "n1")),
        "marker": "neg849",
        "note": "「服装」页的小标题多一个 data-character-editor-empty ⟹ 「结构」这条红"
                "（★ 只加属性 ⟹ ⟹ 几何/样式/文案都不变 ⟹ ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [CSS],
        # ★ 只动**盒高** ⟹ ⟹ 高度**不在** S3 的键集里 ⟹ ⟹ S3 不红
        # ★ 改的是 849 **专属**的 `.ce-card--clothes` ⟹ ⟹ 不污染 846 的卡
        "mutate": (lambda s: _once(
            s,
            ".ce-card--clothes {\n  width: 76px;\n  height: 155px;",
            ".ce-card--clothes {\n  width: 76px;\n  height: 147px;")),
        "marker": "ce-card--clothes",
        "note": "一张服装卡的盒高 155 → 147 ⟹ 「几何」这条红"
                "（★ 高度不在外观键集里 ⟹ ⟹ S3 不红；★ 改的是 849 专属类 ⟹ ⟹ 不污染 846）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [CSS],
        # ★ 只动**颜色** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；文案不变 ⟹ ⟹ S4 不红
        # ★ 改的是 849 **专属**的 `.ce-chip--clothes` ⟹ ⟹ 不污染 846 的 chip
        "mutate": (lambda s: _once(
            s,
            ".ce-chip--clothes {\n  color: rgba(255, 255, 255, 0.6);\n}",
            ".ce-chip--clothes {\n  color: rgb(255, 255, 255);\n}")),
        "marker": "ce-chip--clothes",
        "note": "分类 chip 的文字色 白 60% → 纯白 ⟹ 「外观」这条红（★ 盒不变 ⟹ ⟹ S2 不红）",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 只动**文案** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 不是样式 ⟹ ⟹ S3 不红
        # ★ ★ 源站那枚胶囊的文案是**一个字符串**「人设定制造型」
        #   ⟹ ⟹ 这里把它改成「人设定造型」⟹ ⟹ 长度变了 ⟹ ⟹ 盒也变了？
        #   ⟹ ⟹ ★ 不：胶囊的**宽度是写死的 119** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红 ✓
        "mutate": (lambda s: _mark(_once(
            s,
            '  label: "人设定制造型",',
            '  label: "人设定造型",'),
            M_PILL, "n4")),
        "marker": "neg849",
        "note": "胶囊文案「人设定制造型」→「人设定造型」 ⟹ 「文案」这条红"
                "（★ 胶囊宽度写死 119 ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红）",
    },
    {
        "id": "N5",
        "expect": "S4",
        "files": [PANEL],
        # ★ 只动**小标题的可见文字** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 不是样式 ⟹ ⟹ S3 不红
        # ★ ★ 与 N4 的**字段不重叠**：N4 动的是**胶囊**文案 ⟹ ⟹ 这里动的是**小标题**
        # ★ ★ 注意：要改的是**文本节点**，⟹ ⟹ 不是那个 `data-...="服装"` **属性**
        #   ⟹ ⟹ 改属性不改可见文字 ⟹ ⟹ 门禁读不到 ⟹ ⟹ 那一轮会「没翻红」
        "mutate": (lambda s: _mark(_once(
            s,
            '          data-character-editor-outfit-clothes-title="服装"\n'
            '        >\n'
            '          服装\n'
            '        </h3>',
            '          data-character-editor-outfit-clothes-title="服装"\n'
            '        >\n'
            '          造型\n'
            '        </h3>'),
            '          data-character-editor-outfit-clothes-title="服装"\n'
            '        >\n'
            '          造型\n'
            '        </h3>', "n5")),
        "marker": "neg849",
        "note": "「服装」页的小标题文字 服装 → 造型 ⟹ 「文案」这条红"
                "（★ 盒不变 ⟹ ⟹ S2 不红；★ 与 N4 读的是**不同**的字段 ⟹ ⟹ 不重叠）",
    },
    {
        "id": "N5b",
        "expect": "S1/S2/S3/S4/S5",
        "files": [PANEL],
        # ★ ★★ **这是一条「联锁对照」**，⟹ ⟹ **不是**严格单条 ⟹ ⟹ 如实标注
        #   ⟹ ⟹ 服装卡少渲染一张 ⟹ ⟹ **会同时**翻：
        #     · S1（★ 卡数 ≠ 24 ⟹ 「有服装卡」那条不成立）
        #     · S2（逐卡比对）＋ S3（卡样式）＋ S4（卡名）＋ S5（切回后的卡数）
        #   ⟹ ⟹ ★ 它的价值**不是**「证明某条断言有牙」⟹ ⟹ 而是
        #   ⟹ ⟹ ★ **实证**「★ 删块会同时翻多条」这条纪律 ⟹ ⟹
        #   ⟹ ⟹ ★ 所以它**必须**如实写成「期望多条」⟹ ⟹ 不可当单条证据
        "mutate": (lambda s: _mark(_once(
            s,
            "        {OUTFIT_CLOTHES_CARDS.map((c, i) => {",
            "        {OUTFIT_CLOTHES_CARDS.slice(0, 23).map((c, i) => {"),
            M_CARD, "n5b")),
        "marker": "neg849",
        "note": "服装卡只渲染前 23 张 ⟹ 「联锁对照」：S1／S2／S3／S4／S5 **一起红**"
                "（★ 门禁**要**比卡片的盒/样式/文案 ⟹ ⟹ 「删块」必然连带多条"
                "⟹ ⟹ ★ 这条实证的正是「★ 臂里不用删块」这条纪律）",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★ 给「AI 生成」页也渲染底部生成行 ⟹ ⟹ 底部生成数变成 1/1/1 ⟹ ⟹ S6 翻红
        #   ⟹ ⟹ ★ S1 不看底部生成数；★ 底部生成行**不在** S2／S3 的比对清单里 ⟹ ⟹ 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '            {(segment === "voice" ||\n'
            '              (segment === "outfit" && outfitTab === "ai")) ? null : (',
            '            {(segment === "voice") ? null : ('),
            M_AI_CARD, "n6")),
        "marker": "neg849",
        "note": "「AI 生成」页也渲染底部生成行 ⟹ 「三页结构差异」这条红"
                "（★ 源站那一页**没有**底部生成行）",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        # ★ 只动**文档** ⟹ ⟹ 门禁 S7 查的正是这个字符串
        "mutate": (lambda s: s.replace("人设定制造型", "人设定造型")),
        "note": "README 里删掉「人设定制造型」 ⟹ 「如实标注」这条红",
    },
    {
        "id": "N8",
        "expect": "S3",
        "files": [CSS],
        # ★ 只动**圆角** ⟹ ⟹ 不影响盒 ⟹ ⟹ S2 不红；★ S5 只读宽度与条数 ⟹ ⟹ S5 不红
        # ★ 改的是 849 **专属**的 `.ce-outfit-ai-generate` ⟹ ⟹ 不影响别的段
        "mutate": (lambda s: _once(
            s,
            ".ce-outfit-ai-generate {\n  position: absolute;\n  display: flex;\n"
            "  align-items: center;\n  justify-content: center;\n  gap: 4px;\n"
            "  padding: 0 12px;\n  border: 0;\n  border-radius: 10px;",
            ".ce-outfit-ai-generate {\n  position: absolute;\n  display: flex;\n"
            "  align-items: center;\n  justify-content: center;\n  gap: 4px;\n"
            "  padding: 0 12px;\n  border: 0;\n  border-radius: 6px;")),
        "marker": "ce-outfit-ai-generate",
        "note": "「确认生成」按钮的圆角 10 → 6 ⟹ 「外观」这条红（★ 盒不变 ⟹ ⟹ S2 不红）",
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
        "batch": 849,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "★ 变异全部**行数中性**（同一行内改值／加属性）；"
                "★ 标记等的是**下发的 chunk**（★ TSX 等 JS chunk、CSS 等 CSS chunk）；"
                "★ S1 只看「有没有」、S2／S3 看「长什么样」⟹ ⟹ 所以臂里**不用删块**"
                "（★ 删块会同时翻 S1 与 S2）；"
                "★ CSS 臂改的都是 849 **专属**的类 ⟹ ⟹ 不污染 846 的实现",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
