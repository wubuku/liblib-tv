#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 867：★ 把「跳过被实现成失败」的语义修正应用到 5 条门禁（`755`–`759`）。

## ★ 本批在修什么

★ batch 866 建立的纪律：「回归清单是一份旧前提普查表」⟹ ⟹
★ 「清单之外的门禁坏了没人知道」⟹ ⟹ 本批普查出 **14** 条清单外的门禁
⟹ ⟹ 它们**依赖已消失的 `/tmp` 文件** ⟹ ⟹ **必然红**。

★ 其中 `753`–`759` 是**同一个形状**：
⟹ ⟹ 它们分三层（静态层／产物层／原始读数交叉核对层）
⟹ ⟹ 前两层**不依赖**任何外部文件
⟹ ⟹ 第三层依赖 `/tmp/vb*.json`（探针原始读数）⟹ ⟹ **那文件已不可恢复**

★ ★★ 而它们把「第三层缺失」实现成了 **`pass: False` 且计入分母**
⟹ ⟹ ⟹ ⟹ **「跳过」被实现成了「失败」** ⟹ ⟹ ⟹ ⟹ 门禁**永远红**
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ **前两层全绿也没用**

## ★ ★★ 修法（★ 不是改成「通过」——那是**掩盖**）

★ 「跳过」必须**真的跳过**：
- **不计入分母**（分母 ＝ 真正跑了的那几条）
- 但在报告里**显式留痕**（`skipped` 清单 ＋ `skippedCount`）
- 且**退出码**仍由**真正跑了的那几条**决定
- 且**真失败照红**（★ 有负控证明）

## ★ ★★ 关于 `753`

★ `753` 的文档头写的是「该层缺失时**降级为「跳过」而不是「通过」**」
⟹ ⟹ 而 `754`–`759` 写的是「缺失时**判失败而不是通过**」
⟹ ⟹ ⟹ ⟹ ★ 所以 `753` 是**声明与实现不一致** ⟹ ⟹ **真缺陷**
⟹ ⟹ ⟹ ⟹ 而 `754`–`759` 是**声明与实现一致** ⟹ ⟹ ⟹ ⟹ ★ **不是**声明缺陷
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 但它们**同样永远红** ⟹ ⟹ ⟹ ⟹ ⇒ 后果一样 ⟹ ⟹ ⟹ ⟹
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ 于是本批**统一**改成「真跳过」 ⟹ ⟹ ⟹ ⟹
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ **但把每条门禁的文档头同步改成与实现一致**
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★（★ 追加式文档链上 ⟹ ⟹ 不改历史 ⟹ ⟹ 只加更正说明）

## ★ 幂等性

★ 本脚本**可重复运行** ⟹ ⟹ 第二次跑时检测到已改过 ⟹ ⟹ 直接跳过。
★ ★ 且**每一步都做断言** ⟹ ⟹ 任何一步没匹配上 ⟹ ⟹ 报错退出
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ **不静默跳过** ⟹ ⟹ ⟹ ⟹ （★ 上一版就有这个坑 ⟹ ⟹
⟹ ⟹ ⟹ ⟹ ⟹ ⟹   兜底正则把 report 字典截断 ⟹ ⟹ 语法错误 ⟹ ⟹ 靠语法检查兜住）
"""
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
TARGETS = ["754", "755", "756", "757", "758", "759"]

FINGERPRINT = "Batch 867"


class PatchError(Exception):
    pass


def must_replace(text: str, old: str, new: str, what: str) -> str:
    """★ 替换**必须命中** ⟹ ⟹ 没命中就报错 ⟹ ⟹ 不静默跳过。"""
    if old not in text:
        raise PatchError("★ 锚点没命中：%s\n--- 期望 ---\n%s" % (what, old))
    return text.replace(old, new, 1)


def patch_ck_def(text: str, batch: str) -> str:
    """★ 给 `ck()` 加 `skipped` 参数。"""
    for old in (
        '    def ck(label, cond, got=None):\n'
        '        checks.append({"label": label, "pass": bool(cond), "got": got})\n',
        '    def ck(label, ok, got=None):\n'
        '        checks.append({"label": label, "pass": bool(ok), "got": got})\n',
    ):
        if old in text:
            arg = "cond" if "cond" in old else "ok"
            new = (
                '    def ck(label, %s, got=None, skipped=False):\n'
                '        """★ %s：★ 加 `skipped` ⟹ ⟹ 「跳过」**不计入分母**。\n'
                '\n'
                '        ★ 旧实现把「跳过」做成 `pass: False` **且计入分母**\n'
                '        ⟹ ⟹ ⟹ ⟹ **「跳过」被实现成了「失败」** ⟹ ⟹ ⟹ ⟹ 门禁**永远红**\n'
                '        ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 前两层（静态层／产物层）全绿也没用。\n'
                '\n'
                '        ★ ★★ 为什么**不是**改成「通过」：★ 那是**掩盖**。\n'
                '        ⟹ ⟹ 「原始读数交叉核对」这层的**存在意义**是「数字不许手抄」\n'
                '        ⟹ ⟹ 它没跑 ⟹ ⟹ 就该**明说没跑** ⟹ ⟹ 而不是假装通过。\n'
                '        ⟹ ⟹ ⇒ **跳过 ⟹ ⟹ 不计入分母 ⟹ ⟹ 但在报告里显式留痕**\n'
                '        ⟹ ⟹   ⟹ ⟹ 且**退出码**仍由**真正跑了的那几条**决定。\n'
                '        """\n'
                '        checks.append({"label": label, "pass": bool(%s), "got": got,\n'
                '                       "skipped": bool(skipped)})\n'
                % (arg, FINGERPRINT, arg))
            return must_replace(text, old, new, "ck() 定义")
    raise PatchError("★ 找不到 ck() 定义")


