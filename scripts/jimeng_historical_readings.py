#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②h：共享的「带 sha 的历史实测读数」出处层。

⭐⭐⭐⭐⭐ **为什么要有这一层**
⇒ ⇒ 「判据文本里手写的每一个数都必须有出处」这条契约（1006 立、1007..1013 继承）
⇒ ⇒ 而判据文本里有些数是**写下那一刻宇宙上的读数** ⇒ ⇒ 今天复算不出来
⇒ ⇒ ⇒ **⇒ 「今天复算不出来」≠「它当初是假的」** ⇒ ⇒
⇒ ⇒⇒⇒ **⇒ 处置：出处不是白名单、出处是「带 sha 的历史实测读数」**

⭐⭐⭐⭐⭐ **五步法（②g 在 1007 上立、②h 提成共享模块）**
① **问 git**：哪一次提交写下了这段文本？⇒ `git log -S <marker>`、**取最早一次**
② **取当年的树**：`git archive <sha> scripts docs/research/jimeng-canvas src/components/jimeng`
③ **在那一瞬间重跑当年的探针**（带 `GIT_DIR` / `GIT_WORK_TREE` ⇒ 它 `git show` 的是那棵树）
④ **读它的产物** ⇒ 收集数字 ⇒ **每个数记它在产物里的路径**（出处要能指到具体字段）
⑤ **必须看到「写完了」的标记才能读产物**；且这一层**必须在被测脚本写自己产物之前**跑完
   （否则「当年的产物」与「这一轮的产物」会互相顶掉）

⭐⭐⭐⭐⭐ **「接不接这一层」本身是一条判据（②h 立）**
⇒ ⇒ 1007 的 P7 是**红的**（它判据文本里的数是当年宇宙的读数、今天复算不出来）⇒ ⇒ 接
⇒ ⇒ 而 1008 / 1010 / 1011 / 1012 的同类判据**今天都是绿的** ⇒ ⇒ **不接**
⇒ ⇒ ⇒ **⇒ 理由：接上这一层就等于把那本书的「有出处的数」集合变大 ⇒ ⇒**
⇒ ⇒⇒⇒ **⇒ 而判据的牙 = 「一个编出来的数仍然会被抓住」⇒ ⇒ 集合越大牙越钝 ⇒ ⇒**
⇒ ⇒⇒⇒⇒ **⇒ 所以出处层不是「越多越好」、它只在「真的缺一个出处」时才接上**
⇒ ⇒⇒⇒⇒ ⇒ ⇒ **⇒ 而「缺了才接」也必须可查 —— 接了就必须留下「缺的是哪个数」的记录**

⭐ **被引用的历史读数**（`cited_numbers`）
⇒ ⇒ 有些数**当年就落在散文里**（不是仪器算出来的字段）⇒ ⇒ 那它没有「路径」可指
⇒ ⇒ ⇒ **⇒ 处置：显式声明「这个数在哪个文件的哪个字段里」⇒ ⇒**
⇒ ⇒⇒⇒ **⇒ 而声明必须被**机器验证** —— 那个文件、那个字段、那个数，真的在那个 sha 上吗？**
⇒ ⇒⇒⇒⇒ ⇒ ⇒ **⇒ 验证不过 ⇒ 不放行**（宁可红、也不许悄悄放宽白名单）
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CACHE_DIR = Path("/tmp/jimeng-hist-cache")
_DONE_RE = re.compile(r"PROBE_\d+_DONE\s*->\s*(\S+)")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


class _Result(object):
    """`subprocess.run` 的最小替身（异常时也不抛）。"""

    def __init__(self, returncode=-1, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _run(cmd, cwd, timeout=300, env=None):
    try:
        return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                              timeout=timeout, env=env)
    except Exception as exc:  # noqa: BLE001
        return _Result(-1, "", "spawn failed: %r" % (exc,))


# ── ① 问 git：哪一次提交写下了这段文本？──────────────────────────────
def historical_commit_sha(repo_root, marker,
                          relpath="scripts/jimeng_unclickable_audit.py"):
    """⇒ (sha | None, meta)—— **sha 是问来的、不是手打的**。"""
    res = _run(["git", "log", "-S", marker, "--format=%H", "--", relpath],
               repo_root, timeout=300)
    shas = [ln.strip() for ln in (res.stdout or "").splitlines() if ln.strip()]
    how = "git log -S '%s' -- %s（取最早的一次 = 写下这段文本的那一次）" % (
        marker, relpath)
    if not shas:
        return None, {"marker": marker, "how": how, "why": "no_commit_found",
                      "n_commits_touching": 0}
    return shas[-1], {"marker": marker, "how": how,
                      "n_commits_touching": len(shas)}


