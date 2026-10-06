#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 821 验收器 —— 导演台·相机预设的错误提示是「状态算出来的」还是「操作产生的」

## 为什么换到导演台

815–820 六批全在画布那一条链上（派生节点 → 撤销栈 → 封顶）。
用户指定的两个重点是**画布与导演台**，导演台**六批完全没碰**。

## 起点（读源码发现的）

`directorStore.ts:7565` 的 `applyCameraMotionPreset` 有三条拒绝分支，
反馈机制不一样；**UI 上同一个 `data-director-camera-preset-error`
有两处渲染，驱动源完全不同**：

- `DirectorTimeline.tsx:1097` ← 条件 `cameraFollowActive` ⟹ **状态驱动**
  （用户**一个按钮都没点**，提示就已经在屏幕上了）；
- `DirectorTimeline.tsx:1468` ← `selectedPresetError`（store 的 `error`）
  ⟹ **操作驱动**（只有真按了预设才出现）。

★ 而 `:1084` 的开关按钮是
`disabled={selectedTrack?.kind !== "camera" || cameraFollowActive}`
⟹ **跟随目标时按钮直接 disabled** ⟹ store 的**分支序2 用户走不到**。

## ★ 判据

- **S1 ★★ 前提**：导演台打开、相机轨道存在。
- **S2 ★★★** ★ **状态驱动**：跟随目标激活、**一个按钮都没点**，面板外提示**已经**出现，按钮 disabled。
- **S3 ★★★** ★ 程序化调用**能**走到 store 的分支序2（返回 false ＋ error 被设上），
  而 UI 按钮 disabled ⟹ **该分支用户走不到**。
- **S4 ★★★** ★ **陈旧提示**：清掉跟随目标后面板外的状态提示消失，
  但**打开预设面板时面板内那条仍在** ⟹ 文案与当前状态不符。
- **S5 ★★★** 锁定拒绝：命令反馈出现「目标对象已锁定，未应用修改」＋
  `DIRECTOR_TARGET_LOCKED`，而**预设错误提示不变**。
- **S6 ★★★** 成功路径：两条提示**都清掉**。
- **S7 ★★★** 扫描器自检（两通道各注入一个探针，都必须扫到）。
- **S8 ★★** 静态锚点：`:1084` 的 disabled 条件、`:1097`／`:1468` 两处渲染、
  `:7575` 分支序1 只写 `lastCommandResult`。
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB821_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch821-2026-10-01"
                    / "raw" / "vb821a.json"))
OUT = pathlib.Path(os.environ.get("VB821_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch821-2026-10-01"
                    / "verify-report.json"))
TL = "src/components/director/DirectorTimeline.tsx"
DS = "src/components/director/DirectorDesk.tsx"
ST = "src/store/directorStore.ts"

F_READS = "读取"
F_OPS = "操作"
F_ST = "store"
F_DOM = "dom"
F_PRESET_ERR = "★ 预设错误提示"
F_CMD_FB = "★ 命令反馈"
F_TRIG_DIS = "开关按钮disabled"
F_SELFTEST = "★ 扫描器自检"          # ★ 在 dom 里
F_PROBES = "★ 探针被扫到几个"       # ★ 在 dom 里
# ★ 「★ 预设错误提示」「★ 命令反馈」在**读数的顶层**，
# 而「开关按钮disabled」等在 **dom 里** —— ★ 这两层必须分开写常量，
# 否则判据里就会出现「查错层」的读数（821 连续判红两次都是它）。
F_PROG = "程序化 applyCameraMotionPreset"

#: 七个时刻的标签（★ 写死**顺序**而不是索引 ⟹ 少一个时刻就判红）
TAGS = ["序0·刚打开导演台、什么都还没点",
        "序0b·选中了相机轨道、还没点任何按钮",
        "臂1·设了跟随目标、**一个按钮都还没点**",
        "臂1b·程序化调过预设之后",
        "臂1c·清掉跟随目标之后",
        "臂2·锁住相机、还没按预设",
        "臂2b·打开预设面板之后",
        "臂2c·锁定状态下按了预设之后",
        "臂2d·解锁后按预设（成功路径）"]


