# -*- coding: utf-8 -*-
"""1032-④：**登记册** —— 当前已知的「用户能点、点了什么都不会发生」的地方。

⚠️ **为什么它是真源、而且住在源码里**
  · 「现状」由扫描器扫出来（可枚举的那两类）；
  · 「登记册」是**人工判读**的结果 —— 有一类糊弄**静态枚举不出来**
    （文案承诺了代码里没有的行为、状态只落在本地、参数被丢弃…），
    ⇒ ⇒ 那几类**只能逐条钉**。
  · 而真源**必须住在源码里**（不是产物 JSON）：产物每次都被同步成「现状」
    ⇒ ⇒ 比它的话，「少一条也红」那条判据**根本不成立**（与 1032-① 同因）。

每条登记项长这样：
    id       登记项的编号（C01…）
    state    "open" / "fulfilled" —— **它现在还是不是糊弄形态**
    kind     "TOAST" / "DEAD"（可枚举：现场扫得到的）/ "PROMISE"（枚举不到、逐条钉的）
    key      可枚举项的稳定键（文件 + 属性名 + 同名出现序号；**行号是位置不是身份**）
    file     出问题的文件
    promise  这个界面**承诺给用户**什么（源站 SOURCE_FACT 的逐字依据）
    current  「它现在还是那个糊弄形态」—— 判据：随 `state` 变（见下）
    target   「整改成什么样才算兑现」—— 判据：随 `state` 变（见下）
    why      为什么它是糊弄（人看的理由）

⚠️ `current` 与 `target` 都是**一组**谓词（全部成立才算成立）。

⭐⭐⭐⭐⭐ **`state` 的语义（Batch 1032-④-B 引入）**
------------------------------------------------------
整改一条之后，那条**不能从册子里删掉** —— 删了就没人记得「这里曾经糊弄过」，
下一次改回去也没人拦。⇒ ⇒ 所以登记项**留在册子里**，只改 `state`：

  · `state = "open"`（还没整改）：
      `current` **必须成立**（它现在还是那个糊弄形态）
      `target` **必须不成立**（还没兑现）

  · `state = "fulfilled"`（已整改）：
      `current` **必须不成立**（糊弄形态真的没了）
      `target` **必须成立**（兑现形态真的在）

⇒ ⇒⇒ 于是「改了却不销账」会红（`open` 却 `target` 成立），
⇒ ⇒⇒ 「销了账却没真改」也会红（`fulfilled` 却 `target` 不成立），
⇒ ⇒⇒ **而「整改完又改回去」同样会红**（`fulfilled` 却 `current` 又成立）——
       这一条是**只有留着册子**才可能有的检查。
"""