# ── 产物里的数字 ⇒ 数字 → 它的路径 ─────────────────────────────────
def numbers_with_paths(obj, skip_prefixes=("verdicts_",)):
    """⇒ {数字字符串 → 它在产物里的路径}（**出处要能指到具体字段**）。"""
    out = {}

    def walk(o, p):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, p + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, p + "/" + str(i))
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):
            for s in (str(o), "%.1f" % o):
                out.setdefault(s, p)

    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        if any(str(k).startswith(sp) for sp in skip_prefixes):
            continue
        walk(v, "/" + str(k))
    return out


# ── 已落盘的那份产物（`git show`）──────────────────────────────────
def committed_artifact(repo_root, sha, relpath):
    """⇒ (json | None, meta)—— **当年记录下来的读数**。"""
    res = _run(["git", "show", "%s:%s" % (sha, relpath)], repo_root, timeout=300)
    if res.returncode != 0:
        return None, {"rc": res.returncode, "err": (res.stderr or "")[-200:]}
    try:
        return json.loads(res.stdout), {"rc": 0, "bytes": len(res.stdout)}
    except Exception as exc:  # noqa: BLE001
        return None, {"rc": 0, "parse_failed": repr(exc)}


def _field_at(obj, path):
    """按 `a/b/0` 取字段值；取不到 ⇒ None。"""
    cur = obj
    for seg in [s for s in str(path).split("/") if s]:
        if isinstance(cur, dict):
            if seg not in cur:
                return None
            cur = cur[seg]
        elif isinstance(cur, list):
            try:
                cur = cur[int(seg)]
            except Exception:  # noqa: BLE001
                return None
        else:
            return None
    return cur


def _value_contains_number(value, num):
    """这个值里含不含这个数？（数值本身、或字符串里嵌入的数）"""
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return str(value) == num or ("%.1f" % value) == num
    if isinstance(value, str):
        for m in _NUM_RE.findall(value):
            if m == num or ("%.1f" % float(m)) == num:
                return True
    return False


# ── 被引用的历史读数：逐条**机器验证** ─────────────────────────────
def cited_numbers(repo_root, sha, relpath, citations):
    """⇒ (proven, rejected)—— **验证不过 ⇒ 不放行**。"""
    art, meta = committed_artifact(repo_root, sha, relpath)
    proven, rejected = {}, {}
    for num in sorted((citations or {}).keys()):
        spec = citations[num]
        path = spec["path"] if isinstance(spec, dict) else spec
        c_sha = spec.get("sha", sha) if isinstance(spec, dict) else sha
        c_rel = spec.get("artifact", relpath) if isinstance(spec, dict) else relpath
        if art is None or c_sha != sha or c_rel != relpath:
            got, gmeta = committed_artifact(repo_root, c_sha, c_rel)
            if got is None:
                rejected[num] = {"path": path, "sha": c_sha, "artifact": c_rel,
                                 "why": "artifact_unavailable", "meta": gmeta}
                continue
            art, meta = got, gmeta
        val = _field_at(art, path)
        if val is None:
            rejected[num] = {"path": path, "sha": c_sha, "artifact": c_rel,
                             "why": "field_not_found"}
            continue
        if not _value_contains_number(val, num):
            rejected[num] = {"path": path, "sha": c_sha, "artifact": c_rel,
                             "why": "number_absent_in_field",
                             "value": str(val)[:160]}
            continue
        proven[num] = {"path": path, "sha": c_sha, "artifact": c_rel,
                       "value": str(val)[:200]}
    return proven, rejected


