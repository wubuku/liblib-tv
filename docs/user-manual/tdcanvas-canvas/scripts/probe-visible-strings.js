#!/usr/bin/env node
/**
 * probe-visible-strings.js —— 转储一个路由上「读者能读到的所有字符串」（M245 建立）
 *
 *   要回答的问题：手册里写成「…」或 `code` 的那些界面字符串，
 *   **在真实界面上到底找不找得到？**
 *
 *   种子是 F54（2026-10-05 M244）：R99 与 R100 两处真错同属一族——
 *   **手册用一个「界面上并不存在的名字」去指称一个控件**。
 *   `Close` 是读屏名（屏幕上只有 × 图标），「重新读取 Skill」也是读屏名
 *   （屏幕上只有 ⟳ 图标，悬停提示写的是「重新读取」）。
 *   这类错误**肉眼核图很难发现**，因为图上就是「有个按钮在那儿」——
 *   所以要把它变成一次机械读数：**把界面上能读到的字全倒出来，让手册去撞它。**
 *
 * ══ 为什么这四类要分列，不能只报一坨 ══
 *
 *   1. **可见文字**（leaf 文本，有几何、祖先可见）——读者眼睛能读到的
 *   2. **aria-label**——读屏软件念的，**屏幕上没有**
 *   3. **title**——悬停提示，**默认停留够久才出现**
 *   4. **placeholder**——空输入框里的灰字，**打字就没了**
 *
 *   ★ **F54 的整条教训就是「这四类不是同一回事」**：
 *   把 2/3/4 混进 1，手册就会拿一个只有读屏才有的名字去描述界面。
 *   所以**报告必须让调用方能区分「在界面上找得到」与「只在读屏名里找得到」**。
 *
 * ══ 五条量测纪律（M245 当场踩的与沿用的）══
 *
 * 1. ★ **「没匹配上」先怀疑判据的覆盖面，再怀疑手册**。
 *    手册的「…」里什么都有：界面标签、用户的话、作者自己的用词。
 *    **把三类混在一起当「界面字符串」，产出的假阳性会淹没真错**（M243 的 F53 第 ③ 类）。
 *    → 本探针**只负责转储**，不负责判定；判定在 check-strings 那侧，且必须分层报数。
 *
 * 2. ★ **悬停提示默认不出现**，所以第 3 类要单独 `hover` 一遍按钮才收得到；
 *    不 hover 就报「没有 title」是**把「没触发」说成「不存在」**（M132 同族）。
 *    → 本探针对每个可见按钮都做一次真实鼠标悬停，**只收悬停期间新出现的可见文本**。
 *
 * 3. ★ **命中判据用几何，不用 aria**（M132 第 7b 条）。
 *    悬停时先确认 `document.querySelectorAll(':hover')` 链末端的几何落在按钮矩形内，
 *    **没落在里面就不算命中**——否则「没触发」会被记成「没有提示」。
 *
 * 4. ★ **非零几何 ≠ 可见**（M135 第 8b 条）：类名里带 `-hidden` / `invisible` 的元素
 *    有 12×12 的尺寸、`display`/`visibility`/`opacity` 全正常，**但它根本不显示**。
 *    → 可见性判断里必须包含类名检查。
 *
 * 5. ★ **不碰任何删除类按钮，也不真的去触发它们**。
 *    「移除插件」「移除手动 MCP」「删除」「清空画布」只读它们的文字与状态，不点。
 *
 * 用法：
 *   node scripts/probe-visible-strings.js /            转储一个路由，输出 JSON 到 stdout
 *   ROUTES="/;/config;/assets" node ...               转储多个路由（★ 分号，不是逗号）
 *   ROUTES="/canvas/ID::画布+Agent面板::打开本地 Codex 面板"   进到某个状态再转储一次
 *   ROUTES="/canvas/ID::上传了素材::upload:^上传资产$|/path/to/x.png"   点它并把文件塞进去
 *   OUT=/tmp/strings.json node ...                    写文件而不是 stdout
 *
 * ★ **`upload:按钮文字|文件路径`**（M247 加）
 *   点那个按钮，等系统的文件选择器弹出来，再把本地文件塞进去。
 *   **走的是 Playwright 的 `filechooser` 事件**——
 *   而不是 2026-09-26 那套「拷进 `web/public/__rt__/` 再页内 fetch」的绕行，
 *   那一套是给**内置浏览器**（它不支持文件选择器）准备的，
 *   **外部 Playwright 直接 `setInputFiles` 就行，不用往应用仓里拷文件、也不用删。**
 *   ★ **素材清单见 `TEST_MEDIA_ASSETS.md`**（14 项，10 图 / 2 音 / 2 视频，字节数已核）。
 *   ★ **上传是免费的**：它只把字节存到本机。**计费的是「生图 / 生成」那一步，
 *     而那一步在 `NEVER_CLICK` 里，永远不会被点到。**
 *
 * ══ 状态动作语法（M245 末加）══
 *
 *   状态那一位现在可以写**一串动作**，用 `||` 分隔，**从左到右依次执行**：
 *     click:TEXT      按可见文字点（真实鼠标点击，量矩形再点中心）
 *     dblclick:TEXT   双击
 *     dblclickxy:x,y  在视口坐标双击（用来双击画布空白）
 *     clickxy:x,y     在视口坐标单击
 *     type:TEXT       往当前焦点输入文字
 *     key:Escape      按键
 *     wait:800        单纯等一会儿（毫秒）
 *   例（双击空白建一个文本节点）：
 *     /canvas/ID::建了文本节点::dblclickxy:800,450||wait:600||click:文本||wait:800||type:测试节点||key:Escape
 *   ★ 这样写是因为**手册里大量断言的对象根本不在「空画布」上**：
 *   节点工具条、侧边面板、连接菜单、九宫格对话框……全都要「画布上真的有节点」。
 *   **而一个空的画布转储出来的字，只能覆盖手册的一小半**（F55 的第一个开关）。
 *
 * ══ ★★ 状态覆盖面：这道题的全部难度都在这里 ══
 *
 *   M245 第一版每条路由只导一次，**「」串的 A 可见命中率只有 22/206**。
 *   看着像手册烂得离谱，**其实一份都不算**——逐条读未命中项就知道：
 *   「只需配置一个 API_KEY」是**弹窗**的副标题、「打开导航菜单」是**窄屏**才出现的
 *   汉堡提示、「导航」是**抽屉**的标题、「连接 TDCanvas Agent」是**面板打开后**才有的。
 *   **它们全都存在，只是存在我这次没进的那个状态里。**
 *   → 所以状态不是可选项，是**决定读数有没有意义的那一半**。
 *   ★ 纪律：**不点任何删除类按钮**（「移除插件」「删除」「清空画布」等），
 *     **也不点任何计费的生成按钮**（M0 起就定下的纪律）。
 *     建节点用的是「文本」这类**本机完成、不调用付费生成**的类型。
 */
