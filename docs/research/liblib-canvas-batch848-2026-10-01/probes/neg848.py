#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | **结构**：两页各有哪些块（空态／输入框／按钮／历史区）、有没有「未实测」说明、有没有残留音色卡 |
| S2 | **几何**：所有盒（页签／可见文字／图标／工具／滚动区／空态／P4 的七块） |
| S3 | **计算样式**：页签／可见文字／工具按钮／空态／P4 的六块 |
| S4 | **文案**：空态／占位／按钮／角标数字／历史标题／历史空态 |
| S5 | **交互**：三页的页签宽度 ＋ 切回「音色库」后的卡数与工具数 |
| S6 | **三页的结构差异**：工具数 2／2／0、滚动区 有／有／无 |
| S7 | **README** 文本 |

★★ **S1 与 S2／S3 的分工要小心**：S1 只看「**有没有**」，
S2／S3 看「**长什么样**」⟹ ⟹ 所以「删掉一个块」这种变异会**同时**翻 S1 与 S2
⟹ ⟹ 阴性臂**不能**用删块 ⟹ ⟹ 这里改成「加一个属性／改一个值」。

## ★ 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「我的音色」页的空态上多一个 `data-character-editor-empty` | S1 | ★ 只加**属性** ⟹ ⟹ 几何/样式/文案都不变 ⟹ ⟹ S2–S4 不红；★ 属性不进文案 ⟹ ⟹ S4 不红 |
| N2 | 空态高度 96 → 88 | S2 | 只动**盒高** ⟹ ⟹ 高度**不在** S3 的键集里 ⟹ ⟹ S3 不红；★ S1 只看有没有 ⟹ ⟹ S1 不红 |
| N3 | 空态文字色 白 60% → 纯白 | S3 | 只动**颜色** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 文案不变 ⟹ ⟹ S4 不红 |
| N4 | 输入框占位文案改两个字（「补充输入」→「补充录入」） | S4 | ★ 占位不是**可见文字** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；★ 不是样式 ⟹ ⟹ S3 不红 |
| N5 | 音色卡列表只渲染前 19 条 | S5 | ★ 848 门禁**不**比卡片的盒/样式/文案 ⟹ ⟹ S2–S4 不红；★ S1 只看「我的音色」「AI 生成」两页的卡数（仍是 0）⟹ ⟹ S1 不红 |
| N6 | 「AI 生成」页也渲染工具行 | S6 | ★ S1 不看工具数 ⟹ ⟹ S1 不红；★ S2／S3 只比**「我的音色」页**的工具 ⟹ ⟹ 不红；★ 工具行是绝对定位 ⟹ ⟹ P4 的七块不动 ⟹ ⟹ S2 不红 |
| N7 | README 里的「21」全换成「二十一」 | S7 | 只动**文档**（★ 门禁 S7 查的正是这个数字） |
| N8 | 「生成音色」按钮的圆角 10 → 6 | S3 | ★ 圆角**不影响盒** ⟹ ⟹ S2 不红；★ S5 只读**宽度与条数** ⟹ ⟹ S5 不红 |

## ★ 变异的手法（★ 全部**行数中性**）

★ TSX 的变异都在**同一行内**完成（改值／加属性）⟹ ⟹ 文件行数不变；
★ 每个臂还要在某个元素上**加一个 `data-neg848` 标记** ⟹ ⟹ 好让 harness
等 dev server **真的重建完**（★ 只改 TSX 时，服务端 chunk 里会带上这个标记）。

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
BATCH = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch848.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
README = BATCH / "README.md"

