#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 回归：跑既有门禁清单 ⟹ ⟹ 看本批有没有把别的批次弄坏。

## ★ ★★ 本批**扩大了回归清单**（★ 两条重要的补漏）

★ batch 864 的清单（108 条）里**没有** `77` 与 `788`
⟹ ⟹ 本批**实测发现**：这两个门禁的「旧前提」已经过期很久
（`77` 写死了 `count("object={transformTarget}") == 3`；`788` 写死了行号）
⟹ ⟹ 而它们**不在回归清单里** ⟹ ⟹ 那些红**从来没人看见**
⟹ ⟹ ★ 这本身是「回归清单不全 ⟹ ⟹ 红被漏掉」的典型案例。

★ 本批的处理：
- ① 两条门禁的**旧前提**都已整改（77 → 结构性判据 ＋ 窄口径噪声过滤；
  788 → 锚点式，去掉行号依赖）⟹ ⟹ 现在都**绿**；
- ② 把 `77`／`788` **补进回归清单** ⟹ ⟹ 以后它们再红就会被看见；
- ③ 本批的 `865` 也进清单。

★ ★ 纪律：★ **扩大清单后新出现的红必须定点对照归因** ⟹ ⟹
  这一次「扩大」带出来的红**在扩之前就已经红了**（已逐条归因 ⟹ ⟹ 并整改）。

## ★ 本批动过的**被跟踪**源码（本批：取景框上的**构图参考线**开关）

- `src/components/director/DirectorViewport.tsx`
  （`AspectFrame`：★ 新增**框上那枚 32×32 的「构图参考线」开关**（源站逐字
  class ＋ 位置公式 `left = 框宽 − 40`／`top = 8`）；
  ★ 框的描边从 **border** 改成源站逐字的 **outline**（1px／白 18%／内缩 1px）
  ＋ 圆角 12px；★ 三分线颜色从 白 35% 改成 源站逐字的白 **50%**）
- `src/components/director/DirectorAspectPanel.tsx`
  （**只改注释**：补上「无机位禁用分支在 clone 与源站两侧都不可达」的诚实标注；
  ★ 代码那行 `disabled` 绑定是 batch 860 之后本批补上的源站逐字结构）

★ ★ 本批**动了取景框的呈现** ⟹ ⟹ 所有**看那个区域**的门禁都必须进清单
（`860`／`859`／`590`／`617`／`626`／`45`／`50`／`35`／`645`／`722`／`629`／
`815`／`816`／`817`）⟹ ⟹ 否则「框对了」与「别的地方塌了」分不开。
★ ★ 其中 `35`／`645`／`722`／`629` 是**上一批清单里没有**的 ⟹ ⟹ 本批
**扩大了回归清单**（★ 扩大后新出现的红必须**定点对照归因**）。

## ★ 清单覆盖两类门禁

- **`.py`** ＝ 既有 Python 门禁（有的会起浏览器 ⟹ ⟹ **串行**跑）
- **`.mjs`** ＝ 静态断言门禁（`node` 跑）

## 输出

  /tmp/b864-regression.json
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ (批次号, 扩展名) ⟹ ⟹ 显式写清楚，不靠「猜扩展名」
GATES = [
    ("856", "py"),
    ("854", "py"),
    ("853", "py"),
    ("852", "py"),
    ("851", "py"),
    ("850", "py"),
    ("849", "py"),
    ("848", "py"),
    ("847", "py"),
    ("846", "py"),
    ("845", "py"),
    ("844", "py"),
    ("843", "py"),
    ("842", "py"),
    ("841", "py"),
    ("840", "py"),
    ("839", "py"),
    ("830", "py"),
    ("831", "py"),
    ("543", "py"),
    ("783", "py"),
    ("827", "py"),
    ("826", "py"),
    ("838", "py"),
    ("835", "py"),
    ("62", "py"),
    ("111", "py"),
    ("112", "py"),
    ("113", "py"),
    ("146b", "py"),
    ("169", "py"),
    ("556", "py"),
    ("557", "py"),
    ("536", "py"),
    ("538", "py"),
    ("540", "py"),
    ("575", "py"),
    ("46", "py"),
    ("36", "py"),
    ("720", "py"),
    ("42", "py"),
    ("43", "py"),
    ("550", "py"),
    ("588", "py"),
    ("741", "py"),
    ("797", "py"),
    ("798", "py"),
    ("45", "py"),
    ("47", "py"),
    ("48", "py"),
    ("49", "py"),
    ("50", "py"),
    ("91", "py"),
    ("59", "py"),
    ("792", "py"),
    ("96", "py"),
    ("67", "mjs"),
    ("68", "mjs"),
    ("74", "mjs"),
    ("79", "mjs"),
    ("80", "mjs"),
    ("81", "mjs"),
    ("69", "mjs"),
    ("70", "mjs"),
    ("71", "mjs"),
    ("72", "mjs"),
    ("75", "mjs"),
    ("84", "mjs"),
    ("85", "mjs"),
    ("86", "mjs"),
    ("87", "mjs"),
    ("88", "mjs"),
    ("89", "mjs"),
    ("90", "mjs"),
    ("91", "mjs"),
    ("736", "py"),
    ("748", "py"),
    ("749", "py"),
    ("782", "py"),
    ("857", "py"),
    ("625", "py"),
    ("590", "py"),
    ("626", "py"),
    ("613", "py"),
    ("617", "py"),
    ("619", "py"),
    ("541", "py"),
    ("589", "py"),
    ("546", "py"),
    ("624", "py"),
    ("861", "py"),
    ("542", "py"),
    ("738", "py"),
    ("656", "py"),
    ("858", "py"),
    ("648", "py"),
    ("859", "py"),
    ("860", "py"),
    ("862", "py"),
    ("863", "py"),
    ("864", "py"),
    ("35", "py"),
    ("645", "py"),
    ("722", "py"),
    ("629", "py"),
    ("815", "py"),
    ("816", "py"),
    ("817", "py"),
    # ★ ★★ Batch 865 补漏：★ 这两条**之前不在清单里** ⟹ ⟹ 它们的红没人看见
    ("77", "py"),
    ("788", "py"),
    ("865", "py"),
]