const PW = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
const APP = process.env.TD_APP || 'http://localhost:3000';
/* 每项是 路径 或 路径::标签::动作串（动作用 || 分隔）
 *
 * ★★ **路由之间必须用分号，不能用逗号**——M245 之后踩过一次：
 * 动作语法里有 `dblclickxy:800,450`，**而路由原先正是按逗号切的**，
 * 于是坐标的 `450` 被当成一条新路由，页面 URL 直接变成
 * `http://localhost:3000450||wait:800||...`，**整串动作一个都没执行，
 * 而输出照样打印「执行 1 个动作后」**——只有靠「建完节点可见文字还是 12 条、
 * 和空画布一模一样」才发现。逗号留给坐标，分号给路由。 */
const ROUTES = (process.env.ROUTES || process.argv[2] || '/').split(';').map((r) => {
  const t = r.trim();
  const [path, label, acts] = t.split('::');
  // ★ 路径里只允许 / 与字母数字与 - _；出现 | , : 就是分隔符用错了
  //   （`/800,450` 也以 / 开头，所以「必须以 / 开头」那条判据拦不住它——实测过）
  if (!/^\/[A-Za-z0-9/_-]*$/.test(path)) {
    console.error(`[FAIL] 路由「${t}」的路径部分「${path}」不是合法路径`
      + '（只允许 / 与字母数字与 - _）——'
      + '多半是分隔符用错了：路由之间要用分号 ; 分隔，'
      + '逗号只留给 dblclickxy:800,450 的坐标。'
      + '（M245 之后踩过：坐标的 450 被当成一条路由，'
      + '页面 URL 变成 http://localhost:3000450||…，整串动作一个都没执行，'
      + '而输出照样打印「执行 N 个动作后」。）');
    process.exit(2);
  }
  return { path, label: label || path, acts: (acts || '').split('||').filter(Boolean) };
});
const OUT = process.env.OUT || '';
/* 窄屏状态：VIEWPORT=640x900 */
const VP = (process.env.VIEWPORT || '1600x1000').split('x').map(Number);

