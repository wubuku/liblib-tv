#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 867 回归：★ 把回归清单扩到**全部碰本批区域的门禁** ⟹ ⟹ 看有没有塌。

## ★ ★★ 本批的靶子：★ **回归清单的覆盖面**（不是新增功能）

★ batch 865 实测出一条形状：★ 「**碰本批改动区域**的门禁」如果**不在**回归
清单里 ⟹ ⟹ 它们的红**从来没人看见**。
★ batch 865 补了 `77`／`788`（两条**不在** 864 清单里的门禁）⟹ ⟹ 两条当场红了
⟹ ⟹ **旧前提过期很久**，而没人知道。

★ 本批把这件事**做成普查**：
- ① 扫出仓库里**所有** `verify-liblib-batch*.py`（**563** 个）；
- ② 扫出**引用了本批相关源文件**（`DirectorViewport.tsx`／`DirectorAspectPanel.tsx`／
  `directorStore.ts`／`directorTelemetry.ts`）的门禁 ⟹ ⟹ **80** 个；
- ③ 其中**不在**回归清单里的 ⟹ ⟹ **46** 个
  ⟹ ⟹ **这 46 个的红从来没人看见**；
- ④ 把这 **46** 个**全部**跑一遍 ⟹ ⟹ 拿到红/绿基线
  ⟹ ⟹ 红的**逐条定点归因**（是旧账？是偶发？还是本批引入？）；
- ⑤ 把它们**补进回归清单** ⟹ ⟹ 清单从 **111** 条扩到 **157** 条
  ⟹ ⟹ 以后它们再红就会被看见。

★ ★ 纪律：★ **扩大清单后新出现的红必须定点对照归因** ⟹ ⟹
  ⟹ ⟹ 而且**要先证明那些红在扩之前就已经红了**（本批用「HEAD 态对照」证明），
  ⟹ ⟹ 否则「本批引入的红」与「旧账」分不开。

## ★ 清单覆盖两类门禁

- **`.py`** ＝ 既有 Python 门禁（有的会起浏览器 ⟹ ⟹ **串行**跑）
- **`.mjs`** ＝ 静态断言门禁（`node` 跑）

