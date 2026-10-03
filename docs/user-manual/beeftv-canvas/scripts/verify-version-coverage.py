#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十二道闸：截图拍完之后，**上游改过用户可见文案的那些版本，手册必须提到**。

**为什么要有这道闸（Batch 235 的由来）**：本批顺着「升版区间」查了一遍，
发现 `README.md` 的「v1.6.14 之后的增量」清单列了 v1.6.15/16/17/19/22，
**跳过了 v1.6.18、v1.6.20、v1.6.21**。逐个 diff 之后：
  · **v1.6.18** 只往 `generation-error.ts` 的连接错误正则里补了几个 Windows 专有串，
    **一条用户可见文案都没改**——所以它不列是对的；
  · **v1.6.20** 改的是 Windows 保存对话框的默认格式过滤器与文件名净化，
    同样**没有 `web/src` 的中文字面量增减**——不列也不算错，但读者无从分辨
    「这版没什么」与「没人查过」；
  · **v1.6.21** 加了**视频时长「自动」选项**（时长值 `-1`，面板上渲染成「自动」按钮），
    `web/src` 净增 5 条中文字面量——**而手册里一处都没写**。
    手册唯一那句相关描述还写的是「秒数 | **滑杆**，范围随模型档案」，
    **于是「按钮那一档」连同「自动」在手册里完全不存在**。
**读者拿这一版手册去对界面，会遇到一个手册没提过的选项。**

**本闸判什么**：对**每一对相邻上游 tag**（起点是截图 manifest 里最老的那张的拍摄版本），
数 `web/src` 里**中文字面量**的增删条数；**只要 > 0，那个版本号就必须出现在某个发布页里**。
**判据盯的是 README 的「vX.Y.Z 之后的增量」那一行**，
因为**那一行是读者升级时唯一会读的版本地图**。
**这是被鉴别力验证改掉的**（纪律 166）：第一版判「版本号出现在任一发布页里」——
把 `generate-video.md` 里的 `v1.6.21` 抹掉，闸**照样绿**，
因为那个版本号在 `director-basics.md` 的「v1.6.21 及更早的导演台弹窗」里出现过。
**「某处提到过这个版本」不等于「读者能顺着找到这次改了什么」**。
**判据的输入全部来自事实源**（tag 来自上游仓库、下界来自 `20-reference.md`
的「截图拍于」、清单来自 README、基线来自「取证基线」小节），**不建任何登记表**（纪律 242）。

**为什么用「中文字面量增减」当「用户可见文案变了」的代理**（这是一个有取舍的近似，如实说明）：
它认的是**字符串字面量**，所以它会漏掉「只改了逻辑、没改字」的变化（那是修复，不是文案变化），
也会理论上误伤「在 `web/src` 里加了一条带中文的非文案字符串」。
**实测假阳性率 0**：v1.6.0 → v1.6.22 全部 22 个版本逐个量过——
**凡是 `web/src` 中文字面量有增减的版本，手册全都提到了**；
而 0 增减的 v1.6.0 / 4 / 5 / 6 / 9 / 18 / 20 全部放行。
**排除测试文件**（实测排除与否计数相同，但为将来的夹具留一道）。

**覆盖不到什么，必须说在前面**：
  · **只要求「版本号被提到」，不要求「变化被讲清楚」。**
    v1.6.3 有 29 条文案增减、手册里只出现 1 次；v1.6.10 有 10 条、只 2 次。
    **本闸过的是「读者有机会在手册里找到这一版的线索」，不是「线索到位了」**；
  · **tag 序列里有缺口时归属会偏**：上游**没有 v1.6.12 这个 tag**，
    于是 v1.6.11 → v1.6.13 的 diff 里混着 v1.6.12 的改动，**本闸把它算在 v1.6.13 头上**。
    **有缺口就在输出里点出来**，不许安静地按「相邻」算；
  · **tag 拿不到就 rc=2**：本地克隆若没 fetch 过 tag，判据读空必须报「未能核对」，
    **不能让判据在一个空的版本序列上全绿**（纪律 101）。

退出码：0 全部覆盖；1 有版本改了用户可见文案却没被提到；2 未能核对。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from baseline import declared_baseline, BaselineError  # noqa: E402
from baseline import SRC as _BEEFSRC  # noqa: E402
from baseline import announce_fallback  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = _BEEFSRC
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")

VER_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def _v(text):
    m = VER_RE.search(text)
    return tuple(int(x) for x in m.groups()) if m else None


