#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831：把源站 chunk 里那两段图标 path **机器提取**出来，落成 raw 证据。

## 为什么必须机器提取（不能手抄）

★ 本批第一版把源站 ⌘ 图标的 path **手打**进了门禁脚本（`SRC_COMMAND_PATH`），
门禁 S12 于是变成**自证式判据**：它只证明「clone 里那段文字 == 我手打的那段文字」，
**不证明**「那段文字 == 源站的 path」。
结果：手打时把**下半部两条臂的先后顺序抄反了**（源站先左下、后右下；抄成了先右下、后左下），
门禁照样 15/15 全绿。

⇒ 这正是「手打的标识符是输入，不是测量」的实例：**它被门禁读回后就变成了"事实"**。
⇒ 修法：**期望值从入库的 raw 里读**（raw 由本脚本从源站 chunk 机器提取），
clone 与 raw 比对 ⟹ 抄错一个字符就翻红。

## 用法

    python3 extract831.py <源站chunk路径> <输出raw路径>

默认 chunk 路径是上一批抓到的 `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`
（1,018,130 字节，导演台组件）。
"""
import hashlib
import json
import pathlib
import re
import sys

DEFAULT_CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
DEFAULT_OUT = pathlib.Path(__file__).resolve().parent.parent / "raw" / "source-831-shortcut-code.json"

# 源站组件 → 它在 chunk 里的函数名（mC = ⌘ 符号、mA = ⌫ 符号）
GLYPHS = {
    "command": "mC",
    "delete": "mA",
}

# 面板与菜单的类名锚点（用来证明「抄的确实是那个组件」）
CLASS_ANCHORS = [
    "absolute bottom-full left-0 z-50 pb-2",
    "w-[120px]",
    "bg-[rgba(31,31,31,0.94)]",
    "shadow-[0_8px_24px_rgba(0,0,0,0.35)]",
    "absolute left-[297px] top-[60px]",
    "h-[314px]",
    "w-[480px]",
    "h-[228px]",
    "w-[432px]",
    "mx-6",
    "bg-[#1f1f1f]/95",
    "shadow-[0_2px_4px_rgba(0,0,0,0.04),0_4px_10px_rgba(0,0,0,0.10)]",
    "backdrop-blur-[32px]",
    "flex h-7 min-w-7 shrink-0 items-center justify-center rounded-lg border px-1.5",
    "min-w-0 text-sm leading-5 text-white/80",
    "flex h-7 items-center justify-between gap-2",
]


def extract(chunk_text):
    """从 chunk 文本里提取两段 path，返回 {name: {"path":…, "offset":…}}。"""
    out = {}
    for name, fn in GLYPHS.items():
        idx = chunk_text.find("function %s()" % fn)
        if idx < 0:
            raise SystemExit("chunk 里找不到函数 %s" % fn)
        seg = chunk_text[idx: idx + 1500]
        m = re.search(r'd:"([^"]+)"', seg)
        if not m:
            raise SystemExit("函数 %s 里找不到 d:\"...\"" % fn)
        # 记录 path 在 chunk 里的**绝对偏移**（可复核）
        abs_off = chunk_text.find(m.group(1))
        out[name] = {"fn": fn, "fn_offset": idx, "path": m.group(1),
                     "path_offset": abs_off, "path_len": len(m.group(1)),
                     # ★ 原文摘录：让 raw **自证**是源站代码的一段 ⟹
                     #   门禁能核验「path 确实嵌在这段摘录里」⟹
                     #   raw 不是一个孤立的、来源不明的字符串常量。
                     "excerpt": seg[:seg.find("}") + 1]}
    return out


def excerpt_at(chunk_text, needle, span):
    """截取 chunk 里某段锚点周围的原文（用于面板/菜单的代码摘录）。"""
    off = chunk_text.find(needle)
    if off < 0:
        return None
    return chunk_text[off: off + span]


def main():
    chunk = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CHUNK
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not chunk.exists():
        raise SystemExit("找不到源站 chunk：%s" % chunk)
    raw = chunk.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    glyphs = extract(text)
    anchors = {}
    for cls in CLASS_ANCHORS:
        off = text.find(cls)
        anchors[cls] = off
    missing = [c for c, o in anchors.items() if o < 0]
    doc = {
        "来源": "源站导演台组件 chunk（batch 830 开台时录网络请求抓到的那一份）",
        "chunk_文件": str(chunk),
        "chunk_bytes": len(raw),
        "chunk_sha256": hashlib.sha256(raw).hexdigest(),
        "抓取方式": "本脚本 extract831.py **机器提取**（正则抓 d:\"...\"）⟹ "
                    "★ 不是手打 ⟹ 抄错一个字符会被门禁当场抓住",
        "⚠️ 这份 raw 的作用": "它是门禁 S12 的**期望值来源** ⟹ "
                              "期望值是「源站原文」而不是「我抄的」",
        "图标": glyphs,
        "类名锚点": anchors,
        "未命中锚点": missing,
        "代码摘录": {
            "帮助菜单": excerpt_at(text, 'aria-haspopup":"menu"', 1200),
            "快捷键对话框": excerpt_at(text, "absolute left-[297px] top-[60px]", 400),
            "面板组件": excerpt_at(text, "function mI()", 2100),
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", out_path)
    for name, g in glyphs.items():
        print("  %-8s fn=%s len=%d path@%d" % (name, g["fn"], g["path_len"], g["path_offset"]))
    print("  未命中锚点：", missing or "无")


if __name__ == "__main__":
    main()
