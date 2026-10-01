# Batch 614 — 导演台属性列：面板底色/左边框 + 标题条 + 列的顶边与下沿

日期：2026-10-01
验收脚本：`scripts/verify-liblib-batch614.py`（48 项，桌面 + 移动两腿）
合同迁移：`scripts/verify-liblib-batch610.py`（97 → 99 项）
取证脚本：`/tmp/src593/probe614.py`（列的整棵子树）、`probe614b`（高度是内容驱动还是视口锚定）、`probe614c`（滚动区直接子节点）、`probe614d`（边框色与标题条子节点数、computed 字体）、`probe614e`（3D canvas 盒）
参考图：`docs/design-references/liblib-inspector-column-614-1920.png`

## 靶心

`probe613` 走全量可交互元素时冒出来的一条：源站的属性列**容器**是 `[1639, 0, 281, 1020]`，clone 的是 `[1640, 88, 280, 880]` —— 差 36px 高、1px 宽。与 613 修的左列同根：clone 把列当中间 flex 子节点的 `inset-y-0`，而源站的列是浮在满幅 body 上的覆盖层。

## 源站实测（source fact）

```
div.absolute.right-0.top-0.z-20.flex.w-[281px].flex-col.overflow-hidden
                                                        [1639, 0, 281, 1020]
  div.flex.min-h-0.flex-1.flex-col.overflow-hidden.border.w-[281px]
     .border-y-0.border-l.border-r-0                       bg rgb(33,33,33)
     border-left: 1px rgba(255,255,255,0.08)；右/上/下三边 0px
    div.flex.shrink-0.items-center.justify-between.h-12.px-3
                                                        [1640, 0, 280, 48]
      span.text-[15px].font-medium.text-neutral-50  "摄像机"
                                                [1652, 11.9, 45, 23.3]
        computed font 15px/23.25px/500，color rgb(247,247,247)
                                                ← 恰好 1 个子节点
    div.min-h-0.flex-1.overflow-y-auto                     [1640, 48, 280, 972]
```

`justify-between` 配单个子节点即贴左；x=1652 = 1640 + 12px `px-3`，逐字吻合。

## 两条被推翻的历史读数

**1. batch 610 的「源站该列没有左边框」只对了一半。** 源站确实没有**整列**的边框，但列**内部**的面板有一条 1px `border-l`，落在 1639..1640。所以正确的 border-box 是 **281 @1639**，内容仍是 280 @1640 —— batch 610 当初量到的内容几何是对的，理由错了一半。按约定**迁移**它的两条断言（`panel:width-280` / `panel:x-1640` → `panel:width-281-border-box` / `panel:x-1639`），并补 `panel:1px-left-border-white-8` 与 `panel:content-origin-still-1640` 两条把「内容起点没变」钉住。610 现 99/99。

**2. batch 606 的「右头 280px 定宽列 = 选中对象名」被推翻。** 它量的那条带 —— `div.flex.shrink-0.items-center.justify-between.h-12.px-3` @`[1640,0,280,48]`、内含一个 `text-[15px] font-medium text-neutral-50` @`[1652,11.9,45,23.3]` —— 就是**属性列自己的标题条**，而它的文字是对象**类别名**（选中机位时「摄像机」），不是对象名（对象名在面板更下面的「名称」字段里；该工程机位叫「机位1」）。batch 606 元素认对了，随后却另建了一条通栏顶栏带着它的第二份拷贝。

本批修标题条本身；顶栏右组不动（它有自己 28 条断言的合同），两者相撞的后果记在下面。

## 两处有意偏离

**顶边取 52，不是源站的 0。** 源站的顶栏只有左头 280px（就在左列那块 aside 里），右列上方是空的。clone 的顶栏是**通栏** grid（batch 606 建的），右组 280px 占着 `[1640,0,280,51]` —— 属性列若也放到 `top-0`，它自己的标题条会被顶栏右组整个盖住，等于新造一个看不见的控件。故上沿 52：中间 flex 子节点从 88 起（52 顶栏 + 36 镜头条），用 `-top-9`（−36px）提上去。

