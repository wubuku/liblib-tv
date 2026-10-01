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
#
# M105 订正一处豁免：**SOURCE_OBSERVATIONS.md 从这里移出**。前三个文件是「订正史」
# 载体，必须逐字保留旧说法；它不同——它记的是**当前事实**，出现已订正说法永远是缺陷
# （实测：它的 §2 还停在订正前的「新项目默认标题 TDCanvas 2、编号规则待查」，
#  而该条早在 AUDIT 里订正为「TDCanvas 1、编号全局递增」，手册正文也早已同步）。
# §11 的 i18n 取证纪律属于方法论、不复述被撤回的原句，故不产生假阳性。
EXCLUDED = {"AUDIT.md", "PROGRESS.md", "TEST_MEDIA_ASSETS.md", "PUBLISH.md"}

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
        "id": "R15",
        "wrong": "| 待配置 | 还没提交，节点停在准备状态 |",
        "why": "**M71 的订正方向反了，M85 撤回**。「待配置」等八个中文状态名取自 i18n `canvas.aitudou.status`，而该组文案**从未被任何组件引用**（穷尽 web/src 搜索，`canvas.aitudou.*` 只有 `nodeTypes.aitudou` 被用上）。真正渲染任务阶段的是 `aitudou-native-generation-panel.tsx:513` 的 `TaskStatus`，输出 `{taskPhase}` 原始英文枚举，且**仅在 taskId 存在时渲染**——未提交时页面上没有任何状态徽标。2026-10-01 运行时实测：八个词各出现 0 次",
        "fixed_in": "M85",
    },
    {
        "id": "R16",
        "wrong": "| **已排队** / **处理中** | 任务已提交，正在执行 |",
        "why": "同 R15：界面渲染的是英文 `queued` / `running`，不是中文",
        "fixed_in": "M85",
    },
    {
        "id": "R17",
        "wrong": "| **已完成** | 结果已写入节点 |",
        "why": "同 R15：界面渲染的是英文 `succeeded`",
        "fixed_in": "M85",
    },
    {
        "id": "R18",
        "wrong": "| **部分完成** | 批量中部分失败 |",
        "why": "同 R15：界面渲染的是英文 `partial`",
        "fixed_in": "M85",
    },
    {
        "id": "R19",
        "wrong": "这八个状态名取自 i18n `canvas.aitudou.status`",
        "why": "同 R15：M71 把它当成「界面逐条原文」，实际是死文案。M85 已改写为区分「节点内状态（生成中/生成失败，i18n 有调用点）」与「面板标题行的英文阶段徽标（源码 TaskStatus）」两套",
        "fixed_in": "M85",
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
    {
        "id": "R20",
        "wrong": "用悬浮工具条开启「自由缩放」",
        "why": "「自由缩放」在 zh-CN.ts 的 1821 条字符串值与全部源码中各出现 0 次，界面按钮的真名是「锁比例」（关）/「自由比例」（开）；且该按钮 `defaultVisible: false`，默认根本不在工具条上，必须先经「更多 → 自定义工具栏」勾出来才能点。手册同一页第 16 行的对照表实测写着 13 个按钮、末位是「更多」，与这一句自相矛盾（2026-10-01 M93 i18n 语料 + 运行时双重复现）",
        "fixed_in": "M93",
    },
    {
        "id": "R22",
        "wrong": "方向拖反时连线数确实增加",
        "why": "M98 曾把「把 output 拖到另一个节点的 output 端口、连线数确实增加」记成一条待查的观察。M99 查实：那是**读到了陈旧的应用计数**（离开画布再回来读时，写盘尚未落定），实际该操作**被拒**。源码 `canvas-node-ports.ts` 的 normalizeConnectionHandles 第一句就是两个 handle 同向即返回空，运行时实测 output→output 与 input→input 均 0→0 被拒（2026-10-01 M99）",
        "fixed_in": "M99",
    },
    {
        "id": "R21",
        "wrong": "时长可选 4-8 秒，分辨率 480p / 720p / 1080p 自动匹配",
        "why": "视频面板参数行运行时实测为「4~15 秒 · 480p/720p/1080p/2k/4k/native1080p/native4k · 比例 7 档」。漏掉的 native1080p / native4k 正是价格区间 ¥2.48–5.37 的上下两端，照旧参数算账等于把最贵一档当不存在。M66 / M82 早已在 20-reference 对照表与 manifest 另一条记录写下正确值，只有 generate-images 的本节没跟着改（2026-10-01 M93）",
        "fixed_in": "M93",
    },
    {
        "id": "R23",
        "wrong": "命中区 43×43",
        "why": "M84 记录的这个数字是**带着画布缩放量的一次性读数**。端口命中区在源码里是写死的 `size-12`（48×48），2026-10-02 M107 在 100% 缩放下实测 `getBoundingClientRect()` 为 48×48——43/48≈0.896，正是当时画布处于非 100% 缩放造成的缩水。写死一个像素数会随读者当前缩放而失效，且与源码对不上（2026-10-02 M107）",
        "fixed_in": "M107",
    },
    {
        "id": "R24",
        "wrong": "而顶栏高 48px、工具条高 48px",
        "why": "M31 记录的这两个高度在当前版本都对不上。顶栏源码是写死的 h-14 = 56px，2026-10-02 M108 运行时实测顶栏 y=0、高 56；节点上方有两条不同浮层，实测高分别约 27px（节点名那一条，top:-40px）与 32px（h-8，top:-39px），**都不是 48px**。初版疑似把顶栏高度当成了工具条高度。同一句里的按钮纵坐标 −42 也没注明所属坐标系：该偏移是画布世界单位常量（实测恒为 −40），会随缩放放大到屏幕，42/40 = 1.05 对应约 105% 缩放（2026-10-02 M108）",
        "fixed_in": "M108",
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