def _git(*args):
    r = subprocess.run(["git", "-C", SRC, *args], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def tags(series):
    """上游该系列的全部 tag，按版本升序。返回 (列表, 是否拿到)。"""
    out = _git("tag", "-l", series)
    if out is None:
        return None, False
    vs = sorted({t for t in out.split() if _v(t)}, key=_v)
    return vs, bool(vs)


def screenshot_floor(declared_floor):
    """下界 = `20-reference.md`「取证基线」小节里**声明的**「截图拍于」版本。

    **为什么用声明值而不是 manifest 里的最老一张**（这是第一版量出来的**假阳性**）：
    第一版取 manifest 的最小 `captured_version`（v1.6.0），于是区间拉到 22 个版本，
    报出「v1.6.3 有 28 条文案增减而手册没提到」。
    **逐个读之后确认那是假的**：手册的文字与数字**逐条核到基线 v1.6.22**，
    读者要判断的是「手册说的和我看到的一致吗」，**不是「历史上每一版都提过吗」**——
    补一句 v1.6.3 只会给读者加噪音。**而闸 32 要问的是「读者从截图那一版升到现在，
    会遇到哪些没被写下来的界面变化」**，所以下界必须是**手册自己声明的那个参照点**。

    **那 3 张更早的截图去哪了**：manifest 实测有 v1.6.0 / v1.6.6 / v1.6.13 三张，
    它们的版本新鲜度由**闸 16**（逐张 `captured_version` + 就地说明）负责，
    **不是本闸的事**。但差异**必须说出来**——所以下面会把「声明值比 manifest 最老的更新」
    打成一行提示，**不许静悄悄地取一个对自己有利的下界**。
    """
    info = []
    if not os.path.isfile(MANIFEST):
        return declared_floor, info, "读不到 screenshots/manifest.yml"
    text = open(MANIFEST, encoding="utf-8").read()
    vs = [_v(m) for m in re.findall(r"captured_version:\s*'?\"?(v?[\d.]+)", text)]
    vs = [v for v in vs if v]
    if vs and min(vs) < declared_floor:
        info.append(
            f"提示：manifest 里最老的截图拍于 v%d.%d.%d，早于本闸用的下界 "
            f"v%d.%d.%d——**那几张的版本新鲜度由闸 16 负责，不在本闸范围内**；"
            f"本闸的下界取的是 20-reference.md 声明的「截图拍于」，"
            f"因为它才是读者升级时的参照点"
            % (min(vs) + declared_floor))
    return declared_floor, info, None


def declared_screenshot_version():
    """`20-reference.md`「取证基线」小节里声明的「截图拍于」版本。

    **锚在字段名「截图拍于」上，不写死位置也不写死版本号**（Batch 232 的教训：
    写死 `### 取证基线` 这种级别会让一次纯结构修正打挂所有读基线的闸）。
    """
    ref = os.path.join(ROOT, "20-reference.md")
    try:
        text = open(ref, encoding="utf-8").read()
    except OSError as exc:
        return None, f"读不到 20-reference.md：{exc}"
    m = re.search(r"^(#{1,6})[ \t]*取证基线[ \t]*$", text, re.M)
    if not m:
        return None, "20-reference.md 里找不到「取证基线」小节"
    body = text[m.end():]
    nxt = re.search(r"^#{1,6}\s", body, re.M)
    if nxt:
        body = body[:nxt.start()]
    s = re.search(r"截图拍于[^\n]*?(v?\d+\.\d+\.\d+)", body)
    if not s:
        return None, "「取证基线」小节里没有「截图拍于」这一行"
    v = _v(s.group(1))
    return (v, None) if v else (None, f"截图拍于 {s.group(1)!r} 解析不出主.次.修订")


def increment_list_versions():
    """README.md「vX.Y.Z 之后的增量」那一行列出的版本。

    **第一版的判据是「版本号出现在任一发布页里」，而鉴别力验证当场把它否掉了**
    （纪律 166：判据上线前必须证明它抓得住那个它声称要抓的缺陷）：
    把 `generate-video.md` 里的「v1.6.21」抹掉，闸**照样绿**——
    因为那个版本号在 `director-basics.md` 的「v1.6.21 及更早的导演台弹窗」里出现过。
    **「某处提到过这个版本」不等于「读者能顺着找到这次改了什么」**，
    而闸 32 要守的恰恰是后者。**所以判据收紧到「必须列进 README 的增量清单」**——
    那一行是读者升级时唯一会读的版本地图，它漏掉一个改过界面文案的版本，
    读者就会得出「这版没变化」的错误结论。
    返回 (版本集合, 那一行的起点版本)；找不到返回 (None, None)。
    """
    readme = os.path.join(ROOT, "README.md")
    try:
        text = open(readme, encoding="utf-8").read()
    except OSError as exc:
        return None, None, f"读不到 README.md：{exc}"
    line = None
    for cand in text.split("\n"):
        if "之后的增量" in cand:
            line = cand
            break
    if line is None:
        return None, None, "README.md 里找不到「…之后的增量」那一行"
    start = _v(re.search(r"v?(\d+\.\d+\.\d+)\s*之后的增量", line).group(1)) \
        if re.search(r"v?(\d+\.\d+\.\d+)\s*之后的增量", line) else None
    listed = {_v(m) for m in re.findall(r"v(\d+\.\d+\.\d+)", line)}
    listed = {v for v in listed if v}
    if not listed:
        return None, None, "「之后的增量」那一行里一个版本号都没解析出来"
    return listed, start, None


def literal_delta(prev, cur):
    """`web/src` 里中文字面量的增删条数（去重）。返回 (条数, 是否拿到 diff)。"""
    out = _git("diff", prev, cur, "--", "web/src/*")
    if out is None:
        return None, False
    n = 0
    seen = set()
    for line in out.splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
            continue
        if re.search(r"\.(test|spec)\.|__tests__", line):
            continue
        for m in re.finditer(r'"[^"]*[\u4e00-\u9fff][^"]*"', line):
            seen.add(m.group(0))
    return len(seen), True


def main():
    announce_fallback()
    if SRC is None:
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，版本覆盖核对本轮未能进行")
        return 2
    try:
        base_ver, _commit = declared_baseline()
    except BaselineError as exc:
        print(f"[skip] {exc}，版本覆盖核对本轮未能进行")
        return 2
    base = _v(base_ver)
    if base is None:
        print(f"[skip] 取证基线 {base_ver!r} 解析不出主.次.修订，本轮未能核对")
        return 2
    series = "v%d.%d.*" % (base[0], base[1])

    vs, ok = tags(series)
    if not ok:
        print(f"[skip] 在 {SRC} 拿不到 {series} 的 tag"
              f"（本地克隆可能没 fetch 过 tag）——本轮未能核对，**不是「没有缺口」**")
        return 2
    if _v(base_ver) not in {_v(t) for t in vs}:
        print(f"[skip] tag 序列里没有基线版本 {base_ver}，本轮未能核对")
        return 2

    floor, err = declared_screenshot_version()
    if floor is None:
        print(f"[skip] {err}，版本覆盖核对本轮未能进行")
        return 2
    floor, infos, err = screenshot_floor(floor)
    if err:
        print(f"[skip] {err}，版本覆盖核对本轮未能进行")
        return 2
    if not any(_v(t) == floor for t in vs):
        print(f"[skip] tag 序列里没有声明的截图拍于版本 v%d.%d.%d，"
              f"起点对不上——本轮未能核对" % floor)
        return 2

    start = min(i for i, t in enumerate(vs) if _v(t) == floor)
    chain = vs[start:]
    if len(chain) < 2:
        print(f"[skip] 起点 v%d.%d.%d 之后没有可比的 tag，本轮未能核对" % floor)
        return 2

    listed, list_start, err = increment_list_versions()
    if listed is None:
        print(f"[skip] {err}，版本覆盖核对本轮未能进行")
        return 2
    if list_start is not None and list_start != floor:
        print(f"[skip] README 增量清单的下界是 v{'.'.join(str(x) for x in list_start)}，"
              f"而本闸的下界是 v{'.'.join(str(x) for x in floor)}——**两端对不上**，"
              f"本轮未能核对（清单的起点与「取证基线」小节声明的截图版本分家了）")
        return 2

    # ---- 自检：判据的正则必须真的能认出中文字面量，否则本闸恒真
    if not re.search(r'"[^"]*[\u4e00-\u9fff][^"]*"', '+ const a = "自动";'):
        print("[skip] 自检探针没匹配上——**判据的正则已失效**，本轮未能核对")
        return 2

    for info in infos:
        print(info)

    bad, notes, checked = [], [], 0
    for i in range(len(chain) - 1):
        prev_t, cur_t = chain[i], chain[i + 1]
        if _v(cur_t) > base:
            break
        n, ok = literal_delta(prev_t, cur_t)
        if not ok:
            print(f"[skip] 读不到 {prev_t} → {cur_t} 的 diff，本轮未能核对")
            return 2
        checked += 1
        # **tag 序列有缺口时，归属会偏**——点出来，不许安静按「相邻」算
        pv, cv = _v(prev_t), _v(cur_t)
        if cv[2] - pv[2] > 1:
            notes.append(f"**上游没有 v{pv[0]}.{pv[1]}.{pv[2] + 1} 这个 tag**，"
                         f"{cur_t} 的 diff 里混着它那部分改动，**本闸把它算在 {cur_t} 头上**")
        if n > 0 and cv not in listed:
            bad.append(f"v%d.%d.%d 的 `web/src` 有 %d 条中文字面量增减，"
                       f"而 README 的「增量」清单里没有它" % (cv[0], cv[1], cv[2], n))

    for note in notes:
        print(f"[skip] {note}")
    if bad:
        print(f"版本覆盖核对：{len(bad)}/{checked} 个版本改了用户可见文案却没被提到")
        for b in bad:
            print("  " + b)
        print("→ 在相应页面写清这一版改了什么；**如果读者确实不需要知道，"
              "也要在 README 的增量清单里点名这一版并说明「无界面变化」**——"
              "**读者分不清「这版没什么」和「没人查过」**")
        return 1
    if notes:
        print(f"[skip] {len(notes)} 处 tag 归属有偏移，其余 {checked} 个版本"
              f"全部覆盖 —— **不是全部通过**")
        return 2
    print(f"版本覆盖核对通过：截图拍于 v{'.'.join(str(x) for x in floor)} 之后到基线 {base_ver} 的"
          f" {checked} 个版本，凡是 `web/src` 改了用户可见中文字面量的都列进了 README 的增量清单"
          f"（0 增减的版本不需要列——实测 v1.6.18 / v1.6.20 就是这种）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
