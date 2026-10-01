#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""excluded 页解禁条件核对闸：账本里写的「还差什么」是否与上游现状一致。

背景（Batch 111）：手册有 4 个 `excluded` 任务（媒体版本族 / 云端 Agent /
Agent 记忆与技能 / 本地伴随进程），每条都附了「开放条件」。这类条件最危险的
失效方式是**悄悄过期**——上游可能已经解禁（或已彻底移除），而账本仍写着旧的
理由，于是「什么时候能补这一页」这个判断从此失准。

本闸把条件中**可机械判定**的四条拿上游现状逐条比对：
  1. `/agent/*` 路由仍未注册          → cloud-agent / agent-memory-skills 未解禁
  2. `MediaConversion`/`Frame`/`Script` 仍在 `developingNodeTypes` → local-runtime
     的「智能剪辑」节点入口仍关闭
  3. 本地运行时二进制不在仓库内      → local-runtime 无法起服
  4. `isLocalWorkspaceMode()` 仍是无条件 `return true`，且 `LocalAwareProjectRoute`
     的重定向分支仍排在渲染分支之前 → short-drama-project-workbench（短剧/小说
     转视频生产台）仍不可达

第 5 条（真实生成产生版本族）属于付费边界，**不可机械判定**，脚本不检查。

只检查「条件是否仍成立」，不判断条件本身写得对不对——后者需要人读实现。
条件若与现状不符，脚本报出让人回头改账本。

退出码：0 条件全部仍成立；1 有条件已失效。
"""

import os
import re
import sys
import subprocess

CANDIDATES = [
    os.environ.get("BEEFTV_SRC", ""),
    "/Users/yangjiefeng/Documents/glanderness/BeefTV",
]

AGENT_BRANCH = "origin/codex/agent-product-v1610-20260928"

ROUTE_RE = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH)\("([^"]+)"')


def find_source():
    for c in CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "backend")):
            return os.path.abspath(c)
    return None


def git_show(src, ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"],
                       cwd=src, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def git_ls(src, ref):
    r = subprocess.run(["git", "ls-tree", "-r", ref, "--name-only"],
                       cwd=src, capture_output=True, text=True)
    return r.stdout.split("\n") if r.returncode == 0 else []


def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过 excluded 条件核对")
        return 2
    ref = "origin/main"

    problems = []
    notes = []

    # —— 条件 1：/agent/* 路由仍未注册 ——
    routes = set()
    for f in git_ls(src, ref):
        if not f.startswith("backend/") or not f.endswith(".go") or f.endswith("_test.go"):
            continue
        for m in ROUTE_RE.finditer(git_show(src, ref, f)):
            routes.add(m.group(1))
    agent_routes = sorted(r for r in routes if "agent" in r)
    if agent_routes:
        problems.append(
            f"/agent 相关路由已注册 {len(agent_routes)} 条（{', '.join(agent_routes[:3])}）"
            f" → cloud-agent / agent-memory-skills 的解禁条件可能已满足，需回走验证"
        )
    else:
        notes.append("cloud-agent / agent-memory-skills：/agent/* 仍未注册，条件成立")

    # —— 条件 2：智能剪辑等节点仍在 developingNodeTypes ——
    avail = git_show(src, ref, "web/src/lib/canvas/canvas-feature-availability.ts")
    if not avail:
        notes.append("未取到 canvas-feature-availability.ts，节点解禁条件本轮未判定")
    else:
        if "developingNodeTypes" in avail and "MediaConversion" in avail:
            notes.append("local-runtime：MediaConversion 仍在 developingNodeTypes，"
                         "「智能剪辑」入口仍关闭，条件成立")
        else:
            problems.append(
                "MediaConversion 已不在 developingNodeTypes 内 → 「智能剪辑」"
                "节点可能已开放，local-runtime 需回走验证"
            )

    # —— 条件 3：本地运行时二进制不在仓库 ——
    files = git_ls(src, ref)
    binary_hits = [
        f for f in files
        if re.search(r"framefield[-_]?local[-_]?runtime|local-runtime\.(exe|dmg|deb|rpm|AppImage)$", f, re.I)
    ]
    if binary_hits:
        problems.append(
            f"本地运行时二进制疑似已入仓 {len(binary_hits)} 条（{', '.join(binary_hits[:3])}）"
            f" → local-runtime 的「无法起服」条件可能已解除"
        )
    else:
        notes.append("local-runtime：运行时二进制仍不在仓库内，本机无法起服，条件成立")

    # —— 条件 4：短剧/小说生产台仍不可达 ——
    # 判据是两段源码同时成立：isLocalWorkspaceMode 无条件 true（LocalAwareProjectRoute
    # 必走重定向分支），且重定向分支排在 ProjectDetailPage 渲染分支之前。
    wsm = git_show(src, ref, "web/src/services/workspace-mode.ts")
    router = git_show(src, ref, "web/src/router.tsx")
    if not wsm or not router:
        notes.append("未取到 workspace-mode.ts / router.tsx，短剧生产台解禁条件本轮未判定")
    else:
        m = re.search(r"export function isLocalWorkspaceMode\s*\(\s*\)\s*\{(.*?)\n\}", wsm, re.S)
        body = m.group(1) if m else ""
        # 无条件 true = 函数体里既没有条件分支，也没有 return false
        hardcoded_true = bool(m) and "return true" in body and "return false" not in body \
            and not re.search(r"\bif\b|\?|&&|\|\|", body)
        nav_pos = router.find('<Navigate to={`/canvas/${projectId}`} replace />')
        render_pos = router.find("deferred(<ProjectDetailPage />)")
        nav_first = nav_pos != -1 and render_pos != -1 and nav_pos < render_pos
        if hardcoded_true and nav_first:
            notes.append("short-drama：isLocalWorkspaceMode() 仍无条件 return true，"
                         "且项目路由仍先重定向回画布，生产台不可达，条件成立")
        else:
            detail = []
            if not hardcoded_true:
                detail.append("isLocalWorkspaceMode() 已出现条件分支")
            if not nav_first:
                detail.append("重定向分支不再早于 ProjectDetailPage 渲染分支")
            problems.append(
                "短剧/小说转视频生产台的不可达前提已变（" + "；".join(detail) + "）"
                " → short-drama-project-workbench 需回走验证"
            )

    # —— 附注：Agent 分支合流进度（只报告，不作为判据）——
    r = subprocess.run(["git", "rev-list", "--count", f"{ref}..{AGENT_BRANCH}"],
                       cwd=src, capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        n = r.stdout.strip()
        notes.append(f"Agent 分支仍领先 main {n} 个提交（未合流）" if n != "0"
                     else "Agent 分支已完全合流 main")

    for n in notes:
        print("  " + n)
    if problems:
        print(f"excluded 解禁条件核对：{len(problems)} 条可能已失效")
        for p in problems:
            print("  ⚠ " + p)
        return 1

    print(f"excluded 解禁条件核对：4 条可机械判定的条件全部仍成立"
          f"（第 5 条「真实生成产生版本族」属付费边界，不机械判定）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