/* ★ 不可点清单：命中就直接拒绝执行，并说明为什么。
 *
 *   **用精确全名，不用子串也不用正则**——理由有二，第二条是本批当场撞上的：
 *   ① 语义上就该是精确的：我要拒绝的是「点那个叫『清空画布』的按钮」，
 *      不是「点任何名字里带『清空』的东西」。
 *   ② `check-probe-contracts` 的第三条判据是「危险文案的**真前缀**不许出现在
 *      正则字面量或 `includes('…')` 里，除非文件里出现过完整文案」。
 *      ★ **M246 第一版写成了正则 `/(清空画布|删除全部|^删除$|…)/`，
 *      当场被那条门禁判成「用『删除』这类子串去选『删除当前画布』」。**
 *      **而它是误报**——那串的正用是「不点它们」，方向正好相反。
 *      但**误报不构成放宽门禁的理由**（M195/M155 那条纪律），
 *      正确做法是**让代码满足门禁自己的放行条件**：
 *      改成精确全名数组，六个不可逆按钮**全名照抄文档里的 DESTRUCTIVE 清单**，
 *      门禁的「出现完整文案即放行」自然生效。
 *      ★ **结果是代码比原来更准**——精确匹配不可能误伤同名之外的按钮。
 *
 *   计费动作另算：文本节点右上角那个按钮界面上写「**生图**」而不是「生成」，
 *   ★ **清单最初只有「生成」，漏了这个同义按钮**——
 *   **一个只覆盖了同义按钮一半的护栏，比没有护栏更危险**：
 *   它会让人以为「计费动作已经挡住了」。现在两种写法都在。 */
const NEVER_CLICK = [
  // —— 不可逆的六个，全名与 PUBLISH.md 的 DESTRUCTIVE 清单一致 ——
  '删除当前画布', '移除节点', '删除选中', '删除全部', '删除', '清空画布',
  // —— 计费的（本机不会真的去点）——
  '生图', '生成', '换一换', '重新生成', '创建图片', '创建视频', '创建音频',
];
const isNeverClick = (s) => NEVER_CLICK.includes((s || '').trim());

/* ★ 纪律 4：可见性 = 有几何 + 祖先链正常 +（可选）类名里有「这个元素是隐藏的」标记
 *
 *   ★★★ **这条判据在 M245 第一次跑的时候整页归零，修完又立刻长出第二个假阳性。**
 *   两处都是**我自己写错的**，而两处的表现完全一样：**全页归零 / 砍掉本该算的**。
 *   ① 初版 `/(^|-|_)(hidden|invisible)(-|$)/` **把 Tailwind 的 `overflow-hidden`
 *      判成「这个元素是隐藏的」**——`overflow-hidden` 的意思是「把溢出的裁掉」，
 *      跟显不显示毫无关系，而它是全站最常见的类名之一。`/config` 上那个 logo
 *      往上有两层都是它，于是 **172 个叶节点、22 个按钮，一个都没被判可见**。
 *   ② 修成「按词元、且排除 `overflow-*`」之后，`ant-form-item-required-mark-hidden`
 *      又被抓了——**那是一个 226×16 的 LABEL，明明在显示**，
 *      `-hidden` 说的是它**内部的必填星号**被隐藏，不是这个标签页被隐藏。
 *   ★ **结论：类名不是判可见性的可靠依据。** M135 第 8b 条那个
 *   `ant-input-clear-icon-hidden`（12×12、几何非零、确实不显示）是真的，
 *   而 `ant-form-item-required-mark-hidden` 是假的——**同一条正则，一个真一个假。**
 *
 *   → 修法不是继续加例外，而是**让被拒的元素带着理由一起报出来**：
 *     `out.hidden` 逐条列出「哪个元素、因为哪条规则被拒、它上面写着什么字」。
 *     **判据可以不可靠，但不能悄悄**——M132 那条「报告里只允许出现原始读数」
 *     在这里就是「被丢掉的东西也必须看得见」。
 */
