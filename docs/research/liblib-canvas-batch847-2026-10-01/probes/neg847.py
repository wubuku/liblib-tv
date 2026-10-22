#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

「对照轮全绿」**不能**证明某条断言有牙 ⟹ ⟹ 每条臂**只翻它自己那一条**，
看它**精确地红在指定的那一条上**。

## ★ 字段分工（★ 判据读的字段**互不重叠**）

| 判据 | 读什么 |
| --- | --- |
| S1 | **结构与文案清单**（页签名／工具 aria／条数／滚动高／有无空态） |
| S2 | **几何**（盒：三层／页签／文字／工具／图标／20 张卡的七个盒） |
| S3 | **计算样式**（标题行／页签／工具行／工具按钮／滚动区／卡片的几何类样式／图标区／名字／副标／播放按钮） |
| S4 | **20 条音色的名字与副标**（清单文本） |
| S5 | **选中态**（哪几张 `aria-pressed` ＋ 20 张卡各自的边框色与底色） |
| S6 | **各段底部生成行**（确认生成数／智能调整数／生成行盒） |
| S7 | **README** 文本 ＋ 「我的音色」页的如实说明状态 |

★★ **「随状态变的」与「不随状态变的」必须分开归位**：卡片那三个
（`borderTopColor`／`borderBottomColor`／`backgroundColor`）**随选中态变**
⟹ ⟹ 归 **S5** 一处；S3 只比卡片**不随状态变**的那些键
⟹ ⟹ 否则「改选中态」这一个缺陷会**同时**翻 S3 与 S5 ⟹ ⟹
⟹ ⟹ 阴性对照就**做不到**「每条臂只翻它自己那一条」。

## ★ 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「AI 生成」那枚页签的文案改成「AI生成」 | S1 | ★ **同字数** ⟹ 页签盒 24px 不变 ⟹ S2 不红；★ 那一枚**没被选中** ⟹ 可见文字不渲染 ⟹ S3 不红 |
| N2 | 滚动区下移 6px | S2 | 只动**滚动区**的 y ⟹ 它的**条数**与**滚动高**不变 ⟹ S1 不红；样式不变 ⟹ S3 不红 |
| N3 | 音色的**名字**字号 12px → 13px | S3 | 只动**字号** ⟹ 名字盒是**显式 142×20** ⟹ 盒不变 ⟹ S2 不红；文案不变 ⟹ S4 不红 |
| N4 | 副标里**少一个空格** | S4 | ★ 副标盒是**显式 142×16** ⟹ 盒不变 ⟹ S2 不红；样式不变 ⟹ S3 不红 |
| N5 | 音色卡的 onClick **不改选中态** | S5 | 只动**赋值** ⟹ S1–S4／S6–S7 读的是**初始态**，不受影响 |
| N6 | 「智能调整」在**所有**段都出现 | S6 | 只动**生成行** ⟹ 内容与几何都不变 ⟹ S1–S5 不红 |
| N7 | README 里的 **iconify** 全部替换 | S7 | 只动**文档**（★ 门禁 S7 查的正是这个词） |
| N8 | 播放按钮的**圆角** 8px → 4px | S3 | ★ 圆角**不影响盒** ⟹ S2 不红；★ S5 只读**选中态与边框/底色** ⟹ 不读圆角 ⟹ S5 不红 |

## ★★ 两处「变异自己出了问题」（★ 都不是判据没牙）

- **N6 第一版把代码改坏了**：★ 原来那段是 `{cond ? ( … ) : null}`
  ⟹ ⟹ 换成 `{(cond ? (true) : (true)) && ( … ) : null}` ⟹ ⟹ **尾部那个 `: null}`
  ⟹ ⟹ 就没有配对的对象了 ⟹ ⟹ **整段 JSX 语法错** ⟹ ⟹ dev server 报错
  ⟹ ⟹ ⟹ ⟹ 症状是「**等不到标记**」⟹ ⟹ 而**不是**「判据没红」
  ⟹ ⟹ ⟹ ⟹ ★ 极易误判成「这条臂没生效」⟹ ⟹ 正解：只把**条件**换成恒真
  ⟹ ⟹ ⟹ ⟹ （★ 结构一个字都不动 ⟹ ⟹ 编译得过）
- **N6 第二版（846 的教训）**：`(A ? null : (true)) && (B)` ⟹ ⟹ 在那一段得 `null`
  ⟹ ⟹ **那枚按钮根本不渲染** ⟹ ⟹ 变异等于没发生 ⟹ ⟹ 门禁当然不红
  ⟹ ⟹ ⟹ ⟹ 成 `((A ? (true) : (true)) && (B))`（**恒真**）⟹ ⟹ 才是真缺陷

## ★★ 一处「变异没生效」的预防（★ 846 的教训）

