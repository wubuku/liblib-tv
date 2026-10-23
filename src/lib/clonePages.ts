/**
 * 1032-③：**已完成克隆页面的单一真源**。
 *
 * ⭐⭐⭐⭐⭐ **为什么必须有一份真源**：本仓库有三条线会各自列举「有哪些克隆页」——
 *   ① 应用里的「克隆总览」页；② 仓库根 `README.md` 的路由表；
 *   ③ `docs/CLONE_PAGES_INDEX.md` 的「怎么到达 / 怎么交互测试」。
 *   ⇒ ⇒ ⇒ ⇒ ⇒ 而**三份手写清单必然漂移** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 *   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 所以只允许写一份、其余三处从它派生** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 *   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 `scripts/jimeng_probe1033_clone_reachability.py`
 *   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 会核「三处与真源逐条对得上」⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 *
 * ⭐⭐⭐⭐⭐ **「完成」的定义**：一个页面算「已完成的克隆成果」的条件是
 *   ① 它在 `src/app/**\/page.tsx` 里有**真实的路由文件**（实测，不许手列）；
 *   ② 从站点根目录 `/` **走得到**它（链接闭包里可达）；
 *   ③ 它在本文档里有「怎么到达」＋「怎么交互测试」两段。
 *   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而**光有路由文件还不够** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 *   ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「走得到」是「完成」的一部分，不是附加项** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 *
 * ⚠️ **口径**：本文件只登记**已实现的页面**。
 *   `docs/research/tdcanvas-*`、`docs/research/beeftv-*` 是**研究对象**、不是复刻页面，
 *   ⇒ ⇒ ⇒ ⇒ ⇒ 而研究结论**不许**出现在这里冒充「可交互页面」⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
 */

export type ClonePageKind = "clone" | "site";

export interface ClonePageEntry {
  /** 稳定 id：文档对账与门禁锚点用它，不随文案改动而变。 */
  id: string;
  /** 页面名称（页面上显示的字） */
  name: string;
  /** 可直接打开的路由（必须是真实存在的路由文件） */
  route: string;
  /** 复刻对象：这一页对应源站的哪个产品/页面 */
  product: string;
  /** 一句话：这一页能做什么 */
  summary: string;
  /** 从站点根目录 `/` 怎么走到这里（人类可读，页面与文档共用这一份） */
  reachableVia: string[];
  /** 交互测试：用户可以真的点什么、应该看到什么 */
  trySteps: string[];
  /** mock 边界：哪些是假数据、哪些动作**不接后端**、哪些**绝不能点** */
  mockBoundary: string;
  /** 对应的用户手册（仓库内路径，可为 null） */
  manual: string | null;
  /** `clone` = 克隆成果；`site` = 本站自身的索引页 */
  kind: ClonePageKind;
}