# ★ 本批**动过其比对对象**的门禁（应当全绿 ⟹ ⟹ 红了就说明本批改坏了）
# ★ ★★ Batch 864 **修订**：★ WATCH 的语义是「本批动过其比对对象 ⟹ 应当全绿」
#   ⟹ ⟹ **基线就是红的旧账不许放进来**
#   ⟹ ⟹ 否则脚本会**把旧账算成本批引入的红**（第一版就栽在这：
#   ⟹ ⟹ 它把 `91`／`626`／`546`／`542`／`738`／`656`／`648`／`645`／`722`／`629`
#   ⟹ ⟹ 这 10 条**基线就红**的门禁放进了 WATCH ⟹ ⟹ 报出 10 条「红的 WATCH」⟹ ⟹ 退出码 1
#   ⟹ ⟹ 而**真正**的判据是「**相对基线没有新红**」）。
# ★ 所以：旧账单列一份（KNOWN_RED），WATCH 只留**基线为绿**的。
KNOWN_RED = {
    "831", "835", "741", "91", "736", "748", "749", "782",   # 旧账
    "626",                                                   # D7：源站同款
    "542", "546",                                            # fixture 缺失
    "738",                                                   # C7 写死个数过期
    "656", "648", "645", "722", "629",                       # 扩大清单后可见的旧账
}

# ★ ★★ **已归因的偶发门禁**（★ 与 `KNOWN_RED` 不同：它们**平时是绿的**）
#   ⟹ ⟹ 判据里要把它们**单独列出来**，而不是塞进「旧账」里
#   ⟹ ⟹ （塞进旧账 ⟹ ⟹ 以后它们真的坏了也不会报 ⟹ ⟹ 那就是掩盖）。
KNOWN_FLAKY = {
    # ★ `62` 的红是**图片请求被中止**：
    #   `requestfailed:GET:http://localhost:4317/images/liblib-panels/toolbox-24.webp:net::ERR_ABORTED`
    #   （`toolbox-25.webp` 同款）⟹ ⟹ 典型的**teardown 竞态**（浏览器在图片加载完之前就关了）
    #   ⟹ ⟹ **不是**本批引入：① 本批**只**改了 `directorTelemetry.ts`／`directorStore.ts`／
    #   `DirectorAspectPanel.tsx`／`DirectorViewport.tsx` 四个文件
    #   ⟹ ⟹ 而 `62.py` 里 `aspect`／`telemetry`／`director-aspect` **出现 0 次**；
    #   ② 连跑三次：**红 / 绿 / 绿**（两次绿）⟹ ⟹ 它本来就会偶发。
    "62": "★ toolbox-2x.webp 的 ERR_ABORTED（teardown 竞态）⟹ ⟹ 与本批无关，证据见 README §5.3",
}

WATCH = [
    "856",
    "854",
    "853",
    "852",
    "851",
    "850",
    "849",
    "848",
    "847",
    "830",
    "543",
    "540",
    "550",
    "588",
    "45",
    "50",
    "96",
    "67",
    "68",
    "74",
    "79",
    "80",
    "81",
    "69",
    "70",
    "71",
    "72",
    "75",
    "84",
    "85",
    "86",
    "89",
    "90",
    "857",
    "625",
    "590",
    "613",
    "617",
    "619",
    "541",
    "589",
    "624",
    "536",
    "538",
    "858",
    "859",
    "860",
    "862",
    "35",
    "815",
    "816",
    "817",
    "863",
    "864",
    # ★ Batch 865：★ 77／788 现在**是绿的** ⟹ ⟹ 可以进「盯」名单
    "77",
    "788",
    "865",
]
# ★ ★★ 上面的 WATCH 已经**剔掉了 10 条基线就红的旧账**
#   （`91`／`626`／`546`／`542`／`738`／`656`／`648`／`645`／`722`／`629`）
#   ⟹ ⟹ 「WATCH 里红的」现在**只可能**是本批引入的 ⟹ ⟹ 退出码才有意义。
# ★ 旧账仍在 `GATES` 里跑（⟹ ⟹ 它们的红仍会被记下来 ⟹ ⟹ 可对照），
#   只是**不再算进「本批引入」**。


