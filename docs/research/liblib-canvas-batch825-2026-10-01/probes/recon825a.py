#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 825 源站取证：把**跟随横幅组件**的源码与相关 i18n 键抠出来入库。

★ 为什么用 bundle 而不是继续在源站上点：
  源站那个横幅要在**协作会话**里才出现（要另一个用户跟着我），
  驾驶台里**根本没这个横幅** ⟹ 运行时点不出来，
  ⟹ ★ 唯一可靠的取证手段就是**读源站自己的代码**（823 已证：
  minified bundle 上 grep 字符串指纹是对的工具，REA 的语义图不行）。

★ 本探针做三件事：
  ① 找到渲染 `collab-follow-banner-close` 的组件，**整段抠出来**存成
     `raw/source-825-followbanner.js`（几 KB，可读、可 grep）
  ② 把**所有含 follow/跟随 的 i18n 键 + 中文值**存成
     `raw/source-825-follow-keys.json`
  ③ 记下**调用点**：横幅组件被谁渲染、prefix 传的是什么
     ⟹ 这一条决定「机位跟随」用不用它

★ 前置：/tmp/liblib_srcjs/ 下要有源站 JS 正文（用 /tmp/grab_srcjs825.py 抓）。
"""
import json
import pathlib
import re
import sys

DEST = pathlib.Path("/tmp/liblib_srcjs")
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch825-2026-10-01/raw")
OUT.mkdir(parents=True, exist_ok=True)

if not DEST.exists() or not any(DEST.glob("*.js")):
    print("✘ 缺 /tmp/liblib_srcjs 的 JS 正文（先跑 /tmp/grab_srcjs825.py）")
    sys.exit(1)

# ── ① 组件源码 ──────────────────────────────────────────────
# ★★ 要**同时**圈住两样东西：①组件定义 ②它的**调用点**
#    （第一版只存了组件定义 ⟹ 片段里那个 "prefix:" 是**参数解构** ⟹
#      ★★ 验收器数不出「有几个调用点」⟹ 证据不够用）
snippet = None
src_file = None
call_span = None
for f in sorted(DEST.glob("*.js")):
    text = f.read_text(encoding="utf-8", errors="replace")
    pos = text.find("collab-follow-banner-close")
    if pos < 0:
        continue
    # ★ 往回找组件函数的起点
    start = text.rfind("active:e,prefix:t,nickname:r,colorHex:a,onClose:n", 0, pos)
    if start < 0:
        start = max(0, pos - 2000)
    # ★ 再找**调用点**：`jsx(ro,{active:…,prefix:…})` 那一处
    m = re.search(r"\(0,[A-Za-z_$]+\.jsx\)\([A-Za-z_$]+,\s*\{[^}]{0,400}?prefix:",
                  text)
    if not m:
        print("✘ 找不到调用点")
        sys.exit(1)
    call_span = (m.start(), m.end())
    snippet = text[start:call_span[1] + 400]
    src_file = f.name
    break

if snippet is None:
    print("✘ 源站 bundle 里找不到跟随横幅组件")
    sys.exit(1)

(OUT / "source-825-followbanner.js").write_text(snippet, encoding="utf-8")

# ── ② i18n 键 ──────────────────────────────────────────────
KEY = re.compile(r'"([A-Za-z0-9_]{4,70})":"([^"]{0,50})"')
keys = {}
for f in sorted(DEST.glob("*.js")):
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in KEY.finditer(text):
        k, v = m.group(1), m.group(2)
        if "follow" in k.lower() or "跟随" in v:
            keys.setdefault(k, v)
(OUT / "source-825-follow-keys.json").write_text(
    json.dumps(keys, ensure_ascii=False, indent=1), encoding="utf-8")

# ── ③ 调用点 ────────────────────────────────────────────────
call = snippet[max(0, call_span[0] - 700):call_span[1] + 300] if call_span else None

# ★ 组件的三个关键点：面板按 active 切 pointer-events、按钮自己没写、
#   取消按钮带 aria-keyshortcuts="Escape"、提示 span 带 role="tooltip"
facts = {
    "源文件": src_file,
    "横幅组件源码已存": "source-825-followbanner.js",
    "★ 面板按 active 切 pointer-events":
        "pointer-events-auto" in snippet and "active" in snippet,
    "★ 取消按钮**自己**没写 pointer-events":
        not re.search(r'className:"[^"]*pointer-events[^"]*"[^}]*collab-follow-banner-close',
                      snippet) and 'className:"peer rounded-full bg-white' in snippet,
    "★ 取消按钮带 aria-keyshortcuts=Escape": 'aria-keyshortcuts":"Escape"' in snippet,
    "★ 提示 span 带 role=tooltip": 'role:"tooltip"' in snippet,
    "★ 横幅容器固定 pointer-events-none（只有内层面板在 active 时才 auto）":
        'className:"pointer-events-none fixed left-1/2 top-0' in snippet,
    "★ 横幅是 portal 到 document.body": "document.body)" in snippet,
    "★ 提示是 peer-hover / peer-focus-visible 才显形":
        "peer-hover:opacity-100" in snippet and "peer-focus-visible:opacity-100" in snippet,
    # ★★ 「调用点」数法：`prefix:` 出现次数 **减去 1**（组件的参数解构那处）
    #   ⟹ ★ 不能用 `,{active:` 数 ⟹ 那个形态会把**边框组件**的调用也算进去
    #   （`jsx(rs,{active:L,colorHex:T})`）⟹ ★★ 数出来是 2，**虚高**。
    "★ prefix: 出现次数": snippet.count("prefix:"),
    "★ 参数解构那处（不算调用点）": 1,
    "★ 调用点数": snippet.count("prefix:") - 1,
    "★ 片段是否含调用点": ("prefix:" in snippet
        and snippet.count("prefix:") >= 2),
    "★ 调用点里的 prefix 是**运行时变量**": "prefix:z" in snippet,
    "★ prefix 取的是协作 i18n 键":
        "collabFollowControllerProcessing2" in snippet,
    "★ 片段字节数": len(snippet),
}
(OUT / "source-825-followbanner-facts.json").write_text(
    json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")

print("源文件:", src_file)
print(json.dumps(facts, ensure_ascii=False, indent=1))
print("\n=== 调用点（prefix 传的是什么）===")
print((call or "（没找到）")[:1200])
