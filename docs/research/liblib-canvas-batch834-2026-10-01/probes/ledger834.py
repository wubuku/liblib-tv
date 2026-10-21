#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：把台账那一行**追加**到 `docs/research/VERIFICATION_LEDGER.md`。

★ 台账的规矩：
  - 行首必须是 `| Batch 834 |`；
  - **竖线总数恰好 4**（未转义 `|` 不算，转义 `\\|` 可用）⟹ 正文里**不能**出现裸竖线；
  - **新行 0 个 U+FFFD**（历史 9 处不动）；
  - **只追加**，不重写历史行。

★ 本脚本**自己**校验这三条 ⟹ 不合格就**不写**（不产生半截行）。
"""
import pathlib
import sys

LEDGER = pathlib.Path(__file__).resolve().parents[4] / "docs" / "research" / "VERIFICATION_LEDGER.md"

ROW = (
    "| Batch 834 | LibTV 导演台·源站对照：**时间轴引导气泡补齐 5 步**（源站 chunk 原文照抄 ＋ 定位算法照抄）"
    "＋ 抓出一个真缺陷（`z-[1900]` 在冻结的 Tailwind 扫描下不生成 ⟹ 引导按钮点不动） | ★ **实施批次**"
    "（新增 `src/components/director/DirectorTimelineGuide.tsx` ＋ 改 `DirectorTimeline.tsx`／"
    "`DirectorDesk.tsx`／`scripts/verify-liblib-batch556.py` 的文件头、**跑过 `npm run build`**）。"
    "起因：batch 556 只做了引导的**第 1 步**、batch 831 记下「源站是 5 步、步骤 2–5 **未采样**」。"
    "★★ **源站的 5 步一次采全**（活体 ＋ chunk 原文**两路交叉核对**）："
    "步 1 add-track「请选择一个角色或者摄像机后，可新建轨道」1/5 宽 260 偏移 -80 高 112 按钮 跳过／下一步；"
    "步 2 draw-trajectory「点击创建路径，弹出选项面板」2/5 宽 300 偏移 -64 高 112；"
    "步 3 motion-preset-ring「点击圆环/直线/矩形创建路径，或用铅笔/钢笔工具绘制想要路径」3/5 宽 360 偏移 -48 高 136；"
    "步 4 play「路径绘制后点击播放，可预览动画」4/5 宽 300 偏移 12 高 112；"
    "步 5 export-to-canvas「预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑」"
    "5/5 宽 360 偏移 -268 高 112 按钮 跳过／**完成** ⟹ ★★ **每步宽度都不同** ⟹ 气泡不是固定宽；"
    "★ 第 5 步那枚按钮是**另一个词**（chunk 原文 `4===e?…GuideComplete:…GuideNext`）。"
    "★★ **定位算法照抄**（chunk 原文）：target ＝ 「export-to-canvas」用 ref，否则按 "
    "`data-director-timeline-guide-target` 查 ⟹ 取不到时**兜底**（motion-preset-ring → draw-trajectory → add-track）；"
    "icon ＝ target 里 `data-director-timeline-guide-icon=\"true\"` 的那个；width ＝ min(步宽, 视口-24)；"
    "left ＝ clamp(图标中心 x ＋ bubbleOffsetX, 12, 视口-width-12)；top ＝ 目标顶 - 气泡高 - 2，"
    "不足 12 则改成目标底 + 14；ring ＝ 以图标中心为心的 60×60 盒子（里一枚 24×24 的涟漪圆）。"
    "★★ **状态机照抄**（chunk 原文）：「下一步」逐步推进（第 4 步会**开始播放**）；末步按钮是「完成」；"
    "自动推进（浮层开/关、开始播放）；收起标记 ＝ localStorage `libtv.director.timeline-guide.dismissed.v1`。"
    "★★ **第一版探针为什么「找不到引导」（本批最值得记的一处）**：源站引导**锚在时间轴上**，"
    "而**源站时间轴默认收起** ⟹ 引导根本没机会出现 ⟹ 全页零命中 ⟹ 一度以为源站没有引导 ⟹ "
    "★ 破局靠**换读法**而不是再试一次：`probes/diag834b.py` 拍「可见元素签名表」的**集合差** ⟹ "
    "点「动画时间轴」那一刻页面**多出两枚** `h-7 rounded-lg bg-transparent px-3`／`bg-white/10` 的按钮 ⟹ ⟹ 引导就在那儿 "
    "⟹ ★ 与已存记忆同族：「选择器在源站不存在 ⇒ 那个动作根本没发生」的变体是"
    "「**目标不在 DOM 里 ⇒ 那个东西还没被触发**」⟹ 先问「触发条件满足了吗」再问「读数器写对了吗」。"
    "★★★ **本批抓到的真缺陷**：源站用 Tailwind 任意值类 `z-[1900]` 给引导浮层定层叠，"
    "而 **4317 的 Tailwind 扫描是冻结的**（batch 824）⟹ **新增**任意值类在 dev 上**不生成** ⟹ "
    "z-index 落回 auto ⟹ 整块引导被时间轴 section 的 z-30 盖住 ⟹ ★★ **「下一步」按钮点不动**"
    "（探针的命中测试被时间轴的横向滚动容器截走）⟹ 修法：覆盖层／气泡／光环的 z-index **全走 inline style**"
    "（1900／1／2）⟹ 修完 5 步**都能真点**（探针从「必须 JS 直点」变成「5/5 真点击成功」）⟹ "
    "门禁 S12 把这条钉住（且**只在 className 属性里**找 `z-[` ⟹ 注释里提到不算数："
    "第一版判据全文搜、命中了**自己写的注释** ⟹ 恒红）。★ **clone 的实施**："
    "新增 `DirectorTimelineGuide.tsx`（数据 ＋ 算法 ＋ 类名照抄）⟹ 时间轴换成新组件 ＋ 加步序状态机 ＋ "
    "给 4 枚常驻目标挂 `data-director-timeline-guide-target` ⟹ 「导出视频到画布」按钮挂 target ＋ 1px 图标锚点；"
    "★ **旧属性名保留为别名**（`data-director-timeline-coachmark`／`data-director-coachmark-skip`／"
    "`data-director-coachmark-next`）⟹ 门禁 556／557 仍能定位；★ **收起标记沿用 clone 自己的键** "
    "`director-timeline-coach-dismissed`（源站的键是 `libtv.director.timeline-guide.dismissed.v1`）⟹ "
    "★ 因为门禁 36／575 **直接断言那个键名** ⟹ 改键名会让那两条门禁失效。"
    "★ **验收**：门禁 `scripts/verify-liblib-batch834.py` **主检查 14/14 ｜ 阴性对照 15/15**"
    "（每条阴性**只**翻它自己那一条；期望值从 raw 读、**不手打**；raw 由 `probes/mk834raw.py` 从"
    "**活体 ＋ chunk 原文**两路交叉核对产出，不一致就**拒绝出 raw**）★ **真实注入自检**"
    "（`probes/inject834.py`）：往组件注入一个错字 ⟹ **只有 S2 翻红** ⟹ 按字节复原。"
    "★ 最有分量的判据是 **S6**：判「**渲染出来的气泡位置** == **按源站 chunk 原文的算法重算出来的位置**」"
    "（5 步全对）⟹ 判的是「**算法被照抄了**」而不是「某个绝对坐标碰巧对」⟹ 也正因如此**不**直接比绝对坐标"
    "（源站采集时场景里有相机轨道、clone 默认没有 ⟹ 源站算法会**兜底**到 add-track ⟹ 那是**场景状态不同**）。"
    "★ **更正旧合同**：`scripts/verify-liblib-batch556.py` 的文件头原话「Steps 2-5 are unsampled, so both "
    "actions dismiss the coachmark」**已过时** ⟹ ★ **只更正文件头的背景说明、断言一个字未改**"
    "（跳过→收起、重载后仍收起、第 1 步文案与 1/5 全部仍成立）⟹ 门禁保持绿灯 ⟹ "
    "★ **旧批次 README 不重写**（前缀/后缀式文档不可重写）⟹ 更正写在本行与本批 README。"
    "★ **回归**：门禁 556 **8/8**、557 **5/5**、36 ✔、575 **4/4**、536 **27/27**、540 **10/10**、"
    "649 ✔、650 ✔、652 ✔、656 ✔、657 ✔ —— **全绿**。"
    "★★ **红的逐条归因**（★ 不能只看「红」就当本批的锅）："
    "**748 = 4/7**（C1／C3／C4 红）⟹ ★ **把本批改过的三个文件按 sha256 备份后换回 HEAD（batch 833）版本、"
    "在旧版本上跑同一条门禁**（`probes/attrib834b.py`，**不用 stash、不用 worktree**，复原时逐个复核 sha256）"
    "⟹ **HEAD 上同样是 4/7、同样是 C1／C3／C4 三条红**（静态并集 HEAD 460／461／476 vs 本批 468／469／488；"
    "C4 的 zeroGain 同样是 1 枚 scene）⟹ ★★ **既有旧账、非本批引入**。"
    "★ 但要说清：**旧账归旧账，本批确实把静态并集推得更远** ⟹ 748 的期望值**连着三个批次**"
    "（831 的 help 面板、832 的机位预设面板、本批的引导）都不再对得上 ⟹ 需**单独一批**按新事实更新 ⟹ 本批**不动**它。"
    "**749 = 7/9** ⟹ 换回 HEAD 同样 7/9、C9 数字同为 447 ⟹ 非本批引入。"
    "**750／751** 探针 exit=2（`/tmp/dbg750e.py` 等旧批次探针脚本已不在本机）⟹ 环境性；"
    "**758／759** 需要 `/tmp/vb758*.json`（不在本机）⟹ 环境性。"
    "★ 回归跑出的**副产物**（5 张 batch36 截图 ＋ 649/650/652/656/657/748/749 的 runtime-audit.json ＋ "
    "758/759 的 verify-report.json）**一律 `git checkout --` 复原、不提交**（沿用 832／833 先例）。"
    "★ **不声称**：源站 `onNext` 的**条件式收起**（没画出轨迹就直接收起）在 clone 里**没有照抄**"
    "（clone 的「下一步」无条件推进 ⟹ **有意**简化，不声称同构）；源站第 3 步会**真的套用圆环预设**、"
    "第 5 步会**真的点导出**，clone 的「完成」只是收起 ⟹ 不声称动作链一致；源站的收起标记写在"
    "**第 3 步的 120ms 定时器**里、clone 写在**收起时** ⟹ 时机不同；源站还要求「**有目标上下文**」才启动"
    "（chunk 里的 `!eF` 守卫）、clone 只要没被标记看过就启动 ⟹ 不声称一致；chunk 里那个 `nY.C()` 守卫**没读**；"
    "文案的 i18n 键在 clone 里换成**中文硬编码** ⟹ 不声称 i18n 机制一致；窄屏（<899px）形态**未测**。"
    "★ **源站采集只能跑一次**：走完第 5 步「完成」后，那个帐号的引导就被标记成「看过」了 ⟹ 再跑探针会找不到 ⟹ "
    "★ 所以期望值**必须已经入库**（raw ＋ 门禁），而不是「留个探针以后再跑」。 |"
)


def main():
    row = ROW
    problems = []
    if not row.startswith("| Batch 834 |"):
        problems.append("行首不是 `| Batch 834 |`")
    pipes = row.count("|") - row.count("\\|")
    if pipes != 4:
        problems.append("竖线数 = %d（期望 4）" % pipes)
    if row.count("�"):
        problems.append("含 %d 个 U+FFFD" % row.count("�"))
    if "REGRESSION_PLACEHOLDER" in row:
        problems.append("回归段还是占位符 ⟹ 先填回归结果")
    if problems:
        print("★ 不合格，不写入：")
        for p in problems:
            print("   ", p)
        return 1
    text = LEDGER.read_text(encoding="utf-8")
    if "| Batch 834 |" in text:
        print("★ 台账里已经有 Batch 834 的行了 ⟹ 不重复追加")
        return 1
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(row + "\n")
    print("已追加：", LEDGER)
    print("行长度：", len(row), "｜ 竖线：", pipes, "｜ U+FFFD：", row.count("�"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
