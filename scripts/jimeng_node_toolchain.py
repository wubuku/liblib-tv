"""⭐ 外部工具链的**唯一实现** —— 「node 在不在」只能有一个答案。

⇒ ⇒⇒ **为什么要有这个模块**：多个探针各自 `subprocess.run(["node", ...])`，
⇒ ⇒⇒ 而 `node` 不在 PATH 时，Python 抛的是 `FileNotFoundError`
⇒ ⇒⇒ ⇒ **那个异常被各探针自己的 `except Exception` 吃掉**
⇒ ⇒⇒ ⇒ ⇒ 而 b2/b3/b4/c 会把判据降级成 `None`（**对的**），
⇒ ⇒⇒ ⇒ ⇒ 1032a 与 1032b1 却**继续读上一轮留下的读数文件**
⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ 那两本于是「探针一次没跑，判据却全 true」**
⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ 而 rc=0 ⇒ ⇒ 1015 记「reproduced」⇒ ⇒ ⇒ ⇒ 假绿**
⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ★ ★ ★ 这就是「仪器故障被伪装成数据结论」**

⇒ ⇒⇒ **本模块只回答一件事**：node 能不能用。
⇒ ⇒⇒ **调用方拿到 `False` ⇒ 必须把本轮判据记成 `None`（未测）**，
⇒ ⇒⇒ **且退出码必须是 2（仪器崩）——不许是 0（跑完了）、也不许是 1（判据红）**。
"""
import os
import shutil
import subprocess


def node_available():
    """node 能不能用？⇒ 返回 (bool, 来源说明)。

    ⇒ 来源说明**只进 stderr、不进产物** ⇒ ⇒ 产物里不许出现随机量
    ⇒ ⇒ （机器上 node 的绝对路径每次都一样，但**它不该成为判据的一部分**）。
    """
    exe = shutil.which("node")
    if exe:
        return True, "node=%s" % os.path.basename(exe)
    return False, "node-not-found-in-PATH"


def node_version():
    """node 的版本号 ⇒ **只进 stderr**（版本号会变 ⇒ 进产物就破坏逐字节可复现）。"""
    try:
        r = subprocess.run(["node", "--version"], capture_output=True,
                           text=True, timeout=30)
        return (r.stdout or "").strip() or None
    except Exception:
        return None


# ── ⭐⭐⭐⭐⭐ 跑一段 node 脚本（需要 stdout 的探针走这个）─────────────
#   ⇒ ⇒ ⇒ **为什么必须有它**：`run_node_probe` 只回传「跑没跑成」，
#   ⇒ ⇒ ⇒⇒ 而 1019 / 1020 / 1031 要的**正是 node 的 stdout（读数本身）**
#   ⇒ ⇒ ⇒⇒ ⇒ ⇒ 所以「执行 node」也必须只有**一个入口** ⇒ ⇒ 否则又长出第二个 spawn 点
#   ⇒ ⇒ ⇒⇒ ⇒ ⭐ **stdout / stderr 只许调用方自己用、不许进产物**
#   ⇒ ⇒ ⇒⇒ ⇒   （超时/异常信息里带绝对路径 ⇒ 进产物就变成机器相关量）
def run_node_script(script, cwd=None, timeout=300, env=None):
    """跑一段 node 脚本 ⇒ 返回 dict（`stdout`/`stderr` **不许进产物**）。"""
    ok, why = node_available()
    if not ok:
        return {"ok": False, "rc": None, "crashed": True, "stdout": "", "stderr": "",
                "reason": "node-unavailable",
                "run_info": "probe failed: node unavailable (%s)" % why}
    try:
        r = subprocess.run(["node", str(script)], cwd=cwd,
                           capture_output=True, text=True, timeout=timeout,
                           env=env)
    except Exception as e:                                   # noqa: BLE001
        return {"ok": False, "rc": None, "crashed": True, "stdout": "", "stderr": "",
                "reason": ("timeout" if isinstance(e, subprocess.TimeoutExpired)
                           else "exception"),
                "run_info": "probe failed: %s" % str(e)[:200]}
    _rc = r.returncode
    return {"ok": _rc == 0, "rc": _rc, "crashed": _rc != 0,
            "stdout": r.stdout or "", "stderr": r.stderr or "",
            "reason": "rc",
            "run_info": ("rc=0" if _rc == 0 else "rc=%d probe-crashed" % _rc)}