const VISIBLE = `(() => {
  const why = (e) => {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return ['几何为 0（' + Math.round(r.width) + 'x' + Math.round(r.height) + '）'];
    const out = [];
    for (let n = e; n && n !== document.body; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.display === 'none') out.push('祖先 ' + n.tagName + ' display:none');
      if (s.visibility === 'hidden') out.push('祖先 ' + n.tagName + ' visibility:hidden');
      if (s.opacity === '0') out.push('祖先 ' + n.tagName + ' opacity:0');
    }
    return out;
  };
  /* 类名规则单列，**只做提示不做否决**——理由见上面的判据反思 */
  const classHit = (e) => (e.getAttribute('class') || '').split(/\\s+/).filter((c) => {
    if (!c) return false;
    if (c === 'hidden' || c === 'invisible') return true;
    if (c.startsWith('overflow-')) return false;
    return /-hidden$/.test(c) || /-invisible$/.test(c);
  });
  const visible = (e) => why(e).length === 0;
  return { visible, why, classHit };
})()`;

/* 在页面里跑的转储函数（字符串形式求值，符合本库既有写法） */
const DUMP = `(() => {
  const V = ${VISIBLE};
  const visible = V.visible, why = V.why, classHit = V.classHit;
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim();
  const out = { visibleText: [], aria: [], title: [], placeholder: [], value: [],
                buttons: [], inputs: [], links: [], hidden: [] };
  const push = (arr, v) => { if (v && !arr.includes(v)) arr.push(v); };

  // 1) 可见文字
  //    ★★ **只收叶子节点这个规则本身是个洞（M245 当场撞上的）**：
  //    「注册 AI 土豆 · 获取 API Key ↗」那个按钮里带一个 ↗ 图标，
  //    **于是它不是叶子节点**；而它的父元素也有子节点，同样不是叶子——
  //    **结果这个按钮上的字在转储里彻底消失，尽管它明明在页面上。**
  //    而「文字 + 图标」正是手册引用最多的那类按钮（带 ↗ 的外链、带 svg 的图标按钮）。
  //    → 修法：**叶子节点照收，另外再收「自身直接文本非空」的元素**。
  //      后者会让父级整段文字也进池子，**这只会让匹配更宽、不会更严**，
  //      而宽一点正是这里要的（判据宁可多给证据，也不要悄悄漏）。
  const ownText = (e) => Array.from(e.childNodes)
    .filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join('')
    .replace(/\\s+/g, ' ').trim();
  document.querySelectorAll('body *').forEach((e) => {
    if (!visible(e)) return;
    const leaf = e.children.length === 0;
    const own = ownText(e);
    if (leaf) {
      const t = txt(e);
      if (t) push(out.visibleText, t);
      return;
    }
    if (own) push(out.visibleText, own);
  });
  document.querySelectorAll('body *').forEach((e) => {
    if (e.children.length === 0) return;
    if (visible(e)) return;
    const t = txt(e);
    if (!t) return;
    if (!out.hidden.some((h) => h.text === t.slice(0, 60))) {
      out.hidden.push({ text: t.slice(0, 60), tag: e.tagName,
                        reason: why(e), classHit: classHit(e) });
    }
  });
  // 2~4) 属性
  document.querySelectorAll('[aria-label]').forEach((e) => { if (visible(e)) push(out.aria, e.getAttribute('aria-label').trim()); });
  document.querySelectorAll('[title]').forEach((e) => { if (visible(e)) push(out.title, e.getAttribute('title').trim()); });
  document.querySelectorAll('input,textarea').forEach((e) => {
    if (!visible(e)) return;
    push(out.placeholder, (e.getAttribute('placeholder') || '').trim());
    push(out.value, (e.value || '').trim());
    out.inputs.push({ type: e.getAttribute('type') || '', ph: e.getAttribute('placeholder') || '',
                      disabled: e.hasAttribute('disabled') });
  });
  // 按钮与链接：带禁用态，因为「能不能点」是 F54 的另一半
  document.querySelectorAll('button,[role="button"]').forEach((b) => {
    if (!visible(b)) return;
    out.buttons.push({ text: txt(b), aria: (b.getAttribute('aria-label') || '').trim(),
                       title: (b.getAttribute('title') || '').trim(),
                       disabled: b.hasAttribute('disabled'),
                       cursor: getComputedStyle(b).cursor });
  });
  document.querySelectorAll('a').forEach((a) => {
    if (!visible(a)) return;
    out.links.push({ text: txt(a), href: a.getAttribute('href') || '' });
  });
  out.pageTitle = document.title;
  out.path = location.pathname;
  out.dsf = window.devicePixelRatio;
  return out;
})()`;

