#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST 端点声明核对闸：手册 `20-reference.md` 的端点表 vs 上游生产路由注册。

背景（Batch 96）：手册曾把 6 条 `/agent/*` 端点当作现存接口教读者去排查，
但上游根本没注册这些路由——`agent_retired_test.go` 用真实 HTTP 路由图固化了
「旧内置 Agent 已退场」这条边界。**教用户去调一个不存在的接口，比漏写更糟**：
它会让排障方向整体跑偏（以为是部署/网络问题，其实是能力已下线）。

本脚本抽取上游 `origin/main` 的生产路由注册（排除 `_test.go`），与手册声明比对。

## Batch 165：判据从「誊抄副本」改成「手册正文」

本闸此前把手册声明的端点**誊抄成脚本里的两张硬编码表**（`MANUAL_ENDPOINTS` 10 条、
`RETIRED_ENDPOINTS` 6 条），而**从不读 `20-reference.md`**。实测后果：

- 手册三张表一共声明 **28 条**端点，闸门只核对 **16 条**，**12 条从未被看守**；
- 其中「已下线」表里的跨产品导入 `.../import/libtv` 与 `.../import/tapnow`
  **手册用删除线断言已下线，闸门却完全不知道它们的存在**——
  上游哪天把它们注册回来，闸门一声不吭，而手册还在教读者别去查；
- 第三张表（v1.6.14 新增）的 **8 条全部未被看守**，含任务日志、原任务查询、任务重试、
  时间线渲染与转写、深度捕捉这几条确有注册的生产路由。

**根因与 Batch 164 完全同源**：判据锚的是「某一份文件的样子」（脚本里的副本），
不是事实（手册正文）。**誊抄副本一定会漂移，而没有任何机制会告诉你它漂了。**

现在改成**手册正文即唯一真值**：闸门运行时解析 `20-reference.md` 的三张表，
逐条与上游比对，正文改了就自动跟着变。

## 两个方向都核，名副其实的「双向」

- **仍然存在 / v1.6.14 新增**：每条**必须**在上游注册（末尾 `/*` 按前缀判）；
- **已下线**：每条**必须不在**上游注册（末尾 `/*` 则该前缀下**一条都不该有**）。

## 查不了必须报「未能核对」，不能报「一致」

三处会让人以为「检查过了」的地方，一律 `return 2`（沿用 Batch 160 的三段退出码）：

1. 找不到 BeefTV 源码；
2. `20-reference.md` 读不到，或三张表的**小节锚点任一缺失**；
3. **任一张表解析出 0 条路径**——解析器退化了（分隔符改了、表格搬走了），
   此时若照常比对就会得出「0 条不一致 → 全部通过」。
   **这正是 Batch 157 的「工具失败被当成零命中」**，此处显式堵死。

