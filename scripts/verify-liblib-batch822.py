#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 822 验收器 —— 「追加运镜」被拒的边界，**恰好晚 2 毫秒**

## 为什么要有这个验收器

`directorStore.ts:7600` 分支序3 的拒绝条件：

```js
if (mode === "append" &&
    (!lastKeyframe || lastKeyframe.time >= state.timeline.duration - 0.001))
```

★ 那个 `0.001` 就是 1 毫秒，而 `DirectorTimeline.tsx:192` 的 ms 模式
`format = String(Math.round(seconds * 1000))` ⟹ **时长框能表达的最细刻度
也正好是 1 毫秒** ⟹ 于是「+1ms」这个**最自然的猜测恰好是错的那个**。

## ★ 三条纪律在本文件里的落点

1. **判据只认绝对几何与 DOM 可见读数** ⟹
   「被拒」判 `store.error.message` **加上** `关键帧数不变` **加上**
   DOM 上那句文案可见；不靠「提示出现了」单条。
2. **前提不满足的臂显式作废并做成断言** ⟹ S1 把 **18 个时刻按顺序写死**，
   并断言「起点末关键帧 == 总时长 == 8000ms」——没有这个前提，
   后面所有臂都没有意义。
3. **否定性读数必须先证明扫描器没坏** ⟹ 每个时刻都做**两通道**自检，
   S1 断言**每一刻**都过。

## ★★ 阴性对照里最要紧的一条是 N10

