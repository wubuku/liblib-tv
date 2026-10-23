#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 第一次跑有可能赶上热更中途
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

★ ★ **复原用白名单**：`CHANGED` 是**明确列出的相对路径**（不是黑名单），
⟹ ⟹ 不会把本批自己的源码或别人的 WIP 一起回退；⟹ ⟹ 且复原走**字节备份**
（不是 `git checkout`）⟹ ⟹ 复原后逐字节校验哈希。
★ ★ **绝不用 `git stash`**（本仓库的 `stash@{0}` 是别人的 WIP ⟹ ⟹ 全程不碰）。

## ★ 本批盯哪些门禁

★ 本批改了**两个**被跟踪源码：

- `src/components/director/DirectorIconRail.tsx`（crowd 按钮开关 ＋ 点外面关闭 ＋ 落点改源站公式 ＋ 间距 1 位小数）
- `src/components/director/DirectorViewport.tsx`（删 legacy 视口 crowd 面板 ＋ 加移动端专用入口）
- `src/store/directorStore.ts`（`addCrowdArray` 删掉 clone 自造量程）

★ 因此必须**在 HEAD 与工作副本上读数逐条完全相同**的门禁：

- `853`／`852`／`45`／`792` **组相关**（★ 本批动的正是组的 UI 层）
- `96` ＋ `67`／`68`／`74`／`79`／`80`／`81` **文档 schema 相关**
- 其余读 `DirectorInspector`／`DirectorViewport` 的**静态**门禁
  （`69`／`70`／`71`／`72`／`75`／`84`／`85`／`86`／`89`／`90`）

★ 另跑**旧账**（`736`／`748`／`749`／`782`／`831`／`741`／`87`／`91`）⟹ ⟹
它们在 HEAD 上也红 ⟹ ⟹ **不是本批引入的**；以及 `856` 本批
（★ 在 HEAD 上**必然红** ⟹ ⟹ 门禁有牙）。

