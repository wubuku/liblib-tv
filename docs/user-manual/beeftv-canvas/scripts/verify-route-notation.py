#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十三道闸：登记的**前端路由**，它的占位符写法必须在上游路由表里真的存在。

**为什么要有这道闸（Batch 236 的由来）**：`screenshots/manifest.yml` 的 `route` 字段
与 `task-inventory.yml` 的 `routes` 列表里登记了 102 处前端路由，**而没有任何闸读过它们**。
手工一数就发现**同一个路由在登记处有两种写法**：
  · `/canvas/:id` —— 5 处（manifest），**这也是上游 `web/src/router.tsx` 的写法**
    （24 条声明里 `:param` 用了 8 次，**`{` 一次都没有**），`20-reference.md:94` 的
    路由表也这么写；
  · `/canvas/{id}` —— **4 处**（manifest）+ **2 处**（账本 `routes`），
    **`{param}` 是 OpenAPI 风格，React Router 不认**；
  · `/canvas/tPiyJSrJhwfoLvdDf_6qW` —— **3 处写死了某次走查的真实画布 ID**，
    同一份 manifest 另有 5 处写的是 `/canvas/:id`。
**后果不是不好看**：这 6 处 `{id}` **照抄进地址栏必然匹配不上上游路由**
（可证——上游 24 条声明里没有一条含 `{`），而它们恰好是**只读模式**那几张图的取证记录，
**只读模式是本手册反复强调「入口在哪」的一节**。写死的那个 ID 更进一步：
它既不能复用，又把某次走查的账号内画布 ID 固化进了仓库。

**本闸判三件事**：
  ① **花括号占位**：登记路由里出现 `{...}` → 报。**这不是风格偏好**，
     上游路由表里 `{` 零出现，所以这样的登记**可证匹配不上**；
  ② **占位位置填了具体段**：上游该位置是 `:param`、登记里却写了一个具体 id → 报
     （**同一个路由在同一份登记里已有占位写法**，两套写法并存本身就是缺陷）；
  ③ **完全匹配不上上游任何一条声明** → 报。**这一条是前两条有意义的前提**——
     如果匹配器什么都匹配不上，那前两条就只是在校验一个自造的格式。

**输入范围要说明白（纪律 191）**：本闸读的是**两个数据文件**
（`screenshots/manifest.yml` 的 `route`、`task-inventory.yml` 的 `routes`），
**不是发布页**——因为它要核的是「登记这件事本身的一致性」，
而**账本虽然被 `srcExclude` 排除、读者看不到，它同样是一份登记**（实测 `{id}` 两处就在那里）。
**它不核发布页正文里提到的路由**（那一族由闸 27 核查询参数、闸 26 核链接文字）。

**事实源只有一个**：上游 `web/src/router.tsx` 在**取证基线**上的 `path:` 声明。
**合法集从它算出来，不建人工登记表**（纪律 242）——上游改了写法，本闸跟着变。

**自检（方向四）**：拿两对人造样本喂给匹配器，**必须一正一反都对**——
`/canvas/:id` 要能匹配上 `/canvas/:id`，而 `/canvas/{id}` 必须匹配不上任何一条
（否则匹配器退化了而本闸恒绿，纪律 101）。

退出码：0 三条都过；1 有登记路由写法与上游对不上；2 未能核对（读不到路由表 / 读不到数据文件 / 自检不中）。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from baseline import declared_baseline, BaselineError  # noqa: E402
from baseline import module_ref  # noqa: E402
from baseline import SRC as _BEEFSRC  # noqa: E402
from baseline import announce_fallback  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = _BEEFSRC
REF = module_ref()
ROUTER = "web/src/router.tsx"
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")
INVENTORY = os.path.join(ROOT, "task-inventory.yml")