# ★ 标记锚点（★ 各自**唯一**）
M_EMPTY = '          data-character-editor-voice-empty="mine"'
M_TA = "        data-character-editor-voice-textarea"
M_GEN = "        data-character-editor-voice-generate"
M_AI = "      data-character-editor-voice-ai"
M_CARD = "              data-character-editor-voice-card={v.name}"


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
    return src.replace(line, anchor + ' data-neg848="%s"\n' % mark, 1)


ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 给空态加上 `data-character-editor-empty` ⟹ ⟹ 探针会把它读成「未实测说明」
        #   ⟹ ⟹ S1 的「两页都没有未实测说明」翻红
        #   ⟹ ⟹ ★ 只加**属性** ⟹ ⟹ 几何/样式/文案**都不变** ⟹ ⟹ S2–S4 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '          data-character-editor-voice-empty="mine"',
            '          data-character-editor-voice-empty="mine" data-character-editor-empty'),
            '          data-character-editor-voice-empty="mine" data-character-editor-empty',
            "n1")),
        "marker": "neg848",
        "note": "「我的音色」页的空态多一个 data-character-editor-empty ⟹ 「结构」这条红"
                "（★ 只加属性 ⟹ ⟹ 几何/样式/文案都不变 ⟹ ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        # ★ 只动**盒高** ⟹ ⟹ 高度**不在** S3 的键集里 ⟹ ⟹ S3 不红
        "mutate": (lambda s: _mark(_once(s, "  h: 96,", "  h: 88,"), M_EMPTY, "n2")),
        "marker": "neg848",
        "note": "空态高度 96 → 88 ⟹ 「几何」这条红（★ 高度不在外观键集里 ⟹ ⟹ S3 不红）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★ 只动**颜色** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红；文案不变 ⟹ ⟹ S4 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '  fontSize: "12px",\n  lineHeight: "16px",\n'
            '  color: "rgba(255, 255, 255, 0.6)",\n};',
            '  fontSize: "12px",\n  lineHeight: "16px",\n'
            '  color: "rgb(255, 255, 255)",\n};'),
            M_EMPTY, "n3")),
        "marker": "neg848",
        "note": "空态文字色 白 60% → 纯白 ⟹ 「外观」这条红（★ 盒不变 ⟹ ⟹ S2 不红）",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 只动**占位文案** ⟹ ⟹ 占位不是可见文字 ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红
        "mutate": (lambda s: _mark(_once(
            s,
            'placeholder: "默认基于当前人设生成，可以补充输入音色特征...",',
            'placeholder: "默认基于当前人设生成，可以补充录入音色特征...",'),
            M_TA, "n4")),
        "marker": "neg848",
        "note": "输入框占位文案改两个字 ⟹ 「文案」这条红（★ 盒不变 ⟹ ⟹ S2 不红）",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        # ★ 只让**列表少一条** ⟹ ⟹ 848 门禁**不**比卡片的盒/样式/文案 ⟹ ⟹ S2–S4 不红
        "mutate": (lambda s: _mark(_once(
            s, "{VOICES.map((v) => {", "{VOICES.slice(0, 19).map((v) => {"), M_CARD, "n5")),
        "marker": "neg848",
        "note": "音色卡只渲染前 19 条 ⟹ 「交互」这条红（★ 848 门禁不比卡片 ⟹ ⟹ S2–S4 不红）",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★ 给「AI 生成」页也渲染工具行 ⟹ ⟹ 工具数变成 2/2/2 ⟹ ⟹ S6 翻红
        #   ⟹ ⟹ ★ S1 不看工具数；★ S2／S3 只比**「我的音色」页**的工具 ⟹ ⟹ 不红
        "mutate": (lambda s: _mark(_once(
            s, "                  renderVoiceAi()",
            "                  <>{renderVoiceTools()}{renderVoiceAi()}</>"), M_AI, "n6")),
        "marker": "neg848",
        "note": "「AI 生成」页也渲染工具行 ⟹ 「三页结构差异」这条红"
                "（★ 源站那一页**没有**工具行）",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        # ★ 只动**文档** ⟹ ⟹ 门禁 S7 查的正是这个数字
        "mutate": (lambda s: s.replace("21", "二十一")),
        "note": "README 里的「21」全换成「二十一」 ⟹ 「如实标注」这条红",
    },
    {
        "id": "N8",
        "expect": "S3",
        "files": [PANEL],
        # ★ 只动**圆角** ⟹ ⟹ 不影响盒 ⟹ ⟹ S2 不红；★ S5 只读宽度与条数 ⟹ ⟹ S5 不红
        "mutate": (lambda s: _mark(_once(s, "    radius: 10,", "    radius: 6,"), M_GEN, "n8")),
        "marker": "neg848",
        "note": "「生成音色」按钮的圆角 10 → 6 ⟹ 「外观」这条红（★ 盒不变 ⟹ ⟹ S2 不红）",
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


def wait_for_marker(marker: str, timeout: int = 240) -> bool:
    """等 dev server **真的重建完**（在服务端下发的 JS chunk 里看到标记）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if marker in served_chunks()[0]:
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
                ready = wait_for_marker(arm["marker"])
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
        "batch": 848,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "★ 变异全部**行数中性**（同一行内改值／加属性）；"
                "★ 标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）；"
                "★ S1 只看「有没有」、S2／S3 看「长什么样」⟹ ⟹ 所以臂里**不用删块**"
                "（★ 删块会同时翻 S1 与 S2）",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