def run_checks(raw, src_tl, src_ds, src_st):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    cells = raw["cells"]
    good = [x for x in cells if not x.get("FAILED")]
    r0 = (good[0].get(F_READS) or [])

    def at_r(tag):
        """run_checks 自己的取时刻器（读的是**基线 raw**，不收参数）"""
        return next((r for r in r0 if r.get("时刻") == tag), None)

    # ── S1 ★★ 前提：九个时刻一个不缺，且扫描器自检过
    tags = [r.get("时刻") for r in r0]
    st = (r0[0].get(F_ST) or {}) if r0 else {}
    add("S1:★★ **前提**：导演台打开、相机轨道存在、九个时刻**一个不缺**、"
        "扫描器自检**全程通过**",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。"
        "★ 「时刻一个不缺」写死**顺序**而不是索引 ⟹ 探针中途少读一个时刻"
        "（比如某步异常被吞掉）就会判红，而不是让后面的读数悄悄错位。"
        "★ 扫描器自检是**每一刻**都做的（不是只做一次）",
        bool(r0) and tags == TAGS
        and all((r.get(F_DOM) or {}).get(F_SELFTEST) is True for r in r0)
        and bool(st.get("相机对象")),
        {"时刻": tags,
         "★ 九个时刻齐": tags == TAGS,
         "★ 每刻自检都过": [(r.get("时刻"),
                        (r.get(F_DOM) or {}).get(F_SELFTEST)) for r in r0],
         "★ 起点 store": st, "★ 操作": good[0].get(F_OPS)})

    # ── S2 ★★★ 状态驱动：一个按钮都没点，提示已经在了
    ev = []
    for r in r0:
        d = r.get(F_DOM) or {}
        out = [x for x in (r.get(F_PRESET_ERR) or [])
               if not x.get("在预设面板内部")]
        ev.append({"时刻": r.get("时刻"), "开关disabled": d.get(F_TRIG_DIS),
                   "面板外提示": [x.get("文本") for x in out],
                   "★ 是状态驱动的那一条": bool(out)})
    a1 = at_r(TAGS[2]) or {}
    add("S2:★★★ ★ **状态驱动**：跟随目标一激活，"
        "「跟随目标时不可使用预设运镜」**就已经在屏幕上**（面板外、面板未开）",
        "★★ `DirectorTimeline.tsx:1097` 的渲染条件是 `cameraFollowActive`，"
        "**不读 store 的 `error`** ⟹ ★ 它是「**状态算出来的**」，"
        "不是「**操作产生的**」。"
        "★ 判据要求它出现在**面板外面**（`:1468` 那处在面板内部），"
        "这样才排除「其实是另一处渲染的」；"
        "★ 同时要求此刻按钮 `disabled`（`:1084` 的条件）——"
        "⟹ ★ **这条提示出现的时刻，正是按钮点不动的时刻**",
        # ★ 目标时刻 = 跟随目标刚设上、**一个按钮都没点**的那一刻
        bool([x for x in ev if x["时刻"] == TAGS[2]])
        and all(
            x["面板外提示"] == ["跟随目标时不可使用预设运镜"]
            and x["开关disabled"] is True
            for x in ev if x["时刻"] == TAGS[2])
        # ★ 而**在跟随目标还没设上**的那些时刻，面板外**不该**有这条提示
        and all(x["面板外提示"] == []
                for x in ev if x["时刻"] in (TAGS[0], TAGS[1], TAGS[4])),
        {"逐条": ev,
         "★ 目标时刻": TAGS[2],
         "★ 目标时刻读数": next((x for x in ev if x["时刻"] == TAGS[2]), None)})

    # ── S3 ★★★ 分支序2 程序化可达、但用户走不到
    prog = (good[0].get(F_OPS) or {}).get(F_PROG) or {}
    a1b = at_r(TAGS[3]) or {}
    a1c = at_r(TAGS[4]) or {}
    add("S3:★★★ ★ store 的**分支序2 程序化可达**、而 UI 按钮 `disabled` "
        "⟹ **那条拒绝分支用户走不到**",
        "★★★ `directorStore.ts:7587` 的分支序2（跟随目标）确实存在、"
        "确实会被触发 —— ★ **但 `:1084` 的按钮在跟随目标时是 `disabled` 的** "
        "（`:602`／`:696` 也各有一次同样的守卫）⟹ "
        "★ **从 UI 出发，用户永远走不到它**，只有程序化调用能到达。"
        "★ 这**不是缺陷**（store 层的防御性守卫），但它是一条值得记的结构读数："
        "★ **store 的分支集合 ≠ 用户可达的分支集合**。"
        "★ 判据要求：程序化调用返回 `false` **且** store 的 `presetError` "
        "**被设上**（两件同时）—— ★ 只看返回值不够，"
        "因为 `:7574` 的守卫也会返回 `false` 而什么都不写",
        prog.get("返回") is False
        and prog.get("presetError") == "跟随目标时不可使用预设运镜"
        and (a1b.get(F_DOM) or {}).get(F_TRIG_DIS) is True
        and a1b.get(F_PRESET_ERR) is not None,
        {"程序化调用读数": prog,
         "★ 按钮那一刻 disabled": (a1b.get(F_DOM) or {}).get(F_TRIG_DIS),
         "★ 清掉跟随后按钮": (a1c.get(F_DOM) or {}).get(F_TRIG_DIS),
         "★ 清掉跟随后提示": a1c.get(F_PRESET_ERR)})

    # ── S4 ★★★ 陈旧提示
    a1c_in = [x for x in (a1c.get(F_PRESET_ERR) or [])
              if x.get("在预设面板内部")]
    a2b = at_r(TAGS[6]) or {}
    a2b_in = [x for x in (a2b.get(F_PRESET_ERR) or [])
              if x.get("在预设面板内部")]
    add("S4:★★★ ★ **陈旧提示**：跟随目标**已经清掉**了，"
        "面板外那条随之消失，但**打开预设面板时面板内那条仍在**",
        "★★ 这一条是本批**最有分量**的读数。"
        "★ 同一个 `data-director-camera-preset-error` 有**两处渲染**："
        "`:1097` 是**状态驱动**（跟随目标还在 ⟹ 显示）、"
        "`:1468` 是**操作驱动**（读 store 的 `error`）。"
        "★ 清掉跟随目标之后，`:1097` 那条**正确地**消失了；"
        "★ 但 `:1468` 那条**读的是 store 里没被清掉的 `error`** ⟹ "
        "★ 屏幕上**继续挂着一句「跟随目标时不可使用预设运镜」**——"
        "★ **而此刻已经没有跟随目标了，那句话是错的**。"
        "★ 它一直挂到**下一次成功操作**把它清掉为止（见 S6）。"
        "★ 判据要求**两半同时成立**：状态提示已消失 ＋ 面板内那条仍在。",
        (a1c.get(F_PRESET_ERR) == [] and bool(a2b_in)
         and a2b_in[0].get("文本") == "跟随目标时不可使用预设运镜"
         and (a2b.get(F_ST) or {}).get("跟随目标") is None),
        {"清掉跟随后的提示（面板外）": a1c.get(F_PRESET_ERR),
         "打开面板后的面板内提示": a2b_in,
         "★ 那一刻 store 的跟随目标": (a2b.get(F_ST) or {}).get("跟随目标"),
         "★ 那一刻 store 的 presetError":
             (a2b.get(F_ST) or {}).get("presetError")})

    # ── S5 ★★★ 锁定拒绝走的是**另一条通道**
    a2 = at_r(TAGS[5]) or {}
    a2c = at_r(TAGS[7]) or {}
    fb = a2c.get(F_CMD_FB) or []
    add("S5:★★★ 锁定拒绝的反馈走的是**另一条通道**"
        "（`data-director-command-feedback`），**预设错误提示不变**",
        "★★ `directorStore.ts:7575` 的分支序1（锁定）**只**写 "
        "`lastCommandResult`（REJECTED／`DIRECTOR_TARGET_LOCKED`），"
        "**不碰** `cameraMotionPreset.error` ⟹ 所以它**不该**改变预设错误提示。"
        "★ 它的反馈经 `DirectorDesk.tsx:348` 的 `getDirectorCommandFeedback` "
        "渲染到 `:983` 的 `data-director-command-feedback`，"
        "文案是 `directorCommandFeedback.ts` 里的 "
        "`DIRECTOR_TARGET_LOCKED → 目标对象已锁定，未应用修改`。"
        "★ ★ **本条是探针返工的产物**：第一版压根没扫这条通道，"
        "于是把「锁定拒绝没有任何提示」读成了**静默** —— 而它其实有反馈。"
        "★ 判据要求：命令反馈**出现了**且理由是 `DIRECTOR_TARGET_LOCKED`，"
        "**同时**预设错误提示**一字未变**",
        bool(fb) and fb[0].get("理由") == "DIRECTOR_TARGET_LOCKED"
        and "目标对象已锁定" in (fb[0].get("文本") or "")
        and a2.get(F_CMD_FB) == []
        and a2c.get(F_PRESET_ERR) == a2b.get(F_PRESET_ERR),
        {"按之前（臂2）的命令反馈": a2.get(F_CMD_FB),
         "按之后（臂2c）的命令反馈": fb,
         "★ 预设错误提示按之前": a2b.get(F_PRESET_ERR),
         "★ 预设错误提示按之后": a2c.get(F_PRESET_ERR),
         "★ 两者相同": a2c.get(F_PRESET_ERR) == a2b.get(F_PRESET_ERR)})

    # ── S6 ★★★ 成功路径把两条提示都清掉
    a2d = at_r(TAGS[8]) or {}
    add("S6:★★★ 成功路径（解锁后按预设）把**两条提示都清掉**",
        "★★ `directorStore.ts:7675` 的成功分支显式设 `error: null`，"
        "并且 `lastCommandResult` 变成 `COMMITTED` ⟹ "
        "`getDirectorCommandFeedback` 对 `COMMITTED` 返回 `null`（`:73`）"
        "⟹ ★ **两个通道的提示一起消失**。"
        "★ 这一条顺带给 S4 的「陈旧提示」划了个**边界**："
        "★ 它**不是**永久的，**一次成功操作就把它清掉了**——"
        "★ 所以准确的描述是「**会挂到下一次成功操作为止**」，"
        "而不是「永远错着」。",
        a2d.get(F_PRESET_ERR) == [] and a2d.get(F_CMD_FB) == []
        and (a2d.get(F_ST) or {}).get("presetError") is None,
        {"成功之后的预设错误提示": a2d.get(F_PRESET_ERR),
         "成功之后的命令反馈": a2d.get(F_CMD_FB),
         "成功之后的 store.presetError": (a2d.get(F_ST) or {}).get("presetError"),
         "★ 成功之前的 store.lastCommand": (a2c.get(F_ST) or {}).get("lastCommand")})

    # ── S7 ★★★ 扫描器自检（两通道各注入一个探针）
    got = [(r.get("时刻"), (r.get(F_DOM) or {}).get(F_PROBES))
           for r in r0]
    add("S7:★★★ 扫描器自检：两个通道各注入一个探针，**每一刻都能扫到两个**",
        "★★★ 「屏幕上有／没有提示」是**否定性读数**，"
        "而否定性读数最容易是**探针自己坏了**。"
        "★ 所以每次扫描都往页面注入**两个**探针"
        "（一个挂 `data-director-camera-preset-error`、一个挂 "
        "`data-director-command-feedback`），**必须两个都扫得到**。"
        "★ 只注入一个不够 —— 第一版就因为**只扫了一个通道**、"
        "把「锁定拒绝是静默」读成了假结论（见 S5）。",
        # ★ 修一个**判据与 why 不一致**：第一版只查「每刻扫到 2 个探针」，
        #   于是阴性对照 N9（把自检改成 False）**打不中**这条 ⟹ 而它的 why
        #   明写「S1 与 S7 都要翻红」。⟹ 补上自检条件（**加强**，不是放宽）。
        all(n == 2 for _, n in got) and len(got) == len(TAGS)
        and all((r.get(F_DOM) or {}).get(F_SELFTEST) is True for r in r0),
        {"逐刻扫到的探针个数": got,
         "逐刻自检": [(r.get("时刻"), (r.get(F_DOM) or {}).get(F_SELFTEST))
                  for r in r0],
         "★ 每一刻都是 2": all(n == 2 for _, n in got),
         "★ 每一刻自检都真": all((r.get(F_DOM) or {}).get(F_SELFTEST) is True
                              for r in r0)})

    # ── S8 ★★ 静态锚点
    m_dis = re.search(r"data-director-camera-preset-trigger[\s\S]{0,240}?"
                      r"disabled=\{([^}]*)\}", src_tl)
    n1 = src_tl.count("data-director-camera-preset-error")
    n2 = src_tl.count("selectedPresetError")
    n3 = src_tl.count("cameraFollowActive")
    m_locked = re.search(r"if \(camera\.locked\) \{[\s\S]{0,700}?"
                         r"reason: \"(DIRECTOR_[A-Z_]+)\"", src_st)
    add("S8:★★ 静态锚点：按钮的 `disabled` 条件含 `cameraFollowActive`、"
        "同一个 `data-...-error` **有两处渲染**、分支序1 只写 `lastCommandResult`",
        "★ 静态证据**不能**替代 S2–S6 的行为证据（794 的硬规矩）；"
        "它的作用是把这些读数**归因**到具体那几行，"
        "而不是「屏幕上碰巧是这样」。"
        "★ ★ 注意 `data-director-camera-preset-error` 在 `DirectorTimeline.tsx` 里"
        "**出现两次**（`:1097` 状态驱动／`:1468` 操作驱动）—— "
        "★ **同一个选择器、两处渲染、两种驱动源**，"
        "这是本批全部读数的结构根源。",
        bool(m_dis) and "cameraFollowActive" in (m_dis.group(1) or "")
        and n1 == 2 and n2 >= 2 and n3 >= 3
        and bool(m_locked) and m_locked.group(1) == "DIRECTOR_TARGET_LOCKED",
        {"disabled 条件": m_dis.group(1) if m_dis else None,
         "data-...-error 出现次数": n1,
         "selectedPresetError 出现次数": n2,
         "cameraFollowActive 出现次数": n3,
         "★ 分支序1 的 reason": m_locked.group(1) if m_locked else None,
         "★ 命令反馈渲染点": "data-director-command-feedback" in src_ds})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_tl = (ROOT / TL).read_text(encoding="utf-8")
    src_ds = (ROOT / DS).read_text(encoding="utf-8")
    src_st = (ROOT / ST).read_text(encoding="utf-8")
    checks = run_checks(raw, src_tl, src_ds, src_st)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_tl, src_ds, src_st)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def reads(d):
        return ((d["cells"][0] or {}).get(F_READS)) or []

    def at(d, tag):
        return next((r for r in reads(d) if r.get("时刻") == tag), None)

    def first_good(d):
        return next((x for x in d["cells"] if not x.get("FAILED")), {})

    def state_driven_gone(d):
        """伪造「状态驱动的提示没出现」⟹ S2 翻红"""
        r = at(d, TAGS[2])
        r[F_PRESET_ERR] = []
        r[F_DOM][F_TRIG_DIS] = False
        return 1

    def prog_not_reachable(d):
        """★ 伪造「程序化调用没设 error」⟹ S3 翻红
        （只看返回值不够：`:7574` 的守卫也返回 false 而什么都不写）"""
        first_good(d)[F_OPS][F_PROG]["presetError"] = None
        return 1

    def button_enabled_while_follow(d):
        """★ 伪造「跟随目标时按钮没 disabled」⟹ S3 翻红"""
        at(d, TAGS[3])[F_DOM][F_TRIG_DIS] = False
        return 1

    def stale_hint_cleared(d):
        """★★ 伪造「陈旧提示被清掉了」⟹ S4 翻红
        （本批核心阴性对照：把最关键的读数直接否掉）"""
        at(d, TAGS[6])[F_PRESET_ERR] = []
        return 1

    def still_following(d):
        """伪造「那一刻其实还有跟随目标」⟹ S4 翻红
        （陈旧提示的**前提**是「已经没有跟随目标了」）"""
        at(d, TAGS[6])[F_ST]["跟随目标"] = "director-character-lead"
        return 1

    def no_command_feedback(d):
        """★ 伪造「锁定拒绝没有命令反馈」⟹ S5 翻红
        —— ★ 这正是**第一版探针读到的那个假结论**，做成对照"""
        at(d, TAGS[7])[F_CMD_FB] = []
        return 1

    def preset_hint_changed(d):
        """伪造「锁定拒绝顺带改了预设错误提示」⟹ S5 翻红"""
        r = at(d, TAGS[7])
        r[F_PRESET_ERR] = [{"通道": "预设错误提示",
                            "文本": "某个别的原因", "在预设面板内部": True}]
        return 1

    def success_keeps_hints(d):
        """伪造「成功之后提示还在」⟹ S6 翻红"""
        r = at(d, TAGS[8])
        r[F_PRESET_ERR] = [{"通道": "预设错误提示", "文本": "残留",
                            "在预设面板内部": True}]
        r[F_CMD_FB] = [{"通道": "命令反馈", "文本": "残留"}]
        return 1

    def selftest_broken(d):
        """★ 伪造「扫描器自检失败」⟹ S1 与 S7 必须翻红"""
        n = 0
        for r in reads(d):
            r[F_DOM][F_SELFTEST] = False
            n += 1
        return n

    def one_probe_only(d):
        """★ 伪造「只注入了一个探针」（第一版的形态）⟹ S7 翻红
        （证明「两个通道都要注入」这条不是多余的）"""
        n = 0
        for r in reads(d):
            r[F_DOM][F_PROBES] = 1   # ★ 必须用常量：键名**带 ★ 前缀**，
            #   ★ 第一版手写了不带 ★ 的键名 ⟹ 变异设了个不存在的键、
            #   ★ 阴性对照**打不中**自己的判据
            n += 1
        return n

    def drop_a_moment(d):
        """★ 伪造「少读了一个时刻」⟹ S1 必须翻红
        （时刻写死顺序而不是索引 ⟹ 少一个就判红，而不是读数错位）"""
        d["cells"][0][F_READS] = [r for r in reads(d) if r.get("时刻") != TAGS[4]]
        return 1

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「状态驱动的提示没出现」⟹ S2 翻红",
            state_driven_gone, "S2"),
        neg("N2", "★ 伪造「程序化调用没设 error」⟹ S3 翻红"
                  "（只看返回值不够）", prog_not_reachable, "S3"),
        neg("N3", "★ 伪造「跟随目标时按钮没 disabled」⟹ S3 翻红",
            button_enabled_while_follow, "S3"),
        neg("N4", "★★ 伪造「陈旧提示被清掉了」⟹ S4 翻红"
                  "（本批核心阴性对照：把最关键的读数直接否掉）",
            stale_hint_cleared, "S4"),
        neg("N5", "★ 伪造「那一刻其实还有跟随目标」⟹ S4 翻红"
                  "（陈旧提示的前提是「已经没有跟随目标了」）",
            still_following, "S4"),
        neg("N6", "★★ 伪造「锁定拒绝没有命令反馈」⟹ S5 翻红"
                  "（这正是第一版探针读到的假结论）", no_command_feedback, "S5"),
        neg("N7", "伪造「锁定拒绝顺带改了预设错误提示」⟹ S5 翻红",
            preset_hint_changed, "S5"),
        neg("N8", "伪造「成功之后提示还在」⟹ S6 翻红", success_keeps_hints, "S6"),
        neg("N9", "★ 伪造「扫描器自检失败」⟹ S1 与 S7 翻红", selftest_broken, "S7"),
        neg("N10", "★ 伪造「只注入了一个探针」⟹ S7 翻红"
                   "（证明「两个通道都要注入」不是多余的）",
            one_probe_only, "S7"),
        neg("N11", "★ 伪造「少读了一个时刻」⟹ S1 翻红（顺序写死而不是索引）",
            drop_a_moment, "S1"),
        neg("N12", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 821,
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"]
              + " ｜ 翻红：" + str([f[:4] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())