/* 悬停一遍所有可见按钮，收「悬停期间新出现的可见文本」（纪律 2 + 3） */
async function hoverCollect(page) {
  const boxes = await page.evaluate(`(() => {
    const visible = ${VISIBLE}.visible;
    const b = [];
    document.querySelectorAll('button,[role="button"]').forEach((e, i) => {
      if (!visible(e)) return;
      const r = e.getBoundingClientRect();
      b.push({ i, x: r.x + r.width / 2, y: r.y + r.height / 2,
               w: r.width, h: r.height, name: (e.getAttribute('aria-label') || e.innerText || '').trim() });
    });
    return b;
  })()`);
  const before = new Set(await page.evaluate(
    `Array.from(document.querySelectorAll('body *')).filter((e) => !e.children.length)
       .map((e) => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim()).filter(Boolean)`));

  const found = [];
  for (const b of boxes) {
    if (!b.w || !b.h) continue;
    await page.mouse.move(b.x - 30, b.y - 30);
    await page.mouse.move(b.x, b.y, { steps: 4 });
    await page.waitForTimeout(350);
    // 纪律 3：命中判据 = :hover 链末端几何落在按钮矩形内
    const hit = await page.evaluate((bb) => {
      const chain = document.querySelectorAll(':hover');
      const last = chain[chain.length - 1];
      if (!last) return { hit: false, why: ':hover 链为空（指针多半不在视口内）' };
      const r = last.getBoundingClientRect();
      const inside = r.x <= bb.x && r.y <= bb.y &&
                     r.x + r.width >= bb.x && r.y + r.height >= bb.y;
      if (!inside) {
        const cr = chain[chain.length - 2] ? chain[chain.length - 2].getBoundingClientRect() : null;
        return { hit: false, why: ':hover 链末端几何不在按钮矩形内',
                 lastRect: [r.x, r.y, r.width, r.height],
                 prevRect: cr ? [cr.x, cr.y, cr.width, cr.height] : null };
      }
      return { hit: true };
    }, b);
    if (!hit.hit) { found.push({ name: b.name, skipped: hit.why }); continue; }
    const after = await page.evaluate(
      `Array.from(document.querySelectorAll('body *')).filter((e) => !e.children.length)
         .map((e) => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim()).filter(Boolean)`);
    const added = after.filter((t) => !before.has(t));
    for (const t of added) if (!found.some((f) => f.name === b.name && f.hover === t)) {
      found.push({ name: b.name, hover: t });
    }
  }
  return found;
}