# ── ⭐⭐⭐⭐⭐ 统一跑 node 探针的入口 ─────────────────────────────────
#   ⭐⭐⭐⭐⭐ **退出码语义（本套件全部门统一）**：
#     0 = 探针跑完了
#     1 = 探针跑完了、但判据红（产品/数据问题）
#     2 = **仪器崩了**（node 不可用 / 探针自己崩了 / 探针没写盘）
#   ⇒ ⇒ ⇒ 「跑不动」与「跑完了没过」必须分开 ⇒ ⇒ 否则崩了会被记成绿。
#
#   ⭐⭐⭐⭐⭐ **`nonzero_is_crash` 为什么必须由调用方声明**：
#     · 有一类 .mjs 探针**没有显式 process.exit** ⇒ 跑完即 rc=0
#       ⇒ ⇒ 此时任何 rc≠0 都只可能是「它自己崩了」（uncaught exception）
#       ⇒ ⇒ `nonzero_is_crash=True`
#     · 另一类 .mjs 用 `process.exit(n_failed > 0 ? 1 : 0)`
#       ⇒ ⇒ 此时 rc=1 是「检查没过」（**产品红**），只有 rc=2 / INSTRUMENT_CRASH 才是崩
#       ⇒ ⇒ `nonzero_is_crash=False`
#   ⇒ ⇒ ⇒ **「rc≠0 到底意味着什么」不是探针自己能猜的** ⇒ ⇒ 必须由【知道那个 .mjs 约定】的人声明。
#
#   ⭐⭐⭐⭐⭐ **产物里只留 `run_info`（机器无关的短标签）**
#   ⇒ ⇒ ⇒ 绝对路径 / 版本号 / stderr 全文 / 时间戳 **一律不进产物**
#   ⇒ ⇒ ⇒ 否则产物每次跑都不一样 ⇒ ⇒ 1015 的「逐字节可复现」当场失效。
def run_node_probe(probe, cwd=None, timeout=300, env=None,
                   nonzero_is_crash=True):
    """跑一个 node 探针 ⇒ 返回 dict。

    ⇒ 返回键：`ok`(bool) / `rc`(int|None) / `crashed`(bool) / `run_info`(str)
    ⇒ 调用方约定（**必须照做，否则又是一次假绿**）：
       · `crashed=True`  ⇒ 退出码必须走 **2**，且**不许**读上一轮留下的读数文件
       · `crashed=False` ⇒ 读数文件才可用
    """
    res = run_node_script(probe, cwd=cwd, timeout=timeout, env=env)
    if res["crashed"] is False:
        return {"ok": True, "rc": 0, "crashed": False, "run_info": "rc=0"}
    rc = res["rc"]
    if rc is None:
        return {"ok": False, "rc": None, "crashed": True,
                "run_info": res["run_info"]}
    if rc == 2 or "INSTRUMENT_CRASH" in res["stdout"]:
        return {"ok": False, "rc": rc, "crashed": True,
                "run_info": "rc=2 instrument-crash"}
    if nonzero_is_crash:
        return {"ok": False, "rc": rc, "crashed": True,
                "run_info": "rc=%d probe-crashed" % rc}
    return {"ok": False, "rc": rc, "crashed": False,
            "run_info": "rc=%d" % rc}


def readings_fresh(path, started_at, tolerance=2.0):
    """读数文件是不是【本轮】写的？⇒ 防止「拿旧读数冒充本轮读数」。

    ⭐⭐⭐⭐⭐ **为什么必须量新鲜度、而不能只看「文件在不在」**：
    ⇒ ⇒ 探针崩了但**上一次**跑成功过 ⇒ ⇒ 文件**存在**、内容**看着正常**
    ⇒ ⇒ ⇒ 而它其实是**上一轮的** ⇒ ⇒ 拿它当本轮读数 ⇒ ⇒ **假绿**
    ⇒ ⇒ ⇒ ⇒ 而这次事故里 1032a / 1032b1 正是这么绿的。
    ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ★ 「文件在」≠「是本轮的」⇒ ⇒ 必须比 mtime。
    ⇒ ⇒ ⇒⇒ 容忍 2 秒：文件系统时间戳精度不同（APFS 1ns，但别处可能 1s/2s）。
    """
    try:
        return os.path.getmtime(str(path)) >= (started_at - tolerance)
    except OSError:
        return False
