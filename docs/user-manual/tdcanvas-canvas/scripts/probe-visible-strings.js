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
 *   ROUTES="/ /config /assets" node ...               转储多个路由
 *   ROUTES="/canvas/ID::画布+Agent面板::打开 Agent"    进到某个状态再转储一次
 *   OUT=/tmp/strings.json node ...                    写文件而不是 stdout
 *
 * ══ ★★ 状态覆盖面：这道题的全部难度都在这里 ══
 *
 *   M245 第一版每条路由只导一次，**「」串的 A 可见命中率只有 22/206**。
 *   看着像手册烂得离谱，**其实一份都不算**——逐条读未命中项就知道：
 *   「只需配置一个 API_KEY」是**弹窗**的副标题、「打开导航菜单」是**窄屏**才出现的
 *   汉堡提示、「导航」是**抽屉**的标题、「连接 TDCanvas Agent」是**面板打开后**才有的。
 *   **它们全都存在，只是存在我这次没进的那个状态里。**
 *   → 所以 ROUTES 支持 `路径::标签::要点的 aria` 三段式：
 *     **同一个页面可以转储多次，每次一个状态，标签写清楚这是哪个状态。**
 *     少了这一步，任何命中率都是量具的读数，不是手册的读数（F55）。
 *   ★ 纪律：**不点任何删除类按钮**（「移除插件」「删除」「清空画布」等），
 *     状态步骤只用「打开面板」「点导航」这类不改变数据的动作。
 */
const PW = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
const APP = process.env.TD_APP || 'http://localhost:3000';
/* 每项是 路径 或 路径::标签::aria ；缺省标签就是路径本身 */
const ROUTES = (process.env.ROUTES || process.argv[2] || '/').split(',').map((r) => {
  const [path, label, aria] = r.trim().split('::');
  return { path, label: label || path, aria: aria || '' };
});
const OUT = process.env.OUT || '';
/* 窄屏状态：VIEWPORT=640x900 */
const VP = (process.env.VIEWPORT || '1600x1000').split('x').map(Number);

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
      if (r.aria) {
        // 真实鼠标点击：先量矩形再点中心（不用 el.click()）
        const box = await page.evaluate((re) => {
          const el = Array.from(document.querySelectorAll('button,[role="button"],[role="tab"]'))
            .find((x) => new RegExp(re).test((x.getAttribute('aria-label') || '') + ' ' +
                                             (x.getAttribute('title') || '') + ' ' + (x.innerText || '')));
          if (!el) return null;
          const q = el.getBoundingClientRect();
          return { x: q.x + q.width / 2, y: q.y + q.height / 2, w: q.width, h: q.height };
        }, r.aria);
        if (box && box.w && box.h) {
          await page.mouse.click(box.x, box.y);
          await page.waitForTimeout(1600);
          stepNote = `点开「${r.aria}」后`;
        } else {
          // ★ 点不到必须说出来，不能当成「这个状态没有内容」（M132 纪律）
          stepNote = `★ 点不到「${r.aria}」——本条读数只代表点开之前的状态`;
          console.error('[提醒] ' + stepNote);
        }
      }
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