**下沿止于时间线上沿，不是内容驱动。** 源站那 1020 是**内容驱动**的：`probe614b` 实测 `scrollHeight == clientHeight == 972`，根本不滚动，computed 的 `bottom: 130px` 只是派生值、不是声明。但 clone 的相机属性面板内容实测 **1185**，比源站的 907 高 278（多出 可见/未锁定、当前镜头、镜头名称 等行 —— 另一个靶心）。照抄内容驱动会让列冲出视口 140px。

反过来先试了「拉满到视口底」，结果 batch 95 回归当场抓到**真回归**：clone 的时间线比源站高 52px（182 vs 130），拉满后时间线盖住面板下段，`data-director-panorama-clear` 点不到（Playwright 报 `导出视频到画布 … subtree intercepts pointer events`）。所以下沿交给中间区，**止于时间线上沿 968** —— 这正是源站那 1020 与时间线 1021 的关系。验收里专门加了一条 `panel:deep-content-stays-reachable` 守住这个坑。

`z` 保留 30 而非源站的 20：窄屏下属性列是抽屉，必须压过 `z-20` 的移动端遮罩；桌面上两者无重叠区域。

## 顺带修的两处

- **标题行高**：源站该 span 的 computed 是 `15px/23.25px/500`，clone 继承下来是 `15px/22.5px/500`。`text-[15px]` 只设字号，行高要单给 —— 补 `leading-[23.25px]`。
- **视口框内缩**：613 改完左列后，`main` 的内缩 `left-[46px] / left-[266px] / right-[288px]` 已经和列的实际几何对不上了。改为 `left-[48px] / left-[281px] / right-[281px]`，3D canvas 从 `[266,88,1366,880]` 变为 `[281,88,1358,880]` —— 左缘贴左列右缘、右缘贴右列左缘，中间不再露缝。

## 验收脚本里三处自纠

- `document.querySelector('canvas')` 先命中的是 240×135 的**机位预览小画布**，不是场景画布；改为 `canvas[data-engine]`（并保留宽度兜底）。
- 面板的 border-box 起点是 1639（与源站一致），内容起点才是 1640 —— 断言按各自的实际语义写。
- 移动端抽屉是 `right-0` + 281 宽，390px 视口下开在 x=109、**贴右缘**，不是「靠左」；另外触发器 `打开属性面板` 在 `div.absolute.left-3.top-3.max-[899px]:flex` 里，不在底部药丸 `data-director-viewport-toolbar` 里。

## 记下但不改的（下一批靶心）

1. **源站的 3D canvas 是满幅 `[0,0,1920,1150]`**（`probe614e`），clone 是 `[281,88,1358,880]` 的内缩框 —— 源站把场景铺满整窗、面板浮在上面，clone 把场景挤在两列之间。这是取景差异，不只是外框。
2. **面板内容高差 278px**：源站滚动区是 6 个 `<section class="border-b border-white/8 px-4 py-4">`（页签 / sticky 预览 / 摄像机属性 / FOV / 相机截图 / 隐藏的虚拟相机），clone 是一条 `space-y-4 px-4 py-3` 加若干 `label`/`div`，且页签行在**滚动区外面**（源站在里面）。clone 另有源站此处没有的 可见/未锁定、当前镜头、镜头名称 三组行。
3. **移动端顶栏**：视角切换器（170px、`left-1/2 -translate-x-1/2`、`z-10`）压住「收起」钮，batch 94 移动端那条腿点 56 次都命中不了它。基线对照（`cp` 到 /tmp 再 `git checkout --`，不用 stash）确认与 613/614 无关，是既有缺陷。

## 回归

`614`(48) · `610`(99，合同迁移后) · `95`（本批一度弄红，已修）· `613`(53) · `606`(28) · `609`(76) · `611`(49) · `587`(27) · `605`(38) · `608`(15) · `612`(112) · `93` · `96` · `89` · `35` · `36` · `50` 全绿。

## 不声称

- 标题条的文字**只在「选中机位」这一态**有源站读数；没有把源站驱动到其它类别，故 clone 既有的措辞（角色 / 群众 / 角色组 / 场景物体 / Scene）原样保留并标为推断，不新造文案。
- 源站属性列是容器，本身无点击行为可录；声称的是几何、配色、边框、字体，以及 clone 自己的页签/字段/收起/移动端抽屉仍可用。