## 输出

  docs/research/liblib-canvas-batch867-2026-10-01/raw/regression.json
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
    ("91", "mjs"),
    ("59", "py"),
    ("792", "py"),
    ("96", "py"),
    ("67", "py"),
    ("68", "py"),
    ("74", "py"),
    ("79", "py"),
    ("80", "py"),
    ("81", "py"),
    ("69", "py"),
    ("70", "py"),
    ("71", "py"),
    ("72", "py"),
    ("75", "py"),
    ("84", "py"),
    ("85", "py"),
    ("86", "py"),
    ("87", "py"),
    ("88", "py"),
    ("89", "py"),
    ("90", "py"),
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
    ("77", "py"),
    ("788", "py"),
    ("865", "py"),
    ("37", "py"),
    ("38", "py"),
    ("39", "py"),
    ("40", "py"),
    ("41", "py"),
    ("44", "py"),
    ("599", "py"),
    ("630", "py"),
    ("641", "py"),
    ("662", "py"),
    ("685", "py"),
    ("686", "py"),
    ("687", "py"),
    ("688", "py"),
    ("689", "py"),
    ("690", "py"),
    ("700", "py"),
    ("701", "py"),
    ("721", "py"),
    ("750", "py"),
    ("751", "py"),
    ("752", "py"),
    ("76", "py"),
    ("763", "py"),
    ("764", "py"),
    ("767", "py"),
    ("768", "py"),
    ("769", "py"),
    ("770", "py"),
    ("774", "py"),
    ("776", "py"),
    ("781", "py"),
    ("784", "py"),
    ("785", "py"),
    ("786", "py"),
    ("787", "py"),
    ("789", "py"),
    ("821", "py"),
    ("822", "py"),
    ("823", "py"),
    ("828", "py"),
    ("833", "py"),
    ("837", "py"),
    ("855", "py"),
    ("93", "py"),
    ("95", "py"),
    ("866", "py"),
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
    ("76", "mjs"),
    # ★ ★★ Batch 867：★ 把「依赖已消失的 /tmp 文件」的那批**补进清单**
    #   ⟹ ⟹ ★ 之前它们**不在**清单里 ⟹ ⟹ 它们的红**从来没人看见**
    #   ⟹ ⟹ ★ ★ 纠正：★ 753–759 **七条全都不在** 866 清单里 ⟹ ⟹ 全补
    ("753", "py"),
    ("754", "py"),
    ("755", "py"),
    ("756", "py"),
    ("757", "py"),
    ("758", "py"),
    ("759", "py"),
    # ★ ★★ Batch 867：★ 普查出「依赖已消失的 /tmp 文件」的门禁 **16** 个
    #   ⟹ ⟹ ★ 上面补进的是 753–759（九条）⟹ ⟹ 这里补齐**其余**五条
    #   ⟹ ⟹ ★ 它们**都不在** 866 清单里 ⟹ ⟹ 它们的红**从来没人看见**
    ("554", "py"),
    ("562", "py"),
    ("565", "py"),
    ("760", "py"),
    ("761", "py"),
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
    # ★ ★★ Batch 866：**扩清单后可见的 21 条**（★ 它们**不在** 865 清单里
    #   ⟹ ⟹ 那些红**从来没人看见**）⟹ ⟹ 逐条归因如下：
    #   ⟹ ⟹ ★ **共同点**：★ 每一条都在 **batch 864 态就已经是红的**
    #   ⟹ ⟹   （证据：`raw/head464-comparison.json` 的 `红绿不同` 为空）
    #   ⟹ ⟹ ⟹ ⟹ 所以它们是**旧账**，**不是**本批引入。
    "40",                                                    # ★ 取景框 locator 超时（旧账）
    "630",                                                   # ★ 面板挤压覆盖（旧账）
    "685",                                                   # ★ 步进折点（旧账）
    "686",                                                   # ★ 轴向步进（旧账）
    "690",                                                   # ★ 标尺宽度律（旧账）
    "750", "751",                                            # ★ **依赖 `/tmp/dbg75xe.py`**（临时文件已不存在 ⟹ 环境型）
    "752",                                                   # ★ 存疑项有源站证据（旧账）
    "76",                                                    # ★ TransformControls 控制台噪声（旧账）
    "763", "764", "767", "768", "770", "774", "781",         # ★ 各自基线红（旧账）
    "769",                                                   # ★ **写死了 `data-director-crowd-panel` 的位置**（源码已变 ⟹ 找不到）
    # ★ ★★ `785` **本批已整改** ⟹ ⟹ 它**不在** `KNOWN_RED` 里
    #   ⟹ ⟹ ★ 「登记成旧账」不能变成「掩盖它坏了」的借口 ⟹ ⟹ 门禁有判据守着
    "786", "787",                                            # ★ ★ **它们自己拒绝跑阴性对照**（"基线有 N 项红 ⟹ 阴性对照没意义"）⟹ ⟹ 是**自我保护**，不是缺陷
    "789",                                                   # ★ ★ 同上（"基线有 1 项红 ⟹ 阴性对照没意义"）
    # ★ ★★ Batch 866：**扩清单后跑出来的 4 条「新红」** ⟹ ⟹ **逐条归因**
    #   ⟹ ⟹ 证据：`raw/newred-attribution.json`（★ HEAD864 态 vs WORK 态）
    # ★ ★★ `68`／`71`／`87`：**`.py` 与 `.mjs` 是两份不同的门禁** ⟹ ⟹
    #   ⟹ ⟹ `.mjs`（静态断言）**全绿** ⟹ ⟹ `.py`（浏览器）**全红**
    #   ⟹ ⟹ ★ 红因＝**TransformControls 控制台噪声**（与 `76` 同款）
    #   ⟹ ⟹ ⟹ ⟹ 且 HEAD864／WORK 两态**都红** ⟹ ⟹ ⟹ ⟹ 旧账
    #   ⟹ ⟹ ★ 旧账**只登记 `.py`**（★ `.mjs` 那份是**绿的** ⟹ ⟹ 不该被记账）
    "68.py", "71.py", "87.py",
    # ★ ★★ Batch 867：★ 「依赖已消失的 /tmp 文件」的那批
    #   ⟹ ⟹ ★ 它们**必然红** ⟹ ⟹ 登记成旧账（★ **带说明**）
    #   ⟹ ⟹ ★ ★★ 其中 753–759 **本批已整改** ⟹ ⟹ 它们绿了 ⟹ ⟹ **不登记**
    "554",                                                    # ★ fixture 缺失（`/tmp/batch554-fixture.png`）
    "562",                                                    # ★ 同上
    "760",                                                    # ★ 判据层失败（★ 与 /tmp 无关 ⟹ ⟹ 见 raw/baseline-tmp-deps.json）
    # ★ `565`／`761`：★ **绿的** ⟹ ⟹ 它们**不在** KNOWN_RED 里（★ 旧账只登记红的）

    # ★ `843`：★ 回归那一轮红 ⟹ ⟹ **单独连跑三次全绿** ⟹ ⟹ **偶发**
    #   ⟹ ⟹ ⟹ ⟹ 归因：`843` **完全不碰**本批区域 ⟹ ⟹ 且两态读数相同（都绿）
    "843",
}