(async () => {
  let ctx;
  try {
    ctx = await PW.chromium.launchPersistentContext(PROFILE, {
      headless: true, viewport: { width: VP[0], height: VP[1] } });
  } catch (e) {
    console.error('[FAIL] Playwright 启动失败：' + (e && e.message));
    process.exit(2);
  }
  const page = ctx.pages()[0] || await ctx.newPage();
  const all = {};
  try {
    for (const r of ROUTES) {
      await page.goto(APP + r.path, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
      let stepNote = '';
      for (const act of r.acts) {
        // ★ 不可点清单先查：这一步在本批之前不存在，是 M245 之后补的护栏
        const raw = act;
        // ★ 兼容 M245 的老写法：第三段没有动作前缀时，整段当作「点这个文字」
        const VERBS = ['wait', 'key', 'type', 'dblclickxy', 'clickxy', 'dblclick', 'click', 'upload'];
        const m = raw.match(/^([a-z]+):(.*)$/);
        const verb = m && VERBS.includes(m[1]) ? m[1] : 'click';
        const arg = m && VERBS.includes(m[1]) ? m[2] : raw;
        if (isNeverClick(arg) && (verb === 'click' || verb === 'dblclick')) {
          stepNote = `★ 动作「${act}」命中不可点清单，已跳过（不执行）`;
          console.error('[拒绝] ' + stepNote);
          continue;
        }
        try {
          if (verb === 'wait') { await page.waitForTimeout(Number(arg) || 500); continue; }
          if (verb === 'key') { await page.keyboard.press(arg); await page.waitForTimeout(500); continue; }
          if (verb === 'type') { await page.keyboard.type(arg); await page.waitForTimeout(400); continue; }
          if (verb === 'dblclickxy' || verb === 'clickxy') {
            const [x, y] = arg.split(',').map(Number);
            if (verb === 'dblclickxy') await page.mouse.dblclick(x, y);
            else await page.mouse.click(x, y);
            await page.waitForTimeout(700);
            continue;
          }
          if (verb === 'upload') {
            // 点「按钮文字」→ 等文件选择器弹出来 → 把本地文件塞进去
            const [btnText, filePath] = arg.split('|');
            if (!filePath || !require('fs').existsSync(filePath)) {
              console.error(`[提醒] upload 动作的文件不存在：${filePath}`);
              continue;
            }
            if (isNeverClick(btnText)) {
              console.error(`[拒绝] upload 目标「${btnText}」在不可点清单里`);
              continue;
            }
            const box = await page.evaluate((a) => {
              const re = new RegExp(a);
              const hit = (s) => re.test(s || '');
              const el = Array.from(document.querySelectorAll('button,[role="button"],a,li'))
                .find((x) => hit(x.getAttribute('aria-label')) || hit(x.getAttribute('title')) ||
                              hit((x.innerText || '').replace(/\s+/g, ' ').trim()));
              if (!el) return null;
              const q = el.getBoundingClientRect();
              return { x: q.x + q.width / 2, y: q.y + q.height / 2, w: q.width, h: q.height };
            }, btnText);
            if (!box || !box.w || !box.h) {
              console.error(`[提醒] upload 找不到按钮「${btnText}」`);
              continue;
            }
            const [chooser] = await Promise.all([
              page.waitForEvent('filechooser', { timeout: 8000 }),
              page.mouse.click(box.x, box.y),
            ]);
            await chooser.setFiles(filePath);
            await page.waitForTimeout(2000);
            console.error(`[ok] 已上传 ${filePath.split('/').pop()}（${box.w}x${box.h} 的按钮）`);
            continue;
          }
          if (verb === 'click' || verb === 'dblclick') {
            // 真实鼠标点击：先量矩形再点中心（不用 el.click()）
            // ★ 三个字段**各自**测，不要拿拼接串测——拼接串前后带着分隔用的空格，
            //   `^文字创作$` 这种带锚点的写法必然不中。
            //   （M246 踩过：那个按钮明明存在、明明写着「文字创作」，
            //   而工具报「点不到」——因为它测的是 "  文字创作"。）
            const box = await page.evaluate((a) => {
              const re = new RegExp(a);
              const hit = (s) => re.test(s || '');
              const el = Array.from(document.querySelectorAll('button,[role="button"],[role="tab"],a,li'))
                .find((x) => hit(x.getAttribute('aria-label')) || hit(x.getAttribute('title')) ||
                              hit((x.innerText || '').replace(/\s+/g, ' ').trim()));
              if (!el) return null;
              const q = el.getBoundingClientRect();
              return { x: q.x + q.width / 2, y: q.y + q.height / 2, w: q.width, h: q.height };
            }, arg);
            if (box && box.w && box.h) {
              if (verb === 'dblclick') await page.mouse.dblclick(box.x, box.y);
              else await page.mouse.click(box.x, box.y);
              await page.waitForTimeout(900);
            } else {
              // ★ 点不到必须说出来，不能当成「这个状态没有内容」（M132 纪律）
              console.error(`[提醒] 点不到「${arg}」——本条读数只代表这个动作之前的状态`);
            }
          }
        } catch (e) {
          console.error(`[提醒] 动作「${act}」失败：${e && e.message}`);
        }
      }
      if (r.acts.length) stepNote = `执行 ${r.acts.length} 个动作后`;
      const d = await page.evaluate(DUMP);
      d.hover = await hoverCollect(page);
      d.route = r.path;
      d.label = r.label;
      d.step = stepNote;
      all[r.label] = d;
      console.error(`[ok] ${r.label.padEnd(26)} ${stepNote} 可见文字 ${d.visibleText.length} / ` +
                    `aria ${d.aria.length} / title ${d.title.length} / ` +
                    `placeholder ${d.placeholder.length} / 按钮 ${d.buttons.length} / ` +
                    `悬停新增 ${d.hover.filter((h) => h.hover).length}`);
    }
  } catch (e) {
    console.error('[出错]', e && e.message);
    process.exitCode = 1;
  } finally {
    await ctx.close();
  }
  const json = JSON.stringify(all, null, 2);
  if (OUT) require('fs').writeFileSync(OUT, json, 'utf8');
  else process.stdout.write(json + '\n');
})();