# ⭐⭐⭐⭐⭐ Batch 1032-④-B：11 条**全部已整改** ⇒ `state` 全部是 `fulfilled`。
#
# ⚠️ 「fulfilled」**不是**「删掉」—— 删掉就没有回退防护了（见文件头）。
#    每条的 `target` 现在**必须成立**（兑现形态在），`current` 现在**必须不成立**
#    （糊弄形态没了）⇒ ⇒ 谁把任何一个改回去，这道门当场红。
REGISTRY = [
    {
        "id": "C01",
        "state": "fulfilled",
        "kind": "TOAST",
        "key": "TOAST#src/components/jimeng/nodes/JimengImageNode.tsx#onAction#0",
        "file": "src/components/jimeng/nodes/JimengImageNode.tsx",
        "promise": "图片节点工具条上的每一项（智能改图 / 扩图 / 智能超清 / 抠图 / 多角度 / 工具菜单）"
                   "都要有真动作；本原型没做的，必须是**诚实的禁用态 + 可见理由**",
        "why": "1032 审计 A1：18 项动作全部只弹一句「X已执行」，画面零变化 —— "
               "而文案恰恰在说「已经做完了」",
        "current": [
            {"type": "key_present",
             "key": "TOAST#src/components/jimeng/nodes/JimengImageNode.tsx#onAction#0"},
        ],
        "target": [
            {"type": "key_absent",
             "key": "TOAST#src/components/jimeng/nodes/JimengImageNode.tsx#onAction#0"},
            {"type": "identifier",
             "file": "src/components/jimeng/nodes/JimengImageNode.tsx", "value": "startTask"},
        ],
    },
    {
        "id": "C02",
        "state": "fulfilled",
        "kind": "TOAST",
        "key": "TOAST#src/components/jimeng/JimengTopBar.tsx#onCreate#0",
        "file": "src/components/jimeng/JimengTopBar.tsx",
        "promise": "「新建画布项目」要真的建出一个项目来（并能在项目面板里切回去）",
        "why": "1032 审计 A6：点了只弹一句「新建画布项目」—— 那句话只是把按钮名复述了一遍，"
               "什么也没建（仓内 jimengFeedback.ts 的注释自己就写着：复述按钮名＝零信息量）",
        "current": [
            {"type": "key_present",
             "key": "TOAST#src/components/jimeng/JimengTopBar.tsx#onCreate#0"},
        ],
        "target": [
            {"type": "key_absent",
             "key": "TOAST#src/components/jimeng/JimengTopBar.tsx#onCreate#0"},
            {"type": "identifier", "file": "src/store/jimengStore.ts", "value": "createProject"},
        ],
    },
    {
        "id": "C03",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengAssetsModal.tsx",
        "promise": "资产库顶部那个 200×36 的搜索框要能真的输入（源站 SOURCE_FACT：搜索输入）",
        "why": "1032 审计 A2：那一格是 <span>搜索</span>，画成了输入框的样子却不是控件；"
               "整个模态不 import store ⇒ 永远空态",
        "current": [
            {"type": "tag_count", "file": "src/components/jimeng/JimengAssetsModal.tsx",
             "tag": "input", "op": "==", "n": 0},
        ],
        "target": [
            {"type": "tag_count", "file": "src/components/jimeng/JimengAssetsModal.tsx",
             "tag": "input", "op": ">=", "n": 1},
            {"type": "identifier", "file": "src/components/jimeng/JimengAssetsModal.tsx",
             "value": "query"},
        ],
    },
    {
        "id": "C04",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/nodes/JimengTimelineNode.tsx",
        "promise": "时间线空态的读屏说明承诺了「拖动排序」与「Shift 键移动」，那就得真的有",
        "why": "1032 审计 A3 / ②b 遗留 B2：sr-only 文案逐字承诺了两种操作，"
               "而全文件没有 draggable / onDragStart / shiftKey —— 读屏用户被引导去做不存在的事",
        # ⭐⭐⭐⭐⭐ Batch 1032-④-B：**口径修正** ——
        #   原来的 `current` 写的是「那段 sr-only 文案还在」⇒ ⇒
        #   但那段文案是**承诺**，不是糊弄形态 ⇒ ⇒ 而且整改后**它应该留着**
        #   （现在它是真话：拖动与 Shift 移动**真的**有了）⇒ ⇒
        #   ⇒ ⇒ 用它当 `current` ⇒ ⇒ 整改完反而判「糊弄形态还在」⇒ ⇒ 门红。
        #   ⇒ ⇒ 真正的糊弄形态 =「承诺的操作**没有实现**」⇒ ⇒
        #   ⇒ ⇒ 改成 `identifier_absent shiftKey`（与 `target` 同一条轴，
        #   ⇒ ⇒ 只是方向相反）。
        "current": [
            {"type": "identifier_absent",
             "file": "src/components/jimeng/nodes/JimengTimelineNode.tsx", "value": "shiftKey"},
        ],
        "target": [
            {"type": "identifier",
             "file": "src/components/jimeng/nodes/JimengTimelineNode.tsx", "value": "shiftKey"},
        ],
    },
    {
        "id": "C05",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengAccountPanels.tsx",
        "promise": "「保存设置」要真的把设置存下来（关掉再开还在）",
        "why": "1032 审计 A5：onClick 只 setSaved(true) —— 改的是组件自己的 useState，"
               "关窗即丢；界面上却写着「已保存」",
        "current": [
            {"type": "identifier_absent",
             "file": "src/components/jimeng/JimengAccountPanels.tsx", "value": "watermark"},
        ],
        "target": [
            {"type": "identifier",
             "file": "src/components/jimeng/JimengAccountPanels.tsx", "value": "watermark"},
        ],
    },
    {
        "id": "C06",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/nodes/JimengVideoNode.tsx",
        "promise": "帧选择器里选中的那一帧（时间码）要被真的用起来",
        "why": "1032 审计 A7：JimengFramePicker 的 onConfirm(frameTime) 把时间传出来了，"
               "而调用点 onConfirm={() => …} 把参数丢掉了 ⇒ 用户选的帧不是他要的那一帧",
        "current": [
            {"type": "identifier_absent",
             "file": "src/components/jimeng/nodes/JimengVideoNode.tsx", "value": "frameTime"},
        ],
        "target": [
            {"type": "identifier",
             "file": "src/components/jimeng/nodes/JimengVideoNode.tsx", "value": "frameTime"},
        ],
    },
    {
        "id": "C07",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengZoomMenu.tsx",
        "promise": "「缩放至选中项」要真的缩放到选中的那个节点",
        "why": "1032 审计 A8：fitView({duration:300, maxZoom:1}) 没传 nodes ⇒ "
               "实际做的是「适配画布」，而标签说的是「缩放至选中项」—— 标签与效果不符",
        "current": [
            {"type": "call_arg_text_absent", "file": "src/components/jimeng/JimengZoomMenu.tsx",
             "callee": "fitView", "value": "nodes"},
        ],
        "target": [
            {"type": "call_arg_text_contains", "file": "src/components/jimeng/JimengZoomMenu.tsx",
             "callee": "fitView", "value": "nodes"},
        ],
    },
    {
        "id": "C08",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengPaneContextMenu.tsx",
        "promise": "空白处右键的「时间线 / 主体 / 导演台 / 从资产库添加 / 本地上传」"
                   "这五项，各自都要有它自己的动作",
        "why": "1032 审计 A9：这五项没有 kind ⇒ 消费者只认四类（文本/图片/视频/音频）"
               "⇒ 点完只关菜单，什么也没发生",
        # ⭐⭐⭐⭐⭐ Batch 1032-④-B：**口径修正** ——
        #   `director` 在实现里是**字符串字面量**（kind 的取值），不是标识符
        #   ⇒ ⇒ 「identifier 里没有 director」这件事**整改前后都成立**
        #   ⇒ ⇒ 门读不出「已兑现」。⇒ ⇒ 与 `target` 同口径改成
        #   ⇒ ⇒ `string_literal` / `string_literal_absent`。
        "current": [
            {"type": "string_literal_absent",
             "file": "src/components/jimeng/JimengPaneContextMenu.tsx", "value": "director"},
        ],
        # ⭐⭐⭐⭐⭐ Batch 1032-④-B：**口径修正** —— 原来写的是
        #   `identifier director`，而实现里 `director` 是**字符串字面量**
        #   （kind 的取值），**不是标识符** ⇒ ⇒ 那个谓词恒为「不成立」
        #   ⇒ ⇒ 门**读不出「这一条已兑现」** ⇒ ⇒ 而「读不出」与「没测到」
        #   长得一模一样。⇒ ⇒ 改成 `string_literal`（与实现同口径），
        #   它**仍然能抓住回退**：回退时那个字面量会消失。
        "target": [
            {"type": "string_literal",
             "file": "src/components/jimeng/JimengPaneContextMenu.tsx", "value": "director"},
        ],
    },
    {
        "id": "C09",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengHistoryMenu.tsx",
        "promise": "「生成历史」要列出真的生成任务",
        "why": "1032 审计 A10：面板恒显「暂无生成历史」—— 那是一句写死的文案，"
               "整个文件不 import store（源站这一层是有内容的）",
        "current": [
            {"type": "identifier_absent",
             "file": "src/components/jimeng/JimengHistoryMenu.tsx", "value": "useJimengStore"},
        ],
        "target": [
            {"type": "identifier",
             "file": "src/components/jimeng/JimengHistoryMenu.tsx", "value": "useJimengStore"},
        ],
    },
    {
        "id": "C10",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/JimengOfflineDialog.tsx",
        "promise": "「保留并同步」与「丢弃修改」要有真的同步 / 丢弃动作",
        "why": "1032 审计 A11：两个按钮只弹一句「离线修改已同步 / 已丢弃离线修改」⇒ "
               "一个字都没同步、也没丢弃",
        "current": [
            {"type": "identifier_absent",
             "file": "src/components/jimeng/JimengOfflineDialog.tsx", "value": "syncOfflineEdits"},
        ],
        "target": [
            {"type": "identifier",
             "file": "src/components/jimeng/JimengOfflineDialog.tsx", "value": "syncOfflineEdits"},
        ],
    },
    {
        "id": "C11",
        "state": "fulfilled",
        "kind": "PROMISE",
        "file": "src/components/jimeng/nodes/JimengVideoMediaCard.tsx",
        "promise": "视频节点要有真的 <video>（能播、能停、有画面）",
        "why": "②b 遗留 B1：媒体卡是「背景图 + 模拟进度条」—— 播放时只有时间码在走，"
               "没有任何视频；用户手册里写的「视频节点能播放」这句话当时是假的",
        "current": [
            {"type": "tag_count", "file": "src/components/jimeng/nodes/JimengVideoMediaCard.tsx",
             "tag": "video", "op": "==", "n": 0},
        ],
        "target": [
            {"type": "tag_count", "file": "src/components/jimeng/nodes/JimengVideoMediaCard.tsx",
             "tag": "video", "op": ">=", "n": 1},
        ],
    },
]