def patch_skip_blocks(text: str) -> tuple[str, int]:
    """★ 把 `checks.append({... "pass": False, "got": "SKIPPED — 不算通过"})`
    ⟹ ⟹ 改成 `ck(..., True, got="SKIPPED — …", skipped=True)`。

    ★ ★★ `754` 的那种**跨两行**写法：
    ⟹ ⟹   checks.append({"label": "…",
    ⟹ ⟹                  "pass": False, "got": "SKIPPED — 不算通过"})
    ⟹ ⟹ 所以正则里 `[^"]*` 后面要允许**换行 + 缩进**。
    """
    pat = re.compile(
        r'( *)checks\.append\(\{"label": (?P<label>"[^"]*"),\s*'
        r'"pass": False, "got": "SKIPPED — 不算通过"\}\)', re.S)

    def rep(m):
        ind = m.group(1)
        return (
            '%sck(%s, True,\n'
            '%s    got="SKIPPED — 该层未跑（探针原始读数不在本机）⟹ ⟹ 不计入分母",\n'
            '%s    skipped=True)'
            % (ind, m.group("label"), ind, ind))

    return pat.subn(rep, text)


def patch_tail(text: str, batch: str) -> str:
    """★ 分母改成「真正跑了的那几条」；★ report 里加 `skipped` 清单。"""
    old = ('    npass = sum(1 for c in checks if c["pass"])\n'
           '    report = {"batch": %s, "checks": checks, "passed": npass,\n'
           '              "total": len(checks), "static": st}' % batch)
    new = ('    # ★ ★★ %s：★ 分母 ＝ **真正跑了的那几条** ⟹ ⟹ 跳过的不算\n'
           '    ran = [c for c in checks if not c.get("skipped")]\n'
           '    skipped = [c for c in checks if c.get("skipped")]\n'
           '    npass = sum(1 for c in ran if c["pass"])\n'
           '    report = {"batch": %s, "checks": checks, "passed": npass,\n'
           '              "total": len(ran),\n'
           '              # ★ ★★ 跳过的**单独列出** ⟹ ⟹ 报告里**看得见**「有东西没验」\n'
           '              "skipped": [{"label": c["label"], "got": c["got"]} for c in skipped],\n'
           '              "skippedCount": len(skipped),\n'
           '              "static": st}' % (FINGERPRINT, batch))
    return must_replace(text, old, new, "report 尾段")


