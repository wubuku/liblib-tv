#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838：把台账那一行**追加**到 `docs/research/VERIFICATION_LEDGER.md`。

★ 台账的规矩：
  - 行首必须是 `| Batch 838 |`；
  - **竖线总数恰好 4**（未转义 `|` 不算，转义 `\\|` 可用）⟹ 正文里**不能**出现裸竖线；
  - **新行 0 个 U+FFFD**（历史 9 处不动）；
  - **只追加**，不重写历史行。

★ 本脚本**自己**校验这三条 ⟹ 不合格就**不写**（不产生半截行）。
"""
import pathlib
import sys

LEDGER = pathlib.Path(__file__).resolve().parents[4] / "docs" / "research" / "VERIFICATION_LEDGER.md"

ROW = (
    "| Batch 838 | LibTV 导演台·源站对照：**把默认角色名改成源站口径「角色A」，"
    "并更正 batch 837 的一条结论** | ★ **源站对照 ＋ 实施批次**"
    "（改 `src/store/directorStore.ts` 的种子角色名，"
    "**跑过 `npm run build` ＋ `npx tsc --noEmit`**）。"
    "起因：batch 837 的 README 里写着「源站画布上真实显示的镜头名是『**S83·镜2**』⟹ 源站用的是另一套命名体系」。"
    "★★★ **本批把那条结论查穿了**：权威数据（`api/canvas/project/detail-by-space` 的响应）里，"
    "那个「S83·镜2」是一个 **video 节点**的标题，而它的 `alt` 字段是「**S83·镜2.mp4**」⟹ "
    "★ **它是用户上传的 mp4 文件名**（`action` 是 `video_resource`、`uploaded` 为真、"
    "画布上它是 `react-flow__node-video` 节点 232×133 的标题 ＋ 「864 × 496」尺寸标注）⟹ "
    "★ **不是**任何系统命名规则 ⟹ ★★ **batch 837 那句「源站用 S83·镜2 体系」不成立** ⟹ 本批更正"
    "（旧批次 README 不可重写 ⟹ 更正写在本批 README ＋ 台账）。"
    "★★ **顺带查清第二件事：源站根本没有「镜头」实体** —— 导演台权威数据 `compositionData` 的顶层只有 "
    "characters／characterGroups／cameras／props／animation／environment（**没有 `shots`**），"
    "`animation` 的子键是 version／duration／motionPaths／characterTracks／propTracks／"
    "cameraTracks／groupTracks／activeCameraTrackId（**也没有任何 shot 类键**）⟹ "
    "⟹ ★★ clone 的 `shots[]` 是**借自 StoryAI 上游**的分层设计（batch 96 的 PLAN.md 自己就写明"
    "「只借鉴这种分层方法，不把上游 schema、CSS 或行为称为 LibTV 源站事实」）⟹ "
    "⟹ ★ **镜头命名没有源站口径可对齐** ⟹ 本批**不改**它（不制造假的「已对齐」）。"
    "★★ **源站的命名口径**：相机 `label` 全部是「机位N」（纯数字）、角色 `label` 全部是「角色 + 单个大写字母」。"
    "★★★ **角色默认名规则 = 「角色 + 字母序号」**（实测）：在源站点「添加角色」⟹ 它开的是"
    "**体型预设面板**（11 枚）⟹ 选一枚 ⟹ 源站**新建一个角色** ⟹ 右栏「名称」输入框读到「**角色B**」"
    "（清理后基线里那个叫「角色A」）⟹ ⟹ 字母序号递进成立。"
    "★★ **clone 的改动**：种子对象 `director-character-lead` 的 `name` 由「角色01 · 陈默」改成「**角色A**」"
    "⟹ ★ 源站是「角色 + 字母」，clone 旧名是「数字序号 + 语义后缀」⟹ 与 batch 837 那次机位的事**完全同构**。"
    "★ **派生量自动跟随**（两条都是从 object.name 派生）：变换轨道 label ⟹ 「**角色A · 变换**」、"
    "姿态轨道 label ⟹ 「**角色A · 姿态**」。"
    "★ **被同步的旧门禁（三处真断言）**：720 的 `FIXTURE` 首项、42 的姿态轨道 label、43 的 option 列表；"
    "617／629／666／736 里的同串是 **docstring 历史文字** ⟹ **不动**。"
    "★ **验收**：门禁 `scripts/verify-liblib-batch838.py` **7/7**（S1「S83·镜2」是上传文件名／"
    "S2 源站没有镜头实体／S3 源站命名口径／S4 角色默认名规则／S5 clone 角色名 ＋ 派生跟随／"
    "S6 三处旧门禁期望值已同步／S7 否定性结论的扫描器有效性 ＋ 更正已落地）｜ **阴性对照 11/11**"
    "（N1–N10 每条**只**翻它自己那一条 ＋ 逐文件 SHA-256 复原一致；★ N5／N6／N7／N8／N9 "
    "**改的是权威 raw 本身** ⟹ 证明门禁真的在读那批 raw，不是读一份写死的结论）。"
    "★★★ **本批最刺眼的一处：判据的「状态源」选错了，连踩四次**。v9 跨趟读数无法对齐；"
    "v11 把**浮层面板行**当成新增的角色行 ⟹ 副作用：右键了「标准男性」；v15 收窄几何口径**仍然**"
    "分不开浮层与场景树；v16 用 class 口径修好读数器 ⟹ 却发现「删除在内存里生效、跨刷新又回来了」。"
    "★★ **根因：DOM 不该承担「有几个角色」这个判定** ⟹ ★★ **正解：权威状态 = API** —— "
    "导演台状态在 `api/canvas/project/detail-by-space` 的响应里 ⟹ 节点 `type=36` 的 "
    "`data.compositionData.characters` 就是**权威角色列表**（每项有 `id` 与 `label`）⟹ "
    "于是判定链改成**在权威数据上闭环**：建 ⟹ 右栏读名 ⟹ **轮询 API 直到它真多了一个** ⟹ "
    "★ **重算关系**：新增那项的 `label` **==** 右栏读到的值 ⟹ ⟹ 「默认名规则」这条结论**由权威数据自证**。"
    "★ **等固定秒数后猜是不可靠的**：源站靠**约 30 秒延迟**的 `POST /api/canvas/nodes/batch` "
    "自动保存 ⟹ 正解是**轮询 API 直到它真的变了**（带超时）⟹ 若轮询超时就**如实报告「未落盘」**、"
    "不谎称复原。"
    "★ **读数方法自己坏掉的那次**：源站**不用 cookie 鉴权 API**，而是**自定义请求头** `token` ＋ `webid` ⟹ "
    "页面内 `fetch` 与 `page.request` 不带这两个头都只回 90 字节 `{\"code\":10001,\"msg\":\"用户未授权\"}` ⟹ "
    "**解析不到任何节点** ⟹ 静默返回空列表 ⟹ ★ 那正是「**读数方法坏了**」的典型形态 ⟹ "
    "这两个值**只能从页面自己发的请求里抄**（★ 又一次「手打的标识符是输入，不是测量」）。"
    "★★ **S4 的判据第一版也写错了**：原判据是「场景树真多了一行（+1）」⟹ 那是 DOM 口径 ⟹ "
    "v16 已证明它**在选中态下失效** ⟹ 本批改成 API 口径 ＋ **关系式**：不拿 raw 里那条**存好的布尔**"
    "当判据（那是**结论不是测量**）⟹ 门禁**重算**关系、把它只当**交叉印证**⟹ ★ N8（改新增角色的 label）"
    "与 N9（改独立复核 raw 里的角色 id）各自证明这条关系式判据**独立生效**。"
    "★ **阴性脚本自己踩的坑**（★ 差点让负控「看起来在跑、其实什么都没测」）：N5／N6 里用了 "
    "`global touched` ＋ main 里的局部 `touched = False` ⟹ 两者**不是同一个变量** ⟹ "
    "注入其实**打上了**、主流程却读到一个永远是 False 的局部 ⟹ 「注入没打上」⟹ 中止。★★ 这正是"
    "已入库那条「**工具返回的可能是错误**」与「**手打的标识符是输入**」的近亲 ⟹ ★ 修法："
    "用**可变容器**当标志 ⟹ 并且**注入必须先证明打上了**、打不上就**中止**（别把「没打上」当成「通过」）。"
    "★ N7 第一版写的键名是**旧版 raw** 的键名 ⟹ 注入会打在**不存在的键**上 ⟹ 门禁照绿 ⟹ "
    "负控看起来「通过」实则**什么都没测** ⟹ 改成**先校验键存在**，不存在就中止。"
    "★ **源站复原走了三段，每段都是权威 API 读数**：v19 那趟自己新建的「角色B」（id `p6past1f`）"
    "**没删掉**（选中态下 class 口径找不到那一行）⟹ `cleanup838` 按 API 的 `id` 定位 ⟹ 右键删除 ⟹ "
    "**轮询 16 秒**后 API 只剩「角色A」⟹ ★★ 再用**独立进程、全新浏览器会话、只读不点**复核一次 ⟹ "
    "角色 = `[{id: xqns9rxe, label: 角色A}]`、相机 = `[\"机位1\",\"机位2\"]` ⟹ ⟹ **没有遗留**。"
    "★ 第三段是**必要**的：前两段都在**同一个浏览器进程**里 ⟹ 「内存里消失」与「服务端真存了」"
    "只由**同一份 API 读数**支撑 ⟹ 已入库那条纪律说得很直白：**内存里消失 ≠ 存盘了**。"
    "★ **不声称**：源站角色名一定是字母表 A→B→C（只实测了 A→B 这一步递进）；"
    "clone 的镜头命名体系已对齐源站（源站**没有**镜头实体可比）；"
    "crowd（群众）成员的命名已对齐（源站的 crowd 命名**未测** ⟹ 不猜）；"
    "837 的 README 已被更正（旧批次不可重写）。"
    "★ **回归**：门禁 838 **7/7** ✔；**720 = 7/7 exit=0** ✔（本批改了它的 `FIXTURE`）；"
    "**42** ✔；**43** ✔；556 **8 checks, 0 diagnostics** ✔；557 **5 checks, 0 diagnostics** ✔；"
    "536 **27 checks, 0 diagnostics** ✔；540 **10 checks, 0 diagnostics** ✔；"
    "575 **4 checks, 0 diagnostics** ✔；46 ✔；36 ✔；835 ✔；"
    "748 **4/7** 与 749 **7/9** 为旧账；750 exit=1 为环境性（`/tmp/dbg750e.py` 从未入库）。"
    "★ **回归副产物已复原**：36／42／43／46 的 PNG ＋ 720／748／749 的 runtime-audit 按 "
    "`git checkout` 复原 ⟹ **不带旧批次的产物变更进本次提交**。"
    "★ `npm run build` ✔、`npx tsc --noEmit` ✔、`npm run assertions:check` ✔"
    "（784 个脚本 **0** 个空断言）；`npm run docs:check` **exit=1**，"
    "★ 断链**全部**在 `docs/user-manual/`（**他人并发编辑区**）⟹ 本批**零提及**该目录（已 grep 核实）⟹ "
    "与本批无关。 |"
)


def main():
    row = ROW
    problems = []
    if not row.startswith("| Batch 838 |"):
        problems.append("行首不是 `| Batch 838 |`")
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
    if "| Batch 838 |" in text:
        print("★ 台账里已经有 Batch 838 的行了 ⟹ 不重复追加")
        return 1
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(row + "\n")
    print("已追加：", LEDGER)
    print("行长度：", len(row), "｜ 竖线：", pipes, "｜ U+FFFD：", row.count("�"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
