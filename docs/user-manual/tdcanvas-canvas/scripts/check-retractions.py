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
        "allow_in": ["task-inventory.yml#首页卡片悬停操作（下载/重命名/删除）与多选、封面预览运行时取证"],
    },
    {
        "id": "R2",
        "wrong": "可以整体拷到另一台机器导入",
        "why": "同 R1，画布侧只实现了导出、从未实现读回",
        "fixed_in": "M47",
        "allow_in": ["task-inventory.yml#首页卡片悬停操作（下载/重命名/删除）与多选、封面预览运行时取证"],
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
        "allow_in": ["task-inventory.yml#（撤销/重做/画布更改会自动保存）与刷新持久化多次实测"],
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
        # M159 新增：这句原错误说法在 use-agent.md 的订正说明里被**刻意引述**——
        #   「凡是带坐标系的数字都要警惕」这句话需要一个反面例子，
        #   而读者正是要看到「原来错在哪」才说得清。
        "allow_in": ["10-tasks/use-agent.md#那次的数字带着当时的画布缩放量"],
    },
    {
        "id": "R24",
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
        "wrong": "Dock 认不出 9 个",
        "why": "M125–M129 连续四批据「按 class 名找悬停浮层」写下「左侧 Dock 16 个按钮里有 9 个认不出、悬停无任何提示」，M129 还把它写进了探针的结论。**M132 第 63 次否证整组作废**：Dock 用的是自研浮层，类名 `pointer-events-none absolute left-[calc(100%+8px)]`，**不含 tooltip / tip 任何字样**；按类名找只抓得到同区域的 antd `div.ant-tooltip`。实测 Dock 8 个按钮悬停提示**逐字齐全**，「删除选中」也有浮层。正确判据是**悬停前后全页可见文本取差集**，不依赖类名（2026-10-02 M132）",
        "fixed_in": "M132",
        "allow_in": ["task-inventory.yml#运行时走查完成（清数据首启→新建→空画布→首页项目卡）"],
    },
    {
        "id": "R26",
        "wrong": "三处按钮区",
        "why": "M132 补出**顶栏**这一处按钮区后，两页仍写「三处按钮区」，实际是**四处**（左侧 Dock / 节点悬浮工具条 / 画布视图控制 / 顶栏）。M139 回走时订正为四处并把顶栏列进去。写死数量而不列出处，下批加一处就会漏改（2026-10-02 M139）",
        "fixed_in": "M139",
        "allow_in": ["task-inventory.yml#手工撞见的剪刀复用做成全应用扫描", "SOURCE_OBSERVATIONS.md#三处按钮区的顺序固定"],
    },
    {
        "id": "R27",
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
        "wrong": "所有节点类型的工具条都是 4 个按钮",
        "why": "M137 第一版探针的**假结论**，症状像产品有个统一的 4 按钮工具条。真因：节点默认全部叠在画布中心，按 DOM 顺序取中心点点选，**命中的永远是最上层那一个**，七种类型数出来全是同一个节点（按钮文字还逐轮往后挪一位）。正确判据是 `elementFromPoint` 阳性对照 + 每轮清空画布只留一个节点（2026-10-02 M137）",
        "fixed_in": "M137",
    },
    {
        "id": "R29",
        "wrong": "按钮本身没有状态变化，说明这个功能没有状态",
        "why": "M136 实测 13 个按钮的 `aria-pressed` / `expanded` / `checked` / `current` **全为 null**，点下去信号全不变。但**这是读法边界，不是产品结论**：「隐藏连线」那种开关状态显示在**按钮外观**上、不在这些属性里。**「按钮没有状态变化」≠「这个功能没有状态」**，写进手册时必须把这条边界一起写上（2026-10-02 M136）",
        "fixed_in": "M136",
    },
    {
        "id": "R30",
        "wrong": "顶栏实际是 56px",
        "why": "**错在源码引用指到了另一个组件**。M108 写的类名 `h-14` 确实存在于代码里，但长在 `web/src/components/layout/app-top-nav.tsx:101`（`td-app-top-nav`，工作区层顶栏），而**画布页的顶栏是 `web/src/components/canvas/canvas-top-bar.tsx:70` 的 `h-16` = 64px**。2026-10-03 M160 运行时实测顶栏 `y=0`、高 `64`；`git log` 确认 `h-16` 自首个提交 `f7f06b1` 起从未改过——**属当初取错证据，不是版本漂移**。**「源码里找得到」不等于「就是这个东西的」**（2026-10-03 M160）",
        "fixed_in": "M160",
    },
    {
        "id": "R31",
        "wrong": "x=963",
        "why": "「两把剪刀相距 931 像素」是一次**具体会话的读数，不是界面属性**：左侧 Dock 那一列钉死在屏幕上，节点工具条那一列**跟着节点跑**。2026-10-03 M160 实测同一个有图图片节点放在画布左侧时两把只相距 163px。原记录里的 `x=32` 还有个更隐蔽的问题——**那是按钮内 16px 图标的左边缘，不是按钮本身的左边缘**（按钮本身 x=24，32 = 24 + (32−16)/2）。**「同屏且相距很远、不会误点」的结论不变，变的只是不能靠数像素认按钮**",
        "allow_in": ["SOURCE_OBSERVATIONS.md#这一列的像素值已作废"],
        "fixed_in": "M160",
    },
    {
        "id": "R32",
        "wrong": "批量摆放节点时给画布上方留出至少 50px 的空白",
        "why": "M108 订正后的预防值，而那条订正的**推导前提（顶栏高度）本身就是错的**（见 R30）。2026-10-03 M160 实测：13 按钮工具条顶边恒在**节点顶 − 104**（100% 缩放，8 个拖拽点零偏差坐实），顶栏底边 64，**临界值是节点顶 = 168**，比原值大 3 倍多。**由错数推出的数，错得不随机、错得很整**——所以订正时必须连推导链一起验，不能只验结论那个数",
        "fixed_in": "M160",
    },
    {
        "id": "R33",
        "wrong": "104 那一段是跟着缩放走的",
        "why": "**M160 自己写下、没实测就断言的一句话**，M163 用九档缩放把它否掉。工具条渲染在 `</TDCanvasSurface>` **之外**（屏幕空间），**自身 48px 高度不随画布缩放变**，所以偏移是 **`48×k + 56`** 而不是 `104×k`。实测 25/40/60/80/100/130/160/200/300% 九档，偏移 68/75.2/84.8/94.4/104/118.4/132.8/152/200，**与 `48k+56` 偏差全为 0**；按比例模型在 100% 以外每档都错（25% 档差 42px）。**方向也是反的：缩放越大要留的空白越多**。预防临界值随之改为 `120 + 48k`（2026-10-03 M163）",
        "fixed_in": "M163",
    },
    {
        "id": "R34",
        "wrong": "一个可点的\u300c移除插件\u300d按钮",
        "why": "M174 实测：**它不是一个按钮。** 那行是\u300c标签 + 命令\u300d的说明，\u300c移除插件\u300d是 `<span>`、其父 div 的 class 是 `rounded-md border px-2 py-1.5`（**样式像按钮，所以肉眼会当成按钮**），但 cursor=auto、无 onclick，且**整页 29 个可点元素里含\u300c移除插件\u300d的是 0 个**。旁边那个能点的是右端的复制图标。写\u300c可点\u300d会让读者去找一个点不动的东西，然后以为自己操作错了",
        "fixed_in": "M174",
    },
    {
        "id": "R35",
        "wrong": "到 /config 里搜\u300c插件\u300d能搜到 5 处",
        "why": "**归因错了，而且这一步照做根本看不到。** 那 5 处字全在**右侧常驻 Agent 面板**里，不在配置区：三个路由（/config、/canvas、/）实测\u300c插件\u300d出现次数完全相同（各 7 次 = 5 个文本节点、共 7 次字符出现），5 个命中点 x 坐标全部落在同一个 aside 内，而 /config 的 `main` 与说明栏内均为 **0 次**。更要紧的是**面板默认折叠**：折叠态实测可见命中 **0/5**，点顶栏 title=\u300c打开 Agent\u300d的按钮（1313,12）之后才变成 **5/5**。手册没说这个前提，读者照做会在空配置页上搜个空",
        "fixed_in": "M174",
    },
    {
        "id": "R37",
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
        "id": "R36",
        "wrong": "连线可点击的区域就是那条贝塞尔曲线本身，没有额外的加粗命中层",
        "why": "M177 实测**有**一条 16 像素宽的透明命中带：连线的 path 本身就是 "
        "`stroke=\"transparent\" stroke-width=\"16\"` + `pointer-events: stroke`，"
        "**它不是「那条细线」，它就是加粗层**。实测沿法线偏移：d=0~7 命中连线、d>=8 落空，"
        "**命中半宽 7~8 屏幕像素**，而视觉线宽只有 1~2px（画布缩放实测 100%，"
        "CTM/滑块/节点尺寸/正文百分比四条读数互证）。"
        "**所以「连线点不中」的真正原因是节点盖在上面**（节点 z-10 > 连线层 z-[2]），不是线太细",
        "fixed_in": "M177",
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