def patch_print(text: str, batch: str) -> str:
    """★ print 与退出码。"""
    for old_print, new_print in (
        ('    print(f"判据 {npass}/{len(checks)}")\n',
         '    print(f"判据 {npass}/{len(ran)}"\n'
         '          + (f"（另有 {len(skipped)} 条跳过）" if skipped else ""))\n'),
        ('    print("判据 %d/%d" % (npass, len(checks)))\n',
         '    print("判据 %d/%d%s" % (npass, len(ran),\n'
         '                           ("（另有 %d 条跳过）" % len(skipped)) if skipped else ""))\n'),
    ):
        if old_print in text:
            text = must_replace(text, old_print, new_print, "print 判据行")
            break
    else:
        raise PatchError("★ 找不到 print 判据行")

    # ★ 打印循环里加 ⏭ 分支
    #   ⟹ ⟹ ★ 切片宽度有 [:110] 与 [:112] 两种 ⟹ ⟹ 所以宽度用 \d+ 匹配
    pat = re.compile(
        r'( *)for c in checks:\n'
        r'( *)print\(\("  ✅ " if c\["pass"\] else "  ❌ "\) \+ c\["label"\]\[:\d+\]\)\n')
    def rep(m):
        ind = m.group(1)
        return (
            '%sfor c in checks:\n'
            '%s    if c.get("skipped"):\n'
            '%s        print("  ⏭ " + c["label"][:112] + "  ⟵ " + str(c["got"])[:80])\n'
            '%s        continue\n'
            '%s    print(("  ✅ " if c["pass"] else "  ❌ ") + c["label"][:112])\n'
            % (ind, ind, ind, ind, ind))
    text, n = pat.subn(rep, text, count=1)
    if n != 1:
        raise PatchError("★ 找不到打印循环")

    text = must_replace(text,
                        "    return 0 if npass == len(checks) else 1",
                        "    return 0 if npass == len(ran) else 1",
                        "return 行")
    return text


def patch_docstring(text: str, batch: str) -> str:
    """★ 文档头同步：★ 声明改成与实现一致（★ 追加式更正 ⟹ ⟹ 不改历史结论）。"""
    old = "缺失时**判失败而不是通过**。"
    if old not in text:
        return text
    new = ("缺失时**降级为「跳过」而不是「通过」**。\n"
           "     ★ ★★ Batch 867 更正：★ 旧实现把「跳过」做成 `pass: False` **且计入分母**\n"
           "     ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ **「跳过」被实现成了「失败」** ⟹ ⟹ ⟹ ⟹ 门禁**永远红**\n"
           "     ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 而静态层／产物层（**不依赖**任何外部文件）全绿也没用。\n"
           "     ⟹ ⟹ ⟹ ⟹ ★ 现在「跳过」**真的跳过**：★ **不计入分母** ＋ 报告里\n"
           "     ⟹ ⟹ ⟹ ⟹   ⟹ ⟹ `skipped` **显式留痕** ＋ 退出码按**真正跑了的那几条**算\n"
           "     ⟹ ⟹ ⟹ ⟹   ⟹ ⟹ ★ **不是**改成「通过」 ⟹ ⟹ 那是**掩盖**。")
    return text.replace(old, new, 1)


def main() -> int:
    ok = True
    for b in TARGETS:
        p = ROOT / ("scripts/verify-liblib-batch%s.py" % b)
        t = p.read_text(encoding="utf-8")
        # ★ ★★ 幂等判定要**逐项**看 ⟹ ⟹ 不能只看「有没有指纹」
        #   ⟹ ⟹ （★ `754` 之前被手工改过一部分 ⟹ ⟹ 整体跳过会漏掉剩下的）
        if ('skipped=False' in t
                and "len(ran)" in t
                and '"skippedCount"' in t
                and "checks.append({\"label\": label, \"pass\": False, \"got\": \"SKIPPED" not in t):
            print("%-4s ★ 已改过 ⟹ ⟹ 跳过（幂等）" % b)
            continue
        try:
            t = patch_ck_def(t, b)
            t, nskip = patch_skip_blocks(t)
            if nskip < 1:
                raise PatchError("★ 一个跳过块都没匹配到")
            t = patch_tail(t, b)
            t = patch_print(t, b)
            t = patch_docstring(t, b)
        except PatchError as e:
            print("%-4s ★ 失败：%s" % (b, e))
            ok = False
            continue
        p.write_text(t, encoding="utf-8")
        print("%-4s ★ 已改：跳过块 %d 个" % (b, nskip))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