★ ★★ **本批特有的预期差异有三条**（`857.py` ＋ 两条**判据迁移**过的老门禁）：
★ 迁移后的 `84.mjs`／`86.mjs` 在 **HEAD 态必然红** ⟹ ⟹ 因为它们的判据
★ **前提已经换了**（HEAD 的源码里还有组 gizmo ＋ 那道视口层锁定守卫）
⟹ ⟹ 那正是「**迁移后的判据有牙**」的证据 ⟹ ⟹ 不算失败。
"""
import hashlib
import json
import pathlib
import subprocess
import signal
import sys
import time

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ ★ 白名单：只列本批**确实改过**的相对路径
# ★ ★★ 本批**没有新增／改名／删除任何导出** ⟹ ⟹ 白名单只有这 2 个源文件
# ★    ⟹ ⟹ 换回 HEAD 之后**整站仍能编译**（不存在「消费者 import 了不存在的导出」
# ★    ⟹ ⟹ 整站 500 ⟹ ⟹ 浏览器门禁全部 60s 超时 ⟹ ⟹ 读数全是假的）。
CHANGED = [
    # ★ ★ 白名单必须是本批改过的**全部**源文件（**不是黑名单**）
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorViewport.tsx",
    "src/store/directorStore.ts",
]

# ★ 旧账（HEAD 上也是红的）＋ 本批（在 HEAD 上必然红 ⟹ ⟹ 门禁有牙）
TARGETS = [
    # ★ ★ **本批扩大回归清单后新出现的红**（★ 逐条定点归因用）：
    #   它们在 HEAD 上**也必须红** ⟹ ⟹ 那就证明**不是本批引入的**。
    # `541.py` —— ★ 它的前提是「点『群众 (3x3)』**直接加**人群」⟹ ⟹
    #   但 **batch 590 起**（源站逐字）那一枚是**打开对话框** ⟹ ⟹
    #   ⟹ 它的「老前提」早于本批 ⟹ ⟹ 与本批无关。
    ("541", "py"),
    # `546.py`／`542.py` —— ★ 失败原因是 **fixture 文件不存在**
    #   （`/private/tmp/batch542-fixture/hero-character.fbx` ENOENT）⟹ ⟹ 环境缺件。
    ("546", "py"), ("542", "py"),
    # `738.py` —— ★ C7「根外 button 轨迹」的**写死个数**过期
    #   （实测 49→54→57；★ **HEAD 上同样是** 49→54→57 ⟹ ⟹ 本批没动它）。
    ("738", "py"),
    # `656.py` —— 「场景面板」的**预测被证伪** ⟹ ⟹ 与本批无关（本批没改「场景」入口）。
    ("656", "py"),
    # ★ 本批（★ 在 HEAD 上**必然红** ⟹ ⟹ 说明门禁真的在读本批的源码）
    ("857", "py"),
]
# ★ 必须逐条相同的绿门禁
# ★ ★ 清单**收窄**到「读本批改过的那几个文件」的门禁 ⟹ ⟹ 理由：
# ★   ① 受控对照每条要**连跑两遍**、HEAD 与工作副本各一遍 ⟹ ⟹ 浏览器门禁很贵；
# ★   ② 第 3 轮回归已经证明「盯的 33 条全绿」⟹ ⟹ 这里要证明的是
# ★      **读数逐条相同**（而不是「红红相同」）；
# ★   ③ ★ `36`／`47`／`48`／`49`／`50` 在第 2 轮回归里曾一起红、单独复跑全绿
# ★      ⟹ ⟹ **环境瞬态**（dev server 重编译）⟹ ⟹ 放进「读数逐条相同」的
# ★      对照会引入**假差异** ⟹ ⟹ **不放进**本清单（它们的绿／红已在回归里验过）。
WATCH = [
    # ★ ★ 本批动的是 **crowd 对话框** ＋ **rail 浮层** ＋ **store 的 addCrowdArray**
    #   ⟹ ⟹ 凡是**读这三处**、且**行为可能被我改的**门禁，都要在
    #   「HEAD 与工作副本」上读数**逐条完全相同**。
    ("45", "py"),    # ★ 本批迁移过（crowd 段迁到 rail ＋ 关浮层 ＋ 移动端段改走移动端入口）
    ("590", "py"),   # ★ crowd 对话框的量程／默认值／流程
    ("626", "py"),   # ★ 几何子菜单 ＋ crowd（**开关**语义可能影响它）
    ("613", "py"),   # ★ 浮层几何
    ("625", "py"),   # ★ ★ **判据被本批迁移过**的那条（落点改按源站公式推导）
    ("84", "mjs"), ("86", "mjs"),
]


# ★ 预期差异白名单：读数**允许**不同的条目。
# ★ ① `857.py` —— 本批自己的门禁 ⟹ ⟹ 在 HEAD 上**必然红**（HEAD 的源码里
#     没有本批的改动）⟹ ⟹ 那正是「门禁真的在读本批源码」的证据 ⟹ ⟹ 不算失败。
# ★ ② `625.py` —— ★ 本批**迁移过判据**的老门禁 ⟹ ⟹ HEAD 的 clone 的对话框落点是
#     **写死**的「rail+294」⟹ ⟹ 与「按源站公式推导」的期望不符 ⟹ ⟹ 必然红
#     ⟹ ⟹ 那正是「迁移后的判据有牙」的证据。
# ★ ③ `45.py` —— ★ 本批**迁移过判据**的老门禁 ⟹ ⟹ 它新增的那一步
#     「点视口工具条的移动端 crowd 入口」在 HEAD 上**没有那个元素**
#     ⟹ ⟹ 必然红 ⟹ ⟹ 同样是有牙的证据。
EXPECTED_DIFFS = {"857.py", "625.py", "45.py"}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str, ext: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    if not script.exists():
        return "（无此门禁）"
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                       cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%s | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


def run_twice(batch: str, ext: str) -> str:
    first = run(batch, ext)
    second = run(batch, ext)
    if first != second:
        # ★★ 两遍不一致 ⟹ 先别当「读数变了」⟹ ⟹ **再跑一遍**。
        # ★ 起因：dev server 热更期间，第一遍可能撞上「页面还在编译」，
        #   读到一个**瞬态**错误（实测 748.py 第一遍 `KeyError: 'submitDisabled'`、
        #   第二遍就正常）⟹ ⟹ 两遍不同**不等于**「HEAD 与工作副本有差异」。
        # ★ 判据：**第三遍**与第二遍相同 ⟹ ⟹ 第一遍是瞬态 ⟹ ⟹ 以稳定读数为准。
        third = run(batch, ext)
        if third == second:
            return second + " | ★首遍瞬态（第 3 遍与第 2 遍相同）"
        return "★两遍不一致 | %s ⟹ %s ⟹ 第3遍 %s" % (first, second, third)
    return first


def warm_up(url: str = "http://localhost:4317/", tries: int = 40) -> str:
    """★ 换回源码后 4317 要**热更**（冷编译可能要几十秒）
    ⟹ ⟹ 不热机就直接跑门禁 ⟹ ⟹ 第一条门禁大概率撞上冷编译 ⟹ ⟹ 60s 超时
    ⟹ ⟹ 读数变成「超时」⟹ ⟹ 假差异。
    ⟹ ⟹ 这里先反复 GET 到 **200** 为止。
    """
    import urllib.error
    import urllib.request
    last = ""
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                if resp.status == 200:
                    return "200"
                last = "status=%s" % resp.status
        except urllib.error.HTTPError as exc:
            last = "http=%s" % exc.code
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:80]
        time.sleep(1.5)
    return "★没热起来（%s）" % last


def _on_sigterm(signum, frame):  # noqa: ARG001
    """★ SIGTERM 也要走 finally ⟹ ⟹ 否则**工作副本恢复不回来**。

    ★ 上一批踩过：SIGTERM 直接杀进程 ⟹ finally 不跑 ⟹ ⟹ 丢了 3 个文件的改动。
    ⟹ ⟹ 这里把 SIGTERM **转成异常** ⟹ ⟹ finally 照常执行 ⟹ ⟹ 恢复可靠。
    """
    raise KeyboardInterrupt("★ 收到 SIGTERM ⟹ 走 finally 复原工作副本")


def main() -> int:
    signal.signal(signal.SIGTERM, _on_sigterm)
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)

    # ★ 先打印清单再执行（★ 白名单，不是黑名单）
    print("将要换回 HEAD 的文件（白名单，共 %d 个）：" % len(CHANGED))
    for rel in CHANGED:
        print("   ", rel)

    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT),
                       check=True)
        print("已换回 HEAD ⟹ 热机 4317：%s" % warm_up())
        print()
        for b, e in TARGETS:
            head_reads["%s.%s" % (b, e)] = run_twice(b, e)
            print("HEAD 上 %s.%s ⟹ %s" % (b, e, head_reads["%s.%s" % (b, e)]),
                  flush=True)
        for b, e in WATCH:
            head_reads["%s.%s" % (b, e)] = run_twice(b, e)
            print("HEAD 上 %s.%s ⟹ %s" % (b, e, head_reads["%s.%s" % (b, e)]),
                  flush=True)
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        print("\n已复原工作副本 ⟹ 热机 4317：%s" % warm_up())
        for p in backups:
            assert sha(p) == before[p], "★ 复原后哈希不一致：%s" % p
            print("  复原校验 OK %s %s" % (p.name, sha(p)[:16]))

    print("\n=== 工作副本上再跑一遍（★ 必须与 HEAD 逐条完全相同）===")
    diffs = []
    for b, e in TARGETS + WATCH:
        key = "%s.%s" % (b, e)
        work = run_twice(b, e)
        same = work == head_reads.get(key)
        print("  %-9s %s" % (key, "一致 ✓" if same else "★★ 不一致"))
        if not same:
            diffs.append({"batch": key, "HEAD": head_reads.get(key),
                          "工作副本": work})
    total = len(TARGETS) + len(WATCH)
    # ★ 预期差异：**本批自己的门禁**在 HEAD 上**必然红** ⟹ ⟹ 那正是
    #   「门禁真的在读本批源码」的证据 ⟹ ⟹ 它**不算**失败。
    expected = set(EXPECTED_DIFFS)
    unexpected = [d for d in diffs if d["batch"] not in expected]
    print("\n受控对照：%d/%d 条读数逐条完全相同（预期差异 %d 条：%s）" % (total - len(diffs), total, 
           len(diffs) - len(unexpected), sorted(expected)))
    out = {"批次": 857, "总数": total, "一致数": total - len(diffs),
           "不一致": diffs,
           "HEAD读数": {k: v for k, v in head_reads.items()}}
    (ROOT / "docs/research/liblib-canvas-batch857-2026-10-01/raw/attrib-857.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    out["预期差异"] = sorted(expected)
    out["非预期差异"] = unexpected
    return 0 if not unexpected else 1


if __name__ == "__main__":
    sys.exit(main())