★ 846 的 N6 第一版写 `(A ? null : (true)) && (B)` ⟹ ⟹ 在那一段得 `null && (B)`
＝ **null** ⟹ ⟹ 那枚按钮根本不渲染 ⟹ ⟹ **变异等于没发生** ⟹ ⟹ 门禁当然不红。
⟹ ⟹ 这里 N6 一开始就写成 `((A ? (true) : (true)) && (B))`（**恒真**）⟹ ⟹ 才是真缺陷。

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
BATCH = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch847.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CSS = ROOT / "src/components/character-studio.css"
README = BATCH / "README.md"


def _once(src: str, old: str, new: str) -> str:
    """★ 精确替换**唯一**一处（⟹ ⟹ 源串没匹配上就**报错**，⟹ ⟹ 不许默默没生效）。"""
    if src.count(old) != 1:
        raise SystemExit("锚点命中 %d 处（应为 1）：%r" % (src.count(old), old[:60]))
    return src.replace(old, new, 1)


def _mark(src: str, old: str, mark: str) -> str:
    """★ 在**同一行**上插一个标记属性 ⟹ ⟹ 变异**行数中性** ⟹ ⟹ 标记可被服务端 chunk 看到。

    ★★ 锚点**必须带上换行** ⟹ ⟹ 否则替换回去时**多出一行空行**
    ⟹ ⟹ 那样文件行数就变了 ⟹ ⟹ 「行数中性」这条纪律就破了。
    """
    anchor = old + "\n"
    if src.count(anchor) != 1:
        raise SystemExit("标记锚点命中 %d 处（应为 1）：%r" % (src.count(anchor), old[:60]))
    return src.replace(anchor, old + ' data-neg847="%s"\n' % mark, 1)


