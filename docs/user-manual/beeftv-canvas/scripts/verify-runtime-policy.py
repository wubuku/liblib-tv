#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十二道闸：随部署模式而变的策略常量——**同一个常量在两套策略里取值不同**。

**为什么要有这道闸（Batch 172 的由来）**：手册里「同时排队或运行的任务最多 **5** 个」
被当成固定事实写了 5 处，「素材归档默认 **30 天**后自动彻底清除」也写成了定值。
回源一看，`backend/internal/platform/runtime_policy.go` 里**有两套策略**：

    DefaultRuntimePolicy()      → ActiveTaskLimit: 5            RecycleBinRetentionDays: 30
    selfUseRuntimePolicy()      → ActiveTaskLimit: maxRuntimeConcurrency(999)
                                   RecycleBinRetentionDays: 0

而 `RuntimePolicy()` 的判据是 **`if s.localMode { return selfUseRuntimePolicy() }`**——
**本地部署走的是第二套**。`NewLocal(...)` 正是以 `localMode=true` 构造的。

**后果是手册对本地用户说错了两件会真影响行为的事**：
  · 并发上限不是 5 而是 **999**（所以「最多 5 个」那条报错本地根本撞不到）；
  · 归档保留天数是 **0**，而清理 worker `if retentionDays <= 0 { return }`——
    **本地部署下素材归档永远不会被自动彻底清除**，磁盘只增不减。
手册原来那句「不是手册错了，是你这个部署改了策略」**框错了**：
本地模式不是「改了策略」，而是**另一套内置策略**，且它是本手册读者的主要场景。

**本闸判什么**：手册的「部署模式相关策略」表里，每个策略项的**两个取值**都必须与
上游 `runtime_policy.go` 解析出来的值相符——**两个都核**，少一个就等于放过了
「本地模式那一半」。这与 Batch 164/169 的双向精神同源：**单边判据的绿灯毫无意义。**

**覆盖不到什么（如实说明）**：
  · 只解析 `Key: <字面量>` / `Key: <常量名>` 两种形态；
    形如 `envInt("CANVAS_WORKER_CONCURRENCY", …)` 的**可配置项解析不了**，
    本闸因此**不收**这类行（收进来只会天天误报），它属于部署方配置、不属于本手册的断言；
  · 只覆盖 `runtime_policy.go` 一个文件里的两套策略字面量；
    若上游改成从别处读值，本闸会解析出 None 并**报「未能核对」（rc=2）**，不会假装通过。

退出码：0 全部相符；1 有不符；2 未能核对（找不到源码 / 找不到表 / 任一行解析不出两套取值）。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, "20-reference.md")
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")
REF = os.environ.get("BEEFTV_REF", "origin/main")
POLICY_FILE = "backend/internal/platform/runtime_policy.go"


def _git_show(path):
    r = subprocess.run(["git", "-C", SRC, "show", f"{REF}:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def _const_values(text):
    """const 块里的常量名 → 数值（顺手去掉 Go 的下划线分隔符，如 999_999_999）。"""
    out = {}
    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s+(?:int64|int)?\s*=\s*([0-9_]+)\s*$",
                         text, re.M):
        try:
            out[m.group(1)] = int(m.group(2).replace("_", ""))
        except ValueError:
            pass
    return out


def _func_body(text, func_name):
    m = re.search(r"^func\s+%s\s*\(\)[^{]*\{" % re.escape(func_name), text, re.M)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def _value_of(body, key, consts):
    """在函数体里取 `Key: <值>`。值可能是字面量，也可能是常量名。

    **刻意不收 `envInt(...)` 这类表达式**——它们是**部署方可配置项**，
    收进来只会天天误报；解析不了时返回 None，由调用方按「未能核对」处理。
    """
    m = re.search(r"\b%s\s*:\s*([^,\n]+)" % re.escape(key), body)
    if not m:
        return None
    raw = m.group(1).strip().rstrip(",")
    if re.match(r"^\d[\d_]*$", raw):
        return int(raw.replace("_", ""))
    m2 = re.match(r"^([A-Za-z_]\w*)$", raw)
    if m2 and m2.group(1) in consts:
        return consts[m2.group(1)]
    return None


def parse_table():
    if not os.path.isfile(MANUAL):
        raise ValueError(f"找不到 {MANUAL}")
    text = open(MANUAL, encoding="utf-8").read()
    m = re.search(r"###\s*部署模式相关策略[^\n]*\n(.*?)(?=\n##\s|\n###\s)", text, re.S)
    if not m:
        raise ValueError("20-reference.md 里找不到「部署模式相关策略」小节")
    rows = []
    for line in m.group(1).split("\n"):
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("策略项", ""):
            continue
        key = cells[0].strip("`")
        if not re.match(r"^\d+$", cells[1]) or not re.match(r"^\d+$", cells[2]):
            raise ValueError(f"策略表里 {key} 的两个取值必须都是整数：[{cells[1]}] [{cells[2]}]")
        rows.append((key, int(cells[1]), int(cells[2]),
                     cells[3] if len(cells) > 3 else ""))
    if not rows:
        raise ValueError("策略表里没有数据行")
    return rows


def main():
    try:
        rows = parse_table()
    except ValueError as exc:
        print(f"[skip] {exc}，部署模式策略核对本轮未能进行")
        return 2
    if not os.path.isdir(SRC):
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，部署模式策略核对本轮未能进行")
        return 2
    text = _git_show(POLICY_FILE)
    if text is None:
        print(f"[skip] 读不到 {REF}:{POLICY_FILE}，部署模式策略核对本轮未能进行")
        return 2

    consts = _const_values(text)
    default_body = _func_body(text, "DefaultRuntimePolicy")
    selfuse_body = _func_body(text, "selfUseRuntimePolicy")
    if not default_body or not selfuse_body:
        print("[skip] 在 runtime_policy.go 里找不到 DefaultRuntimePolicy() / "
              "selfUseRuntimePolicy()（上游可能改了函数名），本轮未能核对")
        return 2

    bad, void = [], []
    for key, want_default, want_local, why in rows:
        got_default = _value_of(default_body, key, consts)
        got_local = _value_of(selfuse_body, key, consts)
        if got_default is None or got_local is None:
            void.append(f"{key}：默认={got_default} 本地={got_local}"
                        f"（多半是形如 envInt(...) 的可配置项，本闸不收）")
            continue
        if got_default != want_default:
            bad.append(f"{key} 默认部署：手册写 {want_default}，上游 {got_default}")
        if got_local != want_local:
            bad.append(f"{key} 本地部署（localMode）：手册写 {want_local}，上游 {got_local}")
    for v in void:
        print(f"[skip] {v}")
    if bad:
        print(f"部署模式策略核对：{len(bad)} 处声明与上游不符")
        for b in bad:
            print("  " + b)
        print("→ 更新 20-reference.md 的策略表，并检查手册正文里把它当固定事实的句子；"
              "**两套取值都要核**，少一半就等于放过了本地模式")
        return 1
    if void:
        print(f"[skip] {len(void)}/{len(rows)} 行本轮未能核对，"
              f"其余 {len(rows) - len(void)} 行两套取值都相符 —— **不是全部通过**")
        return 2
    print(f"部署模式策略核对通过：{len(rows)} 个策略项在**默认部署与本地部署两套取值**下"
          f"都与 {REF} 相符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