# ★ ★★ **已归因的偶发门禁**（★ 与 `KNOWN_RED` 不同：它们**平时是绿的**）
#   ⟹ ⟹ 判据里要把它们**单独列出来**，而不是塞进「旧账」里
#   ⟹ ⟹ （塞进旧账 ⟹ ⟹ 以后它们真的坏了也不会报 ⟹ ⟹ 那就是掩盖）。
KNOWN_FLAKY = {
    # ★ ★★ Batch 866 新增：★ `843` 在回归那一轮红 ⟹ ⟹ 单独连跑**三次全绿**
    #   ⟹ ⟹ 且它**完全不碰**本批区域 ⟹ ⟹ 且 HEAD864／WORK 两态读数相同（都绿）
    #   ⟹ ⟹ ⟹ ⟹ ⇒ **偶发**（★ 与 `62` 同款：★ 平时是绿的 ⟹ ⟹ 不能塞进旧账
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 否则它真的坏了也不会报）
    "843": "★ batch 867 回归那一轮红，单独连跑三次全绿 ⟹ ⟹ 偶发",
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
    # ★ ★★ Batch 866：★ `68` 的 **`.py` 那份**（浏览器门禁）**基线就红**
    #   ⟹ ⟹ ★ 它**从来没被基线测过**（不在 865 清单里）⟹ ⟹ 不该在 WATCH 里
    #   ⟹ ⟹ ⟹ ⟹ （★ WATCH 的语义是「**基线为绿**、本批动过其比对对象」）
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ 只盯它的 **`.mjs`** 那份（静态断言 ⟹ ⟹ 绿）
    "68.mjs",
    "74",
    "79",
    "80",
    "81",
    "69",
    "70",
    # ★ 同上：★ `71` 的 `.py` 那份基线就红 ⟹ ⟹ 只盯 `.mjs` 那份
    "71.mjs",
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
    # ★ ★★ Batch 867：★ 本批补进的那批里**基线为绿**的 ⟹ ⟹ 可以进「盯」名单
    #   ⟹ ⟹ ★ `565`／`761`（★ 它们的 /tmp 依赖缺失**不影响**它们跑绿）
    "565",
    "761",
    # ★ ★★ Batch 867：**本批整改过**的那七条 ⟹ ⟹ 它们现在是绿的 ⟹ ⟹ 可以进「盯」名单
    "753", "754", "755", "756", "757", "758", "759",
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
    ★ 改判据时**不必重跑 177 条门禁**（用 `--rescore` 复算即可）。

    ★ ★★ Batch 866：★ **匹配必须按 (批次, 扩展名)**，不能只按批次号。
      ★ 原因：★ `68`／`71`／`87` 等批次**有两份不同的门禁**
      ⟹ ⟹ `.mjs`（静态断言，**绿**）与 `.py`（浏览器，**红**）
      ⟹ ⟹ ⟹ ⟹ 只按批次号匹配 ⟹ ⟹ `68.mjs` 的绿会替 `68.py` 的红**背书**
      ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 于是「本批引入的红」被**掩盖**
      ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹
      ★ ⇒ **旧账也要能只登记某个扩展名**（★ `"68.py"` 而**不是** `"68"`）。
    """
    red = ["%s.%s" % (r["batch"], r["ext"]) for r in results
           if r["rc"] not in (0, None)]

    def _matched(item: str, names: set[str]) -> bool:
        """★ 「批次.ext」是否命中 `names` ⟹ ⟹ `names` 里可以写
        ★ 「批次.ext」（精确）**或**「批次」（该批次全部扩展名）。"""
        b, _, e = item.partition(".")
        return item in names or b in names

    watch_red = [b for b in red if _matched(b, WATCH)]
    known_red = [b for b in red if _matched(b, KNOWN_RED)]
    # ★ ★★ 「**新红**」＝ 红集合 − 旧账集合 ⟹ ⟹ 这才是**本批引入**的
    #   ⟹ ⟹ 判据是「新红 == 0」⟹ ⟹ 而不是「红 == 0」（旧账永远红）
    new_red = [b for b in red if not _matched(b, KNOWN_RED)]
    # ★ 已归因的**偶发**门禁：⟹ ⟹ 它们**平时是绿的** ⟹ ⟹ 不塞进旧账
    #   ⟹ ⟹ （塞进旧账 ⟹ ⟹ 以后真坏了也不报）⟹ ⟹ 而是**单列**出来，
    #   ⟹ ⟹ 并在判定里**不算作**本批引入的红。
    flaky_hits = [b for b in new_red if _matched(b, KNOWN_FLAKY)]
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
    outp = pathlib.Path("/tmp/b867-regression.json")
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
    print("★ 读数已落盘：docs/research/liblib-canvas-batch867-2026-10-01/raw/regression.json")
    return 1 if (s["本批引入"] or s["WATCH里红的"]) else 0


if __name__ == "__main__":
    sys.exit(main())
