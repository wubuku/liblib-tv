#!/usr/bin/env python3
"""探针内联 JS 的**语法**自检（batch 850 加）。

同一个错在这批里犯了**三次**，三次都是「判据自己抛异常，探针跑到一半崩」：

  ① `FOCUS_JS` 少一个右括号 ⇒ `SyntaxError: Unexpected token ':'`
  ② patch 时把 **Python 风格的 `#` 注释**写进了 `page.evaluate` 的三引号
     字符串**内部** ⇒ `SyntaxError: Invalid or unexpected token`
  ③ `ALIVE_JS` 之类新增的内联块没人看过一眼

它们的共同点：**JS 语法错不会让 `py_compile` 报错**，也不会让探针「安静地
少测一个状态」—— 它是**当场崩**，把前面所有已经量好的结果一起带走
（第三次就丢了三个下拉的 ①②④）。

所以：改完探针先跑这个。它把每个 `evaluate` 三引号块和顶层 `*_JS =` 三引号
常量的 JS 体抽出来，交给 `node --check` 逐个验。**不跑浏览器，秒级。**

用法：
    python3 scripts/jimeng_probe_js_syntax_check.py            # 查所有 jimeng 探针
    python3 scripts/jimeng_probe_js_syntax_check.py foo.py bar.py
退出码：有语法错 ⇒ 1（好让 CI / 门禁能接）
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
NODE_CANDIDATES = [
    "/Users/yangjiefeng/.nvm/versions/node/v24.6.0/bin/node",
    "node",
]

# `X = """…"""`（顶层常量）与 `page.evaluate("""…""")`（内联）两种形态
PAT_CONST = re.compile(r"^[A-Z_0-9]+_JS\s*=\s*\"\"\"(.*?)\"\"\"", re.S | re.M)
PAT_EVAL = re.compile(r"\.evaluate\(\s*\"\"\"(.*?)\"\"\"", re.S)


def find_node() -> str | None:
    import shutil
    for c in NODE_CANDIDATES:
        if c == "node":
            p = shutil.which("node")
            if p:
                return p
        elif pathlib.Path(c).exists():
            return c
    return None


def check_file(path: pathlib.Path, node: str) -> list[str]:
    src = path.read_text(encoding="utf-8")
    # 箭头函数**本身就是表达式**，右边不用加任何前缀
    # （加 `const ` 会变成 `const (lay) => {}` —— 那是「解构模式声明」，
    #   解析直接报错。踩过一次。）
    blocks = [(m.group(1), "const")
              for m in PAT_CONST.finditer(src)]
    blocks += [(m.group(1), "eval")
               for m in PAT_EVAL.finditer(src)]
    errs: list[str] = []
    for i, (body, kind) in enumerate(blocks):
        tmp = pathlib.Path(f"/tmp/_jscheck_{path.stem}_{i}.js")
        tmp.write_text("const __f = " + body + ";\n", encoding="utf-8")
        r = subprocess.run([node, "--check", str(tmp)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            errs.append(f"{path.name} 块 {i}（{kind}，共 {len(blocks)} 块）:\n    "
                        + "\n    ".join(r.stderr.strip().splitlines()[1:4]))
        tmp.unlink(missing_ok=True)
    return errs


def count_blocks(path: pathlib.Path) -> int:
    src = path.read_text(encoding="utf-8")
    return len(PAT_CONST.findall(src)) + len(PAT_EVAL.findall(src))


def main(argv: list[str]) -> int:
    node = find_node()
    if not node:
        print("!! 找不到 node —— 这条自检**必须有** node 才跑得了")
        return 2
    if argv:
        files = [pathlib.Path(a) for a in argv]
    else:
        self_path = pathlib.Path(__file__).resolve()
        files = sorted(f for f in ROOT.glob("jimeng_probe*.py")
                       if f.resolve() != self_path)
    all_errs: list[str] = []
    n_blocks = 0
    for f in files:
        if not f.exists():
            print(f"跳过不存在的 {f}")
            continue
        all_errs += check_file(f, node)
        n_blocks += count_blocks(f)
    print(f"检查 {len(files)} 个探针、约 {n_blocks} 段内联 JS："
          f"{'全部语法正确 ✓' if not all_errs else str(len(all_errs)) + ' 段有错 ✗'}")
    for e in all_errs:
        print("  ✗ " + e)
    if all_errs:
        print("\n⚠ JS 语法错**不会**被 py_compile 抓到，而它会让探针当场崩、"
              "\n  把前面已量好的结果一起带走。改完探针先跑这条。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
