#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 844：把台账那一行**追加**到 `docs/research/VERIFICATION_LEDGER.md`。

★ 台账的规矩：
  - 行首必须是 `| Batch 844 |`；
  - **竖线总数恰好 4**（未转义 `|` 不算，转义 `\\|` 可用）⟹ 正文里**不能**出现裸竖线；
  - **新行 0 个 U+FFFD**（历史 9 处不动）；
  - **只追加**，不重写历史行。

★ 本脚本**自己**校验这几条 ⟹ 不合格就**不写**（不产生半截行）。
"""
import pathlib
import sys

LEDGER = pathlib.Path(__file__).resolve().parents[4] / "docs" / "research" / "VERIFICATION_LEDGER.md"

ROW = (
    "| Batch 844 | LibTV 导演台·源站对照：**左列第二段「脸部 & 身体特征」**"
    "（H3「纹身 & 疤痕」＋ 6 张 76×54 贴纸卡） | ★ **源站对照 ＋ 实施批次**"
    "（改 `src/components/CharacterEditorPanel.tsx` ＋ `src/components/character-studio.css`，"
    "新增 `scripts/verify-liblib-batch844.py`，**跑过 `npm run build` ＋ `npx tsc --noEmit`**）。"
    "起因：batch 843 做完了妆造页 ⟹ ⟹ 右栏**六枚页签**全部有内容了 ⟹ ⟹ "
    "「**仍未实现的那一块**」变成**左列第二～五段**。"
    "★★ **这一段不是一列控件**（源站**只读**实测，⚡44 全程未变，**只点分段**）："
    "右栏**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）⟹ ⟹ "
    "内容起点比「脸部精修」段**高 48px**（★ 由 batch 841 raw 与 844 raw 的**两个**盒"
    "**机械算出** ⟹ ⟹ 不是手打常数）；H3「纹身 & 疤痕」240×22（**14px／400／纯白** ⟹ ⟹ "
    "与眉眼页的 H3（13px／500／白 30%）**不是**一个样式）；网格 3 列 × 2 行"
    "（列距 6、行距 8）⟹ ⟹ 6 张 **76×54** 的卡，缩略图是 **76×32 的圆形**"
    "（`rounded-full`，白 5% 底 ＋ 白 8% 边）⟹ ⟹ 与妆造页的 76×76 **方形****不一样**；"
    "名字 11px／16px（`px-1`）⟹ ⟹ 「痣」19px／「疤痕_深」47px／「全脸雀斑」52px ⟹ ⟹ "
    "**逐条对上** ⟹ ⟹ 说明两端**用的是同一套字体栈**（都以 `-apple-system` 开头）。"
    "★★ **「自定义」那枚没有 `aria-pressed`**（前 5 张都是 `false`）⟹ ⟹ "
    "它不是可选中的卡，是**上传入口** ⟹ ⟹ clone 也**不给**它那个属性。"
    "★ **缩略图是引用源站 CDN 的真实贴纸图**（★ 与 `VideoGenerationPanel` 同一做法）⟹ ⟹ "
    "那是**引用**不是复刻 ⟹ ⟹ 不声称资产归本仓库所有。"
    "★★ **clone 的实施**：`TRAIT_CARDS` ＋ `traitSel` ＋ `renderTraits()` ＋ "
    "`.ce-panel--seg`／`.ce-h3--section`／`.ce-trait-*` ＋ 右栏分支 ＋ "
    "删掉 `SEGMENT_NOTE` 里 traits 那条（★ 写着「属后续批次」⟹ ⟹ 已是**假陈述**）＋ "
    "把页签行**抽成 `renderTabs()`**（★ 供阴性臂注入**真实**缺陷）。"
    "★★ **验收**：门禁 `scripts/verify-liblib-batch844.py` **7/7**"
    "（S1 这一段不再是空态／S2 **25 项几何逐像素全等**且**比较数 == 期望项数**"
    "（★ 期望项数**独立从 raw 算** ⟹ ⟹ 不拿 geo 自己的长度当分母）／"
    "S3 **130 项外观**逐键比对（★ 期望值取自 raw 的计算样式 ⟹ ⟹ 不硬编码颜色字符串）／"
    "S4 初始选中态逐张对齐源站（连**有没有** `aria-pressed` 都要一样 ＋ 有图/无图逐张相等）／"
    "S5 点「痣」⟹ 它 `aria-pressed=true` 而其余仍 false／"
    "S6 结构事实（这一段页签数 0、切回 6、两段内容起点差 48）／S7 如实标注）；"
    "★ 前置检查盯**服务端下发的 JS chunk** 里的「纹身 & 疤痕」。"
    "★ **阴性对照 7/7**（N1–N7 每条**只**翻它自己那一条 ＋ 逐文件 SHA-256 **字节级复原**；"
    "N1 改名（**同字数** ⟹ 名字盒 47px 不变）⟹ S1；N2 下移 6px ⟹ S2；"
    "N3 圆角 9999px→16px ⟹ S3；N4 初始就选中「痣」⟹ S4；N5 卡的 onClick 失效 ⟹ S5；"
    "N6 页签行跑错段 ⟹ S6；N7 删掉 README 的 mock 标注 ⟹ S7；"
    "★ 全部臂跑完**按 SHA-256 复原**后重跑门禁 ⟹ ⟹ 必须**回到 7/7**）。"
    "★★ **阴性对照逼出两处「字段重叠」**：① N4 同时翻 S3 ⟹ ⟹ 真因是选中态的样式里改了 "
    "`border-color`（**外观判据**读的字段）⟹ ⟹ 修法：选中态**只改 `box-shadow`**；"
    "② N6 同时翻 S1 ⟹ ⟹ 真因是**页签数**被 S1 与 S6 **同时**读 ⟹ ⟹ 修法：**页签数归 S6**。"
    "★ **通用形态**：两条判据读了同一个字段 ⟹ ⟹ 一条缺陷会**同时**翻两条 ⟹ ⟹ "
    "阴性臂就证明不了「**哪一条**有牙」⟹ ⟹ 字段必须**互不重叠**。"
    "★★ **第四次迁移**：840／841／842／843 四道门禁的「未实现的那一段」断言"
    "**从第二段挪到第三段**（身材塑形）⟹ ⟹ 840 的 S3 里的**分段选中态转移**期望值"
    "也一并改成 face → body ⟹ ⟹ 四道**全绿**（840 7/7、841 6/6、842 7/7、843 7/7）。"
    "★ **回归**：844 7/7 ✔；843 7/7 ✔；842 7/7 ✔；841 6/6 ✔；840 7/7 ✔；839 ✔；783 ✔；"
    "827 ✔；826 ✔；838 ✔；835 ✔；62／111／112／113／146b／169 ✔；556／557／536／540／575 ✔；"
    "46／36 ✔；720 ✔；42／43 ✔；736 6/10、748 4/7、749 7/9、782 53/70 为**旧账**"
    "（★ **受控对照**：把本批改的文件**换回 HEAD** 重跑 ⟹ ⟹ 逐条**完全相同** ⟹ ⟹ "
    "本批**未打破**任何一条）。"
    "★ **回归副产物已复原**（`git checkout` 复原，**不带旧批次的产物变更**进本次提交）。"
    "★ `npm run build` ✔、`npx tsc --noEmit` ✔、`npm run assertions:check` ✔"
    "（790 个脚本 **0** 个空断言）；`npm run docs:check` exit=1 ⟹ ★ 25 条断链**全部**在 "
    "`docs/user-manual/`（**他人并发编辑区**）⟹ 本批**零提及**该目录 ⟹ 与本批无关。"
    "★ **不声称**：点贴纸卡会改角色（源站那趟**只点了分段**）；选中态的**外观**与源站一致"
    "（**没点过卡片** ⟹ ⟹ 没测到 ⟹ ⟹ clone 用中性描边）；缩略图资产归本仓库（那是**引用**）；"
    "左列三段（身材塑形／服装造型／音色音调）已复刻 ⟹ ⟹ 显示**空态说明**；"
    "「确认生成」等按钮会真的产出资产（那是 **mock**、**不消耗** ⚡44）；"
    "图标**字形**与源站一致（源站是 iconify SVG ⟹ ⟹ lucide 占位）。 |"
)


def main():
    row = ROW
    problems = []
    if not row.startswith("| Batch 844 |"):
        problems.append("行首不是 `| Batch 844 |`")
    pipes = row.count("|") - row.count("\\|")
    if pipes != 4:
        problems.append("竖线数 = %d（期望 4）" % pipes)
    if row.count("\ufffd"):
        problems.append("含 %d 个 U+FFFD" % row.count("\ufffd"))
    if "REGRESSION_PLACEHOLDER" in row:
        problems.append("回归段还是占位符 ⟹ 先填回归结果")
    if problems:
        print("★ 不合格，不写入：")
        for p in problems:
            print("   ", p)
        return 1
    text = LEDGER.read_text(encoding="utf-8")
    if "| Batch 844 |" in text:
        print("★ 台账里已经有 Batch 844 的行了 ⟹ 不重复追加")
        return 1
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(row + "\n")
    print("已追加：", LEDGER)
    print("行长度：", len(row), "｜ 竖线：", pipes, "｜ U+FFFD：", row.count("\ufffd"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
