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
# M153 新增：账本也纳入扫描（见 iter_body_pages 里的说明）
LEDGER_PAGES = ["task-inventory.yml", "SOURCE_OBSERVATIONS.md"]
# M203 新增：截图清单也纳入扫描。
# 实测盲区：`screenshots/manifest.yml` 有 112 条目，每条都带 `verified_locator`（取证读数）、
# `alt`、`visible_text`——**它是一份会与订正结论打架的账本**，但从前不在扫描面内。
# 把它加进来时本批当场命中 2 处：R26「三处按钮区」（`04-icon-reuse-same-screen.png` 的
# `step` 字段，已在 manifest 直接订正为四处）与 R31 旧 needle `x=963`
# （该条**有意保留原值**，`m160_correction` 里写明了理由，改判据而非改值）。
MANIFEST_PAGE = "screenshots/manifest.yml"

RETRACTIONS: list[dict[str, str]] = [
    {
        "id": "R11",
        "kind": "conclusion",
        "wrong": "| 排队中 / 生成中 |",
        "why": "任务状态名取自 i18n canvas.aitudou.status 的逐条原文，界面写的是「已排队 / 处理中」，不是「排队中 / 生成中」；读者在节点上找「排队中」找不到（2026-10-01 M71 对拍 zh-CN.ts:651）",
        "fixed_in": "M71",
    },
    {
        "id": "R12",
        "kind": "conclusion",
        "wrong": "| 完成 | 结果写入节点",
        "why": "同 R11，界面写「已完成」",
        "fixed_in": "M71",
    },
    {
        "id": "R13",
        "kind": "conclusion",
        "wrong": "| 部分成功 | 批量中部分失败",
        "why": "同 R11，界面写「部分完成」；且状态表还漏了初始态「待配置」",
        "fixed_in": "M71",
    },
    {
        "id": "R14",
        "kind": "conclusion",
        "wrong": "节点显示「部分成功」",
        "why": "同 R13，90-troubleshooting 的症状描述里也是旧名",
        "fixed_in": "M71",
    },
    {
        "id": "R15",
        "kind": "conclusion",
        "wrong": "| 待配置 | 还没提交，节点停在准备状态 |",
        "why": "**M71 的订正方向反了，M85 撤回**。「待配置」等八个中文状态名取自 i18n `canvas.aitudou.status`，而该组文案**从未被任何组件引用**（穷尽 web/src 搜索，`canvas.aitudou.*` 只有 `nodeTypes.aitudou` 被用上）。真正渲染任务阶段的是 `aitudou-native-generation-panel.tsx:513` 的 `TaskStatus`，输出 `{taskPhase}` 原始英文枚举，且**仅在 taskId 存在时渲染**——未提交时页面上没有任何状态徽标。2026-10-01 运行时实测：八个词各出现 0 次",
        "fixed_in": "M85",
    },
    {
        "id": "R16",
        "kind": "conclusion",
        "wrong": "| **已排队** / **处理中** | 任务已提交，正在执行 |",
        "why": "同 R15：界面渲染的是英文 `queued` / `running`，不是中文",
        "fixed_in": "M85",
    },
    {
        "id": "R17",
        "kind": "conclusion",
        "wrong": "| **已完成** | 结果已写入节点 |",
        "why": "同 R15：界面渲染的是英文 `succeeded`",
        "fixed_in": "M85",
    },
    {
        "id": "R18",
        "kind": "conclusion",
        "wrong": "| **部分完成** | 批量中部分失败 |",
        "why": "同 R15：界面渲染的是英文 `partial`",
        "fixed_in": "M85",
    },
    {
        "id": "R19",
        "kind": "conclusion",
        "wrong": "这八个状态名取自 i18n `canvas.aitudou.status`",
        "why": "同 R15：M71 把它当成「界面逐条原文」，实际是死文案。M85 已改写为区分「节点内状态（生成中/生成失败，i18n 有调用点）」与「面板标题行的英文阶段徽标（源码 TaskStatus）」两套",
        "fixed_in": "M85",
    },
    {
        "id": "R1",
        "kind": "conclusion",
        "wrong": "导出是唯一能带走项目的方式",
        "why": "画布 zip 没有导入功能，带不走项目（2026-10-01 三重取证：i18n 三条文案零引用、首页无文件选择器、喂给导入资产报格式错）",
        "fixed_in": "M47",
        "allow_in": ["task-inventory.yml#首页卡片悬停操作（下载/重命名/删除）与多选、封面预览运行时取证"],
    },
    {
        "id": "R2",
        "kind": "conclusion",
        "wrong": "可以整体拷到另一台机器导入",
        "why": "同 R1，画布侧只实现了导出、从未实现读回",
        "fixed_in": "M47",
        "allow_in": ["task-inventory.yml#首页卡片悬停操作（下载/重命名/删除）与多选、封面预览运行时取证"],
    },
    {
        "id": "R3",
        "kind": "conclusion",
        "wrong": "真正的兜底是定期导出项目 zip",
        "why": "同 R1，导出 zip 救不回画布结构，保不住这个兜底",
        "fixed_in": "M47",
    },
    {
        "id": "R4",
        "kind": "conclusion",
        "wrong": "用「导入资产」恢复其中的资产",
        "why": "readAssetPackage 硬要求 assets.json，画布 zip 里是 projects.json，实测报「导入失败，请选择有效的资产压缩包」",
        "fixed_in": "M47",
    },
    {
        "id": "R5",
        "kind": "conclusion",
        "wrong": "但换机仍只能靠导出 zip",
        "why": "同 R1，换机带不走画布",
        "fixed_in": "M47",
    },
    {
        "id": "R6",
        "kind": "conclusion",
        "wrong": "项目支持导出 zip 备份",
        "why": "同 R1。M47 漏改了 30-concepts 这一处，M52 才发现",
        "fixed_in": "M47",
    },
    {
        "id": "R7",
        "kind": "conclusion",
        "wrong": "用首页的批量导出得到 zip",
        "why": "同 R1。M47 漏改了 undo-persistence 这一处，M52 才发现",
        "fixed_in": "M52",
        "allow_in": ["task-inventory.yml#（撤销/重做/画布更改会自动保存）与刷新持久化多次实测"],
    },
    {
        "id": "R8",
        "kind": "wording",
        "wrong": "与弹窗逐字一致",
        "why": "弹窗 13 行与表格有四处出入；手册自己的截图就证伪了这张表（2026-10-01 实测对拍）",
        "fixed_in": "M44",
    },
    {
        "id": "R9",
        "kind": "conclusion",
        "wrong": "切换后功能完全一致",
        "why": "该节五项全是文案与布局的静态比对，没有一项验证「功能」，标题超出证据范围",
        "fixed_in": "M45",
    },
    {
        "id": "R10",
        "kind": "conclusion",
        "wrong": "均为项目级设置",
        "why": "主题模式其实是全局设置（localStorage:tdcanvas:theme_store），切浅色后 6 条路由全部生效",
        "fixed_in": "M39",
    },
    {
        "id": "R20",
        "kind": "conclusion",
        "wrong": "用悬浮工具条开启「自由缩放」",
        "why": "「自由缩放」在 zh-CN.ts 的 1821 条字符串值与全部源码中各出现 0 次，界面按钮的真名是「锁比例」（关）/「自由比例」（开）；且该按钮 `defaultVisible: false`，默认根本不在工具条上，必须先经「更多 → 自定义工具栏」勾出来才能点。手册同一页第 16 行的对照表实测写着 13 个按钮、末位是「更多」，与这一句自相矛盾（2026-10-01 M93 i18n 语料 + 运行时双重复现）",
        "fixed_in": "M93",
    },
    {
        "id": "R22",
        "kind": "conclusion",
        "wrong": "方向拖反时连线数确实增加",
        "why": "M98 曾把「把 output 拖到另一个节点的 output 端口、连线数确实增加」记成一条待查的观察。M99 查实：那是**读到了陈旧的应用计数**（离开画布再回来读时，写盘尚未落定），实际该操作**被拒**。源码 `canvas-node-ports.ts` 的 normalizeConnectionHandles 第一句就是两个 handle 同向即返回空，运行时实测 output→output 与 input→input 均 0→0 被拒（2026-10-01 M99）",
        "fixed_in": "M99",
    },
    {
        "id": "R21",
        "kind": "conclusion",
        "wrong": "时长可选 4-8 秒，分辨率 480p / 720p / 1080p 自动匹配",
        "why": "视频面板参数行运行时实测为「4~15 秒 · 480p/720p/1080p/2k/4k/native1080p/native4k · 比例 7 档」。漏掉的 native1080p / native4k 正是价格区间 ¥2.48–5.37 的上下两端，照旧参数算账等于把最贵一档当不存在。M66 / M82 早已在 20-reference 对照表与 manifest 另一条记录写下正确值，只有 generate-images 的本节没跟着改（2026-10-01 M93）",
        "fixed_in": "M93",
    },
    {
        "id": "R23",
        "kind": "wording",
        "wrong": "命中区 43×43",
        "why": "M84 记录的这个数字是**带着画布缩放量的一次性读数**。端口命中区在源码里是写死的 `size-12`（48×48），2026-10-02 M107 在 100% 缩放下实测 `getBoundingClientRect()` 为 48×48——43/48≈0.896，正是当时画布处于非 100% 缩放造成的缩水。写死一个像素数会随读者当前缩放而失效，且与源码对不上（2026-10-02 M107）",
        "fixed_in": "M107",
        # M159 新增：这句原错误说法在 use-agent.md 的订正说明里被**刻意引述**——
        #   「凡是带坐标系的数字都要警惕」这句话需要一个反面例子，
        #   而读者正是要看到「原来错在哪」才说得清。
        "allow_in": ["10-tasks/use-agent.md#那次的数字带着当时的画布缩放量"],
    },
    {
        "id": "R24",
        "kind": "wording",
        "wrong": "而顶栏高 48px、工具条高 48px",
        "why": "M31 记录的这两个高度在当前版本都对不上。顶栏源码是写死的 h-14 = 56px，2026-10-02 M108 运行时实测顶栏 y=0、高 56；节点上方有两条不同浮层，实测高分别约 27px（节点名那一条，top:-40px）与 32px（h-8，top:-39px），**都不是 48px**。初版疑似把顶栏高度当成了工具条高度。同一句里的按钮纵坐标 −42 也没注明所属坐标系：该偏移是画布世界单位常量（实测恒为 −40），会随缩放放大到屏幕，42/40 = 1.05 对应约 105% 缩放（2026-10-02 M108）",
        "fixed_in": "M108",
    },
    # ── M152 补登记：M109–M151 这四十三批的订正，此前**一条都没进这张表**。
    #    实测证据：M152 拿本表当权威清单去扫，24 条里 fixed_in 最新只到 M108；
    #    而 AUDIT.md 里提到订正的记录有 86 条、覆盖 M5–M151。
    #    **这张表是「防止已订正说法复现」的唯一机制，表外的订正等于没被守住。**
    {
        "id": "R25",
        "kind": "wording",
        "wrong": "Dock 认不出 9 个",
        "why": "M125–M129 连续四批据「按 class 名找悬停浮层」写下「左侧 Dock 16 个按钮里有 9 个认不出、悬停无任何提示」，M129 还把它写进了探针的结论。**M132 第 63 次否证整组作废**：Dock 用的是自研浮层，类名 `pointer-events-none absolute left-[calc(100%+8px)]`，**不含 tooltip / tip 任何字样**；按类名找只抓得到同区域的 antd `div.ant-tooltip`。实测 Dock 8 个按钮悬停提示**逐字齐全**，「删除选中」也有浮层。正确判据是**悬停前后全页可见文本取差集**，不依赖类名（2026-10-02 M132）",
        "fixed_in": "M132",
        "allow_in": ["task-inventory.yml#运行时走查完成（清数据首启→新建→空画布→首页项目卡）"],
    },
    {
        "id": "R26",
        "kind": "wording",
        "wrong": "三处按钮区",
        "why": "M132 补出**顶栏**这一处按钮区后，两页仍写「三处按钮区」，实际是**四处**（左侧 Dock / 节点悬浮工具条 / 画布视图控制 / 顶栏）。M139 回走时订正为四处并把顶栏列进去。写死数量而不列出处，下批加一处就会漏改（2026-10-02 M139）",
        "fixed_in": "M139",
        "allow_in": ["task-inventory.yml#手工撞见的剪刀复用做成全应用扫描", "SOURCE_OBSERVATIONS.md#三处按钮区的顺序固定"],
    },
    {
        "id": "R27",
        "kind": "wording",
        "wrong": "共 5 种",
        "why": "同一页的对照表逐行点数是 2 / 4 / 5 / 6 / 8 / 13 **共 6 种**，错的是正文那句汇总，**表格每一行都是对的**。读者按汇总去记「只有 5 种」，一遇到第 6 种就以为记错了、以为自己看错了（2026-10-02 M137）",
        "fixed_in": "M137",
        # M152 新增机制：这一条在正文里**必须**原样出现一次——`edit-nodes.md` 的
        # 订正说明块要引述「原文写『长度从 2 到 13 共 5 种』」，
        # 读者正是靠这句引述才知道原文错在哪。改写措辞反而会毁掉这段说明的价值。
        # **豁免必须精确到「文件:行号」**，只写文件名等于把整页都开豁免，
        # 那和 M140 查出的「文档可以比源码写得细」正是反面：**豁免要窄到无法滥用。**
        "allow_in": ["10-tasks/edit-nodes.md#顺带订正本节下方那句汇总", "task-inventory.yml#运行时走查完成（双击标题重命名、双击编辑文字追加"],
        # ↑ 第二处是 M154 补登记 M137 取证时写进账本的——账本同样会引述原错误说法，
        #   而 M153 已把账本纳入扫描范围。**扩了覆盖范围，就要补齐对应的豁免。**
    },
    {
        "id": "R28",
        "kind": "conclusion",
        "wrong": "所有节点类型的工具条都是 4 个按钮",
        "why": "M137 第一版探针的**假结论**，症状像产品有个统一的 4 按钮工具条。真因：节点默认全部叠在画布中心，按 DOM 顺序取中心点点选，**命中的永远是最上层那一个**，七种类型数出来全是同一个节点（按钮文字还逐轮往后挪一位）。正确判据是 `elementFromPoint` 阳性对照 + 每轮清空画布只留一个节点（2026-10-02 M137）",
        "fixed_in": "M137",
    },
    {
        "id": "R29",
        "kind": "conclusion",
        "wrong": "按钮本身没有状态变化，说明这个功能没有状态",
        "why": "M136 实测 13 个按钮的 `aria-pressed` / `expanded` / `checked` / `current` **全为 null**，点下去信号全不变。但**这是读法边界，不是产品结论**：「隐藏连线」那种开关状态显示在**按钮外观**上、不在这些属性里。**「按钮没有状态变化」≠「这个功能没有状态」**，写进手册时必须把这条边界一起写上（2026-10-02 M136）",
        "fixed_in": "M136",
    },
    {
        "id": "R30",
        "kind": "wording",
        "wrong": "顶栏实际是 56px",
        "why": "**错在源码引用指到了另一个组件**。M108 写的类名 `h-14` 确实存在于代码里，但长在 `web/src/components/layout/app-top-nav.tsx:101`（`td-app-top-nav`，工作区层顶栏），而**画布页的顶栏是 `web/src/components/canvas/canvas-top-bar.tsx:70` 的 `h-16` = 64px**。2026-10-03 M160 运行时实测顶栏 `y=0`、高 `64`；`git log` 确认 `h-16` 自首个提交 `f7f06b1` 起从未改过——**属当初取错证据，不是版本漂移**。**「源码里找得到」不等于「就是这个东西的」**（2026-10-03 M160）",
        "fixed_in": "M160",
    },
    {
        "id": "R31",
        "kind": "wording",
        "wrong": "同屏，相距 931 px",
        "why": "「两把剪刀相距 931 像素」是一次**具体会话的读数，不是界面属性**：左侧 Dock 那一列钉死在屏幕上，节点工具条那一列**跟着节点跑**。2026-10-03 M160 实测同一个有图图片节点放在画布左侧时两把只相距 163px。原记录里的 `x=32` 还有个更隐蔽的问题——**那是按钮内 16px 图标的左边缘，不是按钮本身的左边缘**（按钮本身 x=24，32 = 24 + (32−16)/2）。**「同屏且相距很远、不会误点」的结论不变，变的只是不能靠数像素认按钮**\n"
               "★ **M203 换了 needle 本身，原 needle 写错了形态**：原来登记的是 `x=963`——"
               "**那是取证记录里的坐标记法，不是读者会读到的说法**。手册正文里从来没有出现过 "
               "`x=963` 这种写法（正文写的是「931 px」），所以旧 needle **一条都拦不到**："
               "M160 明明把 931px 订正掉了，同一张复用表里的「**同屏，相距 931 px**」"
               "却原封不动活到 M203，跨了两批没人看见。**是量具的毛病，不是产品的问题。**\n"
               "现按 R11/R12/R13 同一写法改成**读者真读到的表格单元形态**，"
               "并撤掉已无用的 allow_in（旧 needle 只在账本里命中，正文里那处豁免形同虚设）\n"
               "★ **M203 当场又用上了 allow_in**：新 needle 换成正文形态的同一刻，"
               "它把 `SOURCE_OBSERVATIONS.md` §13.0.2 里那处**刻意引述原句**的正向记录"
               "也逮了出来——**这说明新 needle 有牙**（旧 needle 从来不会）。"
               "该处是讲这件事的方法论小节，**必须逐字引原句**才说得清，"
               "所以登记内容锚点豁免，**不是把正文那两格放过去**",
        "allow_in": ["SOURCE_OBSERVATIONS.md#发布页表格里的「同屏，相距"],
        "fixed_in": "M160",
    },
    {
        "id": "R32",
        "kind": "conclusion",
        "wrong": "批量摆放节点时给画布上方留出至少 50px 的空白",
        "why": "M108 订正后的预防值，而那条订正的**推导前提（顶栏高度）本身就是错的**（见 R30）。2026-10-03 M160 实测：13 按钮工具条顶边恒在**节点顶 − 104**（100% 缩放，8 个拖拽点零偏差坐实），顶栏底边 64，**临界值是节点顶 = 168**，比原值大 3 倍多。**由错数推出的数，错得不随机、错得很整**——所以订正时必须连推导链一起验，不能只验结论那个数",
        "fixed_in": "M160",
    },
    {
        "id": "R33",
        "kind": "conclusion",
        "wrong": "104 那一段是跟着缩放走的",
        "why": "**M160 自己写下、没实测就断言的一句话**，M163 用九档缩放把它否掉。工具条渲染在 `</TDCanvasSurface>` **之外**（屏幕空间），**自身 48px 高度不随画布缩放变**，所以偏移是 **`48×k + 56`** 而不是 `104×k`。实测 25/40/60/80/100/130/160/200/300% 九档，偏移 68/75.2/84.8/94.4/104/118.4/132.8/152/200，**与 `48k+56` 偏差全为 0**；按比例模型在 100% 以外每档都错（25% 档差 42px）。**方向也是反的：缩放越大要留的空白越多**。预防临界值随之改为 `120 + 48k`（2026-10-03 M163）",
        "fixed_in": "M163",
    },
    {
        "id": "R34",
        "kind": "conclusion",
        "wrong": "一个可点的\u300c移除插件\u300d按钮",
        "why": "M174 实测：**它不是一个按钮。** 那行是\u300c标签 + 命令\u300d的说明，\u300c移除插件\u300d是 `<span>`、其父 div 的 class 是 `rounded-md border px-2 py-1.5`（**样式像按钮，所以肉眼会当成按钮**），但 cursor=auto、无 onclick，且**整页 29 个可点元素里含\u300c移除插件\u300d的是 0 个**。旁边那个能点的是右端的复制图标。写\u300c可点\u300d会让读者去找一个点不动的东西，然后以为自己操作错了",
        "fixed_in": "M174",
    },
    {
        "id": "R35",
        "kind": "conclusion",
        "wrong": "到 /config 里搜\u300c插件\u300d能搜到 5 处",
        "why": "**归因错了，而且这一步照做根本看不到。** 那 5 处字全在**右侧常驻 Agent 面板**里，不在配置区：三个路由（/config、/canvas、/）实测\u300c插件\u300d出现次数完全相同（各 7 次 = 5 个文本节点、共 7 次字符出现），5 个命中点 x 坐标全部落在同一个 aside 内，而 /config 的 `main` 与说明栏内均为 **0 次**。更要紧的是**面板默认折叠**：折叠态实测可见命中 **0/5**，点顶栏 title=\u300c打开 Agent\u300d的按钮（1313,12）之后才变成 **5/5**。手册没说这个前提，读者照做会在空配置页上搜个空",
        "fixed_in": "M174",
    },
    {
        "id": "R37",
        "kind": "conclusion",
        "wrong": "\u751f\u6210\u4e2d\uff08\u8282\u70b9\u5185\u8f6c\u5708\uff09",
        "why": "M180 \u6e90\u7801\u53d6\u8bc1\uff1a**\u8f6c\u5708\u53ea\u5bf9\u7a7a\u8282\u70b9\u6210\u7acb\u3002** "
        "`canvas-node.tsx:516-524` \u662f\u56db\u6761\u4e92\u65a5\u5206\u652f\uff1a\u56fe\u7247/\u89c6\u9891\u4e14 "
        "`status===\'loading\'` \u4e14**\u6709 content** \u65f6\u8d70 `MediaGenerationGlass`\uff08\u6bdb\u73bb\u7483\u906e\u7f69\uff0c"
        "`:587` \u7684 `data-canvas-media-generation-glass`\uff09\u2014\u2014**\u539f\u56fe\u4ecd\u5728\u73bb\u7483\u540e\u9762\uff0c\u4e2d\u95f4\u8fd9\u4e00\u4e2a\u80f6\u56ca\u5199\u300c\u751f\u6210\u4e2d NN%\u300d**\uff1b"
        "\u53ea\u6709\u65e0 content \u65f6\u624d\u662f\u6574\u4f53\u5927\u8f6c\u5708\u3002"
        "**\u8bfb\u8005\u7b49\u56fe\u65f6\u76ef\u7740\u8282\u70b9\u627e\u8f6c\u5708\u627e\u4e0d\u5230\uff0c\u4f1a\u4ee5\u4e3a\u300c\u65e7\u56fe\u88ab\u6e05\u6389\u4e86\u3001\u751f\u6210\u5931\u8d25\u4e86\u300d\uff0c"
        "\u767d\u7b49\u4e00\u8f6e\u751a\u81f3\u91cd\u590d\u8ba1\u8d39**\u3002\u53e6\u8865\uff1a\u8fdb\u5ea6\u5c01\u9876 99%\uff08`:592` \u7684 `Math.min(99, ...)`\uff09",
        "fixed_in": "M180",
    },
    {
        "id": "R38",
        "kind": "conclusion",
        "wrong": "\u63d0\u4ea4\u8fc7\u7684\u4efb\u52a1\u5728\u5237\u65b0\u9875\u9762\u540e\u81ea\u52a8\u6062\u590d\u72b6\u6001",
        "why": "M180 **\u672c\u5730\u6ce8\u5165\u5b9e\u6d4b\uff08\u96f6\u4ed8\u8d39\uff09**\uff1a\u628a\u56fe\u7247\u8282\u70b9\u6ce8\u5165 `status:\'loading\'` \u518d\u5237\u65b0\uff0c"
        "\u5b9e\u6d4b\u5f97\u5230\u7684\u662f**\u9519\u8bef\u6001**\u2014\u2014"
        "`canvas-generation-helpers.ts:247` \u7684 `resetInterruptedGeneration`\uff08\u7531 `project.tsx:375` \u5728**\u6bcf\u6b21\u6253\u5f00\u9879\u76ee**\u65f6\u8c03\u7528\uff09"
        "\u628a `loading` \u8282\u70b9\u4e00\u5f8b\u6539\u5199\u6210 `error` + \u300c\u9875\u9762\u5237\u65b0\u540e\u751f\u6210\u5df2\u4e2d\u65ad\uff0c\u8bf7\u91cd\u65b0\u751f\u6210\u3002\u300d\u3002"
        "**\u9633\u6027\u5bf9\u7167**\uff1a\u6ce8\u5165 `success` \u7684\u8282\u70b9\u5237\u65b0\u540e\u539f\u6837\u4e0d\u52a8\uff0c\u786e\u8ba4\u5b83\u53ea\u78b0 `loading`\u3002"
        "**\u5bf9\u8bfb\u8005\u7684\u5f71\u54cd**\uff1a\u4ee5\u4e3a\u53ef\u4ee5\u5173\u6389\u9875\u9762\u53bb\u5e72\u522b\u7684\u3001\u56de\u6765\u63a5\u7740\u7b49\u7684\u4eba\uff0c"
        "\u5b9e\u9645\u62ff\u5230\u7684\u662f\u5931\u8d25\uff0c\u53ea\u80fd\u70b9\u300c\u91cd\u8bd5\u300d\uff0c**\u800c\u91cd\u8bd5\u4f1a\u91cd\u65b0\u8ba1\u8d39**\u2014\u2014\u4e00\u6b21\u7b49\u5f85\u53d8\u6210\u4e24\u6b21\u4ed8\u8d39",
        "fixed_in": "M180",
    },
    {
        "id": "R45",
        "kind": "wording",
        "wrong": "「工具条最右端的『更多』→『自定义工具栏』→ 勾上『锁比例』」（读起来像一层菜单路径）",
        "why": "M197 运行时实测：**点「更多」就直接弹出标题为「自定义工具栏」的窗口，"
               "中间没有任何一层菜单项**（源码 `canvas-node-hover-toolbar.tsx:259` 的 `more` "
               "直接置位 `imageToolSettingsOpen`，而 `ImageToolSettingsModal` 就在该按钮下方渲染）。\n"
               "**我的探针为此白跑一轮**：它在点完「更多」之后去找一个叫「自定义工具栏」的菜单项，"
               "找不到，于是差点把这个功能记成「坏的」。\n"
               "**结论本身没错**（14 项、默认勾 12、未勾的是锁比例与多角度，双读数一致），"
               "错的只是**路径的写法**——按原文去找那一层菜单的读者会找不到。",
        "fixed_in": "M197",
    },
    {
        "id": "R44",
        "kind": "conclusion",
        "wrong": "左侧 Dock「未选中 15 个按钮 → 单选 16 个 → 多选又回到 15 个」，"
                 "且「「删除选中」**只在单选时出现**，多选时它就没了」",
        "why": "M196 逐档实测（容器 `.td-canvas-dock`，按 `aria-label` 枚举）："
               "**未选中 8 个 → 单选 9 个 → Shift 真多选仍是 9 个 → Cmd+A 全选 3 个也是 9 个**；"
               "只有**点空白取消选中**才回到 8 个。\n"
               "源码侧：`canvas-toolbar.tsx:258` 的条件是 `{selectedCount ? … : null}`——"
               "**只要有选中就显示那个垃圾桶，并不是「正好选中 1 个」**。\n"
               "**上一轮那次读到 8 的 Shift 多选是假的**：点偏移后落在了空白画布上，"
               "那是**取消选中**、不是多选。用「节点工具条数量」当独立读数才分辨开："
               "真多选时工具条为 0（没有单一归属），而单选时为 1。\n"
               "**对读者的影响**：手册据此建议「要一次删掉多个节点，别指望用 Dock 的垃圾桶，"
               "走右键菜单」——**实测多选时那个垃圾桶就在，多节点删除可以走 Dock**。"
               "这条建议让读者放弃了可用的路径。",
        "fixed_in": "M196",
    },
    {
        "id": "R43",
        "kind": "conclusion",
        "wrong": "其余三项（输入模式、网格样式、图片信息）都是**项目级**的",
        "why": "M191 逐项实测「改 → 等 → 刷新 → 读库」：**输入模式 3/3 保住、图片信息 3/3 保住，"
        "而「线格」0/3——每次刷新都被悄悄改回「点阵」，没有任何提示。**\n"
        "根因是 `project.tsx:4198` 的 `migrateCanvasBackgroundMode`：某个项目**第一次**以「线格」被打开时，"
        "它把该值改成「点阵」并按项目 id 在 localStorage 打个标记（`tdcanvas:dots-grid-v1:<项目id>`），"
        "**从那以后「线格」不再被改动**。标记按项目分开，所以**每个画布都要各自被吃掉一次**。"
        "对照组：「空白」3/3 全保住，「点阵」3/3 全保住——**只有线格中招**，与源码里"
        "「`if (mode !== \"lines\") return mode`」的窄条件吻合。\n"
        "**订正方向：不能说「三项都是项目级、跟着项目保存」，要说「线格有一次一次性例外」。**",
        "fixed_in": "M191",
    },
    {
        "id": "R42",
        "kind": "conclusion",
        "wrong": "`chatSessions`（对话记录）",
        "why": "**M188 自己写进去的四个字，M190 当场推翻。** M188 把 12 个字段列进手册时，"
        "给 `chatSessions` 标了「（对话记录）」——**这会引导读者以为 Agent 面板里的对话跟着画布存**。\n"
        "真相：**这个字段一直是空数组**。`setChatSessions` 全仓只有 3 处调用，"
        "全是初始化、从项目恢复、撤销时还原，**没有任何一处写入消息**（`project.tsx:246/379/1228`）。"
        "Agent 的消息在 `use-agent-store.ts:162` 的 `addMessage`，**那个 store 没有 persist**，"
        "只有面板宽度、地址、token、权限模式、模型、推理强度 6 个**设置项**进 localStorage。"
        "「新对话」按钮也在**历史**页签、走 Agent 侧线程，且 `disabled={!connected}`"
        "（`local-agent-panel.tsx:1320`）。\n"
        "运行时佐证：存储里 12 个键齐全（阳性对照：同一对象的 `nodes` 有真数据，不是空壳），"
        "`chatSessions=[]`、`activeChatId=null`，刷新前后一致；"
        "localStorage 里**没有任何消息/会话类键，连 `tdcanvas:agent-*` 都是 0 个**。"
        "**订正方向：不能说「对话记录跟着画布存」，要说「这个字段在，但一直是空的；面板对话不落盘」。**",
        "fixed_in": "M190",
    },
    {
        "id": "R41",
        "kind": "conclusion",
        "wrong": "自动保存（写入有 400ms 防抖），无需手动保存",
        "why": "M188 实测：**400 毫秒那道防抖只管画布内容，管不到视口。** `20-reference` 那张表这一行写的范围是"
        "「节点/连线/**视口**/外观」，可整行只挂了一个 400ms 的数——**视口不适用**。\n"
        "源码是两道串联的防抖：所有改动都要过 `use-canvas-store.ts:56` 的 **400ms 合并写盘**，"
        "而缩放/平移在此之前**还要先过自己的一道 500ms**（`project.tsx:449-459`，清理函数是 clearTimeout、取消而不补写）。\n"
        "实测分界**落在 850 到 900 毫秒之间**（700/750/800/850 全丢，900/1100/1400 全保住，"
        "每个样本先归一化到缩放硬夹 0.05 再做 A→B→A→B，不跨轮复用基准），**与源码相加的 900ms 毫秒级吻合**。"
        "而内容侧仍是 300–420ms（M120 已量）。**两者差的那一段，正好就是视口自己那道 500ms。**",
        "fixed_in": "M188",
    },
    {
        "id": "R40",
        "kind": "conclusion",
        "wrong": "一次拖拽里包含的多个微调无法逐个撤销",
        "why": "M187 实测：这句话**无条件说就站不住**。一次拖角缩放中途**按住不动 400ms**（鼠标全程没松开）再继续拖完，"
        "会多落一条历史——按第一次撤销只退到**拖拽途中的中间尺寸**（实测 520x300 → 640x380 → 580x340 → 520x300，3/3 需要按两次）。"
        "**中途那 400ms 里什么都没发生，历史却已经落了**。\n"
        "另测排除了一种误读：**「拖得慢」不会把一次拖拽拆开**（12 步、每步停 120ms、总耗时 1.9 秒的慢拖，3/3 仍只占 1 条）——"
        "因为源码 `project.tsx:405-437` 那个 180ms 是**尾沿防抖**而不是采样周期，"
        "每次变化都重置定时器，只有**静默满 180ms** 才落一条。**成立条件是「中途没有静默」，不是「拖得慢」**",
        "fixed_in": "M187",
    },
    {
        "id": "R39",
        "kind": "wording",
        "wrong": "连注册表都没有，只有一个类型名和一条文案",
        "why": "M182 源码取证：**前半句对，后半句低估了。** `aitudou` 确实不在节点注册表里"
        "（`web/src/components/canvas/nodes/builtin-nodes.tsx` 只注册了文本/图片/视频/音频/生成配置/组），"
        "**但 `web/src/constant/canvas.ts` 里另有两条完整条目**：默认尺寸 380×220、默认标题、"
        "以及默认元数据 `aitudouOperation: \"video.generate\"`。"
        "**这是一套齐备却只差注册表那一条的规格**，说成「一条文案」会让人以为是随手留的残骸。"
        "**结论（建不出来）一个字没变**——所以这条记为描述性订正，不占结论性订正名额",
        "fixed_in": "M182",
    },
    {
        "id": "R36",
        "kind": "conclusion",
        "wrong": "连线可点击的区域就是那条贝塞尔曲线本身，没有额外的加粗命中层",
        "why": "M177 实测**有**一条 16 像素宽的透明命中带：连线的 path 本身就是 "
        "`stroke=\"transparent\" stroke-width=\"16\"` + `pointer-events: stroke`，"
        "**它不是「那条细线」，它就是加粗层**。实测沿法线偏移：d=0~7 命中连线、d>=8 落空，"
        "**命中半宽 7~8 屏幕像素**，而视觉线宽只有 1~2px（画布缩放实测 100%，"
        "CTM/滑块/节点尺寸/正文百分比四条读数互证）。"
        "**所以「连线点不中」的真正原因是节点盖在上面**（节点 z-10 > 连线层 z-[2]），不是线太细",
        "fixed_in": "M177",
    },
    {
        "id": "R49",
        "kind": "wording",
        "wrong": "同屏，相距 815 px",
        "why": "**M160 就已经撤回过这个数，但发布页一直没改**——这是 M203 查出来的。"
               "依据在 `SOURCE_OBSERVATIONS.md` 的 M160 订正块：它明写「原表给剪刀 931px、"
               "**上传箭头 815px**、对话气泡 x=1322。**这一列的像素值已作废，不要再引用**」，"
               "而 `create-canvas-project.md` 的图标复用表里这两行至今还印着 931 px 与 815 px。\n"
               "**理由与 R31 同源**：左侧 Dock 那一列钉死在屏幕上、节点工具条那一列跟着节点跑，"
               "**距离不是界面属性**（实测同一对图标放在画布左侧时只相距 163 像素）。\n"
               "★ **为什么 R31 拦不到它**：R31 的 needle 只能匹配「同屏，相距 931 px」这一格，"
               "**上传箭头那一格是另一个字符串，从来没被任何一条订正登记过**。"
               "「同一列的像素值一起作废」这件事，写在账本里，但**没有一条 needle 覆盖它**。\n"
               "★ **这一格的订正在正文里从未存在过**：`:122` 那段 M160 订正只谈剪刀（「两把剪刀」），"
               "**读者读到上传箭头那一行时，没有任何一句话告诉他这个数字别信**。"
               "所以这不是「漏改」，是**整条订正只做了一半**——本批补齐",
        "fixed_in": "M160 / M203",
    },
    {
        "id": "R50",
        "kind": "wording",
        "wrong": "59 张截图的 alt 文本里带可数断言",
        "why": "**这个数谁也复现不出来。** M202 记下「59 张截图的 alt 文本里带可数断言」，"
               "M204 试了 8 种判据变体（单位词表宽窄四档 × 是否剔除序数），"
               "得到的数是 **49 / 50 / 56 / 57 / 61 / 63 / 64 / 66，没有一个是 59**——"
               "59 正好卡在「57」与「61」两个任意选择之间。\n"
               "**那是个手数的计数，不是一条可重复规则的结果。** 与 M203 那把从不报警的量具同一个病："
               "**一个看起来一直在维护的数字，实际没有任何人能用同样的办法得到它。**\n"
               "现改为 `scripts/list-screenshot-alt-counts.py` 打印的数："
               "**73 处引用 / 62 张图**，其中 **2 处是序数不是计数**（`第一个文本节点`、"
               "`第一步按钮`），剔掉后 **71 处 / 60 张**。"
               "**工具只依赖标准库、只读**（M204）",
        "fixed_in": "M204",
    },
    {
        "id": "R51",
        "kind": "conclusion",
        "wrong": "「切图」和「替换图片」是两个长得几乎一样的方框图标",
        "why": "**读者照着这句去找，会把两个毫不相干的按钮当成一对。**\n"
               "逐个对源码 `web/src/components/canvas/canvas-image-toolbar-tools.tsx`"
               "（图标取自 lucide-react）：`replace` 用 **`Upload`**（一支朝上的箭头加一条底线，"
               "**根本不是方框**）、`split` 用 **`Grid2x2`**（九宫格）、"
               "`crop` 用 **`Scissors`**、`view` 用 **`Maximize2`**（两支朝外的对角箭头，"
               "**没有放大镜**）。\n"
               "★ **原文两处都错**：① 「替换图片」不是方框图标；"
               "② 把「查看大图」描述成「斜箭头**放大镜**」，而 `Maximize2` 里没有放大镜。"
               "**原文点名的两组，一组长得完全不像，另一组连描述都不对。**\n"
               "★ **而真正会认错的那一对一直没人提**：`download` 用 `Download`、"
               "`replace` 用 `Upload`，**同一个「底线加箭头」造型、只差方向**——"
               "这才是该写进手册的那一句，M206 已换上。\n"
               "**教训：相似是主观的，图标名是客观的。要断言两个图标像不像，先去看它们 import 了什么。**\n"
               "★ **M206 当场又用上了 allow_in**：本条的订正块在正文里**逐字引了原句**（"
               "否则读者不知道错在哪），新 needle 立刻把那一行点了出来——**再次证明它有牙**。"
               "该处是刻意反例引述，登记内容锚点豁免，**不是把真正的错误说法放过去**",
        "allow_in": ["10-tasks/edit-nodes.md#订正本段**：原文写的是"],
        "fixed_in": "M206",
    },
    {
        "id": "R52",
        "kind": "conclusion",
        "wrong": "「拖拽你想生成或编辑的画面」",
        "why": "**这个占位符在代码里根本不存在。** 面板只有一个"
               "（`web/src/components/canvas/aitudou-native-generation-panel.tsx`），"
               "它的输入框占位符全部来自 `nativePromptPlaceholder()`，"
               "对图片节点返回的是 **`描述`你想生成或编辑的画面**——"
               "**全仓 grep「拖拽你想生成或编辑的画面」是 0 处**。\n"
               "**「拖拽」是拖放上传那个动作，占位符却是在让人打字**；"
               "读者照着书去界面上找这句话，一个字都找不到，"
               "而这行表格的用途正是**教他把两个面板区分开**。\n"
               "★ **同表另一格也一并订正**：图片面板的**面板标题不是「文生图」而是「图片创作」**——"
               "标题是 `{nativeKindTitle(kind)}创作` 运行时拼出来的，"
               "**「文生图」是副标题**（`nativeAutomaticMode()` 在无参考图时返回它，"
               "挂参考图则是「参考生图」）。原文那一列只写「文生图」，"
               "**与左边「标题 · 副标题」的写法不一致，读者会默认它是标题**\n"
               "★ **M207 当场用上了 allow_in**：订正块在正文里**逐字引了那个不存在的占位符**"
               "（否则读者不知道错在哪），新 needle 立刻把那行点了出来——**再次证明它有牙**",
        "allow_in": ["10-tasks/generate-images.md#grep「拖拽你想生成或编辑",
                     "SOURCE_OBSERVATIONS.md#占位符「拖拽你想生成"],
        "fixed_in": "M207",
    },
    {
        "id": "R53",
        "kind": "conclusion",
        "wrong": "同一条工具条、长度从 2 到 13 共 6 种",
        "why": "**这个「共」是穷举，而它不是——而手册自己就教读者把它打破。**\n"
               "同一本手册的台账 F12 记着：「更多 → 自定义工具栏」弹窗**列 14 项、默认勾上 12 项**"
               "（未勾的是**锁比例**与**多角度**）。**默认勾的 12 项 + 末尾那个独立渲染的「更多」= 13**，"
               "与 M136 / M194 实测的 13 对得上；"
               "**而一旦在那个弹窗里勾上「多角度」，这条工具条就变成 14 个。**\n"
               "★ **更糟的是**：图片处理那节明写「**多角度需要先在工具条自选里勾出来**」——"
               "**照着手册做，就会得到一个这张表说不存在的长度。**\n"
               "源码侧：`canvas-image-toolbar-tools.tsx` 的 `defaultImageQuickToolIds` = 5 个基础项"
               " + 7 个 `defaultVisible: true` 的图像工具 = 12；`resize`（锁比例）与 `angle`（多角度）"
               "都是 `defaultVisible: false`；末尾的「更多」在 `canvas-node-hover-toolbar.tsx:248` "
               "**独立于 `quickImageToolIdSet` 单独渲染**，所以默认 12 + 1 = 13。\n"
               "**M208 已把两处正文都限定为「默认配置下」，并写明第 7 档是 14。**",
        "fixed_in": "M208",
    },
    {
        "id": "R54",
        "kind": "conclusion",
        "wrong": "那个带边框的框**样式像按钮，但点不动**（实测它是 `<span>`",
        "why": "**框是 `div`，`span` 是它里面的标签。**\n"
               "对源码 `web/src/components/agent/agent-connect-view.tsx`："
               "那个带边框的框是 `div className=\"flex items-center gap-2 rounded-md border …\"`，"
               "里面依次才是 **`<span>`**（装「移除插件」四个字）、**`<code>`**（那条命令）、"
               "以及一个复制 `Button`——**那是整行里唯一能点的东西**。\n"
               "★ **M139 那次运行时读数并没有错**：光标停在框里，落点确实是那个 `span`。"
               "**错在把「标签是 span」推广成了「框是 span」**——"
               "**一次读数只证明它落在的那个元素是什么，不证明它所在的容器是什么。**\n"
               "★ **顺带把「长得一模一样」升级成更强的说法**：源码里「移除插件」与"
               "「移除手动 MCP」两行**由同一个 `.map()` 渲染**（同一个二元数组、同一段 JSX），"
               "**不只是长得像，本来就是同一份代码**——M209 一并写进正文",
        "fixed_in": "M209",
    },
    {
        "id": "R55",
        "kind": "conclusion",
        "wrong": "「最近画布」区**一片空白**",
        "why": "**排障条目把可观察的线索写成了「没有线索」，比不写更糟。**\n"
               "看图与对源码（`web/src/pages/canvas/index.tsx`）都表明：那一区**不是空白**，"
               "而是一张 `min-h-[190px]` 的完整空态卡——一个加号方块、"
               "标题 `canvas.empty`「**还没有画布**」、"
               "说明 `canvas.emptyDescription`「新建一个画布后，就可以独立保存节点、连线和画布外观。」\n"
               "★ **原句后半截「这张图和别的画布列表长得一样」也是错的**："
               "有画布时渲染的是 `CanvasProjectCard` 卡片列表，**与这张空态卡完全不是一回事**。\n"
               "★ **但「画布不见了」和「本来就没有画布」分不出来这半句是对的**——"
               "只是**理由整个错了**：空态由 `sortedProjects` 的 `else` 分支触发，"
               "**应用不记得你删过什么**，所以两种情况看到的是**同一句**「还没有画布」。\n"
               "**这个区别很要紧**：按原文读者会以为界面上没有任何线索、因而忽略那句话，"
               "**而那句「还没有画布」正是排障时唯一能看到的观察**。**M211 已整段重写**",
        "fixed_in": "M211",
    },
    {
        "id": "R56",
        "kind": "conclusion",
        "wrong": "连点复制就会叠加出一长串 Copy",
        "why": "**「复制」有两条路径，原文只测了其中一条，就把结论写成了通则。**\n"
               "★ **错在把一次读数推广成了全局规律**——与 M209 那次同一个毛病，"
               "只是这次栽在「同一个动作有两个入口」上。\n"
               "实测证据（`scripts/probe-copy-title.js`，**阳性对照先成立**）：\n"
               "右键「复制」连按两次 → `文本` / `文本 Copy` / `文本 Copy Copy`，**一路叠加**；\n"
               "再拿**同一个**「文本 Copy Copy」改走 `Ctrl / Cmd + C` 再 `Ctrl / Cmd + V` →\n"
               "新节点**仍然叫「文本 Copy Copy」**，画布上同名节点变成 2 个。\n"
               "源码侧（`web/src/pages/canvas/project.tsx`）：`duplicateNode` 是"
               "**无条件** `` `${source.title} Copy` ``（:1033，位置 +36/+36）；"
               "`pasteCopiedNodes` 则是 `node.title.endsWith(\" Copy\") ? node.title : "
               "`` `${node.title} Copy` ``（:1098，位置摆到**画布中心**）——"
               "**标题已带 ` Copy` 就不再追加**。\n"
               "★ **位置也一并测了**（M212 补）：右键两次实测偏移都是 `+36, +36`，"
               "快捷键那一次是 `-72, -72`（朝画布中心走）。**两条路径位置规则也不同**，"
               "原文只写了前者。\n"
               "★ **为什么这条比一般措辞问题严重**：同一页恰恰在教读者"
               "「多选要用 `Ctrl / Cmd + C / V` 一次复制全部选中」——"
               "**照着推荐做，反而会撞名**，而原文还保证「连点就叠出一长串 Copy」。\n"
               "**M212 已把该段改写成两条路径的对照表，并补了撞名警告与两个交叉引用**",
        # 下面这一处是 SOURCE_OBSERVATIONS 里对**被订正原句的刻意引述**（M212 自己的分析），
        # 不是漏改。锚点按 M205 的规矩取「恰好命中 1 行」的片段。
        "allow_in": [
            "SOURCE_OBSERVATIONS.md#可复制有**两条路径**，标题规则不一样。",
        ],
        "fixed_in": "M212",
    },
    {
        "id": "R57",
        "kind": "conclusion",
        "wrong": "实测断点：≥ 861px 完整导航横排 / ≤ 640px 导航折叠",
        "why": "**把「取样过的三个宽度」当成了「断点」，而真正的分界点被漏掉了。**\n"
               "那张表自己写着「实测断点」，可 861 / 640 / 420 **全都不是断点**——\n"
               "它们只是当时拍过照、量过的三个宽度（`20-responsive-640.png` 拍的就是 640）。\n"
               "后果是 **641–860 整段在表里成了空白**，而它其实**整个都属于「已折叠」**——\n"
               "**表的上下两侧都写错了**：按表在 800px 试会看到导航是横排的（表说 861 以下不是），\n"
               "按表在 700px 试会看到导航已折叠（表里 641–860 没交代）。\n"
               "2026-10-04 逐档实测（只改视口宽，窗口高 950）：\n"
               "380 / 420 / 500 / 640 / **799** → 导航 `display: none`、可见导航项 **0/5**；\n"
               "**800** / 1000 / 1440 → 导航 `display: flex`、可见导航项 **5/5**。\n"
               "**799 与 800 两档正好夹住边界，真实切换点是 800。**\n"
               "★ **机制上还有一层**：实现用的是 `@container` 查询而不是 `@media`\n"
               "（`web/src/styles/globals.css`：`@container (min-width: 800px)` 里\n"
               "`.td-app-top-nav-menu` 与 `.td-app-top-nav-links` 的 display 对调，\n"
               "另有 `@container (max-width: 420px)` 收起品牌文字）。\n"
               "**这里容器宽恰好等于视口宽**（`.td-app-top-nav-inner` 是 `w-full max-w-[1440px]`），\n"
               "所以「按窗口宽度记」在 800 这档上碰巧成立——**但机制不同，别当成同一回事**。\n"
               "**M213 已把表改成 800 分界，并写明 640 / 420 只是取样点、不是断点**",
        "fixed_in": "M213",
    },
]