export const CLONE_PAGES: ClonePageEntry[] = [
  {
    id: "liblib-canvas",
    name: "LibTV 画布",
    route: "/",
    product: "liblib.tv/canvas（视频故事板画布）",
    summary:
      "复刻 LibTV 主画布：故事板节点图、图片上下双浮层、素材库、导演台（3D）、快捷键与生成面板（全部 mock）。",
    reachableVia: [
      "直接打开站点根目录 `/`（这是站点根路由本身）",
      "从任意克隆页点左上角 logo／返回「回到主页」也会回到这里",
    ],
    trySteps: [
      "点画布空白处双击 ⇒ 打开「添加节点」面板；点节点看上下浮层",
      "选中节点后按 ⌘C／⌘V／⌘Z 试复制、粘贴、撤销；框选后试成组",
      "点顶栏「导演台」卡片上的「打开导演台」⇒ 进 3D 场景，可拖机位、拉时间轴",
      "打开顶栏「素材」抽屉看素材库；打开「分享」面板看原型态提示",
    ],
    mockBoundary:
      "所有生成/发布/会员/积分入口都是**原型态**（点了只出本地状态提示，不发任何请求）；画布数据只活在当前标签页内存，刷新即复位。",
    manual: "docs/user-manual/libtv-canvas/README.md",
    kind: "clone",
  },
  {
    id: "liblib-projects",
    name: "LibTV 全部项目",
    route: "/project",
    product: "liblib.tv 的项目列表",
    summary:
      "复刻「全部项目」列表：画布卡片、新建项目、回收站（30 天保留期）、多画布切换。",
    reachableVia: [
      "在站点根目录点顶栏 logo 右侧的**项目菜单**（∨）⇒ 选「全部项目」",
      "也可以直接打开 `/project`",
    ],
    trySteps: [
      "点「新建项目」⇒ 列表里多一张卡片 ⇒ 点卡片在新标签页打开画布",
      "删除一张卡片 ⇒ 进「回收站」⇒ 恢复 ⇒ 剩余天数按删除日期重算",
      "把浏览器窗口缩窄 ⇒ 看左侧栏与卡片区的响应式排布",
    ],
    mockBoundary:
      "项目只存在当前标签页的内存 store 里（不持久化）；「创建新项目」是本地动作，不接任何账号或计费。",
    manual: "docs/user-manual/libtv-canvas/README.md",
    kind: "clone",
  },
  {
    id: "frameos-canvas",
    name: "FrameOS 画布",
    route: "/frameos/canvas/demo",
    product: "frameos.cn 的 AI 画布",
    summary:
      "复刻 FrameOS：Prompt 编辑器 + 节点画布、素材库、历史、右键菜单、生成流程（原型演示）。",
    reachableVia: [
      "在站点根目录点顶栏左上角的 **FrameOS 入口**（logo 芯片）",
      "也可以直接打开 `/frameos`（它会重定向到 demo 画布）",
    ],
    trySteps: [
      "在 Prompt 编辑器里输入文字 ⇒ 点生成 ⇒ 看 mock 结果进画布",
      "点画布空白处右键 ⇒ 看上下文菜单；点节点看浮动工具条与右侧编辑面板",
      "打开「素材库」选素材 ⇒ 试拖进画布；打开「帮助」看快捷键表",
      "用 ⌘Z／⌘⇧Z 试撤销/重做；试框选多个节点后成组",
    ],
    mockBoundary:
      "生成永远返回**本地 mock 结果**，不调用任何模型、账号或计费接口；独立 store，不与 LibTV/即梦共享状态。",
    manual: "docs/user-manual/frameos-canvas/README.md",
    kind: "clone",
  },
  {
    id: "jimeng-canvas",
    name: "即梦 AI 画布",
    route: "/jimeng/canvas/demo",
    product: "jimeng.jianying.com 的 AI 画布",
    summary:
      "复刻即梦画布：节点工具条、AI 对话抽屉、生成面板（图片/视频/音频/重绘/扩图）、资产库、时间线/主体/导演台节点、右键菜单与快捷键。",
    reachableVia: [
      "在站点根目录左下角的**站点导航条**点「即梦画布」",
      "也可以直接打开 `/jimeng`（它会重定向到 demo 画布）",
    ],
    trySteps: [
      "点节点 ⇒ 看节点工具条；拖节点 ⇒ 看跟随移动与吸附辅助线",
      "点左侧 AI 按钮 ⇒ 打开 AI 对话抽屉 ⇒ 输入文字看引用与插入面板",
      "点顶栏「资产」⇒ 打开资产库；点节点图片 ⇒ 试裁剪、扩图、重绘面板",
      "新建「时间线」「主体」「导演台」节点 ⇒ 看它们各自的参数面板",
      "画布空白处右键 ⇒ 看画布右键菜单；按 ⌘K／? ⇒ 看快捷键面板",
    ],
    mockBoundary:
      "**所有生成类按钮都只出「执行前一步」的本地状态**，不发起真实生图/生视频、不消耗积分；节点数据是 demo mock，刷新即复位。",
    manual: "docs/user-manual/jimeng-canvas/README.md",
    kind: "clone",
  },
  {
    id: "clone-index",
    name: "克隆总览",
    route: "/clones",
    product: "本站自身的索引页（不是某个源站的复刻）",
    summary:
      "一页列全所有已完成的克隆页：每页的路由、从根目录怎么走到、可以怎么交互测试、mock 边界与手册入口。",
    reachableVia: [
      "在站点根目录左下角的**站点导航条**点「克隆总览」",
      "也可以直接打开 `/clones`",
    ],
    trySteps: [
      "点页面上任意一条目的「打开」⇒ 新标签页打开对应克隆页",
      "点「从根目录怎么走」里的那一步 ⇒ 看它描述的入口确实在根目录上",
      "改浏览器窗口宽度 ⇒ 看索引页的响应式排布",
    ],
    mockBoundary:
      "本页是**纯索引**：内容全部来自 `src/lib/clonePages.ts` 这一份真源，不含任何 mock 数据、也不发起任何请求。",
    manual: "docs/CLONE_PAGES_INDEX.md",
    kind: "site",
  },
];

/** 按 id 取一页（取不到就抛 —— 不许静默返回 undefined）。 */
export function getClonePage(id: string): ClonePageEntry {
  const hit = CLONE_PAGES.find((p) => p.id === id);
  if (!hit) throw new Error(`clonePages: 没有 id 为 ${id} 的页面`);
  return hit;
}

/** 全部页面的路由（去重、保序）。 */
export function clonePageRoutes(): string[] {
  return Array.from(new Set(CLONE_PAGES.map((p) => p.route)));
}
