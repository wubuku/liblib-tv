#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST 端点声明核对闸：手册 20-reference.md 列出的端点 vs 上游生产路由注册。

背景（Batch 96）：手册曾把 6 条 `/agent/*` 端点当作现存接口教读者去排查，
但上游根本没注册这些路由——`agent_retired_test.go` 用真实 HTTP 路由图固化了
「旧内置 Agent 已退场」这条边界。**教用户去调一个不存在的接口，比漏写更糟**：
它会让排障方向整体跑偏（以为是部署/网络问题，其实是能力已下线）。

本脚本抽取上游 `origin/main` 的生产路由注册（排除 `_test.go`），与手册声明比对。

注意：后端把路由挂在 `/api` 组下（`backend/internal/bootstrap/runtime.go`），
注册时写的是相对路径，故比对前给手册侧补上 `/api` 前缀。

找不到 BeefTV 源码时静默跳过——手册构建不应依赖同级仓库存在。

退出码：0 一致（或跳过）；1 手册声明了上游没有的端点。
"""

import os
import re
import sys
import subprocess

# 上游仓库候选位置：环境变量优先，其次同级目录
CANDIDATES = [
    os.environ.get("BEEFTV_SRC", ""),
    "/Users/yangjiefeng/Documents/glanderness/BeefTV",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "glanderness", "BeefTV"),
]

# 手册 20-reference.md「仍然存在」表格中声明的端点路径（可写相对 /api 组的形式）
MANUAL_ENDPOINTS = [
    "/tasks",
    "/tasks/:id/cancel",
    "/resources/uploads",
    "/skills/:id/files",
    "/diagnostics/preview",
    "/diagnostics/export",
    "/system/version",
    "/health/live",
    "/health/ready",
    "/health/startup",
]

# 明确标注为「已下线、不要再按这些路径排查」的端点——它们**应当**在生产路由中缺席
RETIRED_ENDPOINTS = [
    "/agent/runs",
    "/agent/runs/:id/events",
    "/agent/runs/:id/messages",
    "/agent/runs/:id/interjections",
    "/agent/runs/:id/cancel",
    "/agent/memories/compact",
]

ROUTE_RE = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH)\("([^"]+)"')


def find_source():
    for c in CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "backend")):
            return os.path.abspath(c)
    return None


def collect_routes(src, ref="origin/main"):
    """从指定 ref 的工作树抽取生产路由（排除 _test.go）。"""
    files = subprocess.run(
        ["git", "ls-tree", "-r", ref, "--name-only"],
        cwd=src, capture_output=True, text=True, check=True,
    ).stdout.split()
    go_files = [
        f for f in files
        if f.startswith("backend/") and f.endswith(".go") and not f.endswith("_test.go")
    ]
    routes = set()
    for f in go_files:
        content = subprocess.run(
            ["git", "show", f"{ref}:{f}"],
            cwd=src, capture_output=True, text=True,
        ).stdout
        for m in ROUTE_RE.finditer(content):
            routes.add(m.group(1))
    return routes


def norm(p):
    """把 :id / {id} 统一成占位符，忽略参数命名差异。"""
    return re.sub(r":[a-zA-Z_]+|\{[^}]+\}", "{id}", p)


def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过端点核对")
        return 0

    try:
        routes = collect_routes(src)
    except subprocess.CalledProcessError as e:
        print(f"[skip] 读取上游源码失败（{e}），跳过端点核对")
        return 0
    if not routes:
        print("[skip] 未抽取到任何生产路由，跳过端点核对")
        return 0

    rn = {norm(r) for r in routes}
    problems = []

    for p in MANUAL_ENDPOINTS:
        if norm(p) not in rn:
            problems.append(f"[声明但上游无] {p}")

    for p in RETIRED_ENDPOINTS:
        if norm(p) in rn:
            problems.append(f"[已下线却又注册了] {p}  ← 手册说它已下线，但上游注册了，需复核")

    if problems:
        print(f"端点核对不一致：上游生产路由 {len(routes)} 条，"
              f"手册声明现存 {len(MANUAL_ENDPOINTS)} 条 / 标注已下线 {len(RETIRED_ENDPOINTS)} 条")
        for x in problems:
            print("  " + x)
        return 1

    print(f"端点核对一致：手册声明现存 {len(MANUAL_ENDPOINTS)} 条全部在生产路由中；"
          f"标注已下线的 {len(RETIRED_ENDPOINTS)} 条确认未注册（上游 {len(routes)} 条生产路由）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