def iter_body_pages(root: Path):
    for name in BODY_PAGES:
        path = root / name
        if path.is_file():
            yield path
    for pattern in BODY_GLOBS:
        yield from sorted(root.glob(pattern))
    # M153：把**账本**纳入扫描范围。
    # 实测盲区：把已订正的「Dock 认不出 9 个」写进 `task-inventory.yml`，
    # 本门禁报 ok——**它连扫都没扫到那个文件**。
    # M152 补登记 R25 时只扫了正文三页，**「补登记」这件事自己也有覆盖不全**。
    #
    # ★ **AUDIT.md / PROGRESS.md 不纳入**：那两个文件本身就是订正记录，
    #   逐行豁免不现实（全库命中 22 处），而且把它们纳入会让本门禁的信号淹没在噪声里。
    #   **账本不一样**——它的 review_note 记录的是各任务的取证结论，
    #   **未订正的错误说法混进去就是真的错了**，值得守。
    for name in LEDGER_PAGES:
        path = root / name
        if path.is_file():
            yield path
    # M203：截图清单同理纳入（理由见 MANIFEST_PAGE 处的注释）。
    # 它是**唯一一份逐条记「当时量到了什么」的清单**，112 条 `verified_locator`
    # 里任何一个数字过期，正文都不会自动知道。
    mpath = root / MANIFEST_PAGE
    if mpath.is_file():
        yield mpath


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    pages = list(iter_body_pages(root))
    if not pages:
        print("[FAIL] 没有扫到任何正文页，检查传入的路径")
        return 1

    problems: list[str] = []
    checked = 0

    # M183：**每条订正都必须声明它改的是「结论」还是「描述」**，否则这个计数会失真——
    # M182 就出现过「改了事实、计数却没动」的情况，审计时看不出来。
    # 判据只有一条：照着原说法做，会不会做错事？
    #   conclusion —— 会：找错入口、以为能做不能做、以为状态会自己恢复、归因归错
    #   wording    —— 不会：结论与行动都不受影响，受影响的只是数字、措辞、标签
    VALID_KINDS = {"conclusion", "wording"}
    kind_counter: dict[str, int] = {}
    missing_kind: list[str] = []
    bad_kind: list[str] = []
    for item in RETRACTIONS:
        kind = item.get("kind")
        if not kind:
            missing_kind.append(item.get("id", "?"))
            continue
        if kind not in VALID_KINDS:
            bad_kind.append(f"{item.get('id', '?')}={kind!r}")
            continue
        kind_counter[kind] = kind_counter.get(kind, 0) + 1
    if missing_kind:
        problems.append(
            f"有 {len(missing_kind)} 条订正没写 \"kind\"：{'、'.join(missing_kind)}。"
            "**每条都必须声明它改的是结论还是描述**——"
            "M182 出现过「改了事实、计数却没动」的情况，"
            "分不开这两类，『已订正 N 条』这个数字就说明不了手册到底被改过多少次"
        )
    if bad_kind:
        problems.append(
            f"有 {len(bad_kind)} 条订正的 kind 不在 {sorted(VALID_KINDS)} 内：{'、'.join(bad_kind)}。"
            "**取值写错等于没分类**，门禁不许它悄悄过"
        )

    # M203 新增：needle **不得是纯「键=数字」的取证记法**。
    #
    # ★ **这条判据是从一次真实漏改里长出来的，不是预防性想象。**
    #   R31 当年登记的 needle 是 `x=963`——那是 `SOURCE_OBSERVATIONS.md` 里
    #   一条坐标记录的**内部写法**，而手册正文从来没有这么写过（正文写「931 px」）。
    #   结果：**M160 把 931px 订正掉了，同一张表里的「同屏，相距 931 px」却活了两批没人发现**，
    #   而门禁一路报 ok——**needle 与读者会读到的说法不是同一个字符串，等于没设防。**
    #
    # **判据为什么取这一种形态**（M195 的教训：判据必须窄到能全对，窄不到就别假装是门禁）：
    #   先量过全库 45 条 needle 的形态——**纯「键=数字」只有 R31 这一条**。
    #   逐条排除过几个更宽的候选，它们都会误报：
    #     - 「needle 不得短于 N 字」→ R26 `三处按钮区`、R27 `共 5 种` 都只有 5 个字，
    #       **但它们是读者真会读到的说法**，是好的 needle。长度不是判据。
    #     - 「needle 必须含汉字」→ 英文界面文案（如 `Connection settings`）是合法 needle，
    #       那条判据会把正确的登记判成错。
    #   只有 `^[A-Za-z_][A-Za-z0-9_]*=\d+$` 这一种形态**既覆盖真实漏改、又不误报**：
    #   手册正文是中文散文，读者读到的说法必含汉字或中文标点；
    #   `x=963` 这种形态**只可能来自取证记录**，而取证记录属于账本——
    #   **拿 needle 去守一个读者从不读的地方，等于给自己发一张假的免检章。**
    #
    # ★ **有意不禁止的**：其它 ASCII needle（英文界面文案、DOM 选择器片段）仍然合法。
    #   这里只禁「纯键=数字」这一种精确形态，**不扩大**。
    NOTATION_ONLY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\d+$")
    notation_needles: list[str] = []
    for item in RETRACTIONS:
        needle = item.get("wrong", "")
        if NOTATION_ONLY.fullmatch(needle):
            notation_needles.append(f"{item.get('id', '?')}={needle!r}")
    # M205 新增：**每个内容锚点必须恰好命中 1 行**。
    #
    # ★ 这道判据盯的是一个**正在恶化、还没恶化**的结构性漏洞（M204 量出来的）：
    #   `allow_in` 的内容锚点形态是「文件#行内片段」，而**匹配用的是逐字子串**。
    #   一旦同一个片段在该文件里出现两行以上，**豁免会同时罩住那几行**——
    #   而门禁不会报任何东西。写锚点的人以为只放行了 1 行，实际放行了 N 行。
    #   **这与 M203 那把从不报警的量具是同一族病：看起来在约束，实际在放宽。**
    #
    #   两种坏法方向相反，必须分开报：
    #     命中 **0 行** = 死配置。锚点已经对不上任何行，**豁免根本没在生效**
    #       （此时门禁会因为 needle 命中而报红，但报的是「错误说法复现」，
    #        读者会以为正文出了新错，其实是自己的豁免烂了）；
    #     命中 **≥2 行** = 偷偷放宽。**这才是危险的那一种，且完全静默。**
    #
    # 为什么判据取「恰好 1 行」而不是别的：M204 实测全库 10 个内容锚点**无一例外都是 1 行**，
    # 判据在现有数据上全对；而任何更宽的判据（例如「不得多于 2 行」）都会放过真正的放宽。
    # 现有形态里不存在「有意锚定多行」的用法——**要放行多行就多登记几条**。
    anchor_breadth: list[str] = []
    for item in RETRACTIONS:
        for where in sorted(item.get("allow_in", [])):
            if "#" not in where:
                continue
            fname, frag = where.split("#", 1)
            path = root / fname
            if not path.is_file():
                # 文件不在（被改名/删掉）——交给上面的写法校验与扫描时报错，不在这里重复
                continue
            n = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if frag in line)
            if n != 1:
                kind = "死配置（0 行，豁免根本没生效）" if n == 0 else f"偷偷放宽（罩住 {n} 行）"
                anchor_breadth.append(f"{item.get('id', '?')} 的 {where} 命中 {n} 行，{kind}")
    if anchor_breadth:
        problems.append(
            f"有 {len(anchor_breadth)} 个内容锚点没有恰好命中 1 行：\n"
            + "\n".join("      " + b for b in anchor_breadth) + "\n"
            "  **豁免必须精确到一行。** 0 行是死配置（锚点已对不上，豁免没在生效）；\n"
            "  2 行以上是**偷偷放宽**——匹配用的是逐字子串，同一片段出现在几行就放行几行，\n"
            "  而门禁不会报任何东西。**要放行多行就多登记几条，别让一个片段罩住一片。**"
        )

    if notation_needles:
        problems.append(
            f"有 {len(notation_needles)} 条订正的 needle 是**纯「键=数字」的取证记法**："
            f"{'、'.join(notation_needles)}。\n"
            "  **needle 必须是读者真会读到的说法**，而不是取证记录里的坐标写法——\n"
            "  R31 当年就登记了 `x=963`，而正文写的是「931 px」，**两者根本不是同一个字符串**：\n"
            "  M160 把 931px 订正掉了，表格里那处「同屏，相距 931 px」照样活了两批，门禁一路报 ok。\n"
            "  **要守读者读得到的那句话**（表格单元就按 R11/R12/R13 的写法整格取），\n"
            "  取证坐标留在账本里，不要登记成 needle。"
        )

    for item in RETRACTIONS:
        needle = item["wrong"]
        # 豁免位置只有一种写法：`文件#行内稳定片段`。
        # M152 起先是「文件:行号」，M160 查出它**一插行就错位**，
        # 于是增设了内容锚点形态。**M173 把行号形态正式退役**——
        # 当时全仓还有 2 处在用行号，迁完之后一个使用者都不剩。
        # 保留两种写法等于让人自己判断「哪种情况用哪种」，
        # 而手册文件全都在频繁编辑，**答案是恒定的：都用锚点**。
        # M172 做过严格 A/B 对照：同一份插了 2 行的内容，
        # 行号形态 exit=1（5 条假阳性），内容锚点形态 exit=0。
        # 另外豁免必须窄：写全名文件等于整页开豁免，那会让这道门禁形同虚设。
        allowed = set(item.get("allow_in", []))
        for where in sorted(allowed):
            if re.fullmatch(r"[^:#]+#\S{8,}", where):
                continue  # 内容锚点形态
            if re.fullmatch(r"[^:]+:\d+", where):
                problems.append(
                    f"[{item['id']}] allow_in 的豁免位置仍是已退役的行号写法：{where!r}。"
                    "**必须写成「文件#行内稳定片段」**"
                    "（如 `SOURCE_OBSERVATIONS.md#三处按钮区的顺序固定`）。"
                    "行号精确但**插入即错位**：M172 实测，在该行上方插 2 行，"
                    "5 个行号豁免全部失配、门禁报出 5 条根本不存在的复现。"
                )
            else:
                problems.append(
                    f"[{item['id']}] allow_in 的豁免位置写法不合法：{where!r}。"
                    "**必须精确到「文件#行内锚点」**"
                    "（如 `SOURCE_OBSERVATIONS.md#三处按钮区的顺序固定`）；"
                    "**锚点那一段不得含任何空白**（含空格）且须满 8 个字符——"
                    "中文行文里英文术语前后常有空格，随手挑的片段多半不合法；"
                    "只写文件名等于把整页都开豁免，读者再也拦不住这里出错的说法。"
                )
                allowed = {w for w in allowed if w != where}
        # 把内容锚点预解析成「文件 → 锚点片段集合」，供下面逐行匹配
        anchors: dict[str, set[str]] = {}
        for where in allowed:
            if "#" in where:
                fname, frag = where.split("#", 1)
                anchors.setdefault(fname, set()).add(frag)
        hits: list[str] = []
        exempted: list[str] = []
        for page in pages:
            rel = page.relative_to(root).as_posix()
            for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
                if needle in line:
                    where = f"{rel}:{lineno}"
                    # 行号命中，或本行含本文件登记过的任一锚点片段 → 豁免
                    hit_anchor = next(
                        (f"{rel}#{frag}" for frag in anchors.get(rel, ()) if frag in line),
                        None,
                    )
                    if where in allowed:
                        exempted.append(where)
                    elif hit_anchor:
                        exempted.append(hit_anchor)
                    else:
                        hits.append(where)
        checked += 1
        if hits:
            problems.append(f"[{item['id']}] 订正过的错误说法重新出现：{needle!r}\n      {item['why']}\n      出现在：{', '.join(hits)}")
        if exempted:
            print(f"  [豁免] [{item['id']}] {', '.join(exempted)} 是刻意反例引述（已登记 allow_in）")

    _c = kind_counter.get("conclusion", 0)
    _w = kind_counter.get("wording", 0)
    print(
        f"[retractions] 已登记订正 {len(RETRACTIONS)} 条"
        f"（结论性 {_c} / 描述性 {_w}），扫描正文 {len(pages)} 页"
    )

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