def _git_show(path):
    r = subprocess.run(["git", "-C", SRC, "show", f"{REF}:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def upstream_paths():
    text = _git_show(ROUTER)
    if text is None:
        return None
    return re.findall(r'path:\s*"([^"]+)"', text)


def _segs(path):
    return [s for s in path.split("/") if s]


def match_slots(recorded, pattern):
    """登记路径能否匹配上游模式；能则返回「哪些段位是 `:param` 占位」的下标列表。

    **`:param` 与 `*` 必须分开算**（Batch 236 反验钉出来的判据自身缺陷）：
    `*` 的语义是「这一段随便什么都行」，所以**在 `*` 的位置上填一个具体子路径是合法的**
    （上游 `/project/:projectId/*` 就是给子路径用的）；
    而 `:param` 的语义是「这一段是个 id」，**填具体值就是本闸要报的形态**。
    第一版把两者混在一个 `wild` 列表里，**于是 `/project/:projectId/*` 这样的合法登记
    被报成「第 3 段在上游是占位却填了具体值」**——而 `*` 根本不是占位。
    """
    a, b = _segs(recorded), _segs(pattern)
    if len(a) != len(b):
        return None
    params = []
    for i, (x, y) in enumerate(zip(a, b)):
        if y == "*":
            continue
        if y.startswith(":"):
            # **占位不许写成花括号形式**——这正是本闸要抓的形态，所以匹配器也不能接受它
            if not x or x.startswith("{"):
                return None
            params.append(i)
        elif x != y:
            return None
    return params


def collected_routes():
    """两个数据文件里登记的全部路由，带出处。"""
    out = []
    if os.path.isfile(MANIFEST):
        text = open(MANIFEST, encoding="utf-8").read()
        cur = None
        for line in text.split("\n"):
            m = re.match(r"\s*- file:\s*(\S+)", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"\s+route:\s*'([^']+)'", line)
            if m:
                out.append((os.path.join("screenshots", "manifest.yml"), cur, m.group(1)))
    if os.path.isfile(INVENTORY):
        text = open(INVENTORY, encoding="utf-8").read()
        for blk in re.finditer(r"^\s+routes:\n((?:\s+- '[^']+'\n)+)", text, re.M):
            for r in re.findall(r"- '([^']+)'", blk.group(1)):
                out.append(("task-inventory.yml", None, r))
    return out


def main():
    announce_fallback()
    if SRC is None:
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，路由写法核对本轮未能进行")
        return 2
    try:
        base_ver, _c = declared_baseline()
    except BaselineError as exc:
        print(f"[skip] {exc}，路由写法核对本轮未能进行")
        return 2

    paths = upstream_paths()
    if not paths:
        print(f"[skip] 在 {REF}:{ROUTER} 里抽不到 path 声明，路由写法核对本轮未能进行")
        return 2

    # ---- 方向四：自检。一正一反，缺一不可
    if match_slots("/canvas/:id", "/canvas/:id") is None:
        print("[skip] 自检失败：占位形式匹配不上自己的模式——**匹配器已失效**")
        return 2
    if match_slots("/canvas/{id}", "/canvas/:id") is not None:
        print("[skip] 自检失败：花括号形式竟然匹配上了 `:id` 模式——**匹配器比声称的宽**")
        return 2
    if any("{" in p for p in paths):
        print(f"[skip] 上游 {ROUTER} 里出现了含 `{{` 的 path 声明——"
              f"**本闸的前提（上游零处使用花括号占位）已经不成立**，"
              f"须重新确认合法写法后再改判据")
        return 2

    records = collected_routes()
    if not records:
        print("[skip] 两个数据文件里一处路由都没读到，判据读空 —— 不是「没有不一致」")
        return 2

    #: 同一登记里**已经用过占位写法**的模式——用它来证明「两套写法并存」而不是「风格」
    placeholder_forms = set()
    for _src, _where, route in records:
        p = route.split("?")[0]
        if re.search(r"/:[A-Za-z_]\w*", p):
            placeholder_forms.add(p)

    bad, by_kind = [], {"brace": 0, "concrete": 0, "nomatch": 0}
    for src, where, route in records:
        p = route.split("?")[0]
        loc = f"{src}" + (f"（{where}）" if where else "")
        if "{" in p or "}" in p:
            by_kind["brace"] += 1
            bad.append(f"{loc}：{route} —— **上游 {REF} 的 {ROUTER} 里 24 条 path 声明"
                       f"零处使用 `{{param}}`**，所以这一条**可证匹配不上路由表**；"
                       f"上游与本手册参考页用的都是 `:param`")
            continue
        hits = [(u, w) for u, w in ((u, match_slots(p, u)) for u in paths) if w is not None]
        if not hits:
            by_kind["nomatch"] += 1
            bad.append(f"{loc}：{route} 的路径在上游路由表里**匹配不上任何一条声明**")
            continue
        pattern, params = hits[0]
        concrete = [i for i in params if not _segs(p)[i].startswith(":")]
        if concrete:
            by_kind["concrete"] += 1
            other = "；同一份登记里另写成占位形式的是 " + "、".join(sorted(placeholder_forms)) \
                if placeholder_forms else ""
            bad.append(f"{loc}：{route} 的第 {concrete[0] + 1} 段在上游 `{pattern}` 里是占位，"
                       f"这里却填了具体值 —— 同一个路由两套写法并存{other}")

    if bad:
        print(f"路由写法核对：{len(bad)}/{len(records)} 处登记与上游路由表对不上"
              f"（花括号 {by_kind['brace']} / 占位位填具体值 {by_kind['concrete']} / "
              f"匹配不上 {by_kind['nomatch']}）")
        for b in bad:
            print("  " + b)
        print(f"→ 改这两个数据文件（{os.path.relpath(MANIFEST, ROOT)} 与 "
              f"{os.path.relpath(INVENTORY, ROOT)}）的路由写法，"
              f"**占位一律用上游那种 `:param`**；"
              # **花括号在 f-string 里必须写双层**——第一版写成 `{param}`，
              # 而那正是本闸要抓的形态，**判据自己的输出把它当成了占位符**（NameError 崩在收尾那行）。
              # **一个判据的输出里出现它自己要判的形态，就得先把输出写对**。
              f"**理由不是「统一风格」，是 `{{param}}` 在 React Router 里根本匹配不上**")
        return 1
    print(f"路由写法核对通过：{len(records)} 处登记的前端路由，"
          f"占位风格与 {REF} 的 {ROUTER}（{len(paths)} 条声明）一致，"
          f"且都能匹配上某一条已声明路由")
    return 0


if __name__ == "__main__":
    sys.exit(main())