# ── ②③⑤：取当年的树、在那一瞬间重跑当年的探针、读它的产物 ─────────
def rerun_at(repo_root, sha, probe_relpath, work_dir, timeout=2400):
    """⇒ (artifact json | None, meta)。"""
    dest = Path(work_dir) / sha[:12]
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        return None, {"mkdir_failed": repr(exc)}
    try:
        arc = subprocess.run(
            "git archive " + sha + " scripts docs/research/jimeng-canvas"
            " src/components/jimeng | tar -x -C " + str(dest),
            shell=True, cwd=str(repo_root), capture_output=True, text=True,
            timeout=900)
    except Exception as exc:  # noqa: BLE001
        return None, {"archive_failed": repr(exc)}
    if arc.returncode != 0:
        return None, {"archive_rc": arc.returncode,
                      "archive_err": (arc.stderr or "")[-200:]}
    probe = dest / probe_relpath
    if not probe.exists():
        return None, {"probe_missing": True, "probe_relpath": probe_relpath}
    env = dict(os.environ)
    env["GIT_DIR"] = str(Path(repo_root) / ".git")
    env["GIT_WORK_TREE"] = str(dest)
    try:
        run = subprocess.run([sys.executable, str(probe)], cwd=str(dest),
                             capture_output=True, text=True, timeout=timeout,
                             env=env)
    except subprocess.TimeoutExpired:
        return None, {"probe_timeout": True, "timeout_s": timeout}
    except Exception as exc:  # noqa: BLE001
        return None, {"probe_spawn_failed": repr(exc)}
    text = (run.stdout or "") + (run.stderr or "")
    hits = _DONE_RE.findall(text)
    if not hits:
        return None, {"probe_rc": run.returncode,
                      "why": "当年的探针没跑到写产物那一步（没有 DONE 标记）"}
    art_path = Path(hits[-1])
    if not art_path.exists():
        return None, {"probe_rc": run.returncode, "why": "产物文件不在",
                      "path": str(art_path)}
    try:
        return (json.loads(art_path.read_text(encoding="utf-8")),
                {"probe_rc": run.returncode, "artifact": str(art_path)})
    except Exception as exc:  # noqa: BLE001
        return None, {"probe_rc": run.returncode, "parse_failed": repr(exc)}


# ── 整层出处：一次调用拿到全部 ─────────────────────────────────────
def historical_layer(repo_root, marker, probe_relpath, work_dir,
                     committed_relpath=None, citations=None, timeout=2400,
                     use_cache=True):
    """⇒ 一层出处的完整记录（**可落进书级产物**）。

    ⭐ 缓存按 **sha + 探针路径** 寻址 ⇒ ⇒ 内容寻址 ⇒ ⇒ 同一棵树重跑多轮只付一次代价
    ⇒ ⇒ 而缓存里存的是**解析后的内容**（不是那个会被顶掉的 /tmp 文件）
    ⇒ ⇒ ⇒ 缓存读不出来 ⇒ 当场重跑（**不拿缓存当事实**）
    """
    root = Path(repo_root)
    sha, sha_meta = historical_commit_sha(root, marker)
    res = {
        "marker": marker,
        "sha": sha,
        "sha_derivation": sha_meta.get("how"),
        "n_commits_touching_marker": sha_meta.get("n_commits_touching"),
        "probe_relpath": probe_relpath,
        "committed_relpath": committed_relpath,
        "how": ("git log -S → git archive → 在那一瞬间重跑当年的探针"
                " → 读它的产物 → 每个数记它在产物里的路径"),
    }
    if not sha:
        res.update({"reproduced": False, "n_numbers": 0, "numbers": {},
                    "cited_verified": {}, "cited_rejected": {},
                    "n_cited_verified": 0, "why": "sha 没问出来",
                    "meta": sha_meta})
        return res

    cache = CACHE_DIR / ("%s_%s.json" % (sha[:12], Path(probe_relpath).stem))
    art = None
    rmeta = {}
    if use_cache and cache.exists():
        try:
            blob = json.loads(cache.read_text(encoding="utf-8"))
            if blob.get("sha") == sha and isinstance(blob.get("artifact"), dict):
                art = blob["artifact"]
                rmeta = blob.get("meta") or {}
                rmeta["from_cache"] = True
        except Exception:  # noqa: BLE001
            art = None
    if art is None:
        art, rmeta = rerun_at(root, sha, probe_relpath, work_dir, timeout=timeout)
        rmeta["from_cache"] = False
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"sha": sha, "probe": probe_relpath,
                                         "artifact": art, "meta": rmeta},
                                        ensure_ascii=False), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    numbers = numbers_with_paths(art)
    proven, rejected = {}, {}
    if committed_relpath and citations:
        proven, rejected = cited_numbers(root, sha, committed_relpath, citations)
    res.update({
        "reproduced": bool(numbers),
        "n_numbers": len(numbers),
        "numbers": dict(sorted(numbers.items())),
        "cited_verified": proven,
        "cited_rejected": rejected,
        "n_cited_verified": len(proven),
        "meta": rmeta,
    })
    return res