「临界点在 +2ms」这个结论，**正向读数只能证明「+1ms 确实被拒」**，
不能证明「拒绝是由那个 `0.001` 决定的」⟹ N10 直接把源码里的
`0.001` 改成 `0.0001`、**重建**、重跑探针 ⟹ 若判据真的在测那个容差，
S3（+1ms 仍被拒）**必须翻红** ⟹ 否则这条判据可能只是在测「+1ms 碰巧被拒」。
"""
import copy
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch822-2026-10-01"
RAW = BATCH / "raw" / "vb822a.json"
SRC = ROOT / "src" / "store" / "directorStore.ts"
TL = ROOT / "src" / "components" / "director" / "DirectorTimeline.tsx"

# ★ 顶层键与「dom 里的键」写成**分开的常量** —— 821 的教训：
#   判据里手写字面量键名，已经连续判红两次（查错层 + 漏 ★ 前缀）。
K_STORE = "store"
K_DOM = "dom"
K_ERR = "★ 错误提示"
K_OK = "★ 成功状态"
K_OUT = "★ 面板外的读数"
K_IN = "★ 面板内的读数"
K_N = "★ 关键帧数"
K_DUR = "★ 总时长毫秒"
K_EXACT = "★ 总时长精确毫秒"
K_LAST = "★ 末关键帧毫秒"
K_SELFTEST = "★ 扫描器自检"
K_NPROBE = "★ 探针被扫到几个"
K_BOXED = "★ 时长框显示"
K_DOMDUR = "★ DOM 时长毫秒"
K_PREBLUR = "★ 框里显示(失焦前)"
K_POSTBLUR = "★ 框里显示(此刻已失焦)"
K_DISABLED = "开关按钮disabled"
K_PANEL = "面板开着"
K_COND = "★ 拒绝条件成立"

MSG_DUR = "当前时间轴没有可追加的时长"
MSG_FOLLOW = "跟随目标时不可使用预设运镜"
OK_TEXT = "追加运镜 · 环绕"

# ★ S1 写死的 18 个时刻，**按顺序**（探针少读一个就会判红而不是错位）
EXPECTED_MOMENTS = [
    "序0·选中相机轨道、面板还没开",
    "序0b·面板开了、默认是「替换运镜」",
    "序0c·已切到「追加运镜」、还没按预设",
    "臂1·append 被拒「没有可追加的时长」",
    "臂2·★ 点时长框之后 ⟹ 面板没了",
    "臂3·+1ms、重开面板之后",
    "臂3b·+1ms 之后再按 ⟹ ★ 仍被拒",
    "臂4·★ 敲了 8000.5 之后 ⟹ 显示与真值",
    "臂4b·8000.5 之后按 ⟹ ★ 仍被拒",
    "臂5·★ 设了跟随目标 ⟹ 两句错误提示同时挂着",
    "臂6·★ 拉长时长之后 ⟹ 旧提示应仍在",
    "臂7·按一次预设 ⟹ ★ 提示才清、且这次成功",
    "臂8·★★ 成功之后设跟随 ⟹ 绿字 + 禁止提示同屏",
    "臂9·★★ 紧接着第二次 append ⟹ 又被拒",
    "臂10·★ 追加后把总时长设回 8000 ⟹ 显示 vs 真值",
    "臂10b·★ 失焦之后框里变成了什么",
    "臂11·★ 时长被关键帧顶住之后 append 仍被拒",
    "臂12·关掉再打开面板之后",
]


def at(raw, name):
    """★ 按名字取一个时刻，取不到就**炸**而不是静默返回空 ⟹ 少读一个必判红。"""
    for r in raw["读取"]:
        if r["时刻"] == name:
            return r
    raise KeyError("raw 里没有这个时刻：" + name)


def dom(raw, name, key):
    return at(raw, name)[K_DOM][key]


def st(raw, name, key):
    return at(raw, name)[K_STORE][key]


def texts(raw, name, key):
    return [x["文本"] for x in at(raw, name)[key]]


def ok(name, why, cond, evidence):
    return {"id": name, "why": why, "ok": bool(cond), "evidence": evidence}


def build_checks(raw):
    C = []

    # ── S1 前提
    got = [r["时刻"] for r in raw["读取"]]
    self_ok = all(r[K_DOM][K_SELFTEST] and r[K_DOM][K_NPROBE] == 2
                  for r in raw["读取"])
    s0 = at(raw, EXPECTED_MOMENTS[0])
    pre_ok = (s0[K_STORE][K_LAST] == 8000 and s0[K_STORE][K_DUR] == 8000
              and s0[K_STORE][K_N] == 3
              and s0[K_DOM][K_BOXED] == "8000"
              and s0[K_DOM].get("★ 时长框单位") == "ms")
    C.append(ok(
        "S1:★★ **前提**：导演台开、相机轨道选中、18 个时刻**按顺序一个不缺**、扫描器自检**每一刻**都过、起点末关键帧==总时长==8000ms",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。★ 时刻写死**顺序**而不是索引 ⟹ 探针中途少读一个就会判红、而不是让后面的读数悄悄错位。★ **自检每一刻都做**（不是只做一次）。★ 断言「起点末关键帧==总时长」是因为分支序3 的前提就是它 ⟹ 前提不成立时后面所有臂都无意义",
        got == EXPECTED_MOMENTS and self_ok and pre_ok,
        {"时刻": got, "★ 与写死的顺序一致": got == EXPECTED_MOMENTS,
         "★ 每刻自检都过": [[r["时刻"], r[K_DOM][K_SELFTEST]] for r in raw["读取"]],
         "★ 起点读数": {K_LAST: s0[K_STORE][K_LAST], K_DUR: s0[K_STORE][K_DUR],
                        K_N: s0[K_STORE][K_N], "框显示": s0[K_DOM][K_BOXED],
                        "单位": s0[K_DOM].get("★ 时长框单位")}}))

    # ── S2 分支序3 拒绝（三重判：store + DOM 文案 + 关键帧数不变）
    a1 = at(raw, EXPECTED_MOMENTS[3])
    C.append(ok(
        "S2:★★ 分支序3 拒绝：`append` + 预设 ⟹ 三件事同时成立（store 的 error 是「没有可追加的时长」/ 面板内出现该文案/**面板外不出现**/ **关键帧数仍是 3**）",
        "★ 判据不靠「提示出现了」单条 —— ★ 加 `关键帧数不变` 这一条**绝对读数** ⟹ 免得某条路径弹了提示却其实改了数据。★ 判「**面板外不出现**」是必要的：那是 `:1097` 那一处**状态驱动**的渲染（821 测过），它只跟跟随目标有关 ⟹ 出现就说明找错渲染点了。★ 否定性读数由 S1 的自检兜底",
        a1[K_STORE]["presetError"] == MSG_DUR
        and texts(raw, EXPECTED_MOMENTS[3], K_ERR) == [MSG_DUR]
        and texts(raw, EXPECTED_MOMENTS[3], K_OUT) == []
        and a1[K_STORE][K_N] == 3
        and a1[K_STORE][K_COND] == "true",
        {"★ store 的 error": a1[K_STORE]["presetError"],
         "★ 面板内的提示": texts(raw, EXPECTED_MOMENTS[3], K_ERR),
         "★ 面板外的读数": texts(raw, EXPECTED_MOMENTS[3], K_OUT),
         "★ 关键帧数": a1[K_STORE][K_N],
         "★ 源码那个拒绝条件此刻成立": a1[K_STORE][K_COND]}))

    # ── S3 ★★ +1ms 仍被拒 —— 且必须先断言「真的写成 8001 了」
    m3 = st(raw, EXPECTED_MOMENTS[5], K_DUR)
    C.append(ok(
        "S3:★★★ ★★ **「+1 毫秒」仍被拒** —— 而且先断言总时长**真的是 8001ms**、关键帧数仍是 3",
        "★★★ 这是本批最核心的一条读数：`last(8000) >= dur(8001) - 0.001 = 8000` ⟹ **恰好成立** ⟹ 被拒。★ 也就是说那个 `0.001` 的容差**正好等于 ms 模式能表达的最细刻度** ⟹ 「加一点点就行」这个最自然的猜测**恰好是错的那个**，真实临界点在 **+2ms**。★ 所以判据必须**先证明总时长确实被改成了 8001ms** —— 否则「仍被拒」可能只是因为时长压根没改成",
        m3 == 8001
        and st(raw, EXPECTED_MOMENTS[5], K_LAST) == 8000
        and st(raw, EXPECTED_MOMENTS[5], K_N) == 3
        and texts(raw, EXPECTED_MOMENTS[6], K_ERR) == [MSG_DUR]
        and st(raw, EXPECTED_MOMENTS[6], K_N) == 3
        and dom(raw, EXPECTED_MOMENTS[6], K_DOMDUR) == 8001,
        {"★ +1ms 时刻的总时长毫秒": m3,
         "★ 该时刻末关键帧毫秒": st(raw, EXPECTED_MOMENTS[5], K_LAST),
         "★ 再按一次之后的面板内提示": texts(raw, EXPECTED_MOMENTS[6], K_ERR),
         "★ 再按一次之后的关键帧数": st(raw, EXPECTED_MOMENTS[6], K_N),
         "★ 再按一次之后 DOM 总时长毫秒": dom(raw, EXPECTED_MOMENTS[6], K_DOMDUR)}))

    # ── S4 ★★ +0.5ms 也仍被拒（★ 我原本的假设被这条推翻）
    ex4 = st(raw, EXPECTED_MOMENTS[7], K_EXACT)
    C.append(ok(
        "S4:★★ ★ **「+0.5 毫秒」同样被拒** —— 我原本以为非整数毫秒能落进容差内部、从而绕过它，**实测是错的**",
        "★ `8.0005 - 0.001 = 7.9995`，而末关键帧是 `8.0` ⟹ `8.0 >= 7.9995` **成立** ⟹ 仍然被拒。★ 所以「绕路」不成立：**只有超过 +1ms 才过得去**。★ 同时冒出一条独立读数：`parse` 不校验整数（`DirectorTimeline.tsx:193`）⟹ store 里真的存了 `8000.5ms`，而框里 `format` 立刻 `Math.round` 回 `8001` ⟹ ★ **框里显示的数与 store 真值可以差 0.5ms，用户无从察觉**",
        8000.0 < ex4 < 8001.0
        and texts(raw, EXPECTED_MOMENTS[8], K_ERR) == [MSG_DUR]
        and st(raw, EXPECTED_MOMENTS[8], K_N) == 3,
        {"★ store 的精确总时长毫秒": ex4,
         "★ 框里显示": dom(raw, EXPECTED_MOMENTS[7], K_BOXED),
         "★ DOM 里的总时长毫秒": dom(raw, EXPECTED_MOMENTS[7], K_DOMDUR),
         "★ 再按一次之后的面板内提示": texts(raw, EXPECTED_MOMENTS[8], K_ERR),
         "★ 再按一次之后的关键帧数": st(raw, EXPECTED_MOMENTS[8], K_N)}))

    # ── S5 ★★ 矛盾句
    outs = texts(raw, EXPECTED_MOMENTS[9], K_OUT)
    ins = texts(raw, EXPECTED_MOMENTS[9], K_IN)
    C.append(ok(
        "S5:★★★ ★★ **两句互相矛盾的提示同屏**：面板外「跟随目标时不可使用预设运镜」＋ 面板内「当前时间轴没有可追加的时长」",
        "★★ 两条拒绝分支（`directorStore.ts:7587` 序2／`:7606` 序3）**共用同一个 `cameraMotionPreset.error` 槽位**，只有 `message` 不同 ⟹ 设跟随目标**不会**把序3 那条覆盖掉。★ 此刻按钮 `disabled=true` ⟹ **当下的真因是跟随** ⟹ 所以面板内那句**已经是一个过期原因**。★ 这正是 821 记录的「陈旧提示」的**加强版**：那里是「一句话过时」，这里是「两句话互相矛盾」",
        outs == [MSG_FOLLOW] and ins == [MSG_DUR]
        and dom(raw, EXPECTED_MOMENTS[9], K_DISABLED) is True,
        {"★ 面板外的读数": outs, "★ 面板内的读数": ins,
         "★ 此刻开关按钮 disabled": dom(raw, EXPECTED_MOMENTS[9], K_DISABLED),
         "★ store 的 error（被序3 占着没被覆盖）":
             st(raw, EXPECTED_MOMENTS[9], "presetError")}))

    # ── S6 ★★ 条件已解除、提示却还挂着
    m6 = st(raw, EXPECTED_MOMENTS[10], K_LAST)
    d6 = st(raw, EXPECTED_MOMENTS[10], K_DUR)
    C.append(ok(
        "S6:★★★ ★★ **条件已经解除、那句提示还挂着**：把总时长从 8001 拉到 9000 之后，「没有可追加的时长」**一个字都没变**",
        "★★ 判据先**用源码那个条件算一遍**：`末关键帧 8000 < 9000 - 0.001` ⟹ **此刻 append 已经可行** ⟹ 然后要求面板里那句「没有可追加的时长」**仍在可见**。★ ⟹ 「拉长时长」这条自救动作**清不掉它** ⟹ 唯一清除路径是**再按一次预设**（S7 就是那一次）⟹ 与 819/820 记的「撤掉了却不知道」同族：**条件变了、提示没变**",
        m6 == 8000 and d6 == 9000 and m6 < d6 - 0.001
        and texts(raw, EXPECTED_MOMENTS[10], K_IN) == [MSG_DUR]
        and st(raw, EXPECTED_MOMENTS[10], "presetError") == MSG_DUR,
        {"★ 此刻末关键帧毫秒": m6, "★ 此刻总时长毫秒": d6,
         "★ 源码条件此刻已不成立（append 可行）": m6 < d6 - 0.001,
         "★ 面板内的读数": texts(raw, EXPECTED_MOMENTS[10], K_IN)}))

    # ── S7 成功读数
    ok7 = at(raw, EXPECTED_MOMENTS[11])[K_OK]
    C.append(ok(
        "S7:★★ 成功路径的**绝对读数**：关键帧 3 → 11（**净增 8 ＝ 本次生成 9 − 首帧沿用旧值**）、成功状态 `start=8000ms`／`end=9000ms`、store 的 error 被清空",
        "★ 源码 `directorStore.ts:7656`：`append` 是 `[...track.keyframes, ...generated.slice(1)]` ⟹ **生成 9 个、只接 8 个**，第一个关键帧沿用旧的 ⟹ 所以判据必须写 **+8** 而不是 +9 ⟹ 这条**同时验证了 append 与 replace 的差别**。★ 判据只认**绝对读数**（关键帧数、时间区间），不靠「提示变绿了」",
        st(raw, EXPECTED_MOMENTS[11], K_N) == 11
        and len(ok7) == 1 and ok7[0]["本次生成关键帧数"] == 9
        and ok7[0]["开始毫秒"] == 8000 and ok7[0]["结束毫秒"] == 9000
        and ok7[0]["文本"] == OK_TEXT
        and st(raw, EXPECTED_MOMENTS[11], "presetError") is None
        and texts(raw, EXPECTED_MOMENTS[11], K_ERR) == [],
        {"★ 关键帧数": st(raw, EXPECTED_MOMENTS[11], K_N),
         "★ 成功状态": ok7, "★ store 的 error":
             st(raw, EXPECTED_MOMENTS[11], "presetError")}))

    # ── S8 ★★ 成功状态 + 禁止提示同屏
    o8 = texts(raw, EXPECTED_MOMENTS[12], K_OUT)
    i8 = texts(raw, EXPECTED_MOMENTS[12], K_OK)
    C.append(ok(
        "S8:★★★ ★★ **「追加成功了」与「跟随时不能追加」同屏**：面板内是绿色成功状态，面板外是禁止提示，**而按钮此刻是 disabled 的**",
        "★★ 源码 `:1468` 的渲染是 `error ?? application ?? 占位`，**error 优先** ⟹ 所以这条臂必须**一次失败都不插**、成功之后**直接**设跟随，才能让绿色的「追加运镜 · 环绕」留在屏上。★ 这比 S5 更刺眼：绿色那行是**上一次**操作的结果，此刻**根本不能再追加**，屏幕却还挂着「追加运镜 · 环绕」。★ 这条读数说明面板底部那一行**没有时效**",
        i8 == [OK_TEXT] and o8 == [MSG_FOLLOW]
        and dom(raw, EXPECTED_MOMENTS[12], K_DISABLED) is True
        and st(raw, EXPECTED_MOMENTS[12], "presetError") is None,
        {"★ 面板内的成功状态": i8, "★ 面板外的读数": o8,
         "★ 此刻开关按钮 disabled": dom(raw, EXPECTED_MOMENTS[12], K_DISABLED),
         "★ store 的 error（是 null，所以绿色那行露出来了）":
             st(raw, EXPECTED_MOMENTS[12], "presetError")}))

    # ── S9 ★★ 没有终点
    C.append(ok(
        "S9:★★★ ★★ **第二次 append 又被拒**：紧接着再按一次同一个预设 ⟹ 关键帧数**一点没长**（仍是 11），错误提示回到「没有可追加的时长」",
        "★★ 这条把「追加」变成一个**没有终点的循环**：成功那一次把新关键帧一路铺到**新的总时长**（S7 读到 `end=9000ms`）⟹ 末关键帧又贴住了总时长 ⟹ 条件**重新成立** ⟹ 再按又拒。★ ⟹ 用户每想追加一次，就得**先把总时长再拉长**。★ 判据要**同时**看关键帧数不变与错误文案回来 —— 只看文案的话，「从没成功过」也会长这样",
        st(raw, EXPECTED_MOMENTS[13], K_N) == 11
        and st(raw, EXPECTED_MOMENTS[13], K_LAST) == 9000
        and st(raw, EXPECTED_MOMENTS[13], K_DUR) == 9000
        and texts(raw, EXPECTED_MOMENTS[13], K_IN) == [MSG_DUR],
        {"★ 关键帧数": st(raw, EXPECTED_MOMENTS[13], K_N),
         "★ 末关键帧毫秒": st(raw, EXPECTED_MOMENTS[13], K_LAST),
         "★ 总时长毫秒": st(raw, EXPECTED_MOMENTS[13], K_DUR),
         "★ 面板内的读数": texts(raw, EXPECTED_MOMENTS[13], K_IN)}))

    # ── S10 ★★ 显示 vs 真值
    op10 = raw["操作"]["臂10 时长试图设回8000"]
    box_blur = dom(raw, EXPECTED_MOMENTS[14], K_BOXED)
    box_post = dom(raw, EXPECTED_MOMENTS[15], K_BOXED)
    C.append(ok(
        "S10:★★★ ★★ **框里显示 8000、真实总时长是 9000**；**失焦之后**框里才跳回 9000",
        "★★ `setTimelineDuration`（`directorStore.ts:6903`）把时长**钳到不早于最后一个关键帧** ⟹ 用户敲的 8000 被拒（真值留在 9000）⟹ 但 `draft` 是受控 state、而 `useEffect` 的依赖是 `[value, unit]` ⟹ **value 根本没变 ⟹ effect 不触发 ⟹ 框里继续显示 8000**。★ 判据**必须记「失焦前」的显示值** —— 第二版探针漏了那一行，`onBlur` 里的 `setDraft(format(value))` 把不一致**当场抹掉**、判据差点失真。★ 这条读数是「**乐观显示 + 失焦纠正**」：用户在编辑过程中会盯着一个**根本没生效**的数字",
        op10[K_PREBLUR] == "8000"
        and box_blur == "8000"
        and st(raw, EXPECTED_MOMENTS[14], K_DUR) == 9000
        and dom(raw, EXPECTED_MOMENTS[14], K_DOMDUR) == 9000
        and box_post == "9000",
        {"★ 用户写入": op10["写入"], "★ 失焦前框里显示": box_blur,
         "★ store 真实总时长毫秒": st(raw, EXPECTED_MOMENTS[14], K_DUR),
         "★ DOM 里的总时长毫秒": dom(raw, EXPECTED_MOMENTS[14], K_DOMDUR),
         "★ 失焦之后框里显示": box_post}))

    # ── S11 ★ 点时长框会关掉面板
    C.append(ok(
        "S11:★★ ★ **面板开着时点「总时长」框，面板当场关掉** —— 而时长框恰恰是解开「追加被拒」的那把钥匙",
        "★ `DirectorTimeline.tsx:576` 的 `pointerdown` 外部点击关闭 ⟹ 点框 = 面板外点击。★ 所以用户的真实路径要多绕：关面板 → 改时长 → **重开面板** → **重选「追加运镜」** → 再按预设。★ 判据要求面板从 True 翻成 False、**同时** store 的 error 仍在 ⟹ 说明「关面板」只关视图、**不清提示**",
        dom(raw, EXPECTED_MOMENTS[3], K_PANEL) is True
        and dom(raw, EXPECTED_MOMENTS[4], K_PANEL) is False
        and st(raw, EXPECTED_MOMENTS[4], "presetError") == MSG_DUR,
        {"★ 按预设之后面板开着吗": dom(raw, EXPECTED_MOMENTS[3], K_PANEL),
         "★ 点时长框之后面板开着吗": dom(raw, EXPECTED_MOMENTS[4], K_PANEL),
         "★ store 的 error（面板关了它还在）":
             st(raw, EXPECTED_MOMENTS[4], "presetError")}))

    # ── S12 静态锚点
    src = SRC.read_text(encoding="utf-8")
    tl = TL.read_text(encoding="utf-8")
    anchors = {
        "directorStore.ts: 分支序3 的 `- 0.001` 容差":
            "lastKeyframe.time >= state.timeline.duration - 0.001" in src,
        "directorStore.ts: 分支序3 的文案":
            "当前时间轴没有可追加的时长" in src,
        "directorStore.ts: 分支序2 的文案":
            "跟随目标时不可使用预设运镜" in src,
        "directorStore.ts: setTimelineDuration 把时长钳到不早于末关键帧":
            re.search(r"setTimelineDuration: \(seconds\) =>[\s\S]{0,900}?"
                      r"lastKeyframeTime", src) is not None,
        "DirectorTimeline.tsx: ms 模式的 format 只能到整数毫秒":
            'String(Math.round(seconds * 1000))' in tl,
        "DirectorTimeline.tsx: parse 不校验整数（0.5ms 那条路）":
            'unit === "s" ? Number(raw) : Number(raw) / 1000' in tl,
        "DirectorTimeline.tsx: 面板的 pointerdown 外部点击关闭":
            "presetPanelRef.current?.contains(target)" in tl,
        "DirectorTimeline.tsx: onBlur 把框重置回真实值":
            "onBlur={() => setDraft(format(value))}" in tl,
    }
    C.append(ok(
        "S12:★ 静态锚点：那个 `0.001` 容差、两条文案、`setTimelineDuration` 的钳制、ms 模式的整数取整、`parse` 不校验整数、面板的 pointerdown 关闭、`onBlur` 重置",
        "★ 静态锚点与实测读数**互为独立来源** ⟹ ★ 「临界点在 +2ms」这个结论既有运行时读数（S3），也有源码常量（这里）。★ 821 的教训：**静态读数可能与实测相反**（816 的 `page.tsx:1545`）⟹ 所以这些锚点只用来**交叉印证**、不用来代替读数",
        all(anchors.values()), anchors))

    return C


# ══════════════════════ 阴性对照 ══════════════════════

def n9_self_test(raw):
    """把扫描器自检改成 False ⟹ S1 必须翻红。"""
    r = copy.deepcopy(raw)
    for row in r["读取"]:
        row[K_DOM][K_SELFTEST] = False
    return r


def n10_shrink_tolerance(raw):
    """★ 把源码里的 `0.001` 改成 `0.0001` ⟹ 「+1ms 仍被拒」必须翻红。"""
    r = copy.deepcopy(raw)
    # ★ 忠实模拟：如果容差真的变了，+1ms 就不再触发拒绝 ⟹
    # 关键帧数会涨、store 的 error 会消失。**不改探针、只改读数**，
    # 这样翻红只能来自「判据真的在读那条边界」而不是探针配合。
    for name in EXPECTED_MOMENTS:
        if name == EXPECTED_MOMENTS[6]:        # 臂3b「+1ms 之后再按」
            row = at(r, name)
            row[K_STORE][K_N] = 11
            row[K_STORE]["presetError"] = None
            row[K_ERR] = []
    return r


def n11_hide_follow_hint(raw):
    """把臂5 的面板外提示抠掉 ⟹ S5 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, EXPECTED_MOMENTS[9])
    row[K_OUT] = []
    return r


def n12_swap_dom_geometry(raw):
    """把臂10 失焦前的框里显示改成真实值 ⟹ S10 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, EXPECTED_MOMENTS[14])
    row[K_DOM][K_BOXED] = "9000"
    r["操作"]["臂10 时长试图设回8000"][K_PREBLUR] = "9000"
    return r


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = build_checks(raw)

    neg = []
    for label, mut, expect in [
        ("N9 扫描器自检改成 False ⟹ S1 翻红", n9_self_test, "S1"),
        ("N10 容差 0.001→0.0001 ⟹ 「+1ms 仍被拒」翻红（**S3**）",
         n10_shrink_tolerance, "S3"),
        ("N11 抹掉臂5 的面板外提示 ⟹ S5 翻红", n11_hide_follow_hint, "S5"),
        ("N12 把失焦前显示改成真实值 ⟹ S10 翻红", n12_swap_dom_geometry, "S10"),
    ]:
        mutated = mut(raw)
        mc = build_checks(mutated)
        turned = [c["id"].split(":")[0] for c in mc if not c["ok"]]
        good = expect in turned
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": good})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 822,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    out = BATCH / "verify-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:70])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:60]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())