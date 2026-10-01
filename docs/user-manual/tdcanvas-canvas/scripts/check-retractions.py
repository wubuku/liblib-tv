#!/usr/bin/env python3
"""订正回归门禁：已经订正过的错误说法，不许在正文里重新出现。

背景（M52 踩坑）：M47 订正「导出 zip 可以恢复画布」这处硬伤时，只改了审计
点名的 3 个文件，漏掉了另外 2 处重复同样错误说法的地方（undo-persistence、
30-concepts）。**改一处事实错误的风险不在于改错，而在于漏改。**

本脚本把每一次订正登记成一条"撤回记录"（错误原句 + 为什么错 + 在哪一批改的），
然后扫描正文，确认这些原句没有重新长出来。

它只覆盖**已登记的订正**，不检查手册里尚未发现的错误——这一点写在下面，
不要把它当成"手册没有矛盾了"的证明。新发现的错误应当先登记进 RETRACTIONS，
再改正文。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 内部账本与分析性记录不扫：它们本来就要原样记下"曾经写错过什么"。
EXCLUDED = {"AUDIT.md", "PROGRESS.md", "SOURCE_OBSERVATIONS.md", "TEST_MEDIA_ASSETS.md", "PUBLISH.md"}

# 用白名单而不是 rglob：手稿目录下有 node_modules 与构建产物，
# rglob 会把 137 个第三方文档一起扫进来，制造假阳性。与 check-claims.py 保持一致。
BODY_PAGES = ["README.md", "00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"]
BODY_GLOBS = ["10-tasks/*.md"]

RETRACTIONS: list[dict[str, str]] = [
    {
        "id": "R11",
        "wrong": "| 排队中 / 生成中 |",
        "why": "任务状态名取自 i18n canvas.aitudou.status 的逐条原文，界面写的是「已排队 / 处理中」，不是「排队中 / 生成中」；读者在节点上找「排队中」找不到（2026-10-01 M71 对拍 zh-CN.ts:651）",
        "fixed_in": "M71",
    },
    {
        "id": "R12",
        "wrong": "| 完成 | 结果写入节点",
        "why": "同 R11，界面写「已完成」",
        "fixed_in": "M71",
    },
    {
        "id": "R13",
        "wrong": "| 部分成功 | 批量中部分失败",
        "why": "同 R11，界面写「部分完成」；且状态表还漏了初始态「待配置」",
        "fixed_in": "M71",
    },
    {
        "id": "R14",
        "wrong": "节点显示「部分成功」",
        "why": "同 R13，90-troubleshooting 的症状描述里也是旧名",
        "fixed_in": "M71",
    },
    {
        "id": "R1",
        "wrong": "导出是唯一能带走项目的方式",
        "why": "画布 zip 没有导入功能，带不走项目（2026-10-01 三重取证：i18n 三条文案零引用、首页无文件选择器、喂给导入资产报格式错）",
        "fixed_in": "M47",
    },
    {
        "id": "R2",
        "wrong": "可以整体拷到另一台机器导入",
        "why": "同 R1，画布侧只实现了导出、从未实现读回",
        "fixed_in": "M47",
    },
    {
        "id": "R3",
        "wrong": "真正的兜底是定期导出项目 zip",
        "why": "同 R1，导出 zip 救不回画布结构，保不住这个兜底",
        "fixed_in": "M47",
    },
    {
        "id": "R4",
        "wrong": "用「导入资产」恢复其中的资产",
        "why": "readAssetPackage 硬要求 assets.json，画布 zip 里是 projects.json，实测报「导入失败，请选择有效的资产压缩包」",
        "fixed_in": "M47",
    },
    {
        "id": "R5",
        "wrong": "但换机仍只能靠导出 zip",
        "why": "同 R1，换机带不走画布",
        "fixed_in": "M47",
    },
    {
        "id": "R6",
        "wrong": "项目支持导出 zip 备份",
        "why": "同 R1。M47 漏改了 30-concepts 这一处，M52 才发现",
        "fixed_in": "M47",
    },
    {
        "id": "R7",
        "wrong": "用首页的批量导出得到 zip",
        "why": "同 R1。M47 漏改了 undo-persistence 这一处，M52 才发现",
        "fixed_in": "M52",
    },
    {
        "id": "R8",
        "wrong": "与弹窗逐字一致",
        "why": "弹窗 13 行与表格有四处出入；手册自己的截图就证伪了这张表（2026-10-01 实测对拍）",
        "fixed_in": "M44",
    },
    {
        "id": "R9",
        "wrong": "切换后功能完全一致",
        "why": "该节五项全是文案与布局的静态比对，没有一项验证「功能」，标题超出证据范围",
        "fixed_in": "M45",
    },
    {
        "id": "R10",
        "wrong": "均为项目级设置",
        "why": "主题模式其实是全局设置（localStorage:tdcanvas:theme_store），切浅色后 6 条路由全部生效",
        "fixed_in": "M39",
    },
]


def iter_body_pages(root: Path):
    for name in BODY_PAGES:
        path = root / name
        if path.is_file():
            yield path
    for pattern in BODY_GLOBS:
        yield from sorted(root.glob(pattern))


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    pages = list(iter_body_pages(root))
    if not pages:
        print("[FAIL] 没有扫到任何正文页，检查传入的路径")
        return 1

    problems: list[str] = []
    checked = 0

    for item in RETRACTIONS:
        needle = item["wrong"]
        hits: list[str] = []
        for page in pages:
            for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
                if needle in line:
                    hits.append(f"{page.relative_to(root)}:{lineno}")
        checked += 1
        if hits:
            problems.append(f"[{item['id']}] 订正过的错误说法重新出现：{needle!r}\n      {item['why']}\n      出现在：{', '.join(hits)}")

    print(f"[retractions] 已登记订正 {len(RETRACTIONS)} 条，扫描正文 {len(pages)} 页")

    if problems:
        print("[FAIL] 订正回归检查失败：")
        for p in problems:
            print("  " + p)
        print()
        print("  提示：确认这处说法是否在新内容里被无意识地复述。")
        print("        如果是刻意保留（例如作为反例引述），请改写措辞，不要原样照抄。")
        return 1

    print(f"[ ok ] 订正回归：{checked} 条已订正的错误说法均未在正文复现")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