退出码：0 三张表全部一致；1 有端点与上游不符；2 未能核对。
"""

import os
import re
import sys
import subprocess
from baseline import resolve_ref, BaselineError
from batchread import read_many

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 上游仓库候选位置：环境变量优先，其次同级目录
CANDIDATES = [
    os.environ.get("BEEFTV_SRC", ""),
    "/Users/yangjiefeng/Documents/glanderness/BeefTV",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "glanderness", "BeefTV"),
]

REFERENCE_REL = "20-reference.md"

# 小节锚点。**三张表全都要找到**——缺任何一个都判「未能核对」，
# 而不是「那张表为空所以没问题」。
SECTION_ANCHORS = [
    ("仍然存在", "**仍然存在：**", "### 已下线端点"),
    ("已下线", "### 已下线端点", "### v1.6.14 运行时核对新增"),
    ("v1.6.14 新增", "### v1.6.14 运行时核对新增", "## 本地伴随进程"),
]

# 不经过本后端的路径：连前缀匹配都不适用，必须显式豁免并写明理由。
# **豁免表只增不减会变成谁都不敢碰的清单**，所以每条都要写清为什么。
NON_BACKEND = {
    "/runtime/session/*": "本地伴随进程的会话端点，强制 127.0.0.1:17371 精确回环，"
                          "由独立进程提供、不经过本后端（本闸抽的是后端路由注册）",
    "/api/plugins/eagle/*": "注册写作 `pluginRoutes := r.Group(\"/plugins\")` + "
                            "`pluginRoutes.GET(\"/eagle/library\", …)`，**路径分两处**。"
                            "本闸抽取的是第二个参数（组内相对路径），"
                            "**拿不到组前缀**，故前缀匹配必然落空——"
                            "如实豁免，不假装能判。要判它得解析 Group 链，"
                            "那会让抽取逻辑复杂到不值得（本条已由 Batch 96 的证据链单独覆盖）",
}

ROUTE_RE = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH)\("([^"]+)"')

# 反引号内的端点令牌。**方法与路径分开捕获**——
# Batch 165 的探针曾用 `"/api/x".partition(" ")`，而它在**没有空格**时
# 返回 `(整串, "", "")`，路径变成空串；接着 `str.endswith("")` 恒为真，
# 于是「空的已下线端点」匹配上了全部 135 条路由，量出「上游居然有」。
# 两处都是一次性的测量脚本犯的，但结论当时差点据此写错，故在此钉死。
TOKEN_RE = re.compile(r"`\s*(?:(GET|POST|PUT|DELETE|PATCH|GET/POST)\s+)?(/[^`\s]+)`")

METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "GET/POST"}


def find_source():
    for c in CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "backend")):
            return os.path.abspath(c)
    return None


def collect_routes(src, ref=None):
    """从指定 ref 抽取生产路由（排除 _test.go）。

    ref=None → 由 baseline.resolve_ref() 按手册声明的基线解析。
    """
    if ref is None:
        ref = resolve_ref()
    files = subprocess.run(
        ["git", "ls-tree", "-r", ref, "--name-only"],
        cwd=src, capture_output=True, text=True, check=True,
    ).stdout.split()
    go_files = [
        f for f in files
        if f.startswith("backend/") and f.endswith(".go") and not f.endswith("_test.go")
    ]
    # **Batch 181 改**：原先每个 go 文件一次 `git show` 子进程
    #（实测 347 个 × 25ms ≈ 9 秒，闸门本体 10 秒、反验 7 例 43 秒）。
    # 改成 batchread.read_many：**两次进程调用取代 347 次**，
    # 实测 0.19 秒且与逐个 `git show` **逐字节一致**。
    # **只改读取方式，不改判据逻辑**——`norm()` / `strip_api()` 之后一步没动。
    routes = set()
    for _f, body in read_many(src, ref, go_files).items():
        for m in ROUTE_RE.finditer(body.decode("utf-8", "replace")):
            routes.add(m.group(1))
    return routes


def norm(p):
    """把 :id / {id} 统一成占位符，忽略参数命名差异。"""
    return re.sub(r":[a-zA-Z_]+|\{[^}]+\}", "{id}", p)


def strip_api(p):
    """手册第一张表省略了 /api 前缀（页首已注明），第三张表却带着——比对前统一剥掉。"""
    return p[4:] if p.startswith("/api/") else p


def parse_tables(ref_text):
    """解析三张端点表。返回 (tables, error)；error 非 None 表示**未能核对**。

    tables[name] = [(method, path)]，路径已按 `·` 拆成独立条目
    （`/api/tasks/:id/text-deltas·text-events·text-replay-complete` 是三个端点，
    不是端点名里带个中点）。
    """
    tables = {}
    for name, start, end in SECTION_ANCHORS:
        if start not in ref_text or end not in ref_text:
            return None, f"20-reference.md 缺少小节锚点（{name}：需要 {start!r} 与 {end!r}）"
        body = ref_text.split(start, 1)[1].split(end, 1)[0]
        rows = []
        for line in body.split("\n"):
            s = line.strip()
            if not s.startswith("|"):
                continue
            # 转义竖线先换占位符，否则 `a \| b` 会被当成两个单元格
            safe = s.replace("\\|", "\x00")
            cells = [c.strip() for c in safe.split("|")
                     if c.strip() and not set(c.strip()) <= set("-: ")]
            if not cells:
                continue
            for m in TOKEN_RE.finditer(cells[0].replace("\x00", "\\|")):
                method = m.group(1) or ""
                # 单元格里的 `·` 是**端点分隔符**，不是路径的一部分：
                # `/api/tasks/:id/text-deltas·text-events` 是两个端点。
                for piece in m.group(2).split("·"):
                    piece = piece.strip()
                    if piece.startswith("/"):
                        rows.append((method if method in METHODS else "", piece))
        tables[name] = rows

    empty = [n for n, rows in tables.items() if not rows]
    if empty:
        return None, (f"以下小节解析出 0 条端点：{', '.join(empty)}——"
                      f"解析器很可能已退化（分隔符/表格结构变了），"
                      f"此时若照常比对就会得出「0 条不一致 → 全部通过」，故本轮判未能核对")
    return tables, None


def prefix_of(p):
    """末尾 `/*` 的前缀；非通配返回 None。"""
    return p[:-2] if p.endswith("/*") else None


def exempt_reason(path):
    """命中豁免表则返回理由，否则返回 None。**没有理由就不能豁免。**"""
    for exempt, why in NON_BACKEND.items():
        if path == exempt or path.rstrip("*") == exempt.rstrip("*"):
            return why
    return None


def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过端点核对")
        return 2

    ref_path = os.path.join(ROOT, REFERENCE_REL)
    if not os.path.isfile(ref_path):
        print(f"[skip] 未找到 {REFERENCE_REL}，端点声明核对本轮未能进行")
        return 2
    ref_text = open(ref_path, encoding="utf-8").read()
    tables, err = parse_tables(ref_text)
    if err:
        print(f"[skip] {err}")
        return 2

    try:
        routes = collect_routes(src)
    except subprocess.CalledProcessError as e:
        print(f"[skip] 读取上游源码失败（{e}），跳过端点核对")
        return 2
    if not routes:
        print("[skip] 未抽取到任何生产路由，跳过端点核对")
        return 2

    rn = {norm(r) for r in routes}
    problems = []
    checked = 0
    skipped = []

    def exists(path):
        """手册侧剥掉 /api 前缀后，是否能在上游注册里找到。"""
        key = norm(strip_api(path))
        if key in rn:
            return True
        pre = prefix_of(key)
        if pre is not None:
            return any(x.startswith(pre) for x in rn)
        return any(x.endswith(key) for x in rn)

    for name, rows in tables.items():
        want_absent = name == "已下线"
        for method, path in rows:
            exempt = exempt_reason(path)
            if exempt:
                skipped.append(f"{path}（{exempt}）")
                continue
            hit = exists(path)
            if hit == want_absent:
                verb = "已下线却在生产路由里注册了" if want_absent else "声明存在但上游没有注册"
                problems.append(f"[{name}] {method + ' ' if method else ''}{path} —— {verb}")
            checked += 1

    if problems:
        print(f"端点核对不一致：上游生产路由 {len(routes)} 条，"
              f"手册声明 {sum(len(v) for v in tables.values())} 条（实际核对 {checked} 条）")
        for x in problems:
            print("  " + x)
        return 1

    total = sum(len(v) for v in tables.values())
    print(f"端点核对一致：手册 {len(tables)} 张表共 {total} 条端点全部与上游相符"
          f"（现有 {len(tables['仍然存在']) + len(tables['v1.6.14 新增'])} 条须已注册 / "
          f"已下线 {len(tables['已下线'])} 条确认未注册；上游 {len(routes)} 条生产路由）")
    for s in skipped:
        print(f"  · 豁免：{s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