def run(batch: str, ext: str) -> dict:
    script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    if not script.exists():
        return {"batch": batch, "ext": ext, "rc": None, "verdict": "（无此门禁）"}
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=3600, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"batch": batch, "ext": ext, "rc": "timeout", "verdict": "超时"}
    out = (r.stdout or "") + (r.stderr or "")
    verdict = None
    for ln in out.splitlines():
        if ln.strip().endswith("通过") and "/" in ln:
            verdict = ln.strip().split()[-1]
    if verdict is None:
        tail = [x.strip() for x in out.splitlines() if x.strip()][-3:]
        verdict = "rc=%s " % r.returncode + " ／ ".join(tail)[-160:]
    return {"batch": batch, "ext": ext, "rc": r.returncode, "verdict": verdict}


def score(results: list) -> dict:
    """★ 把「跑出来的读数」变成「判定」⟹ ⟹ 判定与「跑」**分开** ⟹ ⟹
    ★ 改判据时**不必重跑 108 条门禁**（用 `--rescore` 复算即可）。"""
    red = ["%s.%s" % (r["batch"], r["ext"]) for r in results
           if r["rc"] not in (0, None)]
    watch_red = [b for b in red if b.split(".")[0] in WATCH]
    known_red = [b for b in red if b.split(".")[0] in KNOWN_RED]
    # ★ ★★ 「**新红**」＝ 红集合 − 旧账集合 ⟹ ⟹ 这才是**本批引入**的
    #   ⟹ ⟹ 判据是「新红 == 0」⟹ ⟹ 而不是「红 == 0」（旧账永远红）
    new_red = [b for b in red if b.split(".")[0] not in KNOWN_RED]
    # ★ 已归因的**偶发**门禁：⟹ ⟹ 它们**平时是绿的** ⟹ ⟹ 不塞进旧账
    #   ⟹ ⟹ （塞进旧账 ⟹ ⟹ 以后真坏了也不报）⟹ ⟹ 而是**单列**出来，
    #   ⟹ ⟹ 并在判定里**不算作**本批引入的红。
    flaky_hits = [b for b in new_red if b.split(".")[0] in KNOWN_FLAKY]
    attributed_new = [b for b in new_red if b.split(".")[0] not in KNOWN_FLAKY]
    print("\n== 回归：%d 条，红 %d 条 %s ==" % (len(results), len(red), red))
    print("== 其中旧账 %d 条：%s ==" % (len(known_red), known_red))
    print("== ★ 新红（相对基线）%d 条：%s ==" % (len(new_red), new_red))
    if flaky_hits:
        print("== ★ 其中**已归因的偶发** %d 条：%s ==" % (len(flaky_hits), flaky_hits))
        for b in flaky_hits:
            print("     ⟹ %s" % KNOWN_FLAKY.get(b.split(".")[0], ""))
    print("== ★★★ 本批引入的红 %d 条：%s ==" % (len(attributed_new), attributed_new))
    print("== 盯的 %d 条里红的：%s ==" % (len(WATCH), watch_red))
    return {"红": red, "旧账": known_red, "新红": new_red,
            "已归因的偶发": flaky_hits, "本批引入": attributed_new,
            "WATCH里红的": watch_red}


def main() -> int:
    outp = pathlib.Path("/tmp/b865-regression.json")
    # ★ ★ `--rescore`：不跑门禁，**只按已有读数复算判定**
    #   ⟹ ⟹ 改判据时不必重跑 108 条 ⟹ ⟹ 但**读数必须来自真实那一跑**
    if "--rescore" in sys.argv:
        results = json.loads(outp.read_text(encoding="utf-8"))
        s = score(results)
        ok = not (s["本批引入"] or s["WATCH里红的"])
        print("\n== 复算判定：%s ==" % ("通过" if ok else "不通过"))
        return 0 if ok else 1

    results = []
    for batch, ext in GATES:
        res = run(batch, ext)
        results.append(res)
        print("%-6s %-4s rc=%-5s %s"
              % (res["batch"], res["ext"], res["rc"], res["verdict"]), flush=True)
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    # ★ ★★ 读数**落进批次目录** ⟹ ⟹ README 的「产物索引」才是真的
    #   ⟹ ⟹ （原来只写 `/tmp` ⟹ ⟹ 提交后**证据不存在**）
    s = score(results)
    raw = (pathlib.Path(__file__).resolve().parents[1] / "raw")
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "regression.json").write_text(
        json.dumps({"逐条读数": results, "判定": s}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("★ 读数已落盘：docs/research/liblib-canvas-batch865-2026-10-01/raw/regression.json")
    return 1 if (s["本批引入"] or s["WATCH里红的"]) else 0


if __name__ == "__main__":
    sys.exit(main())
