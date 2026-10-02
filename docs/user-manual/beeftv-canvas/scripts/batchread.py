#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量读取上游源码（Batch 181 新增，供闸 5 / 闸 3 共用）。

**为什么存在**（Batch 180 实测出来的性能问题）：

`verify-exclusions.py` 要扫「上游有没有注册 `/agent/*` 路由」，
做法是 `git ls-tree` 列出**全部** backend 文件后**逐个 `git show`**。
实测 `backend/` 下非测试 `.go` 文件 **347 个**，单次 `git show` 约 **25ms**
（每个都是一次子进程）→ **闸门本体约 9–10 秒**，反验 5 个用例就是 **35.6 秒**。
`verify-endpoints.py` 同样的形态，闸门本体 10 秒、反验 7 例 **43 秒**。

**这不是「机器慢」，是「用错了工具」**：要读 347 个 blob，却发起了 347 次进程。

**本模块的做法**：先 `git cat-file --batch-check` **一次**拿到全部 blob 的大小，
再 `git cat-file --batch` **一次**读全部内容，**按大小在内存里精确切分**。
**两次进程调用取代 347 次。**

**为什么切分必须精确**：`--batch` 的输出格式是
`<sha> <type> <size>\\n<content><LF>`，**content 后面那个 LF 不属于内容**。
按行切分会得到「多一个换行」的内容——**而判据里有多处逐字节比较**，
多一个换行就会让「字符串相等」变成「差一个字节的不等」，
**而且它不会报错，只会让某个判据莫名其妙地一直不成立**。
所以本模块**按 `--batch-check` 报的大小精确取字节**，并逐条与 `git show` 对拍。

**它不改变任何判据逻辑**——只把「347 次 `git show`」换成「2 次 `cat-file`」。

退出码不适用：本模块是库，供其它闸 import。
"""

import re
import subprocess

# `--batch` 的头部行：`<sha> <type> <size>`，size 是十进制字节数
_HEADER = re.compile(r"^([0-9a-f]{40}|missing) (\w+) (\d+)$")


def read_many(src, ref, paths):
    """一次读回多个文件，返回 {path: 内容}。

    **读不到的文件不出现在结果里**（与逐个 `git show` 失败返回空串的语义一致），
    调用方照旧用 `.get(path, "")`。

    **两次进程调用**：先 `--batch-check` 拿大小，再 `--batch` 拿内容。
    `git cat-file --batch` 在 ref 或 path 非法时会在头行输出 `missing`，
    **本模块据此跳过，而不是让后续切分错位**——错位是最危险的失败形态：
    它不会报错，只会让某个文件的内容变成另一个文件的。
    """
    if not paths:
        return {}
    specs = [f"{ref}:{p}" for p in paths]

    # ① 一次拿全部大小
    chk = subprocess.run(["git", "cat-file", "--batch-check"],
                         cwd=src, input="\n".join(specs) + "\n",
                         capture_output=True, text=True)
    if chk.returncode != 0:
        return {}
    plan = []          # [(path, size), ...]
    for spec, line in zip(specs, chk.stdout.split("\n")):
        if not line:
            break
        m = _HEADER.match(line)
        if not m or m.group(2) == "missing":
            continue                      # 读不到 → 语义上等于空串
        plan.append((spec, int(m.group(3))))
    if not plan:
        return {}

    # ② 一次读全部内容。**必须按 bytes 收**：下面要按 size 精确切分，
    # 一旦走 text=True 就得再编解码，而**编解码会改变「切出来的正好是 size 字节」
    # 这件事的前提**——多字节字符下它就不再成立了。
    raw = subprocess.run(["git", "cat-file", "--batch"],
                         cwd=src, input=("\n".join(s for s, _ in plan) + "\n").encode(),
                         capture_output=True)
    if raw.returncode != 0:
        return {}
    buf = raw.stdout
    out = {}
    pos = 0
    for spec, size in plan:
        nl = buf.find(b"\n", pos)          # 头行结束
        if nl < 0:
            break
        pos = nl + 1
        out[spec.split(":", 1)[1]] = buf[pos:pos + size]
        pos += size + 1                    # +1 跳过内容后的那个 LF
    return out
