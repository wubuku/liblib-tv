#!/usr/bin/env python3
"""编码完整性校验（M131 建立，第十六道门禁）

**要抓的东西**：U+FFFD（`\ufffd`）替换字符——多字节 UTF-8 被截断后留下的残骸。

**为什么值得单开一道门禁**（M131 的由来）：

- 2026-10-02 查「弹窗按钮写法」时顺手 grep 了一下，**发现手册里早就有 8 处 U+FFFD**，
  产物侧也照渲染出来了（读者看到的是「上传的<三个坏字节>片节点」）。
- 追溯 git 发现它们分别来自 **M71 / M108 / M113** 三个几十批前的提交，
  **`append-audit.py` 里的那处从 M71 起就一直带着病在跑**。
- **十五道门禁没有一道扫 U+FFFD**，于是它潜伏了几十批。

**根因是写入路径，不是内容**：U+FFFD 只会由「把 UTF-8 多字节字符截断」产生。
本专项里已确认的两种触发方式：

1. **用 bash heredoc 传中文**。M130 写 commit message 时就在最后一行踩到——
   「对的」被截成「对\ufffd」。同一批里用 `write` 工具落盘的文件则完好。
   → **写文件与写 commit message 一律用 `write` 工具或 python 脚本，别用 heredoc 传中文。**
2. 早期批次把长中文片段经 shell 变量中转。

**判据边界（如实声明）**：

- 本门禁**只管仓库里的文件**，**管不到 git commit message**。M130 那次 commit message
  的乱码就漏在这里——它已经推上去了，**共享分支上不做 force push**，故如实留档不修。
- 本门禁**不做完整 UTF-8 合法性校验**（`UnicodeDecodeError` 那层由读取时的异常兜）。
  它只认一个信号：**文件里出现了不该出现的 U+FFFD**。
- 「替换字符的个数 = 该 UTF-8 字被破坏的字节数」（1~3）。**2 个仍能辨认出是哪个汉字**，
  3 个则是一个完整汉字被打散——修的时候要靠上下文判断，**不要盲猜**。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAD = "\ufffd"   # 文档里不写字面量，否则门禁会判自己不合规

# ★ 自指提醒（本文件第一版就被自己的判据判为不合法，抓出 7 处）：
#   写这份文档时，为了说明 U+FFFD 是什么，我在注释里写了它的**字面量**，
#   结果 check-encoding.py 把自己判成了不合规。
#   → 办法是**文档里一律不写字面量**（写 U+FFFD 这个名字、或 \\ufffd 这种转义），
#   **不要给自己开豁免**——豁免名单会变成真实的后门，脏字符从此有了合法藏身处。
SCAN_SUFFIX = {".md", ".yml", ".yaml", ".py", ".sh", ".js"}
SKIP_PARTS = {"node_modules", ".vitepress", "dist", ".git"}


def main():
    hits = []
    scanned = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if p.suffix not in SCAN_SUFFIX:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            hits.append((str(rel), 0, f"**根本不是合法 UTF-8**：{e}"))
            continue
        scanned += 1
        for i, line in enumerate(text.split("\n"), 1):
            n = line.count(BAD)
            if n:
                seg = line.split(BAD)
                before = seg[0][-28:]
                after = seg[-1][:28]
                hits.append((str(rel), i, f"{n} 个替换字符，附近文字：…{before}【坏】{after}…"))

    if hits:
        print("编码校验未通过（文件里出现了 U+FFFD 替换字符）：")
        for rel, line, msg in hits:
            where = f"{rel}:{line}" if line else rel
            print(f"  [乱码] {where}  {msg}")
        print()
        print("  **这些是 UTF-8 多字节字符被截断的残骸**，不是正文内容。")
        print("  修法：结合上下文判断原字（**2 个替换字符仍能认出是哪个汉字**，")
        print("       3 个是一个完整汉字被打散，别盲猜），改完重跑本门禁。")
        print("  写文件请用 write 工具或 python 脚本，**别用 bash heredoc 传中文**——")
        print("  M130 写 commit message 时就是这么把「对的」截成「对\ufffd」的。")
        return 1

    print(f"[ ok ] 编码校验：{scanned} 个文本文件均无 U+FFFD 替换字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