# ★ 标记锚点（★ 各自**唯一**）
M_TAB = "          data-character-editor-voice-tab={item.id}"
M_MAIN = "                data-character-editor-voice-main={v.name}"
M_SMART = "                    data-character-editor-smart"


ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        # ★ 改「AI 生成」的 label ⟹ ⟹ 页签的 aria-label 跟着变 ⟹ ⟹ S1 的**页签名**列表不匹配
        #   ⟹ ⟹ ★ **同字数** ⟹ ⟹ 页签盒 24px 不变 ⟹ ⟹ S2 不红
        #   ⟹ ⟹ ★ 那一枚**不是选中项** ⟹ ⟹ clone 只给选中项渲染可见文字 ⟹ ⟹ S3 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '  { id: "ai", label: "AI 生成", w: 24, icon: Sparkles },',
            '  { id: "ai", label: "AI生成", w: 24, icon: Sparkles },'),
            M_TAB, "neg847n1")),
        "marker": "neg847n1",
        "note": "「AI 生成」那枚页签的文案改成「AI生成」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [CSS],
        # ★ 只动**滚动区**的 top ⟹ ⟹ 它的**条数**与**滚动高**不变 ⟹ ⟹ S1 不红
        "mutate": (lambda s: _once(s, "  top: 88px;", "  top: 94px;")),
        "note": "滚动区下移 6px ⟹ 几何与源站差 6px（★ 条数与滚动高不变 ⟹ S1 不红）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [CSS],
        # ★ 只动**字号** ⟹ ⟹ 名字盒是**显式 142×20** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红
        "mutate": (lambda s: _once(
            s,
            "  height: 20px;\n  font-size: 12px;\n  line-height: 20px;",
            "  height: 20px;\n  font-size: 13px;\n  line-height: 20px;")),
        "note": "音色的名字字号 12px → 13px ⟹ 「外观」这条红（盒不变 ⟹ S2 不红）",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        # ★ 副标里**少一个空格** ⟹ ⟹ 清单文本变了 ⟹ ⟹ S4 红
        #   ⟹ ⟹ ★ 副标盒是**显式 142×16** ⟹ ⟹ 盒不变 ⟹ ⟹ S2 不红
        "mutate": (lambda s: _mark(_once(
            s,
            '  { name: "青涩青年音色", sub: "中文(普通话) · 男" },',
            '  { name: "青涩青年音色", sub: "中文(普通话)·男" },'),
            M_MAIN, "neg847n4")),
        "marker": "neg847n4",
        "note": "第一条音色的副标少一个空格 ⟹ 「清单」这条红（★ 盒不变 ⟹ S2 不红）",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        # ★ 点音色卡**不改选中态** ⟹ ⟹ S5（点完之后的选中态）红
        #   ⟹ ⟹ S1–S4／S6–S7 读的都是**初始态** ⟹ ⟹ 不受影响
        "mutate": (lambda s: _mark(_once(
            s,
            "                onClick={() => setVoiceSel(v.name)}",
            "                onClick={() => void v.name}"),
            M_MAIN, "neg847n5")),
        "marker": "neg847n5",
        "note": "音色卡的 onClick 不再改选中态 ⟹ 点第三张不转移 ⟹ 「选中态」这条红",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [PANEL],
        # ★★ 让「智能调整」在**所有**段都出现（★ 源站只有脸部段有它）
        #   ⟹ ⟹ 条件改成**恒真** ⟹ ⟹ 于是「智能调整」在每一段都渲染
        #   ⟹ ⟹ ★★ **必须编译得过**（★ 第一版写的是
        #   ⟹ ⟹ `{(segment === "face" ? (true) : (true)) && (`
        #   ⟹ ⟹ 而原来的结构是 `{cond ? ( … ) : null}`
        #   ⟹ ⟹ 换过去以后**尾部那个 `: null}` 就没有配对的对象了**
        #   ⟹ ⟹ ⟹ ⟹ **整段 JSX 语法错** ⟹ ⟹ dev server 报错
        #   ⟹ ⟹ ⟹ ⟹ 于是**标记永远等不到**（⟹ ⟹ 报「等不到标记」）
        #   ⟹ ⟹ ⟹ ⟹ ★ 这是「**变异把代码改坏了**」的一例 ⟹ ⟹ 症状是
        #   ⟹ ⟹ ⟹ ⟹ 「等不到标记」⟹ ⟹ 而**不是**「判据没红」⟹ ⟹ 极易误判
        #   ⟹ ⟹ ⟹ ⟹ 正解：只把**条件**换成恒真 ⟹ ⟹ **结构一个字都不动**
        "mutate": (lambda s: _mark(_once(
            s,
            "                {segment === \"face\" ? (",
            "                {(true) ? ("),
            M_SMART, "neg847n6")),
        "marker": "neg847n6",
        "note": "「智能调整」在**所有**段都出现 ⟹ 「底部生成行按段不同」这条红",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [README],
        # ★ 删掉「iconify」⟹ ⟹ 门禁 S7 那条「★README写明图标字形是占位」红
        "mutate": (lambda s: re.sub(r"iconify", "某个图标库", s)),
        "note": "README 里的「iconify」全部替换 ⟹ 「如实标注」这条红",
    },
    {
        "id": "N8",
        "expect": "S3",
        "files": [CSS],
        # ★ 只动**播放按钮的圆角** ⟹ ⟹ 圆角**不影响盒** ⟹ ⟹ S2 不红
        #   ⟹ ⟹ S5 只读**选中态与边框/底色** ⟹ ⟹ 不读圆角 ⟹ ⟹ S5 不红
        "mutate": (lambda s: _once(
            s,
            ".ce-voice-play {\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: center;\n"
            "  flex: none;\n"
            "  width: 32px;\n"
            "  height: 32px;\n"
            "  border: 0;\n"
            "  border-radius: 8px;",
            ".ce-voice-play {\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: center;\n"
            "  flex: none;\n"
            "  width: 32px;\n"
            "  height: 32px;\n"
            "  border: 0;\n"
            "  border-radius: 4px;")),
        "note": "播放按钮的圆角 8px → 4px ⟹ 「外观」这条红（★ 盒不变 ⟹ S2 不红）",
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


def wait_for_marker(marker: str, timeout: int = 180) -> bool:
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


def wait_for_css_change(before: str, timeout: int = 180) -> bool:
    """★ 只改 CSS 时 ⟹ ⟹ **等 CSS chunk 的哈希变了**（⟹ ⟹ 比 sleep 可靠）。

    ★ 为什么不用「sleep 8 秒」：★ 4317 是**多人共用**的 ⟹ ⟹ dev server 的
    重建时机不可控 ⟹ ⟹ sleep 够短 ⟹ ⟹ 读数还是**改动前**的 ⟹ ⟹
    ⟹ ⟹ 那个臂会「没红」⟹ ⟹ 而**看起来**像「判据没牙」⟹ ⟹ **误判**。
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if hashlib.sha256(served_chunks()[1].encode("utf-8")).hexdigest() != before:
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
            css_before = ""
            if any(f.suffix == ".css" for f in arm["files"]):
                css_before = hashlib.sha256(
                    served_chunks()[1].encode("utf-8")).hexdigest()
            for f in arm["files"]:
                src = f.read_text(encoding="utf-8")
                dst = arm["mutate"](src)
                if dst == src:
                    raise SystemExit("%s 变异没有生效（源串没匹配上）" % aid)
                f.write_text(dst, encoding="utf-8")
            # ★ 等重建（★ 标记等的是**下发的 JS chunk**；只改 CSS 的臂等 **CSS chunk 的哈希变化**）
            # ★ ★ 等不到 ⟹ ⟹ **多半是「变异把代码改坏了」**（★ 846 与 847 各踩过一次）
            #   ⟹ ⟹ 那时**记成失败并继续** ⟹ ⟹ 免得因为一条臂把其余臂全丢掉
            if arm.get("marker"):
                ready = wait_for_marker(arm["marker"])
            else:
                ready = wait_for_css_change(css_before)
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
        "batch": 847,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "标记等的是**下发的 JS chunk**（★ 打在 TSX 上 ⟹ 不用 CSS 注释）；"
                "★ 只改 CSS 的臂等的是 **CSS chunk 的哈希变化**（★ 4317 多人共用 ⟹ ⟹ "
                "sleep 不可靠 ⟹ ⟹ 「没红」会被误判成「判据没牙」）；"
                "★ S3 与 S5 的字段**已分开**：卡片那三个「随选中态变」的颜色归 S5 一处",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
