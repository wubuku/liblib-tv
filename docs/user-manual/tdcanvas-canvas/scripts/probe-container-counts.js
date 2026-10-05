/* probe-container-counts.js —— 同一个容器，用几种「彼此不看对方」的方法各数一遍（M249 建立）
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-container-counts.js
 *
 * ── 为什么要有第二遍 ─────────────────────────────────────────────
 * M248 定了案一条规矩：**两处计数用两条独立读数定案**。当时「自定义工具栏」
 * 那条凑巧有现成的第二条（面板右上角自己写着 12/14），**别的容器没有**。
 * 而没有第二条的容器，等于我只有一个数——**一个数不能证明自己没数错**：
 * M248 自己的两个坏读数（43 与 0）都是「一个数」，而且都长得像真的。
 *
 * ── 几种方法为什么算「独立」 ─────────────────────────────────────
 * **独立性不能靠「我重新数了一遍」**——同一个判据跑两遍还是同一个判据。
 * 这里让它们**在能看见的东西上互不相交**：
 *   · 方法 A（结构族）只读 **标签名 / role / aria-* / 可见几何**，
 *     问「无障碍树里这里有几个控件」。
 *   · 方法 B（指针族）**一个字都不读 role、aria、class**，
 *     只读 **布局引擎的答案**：元素中心是否落在容器矩形内、尺寸是否非零、
 *     `cursor` 是不是 `pointer`、`pointer-events` 有没有被关掉。
 *   · 方法 A 的几何版（`aGeom`）与相交版（`aOverlap`）**判据同 A，只换划范围的方式**。
 * ★ 于是它们可以各自错，而且**错法各不相同——差集本身就是产出**。
 *
 * ── 划范围的三种方式，各自有一种错法（F60） ─────────────────────
 *   · **DOM 包含**：顶栏那条「容器外 1」按定义看不见（它就不在子树里）。
 *   · **中心点落入**：顶栏那条**还是**看不见——那根把手是整面板高（1000px）的元素，
 *     中心在 y=500，远在顶栏那条 64px 高的带子之外。
 *     **中心点判据默认「容器就是目标本身」，而把手的目标是它顶上的那一小截。**
 *   · **矩形相交**：找得到那根把手了，**但反过来会多算**——节点悬浮工具条只有一条窄带，
 *     Dock 飞出的菜单（画布/资产/提示词库）恰好与它相交，多出 3 个。
 *   ★ **没有一种普适。写「容器里有几项」时必须把用的哪种范围一起写出来。**
 *
 * ── 方法 B 踩过的那个坑：`cursor` 是可继承属性（F59） ──────────────
 *   第一版 B 数出来的是**图标有几个零件**（顶栏 6、Dock 10/11，全是 `path`/`circle`）——
 *   按钮上的 `cursor-pointer` 会一路继承给它的 `<svg><path>`，去重又取的最内层。
 *   修法：**只认「自己起头」的那个**——`computed(el)==='pointer'` 且
 *   **父元素的 computed 不是 pointer**（说明这个 pointer 不是继承来的）。
 *   ★ 修完仍不等于「可点」：顶栏 10 个里只有 5 个声明了指针形状，
 *   节点工具条 13 个、Agent 行 7 个**一个都没声明**（实测 0）。
 *   **所以 `cursor:pointer` 量的是「作者给不给指针」，不是「能不能点」。**
 *   那个问题只能靠第五段的真事件回答。
 *
 * ★ **纪律**：无头；真实鼠标点击；`finally` 还原；不点任何删除类或计费类按钮。
 */

const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');
const APP = process.env.TD_APP || 'http://localhost:3000';
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m244-profile';
const CANVAS = process.env.CANVAS_URL || '/canvas/H4UgDBdT3NxvK_C5MLMq5';

const DESTRUCTIVE = new Set([
  '删除', '删除当前画布', '删除全部', '删除节点', '删除所有节点',
  '生图', '生成', '换一换', '重新生成', '运行',
]);

const say = (...a) => console.log(...a);
const J = (o) => JSON.stringify(o, null, 2);

// 页面里读一遍所有计数的实现。**刻意整体放进 evaluate**，
// 免得「Node 侧过滤」与「页面侧过滤」两套语义混起来
// （F58：去重与筛选必须在一处做完，且做完要说清是按什么）。
const IN_PAGE = () => {
  const A_SELECTOR = 'button,[role="button"],[role="menuitem"],[role="tab"],[role="option"],[role="switch"],a[href]';
  const label = (el) => {
    const t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    return t || el.getAttribute('aria-label') || el.getAttribute('title') || '';
  };
  const box4 = (el) => {
    const r = el.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  };
  const shown = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const s = getComputedStyle(el);
    return !(s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0);
  };

  /** 方法 A：只看结构/无障碍属性 + **DOM 包含**。去重取最外层。 */
  function methodA(container) {
    const all = Array.from(container.querySelectorAll(A_SELECTOR)).filter(shown);
    const outer = all.filter((el) => !all.some((o) => o !== el && o.contains(el)));
    return outer.map((el) => ({
      how: el.tagName.toLowerCase() + (el.getAttribute('role') ? '[' + el.getAttribute('role') + ']' : ''),
      name: label(el).slice(0, 24), rect: box4(el),
    }));
  }

  /** 方法 A 的**中心点版**与**相交版**：判据完全一样，只换划范围的方式。 */
  function methodAGeom(container, mode) {
    const cr = container.getBoundingClientRect();
    if (!cr.width || !cr.height) return { hits: [], band: null };
    const hits = [];
    for (const el of Array.from(document.querySelectorAll(A_SELECTOR)).filter(shown)) {
      const r = el.getBoundingClientRect();
      if (mode === 'overlap') {
        if (r.right <= cr.x || r.left >= cr.right || r.bottom <= cr.y || r.top >= cr.bottom) continue;
      } else {
        const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
        if (cx < cr.x || cx > cr.right || cy < cr.y || cy > cr.bottom) continue;
      }
      hits.push(el);
    }
    const outer = hits.filter((el) => !hits.some((o) => o !== el && o.contains(el)));
    return {
      band: box4(container),
      hits: outer.map((el) => ({
        how: el.tagName.toLowerCase() + (el.getAttribute('role') ? '[' + el.getAttribute('role') + ']' : ''),
        name: label(el).slice(0, 24),
        inside: container.contains(el),
        rect: box4(el),
      })),
    };
  }

  /** 方法 B：**不读 role / aria / class / DOM 包含**，只读布局与指针样式。去重取最内层。
   *  ★ 只认「自己起头」的 pointer（父元素不是 pointer）——`cursor` 可继承，见文件头 F59。 */
  function methodB(container) {
    const cr = container.getBoundingClientRect();
    if (!cr.width || !cr.height) return { hits: [], inheritedCount: 0, band: null };
    const ptr = (el) => (el ? getComputedStyle(el).cursor : 'auto');
    const hits = [];
    let inherited = 0;
    for (const el of document.querySelectorAll('*')) {
      if (el === container) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      if (cx < cr.x || cx > cr.right || cy < cr.y || cy > cr.bottom) continue;   // ← 范围判据
      const s = getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) continue;
      if (s.pointerEvents === 'none') continue;
      if (s.cursor !== 'pointer') continue;                                     // ← 命中判据
      if (ptr(el.parentElement) === 'pointer') { inherited++; continue; }      // ← 继承来的，不算
      hits.push(el);
    }
    const inner = hits.filter((el) => !hits.some((o) => o !== el && el.contains(o)));
    return {
      band: box4(container),
      hits: inner.map((el) => ({
        tag: el.tagName.toLowerCase(),
        name: label(el).slice(0, 24),
        inside: container.contains(el),
        rect: box4(el),
      })),
      inheritedCount: inherited,
    };
  }

  /** 容器自己写的数：「12/14」「共 3 条」「0 / 0」都收。 */
  function selfDeclared(container) {
    const t = (container.innerText || '').replace(/\s+/g, ' ');
    const out = [];
    const slash = t.match(/(\d+)\s*\/\s*(\d+)/);
    if (slash) out.push({ kind: 'slash', text: slash[0], nums: [+slash[1], +slash[2]] });
    const gong = t.match(/(?:共|总共|合计)\s*(\d+)\s*(条|个|项|张|款)/g);
    if (gong) out.push({ kind: 'gong', text: gong.join(' | ') });
    return out;
  }

  return { methodA, methodAGeom, methodB, selfDeclared, label, box4 };
};

async function realClick(page, re) {
  const box = await page.evaluate((r) => {
    const rx = new RegExp(r);
    const hit = (s) => rx.test(s || '');
    const el = Array.from(document.querySelectorAll('button,[role="button"],[role="tab"],a,li'))
      .find((x) => hit(x.getAttribute('aria-label')) || hit(x.getAttribute('title')) ||
                    hit((x.innerText || '').replace(/\s+/g, ' ').trim()));
    if (!el) return null;
    const q = el.getBoundingClientRect();
    return { x: q.x + q.width / 2, y: q.y + q.height / 2, w: q.width, h: q.height };
  }, re);
  if (!box) return { ok: false, why: 'no match: ' + re };
  if (!box.w || !box.h) return { ok: false, why: 'zero-size' };
  await page.mouse.click(box.x, box.y);
  return { ok: true };
}

async function countIn(page, defs) {
  return page.evaluate(({ defs }) => {
    const { methodA, methodAGeom, methodB, selfDeclared } = window.__CC__;
    const out = [];
    for (const d of defs) {
      let box = null;
      let nodes = [];
      // ★ M249 第三次 F57：第一版把 `[data-canvas-view-control]`（**4 个按钮本身**）
      //   当成容器传进来，于是「按钮里数按钮」得 0。容器得**解析**出来，不是随便一个选择器。
      //
      // ★ Agent 面板那一行**刻意不用 setAttribute 打一个 data-* 临时标记再回头选**：
      //   那样会在页面里留下一个只属于本手册探针的属性，
      //   **而它不是产品的标记**——探针契约门禁会要求把它登记进 `PUBLISH.md` 第九条
      //   那张「定位靠标记」的表，**而那张表的每一条都该是读者能在应用里找到的东西**。
      //   （本批就是这么被拦了一次：门禁说「顺手确认它在应用源码里真的存在」——
      //   **它不存在，因为它本来就不该存在**。）在这里就地解析容器，页面保持干净。
      if (d.resolve === 'agent-row') {
        const c = Array.from(document.querySelectorAll('button,[role="button"]'))
          .find((b) => /收起 Agent 面板|Collapse Agent/.test(b.getAttribute('aria-label') || ''));
        if (!c) { out.push({ name: d.name, found: false, note: 'Agent 面板没打开（不报 0）' }); continue; }
        for (let up = 0; up < 6; up++) {
          let p = c.parentElement;
          for (let i = 0; i < up; i++) p = p && p.parentElement;
          if (!p) break;
          const n = p.querySelectorAll('button,[role="button"]').length;
          if (n >= 6 && !p.querySelector('.td-canvas-dock') && !p.querySelector('.td-canvas-topbar')) {
            box = p; nodes = [];
            break;
          }
        }
        if (!box) { out.push({ name: d.name, found: false, note: '往上走 6 层都定位不到面板行容器' }); continue; }
      } else if (d.resolve === 'common-ancestor') {
        const seeds = Array.from(document.querySelectorAll(d.of || d.sel));
        if (!seeds.length) { out.push({ name: d.name, found: false, note: '种子元素没命中（不报 0）' }); continue; }
        let p = seeds[0].parentElement;
        while (p && !seeds.every((s) => p.contains(s))) p = p.parentElement;
        box = p; nodes = seeds;
        if (!box) { out.push({ name: d.name, found: false, note: '找不到包含全部种子的共同祖先' }); continue; }
      } else {
        nodes = Array.from(document.querySelectorAll(d.sel));
        box = nodes.find((n) => n.getBoundingClientRect().width > 0) || nodes[0];
      }
      if (!box) { out.push({ name: d.name, found: false, note: '选择器没命中任何元素（不报 0）' }); continue; }
      const a = methodA(box);
      const ag = methodAGeom(box, 'center');
      const ao = methodAGeom(box, 'overlap');
      const b = methodB(box);
      const aNames = new Set(a.map((x) => x.name));
      const bNames = new Set(b.hits.map((x) => x.name));
      out.push({
        name: d.name, found: true, matchedNodes: nodes.length,
        aCount: a.length, bCount: b.hits.length, inheritedCount: b.inheritedCount,
        aCenterCount: ag.hits.length,
        aCenterOutside: ag.hits.filter((x) => !x.inside).map((x) => x.how + '「' + x.name + '」@' + x.rect.join(',')),
        aOverlapCount: ao.hits.length,
        aOverlapInside: ao.hits.filter((x) => x.inside).length,
        aOverlapOutside: ao.hits.filter((x) => !x.inside).map((x) => x.how + '「' + x.name + '」@' + x.rect.join(',')),
        agreeAB: a.length === b.hits.length,
        onlyA: a.filter((x) => !bNames.has(x.name)).map((x) => x.how + '「' + x.name + '」'),
        onlyB: b.hits.filter((x) => !aNames.has(x.name)).map((x) => x.tag + '「' + x.name + '」'),
        selfDeclared: selfDeclared(box),
        aList: a.map((x) => x.how + '「' + x.name + '」'),
      });
    }
    return out;
  }, { defs });
}

const CANVAS_CONTAINERS = [
  { name: '顶栏 .td-canvas-topbar', sel: '.td-canvas-topbar' },
  { name: '左侧 Dock .td-canvas-dock', sel: '.td-canvas-dock' },
  { name: '缩放条（4 个视图控制的共同祖先）', resolve: 'common-ancestor', of: '[data-canvas-view-control]' },
  { name: '节点悬浮工具条 [data-canvas-node-hover-toolbar]', sel: '[data-canvas-node-hover-toolbar]' },
];

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 1000 },
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1800);
    await page.addScriptTag({ content: 'window.__CC__ = (' + IN_PAGE.toString() + ')();' });
    // 阳性对照：内核没装载的话后面全是 undefined——所以先证明它装载成功
    const boot = await page.evaluate(() => !!(window.__CC__ && window.__CC__.methodA));
    say('[阳性对照] 计数内核装载 =', boot);
    if (!boot) { process.exitCode = 1; return; }

    say('\n===== 画布页 · 状态一：未选中任何节点 =====');
    say(J(await countIn(page, CANVAS_CONTAINERS)));

    say('\n===== 画布页 · 状态二：选中图片节点 =====');
    say('[选中图片节点]', J(await realClick(page, '^55dd39e3')));
    await page.waitForTimeout(1200);
    say(J(await countIn(page, CANVAS_CONTAINERS)));

    say('\n===== 画布页 · 状态三：Shift 多选两个节点 =====');
    const two = await page.evaluate(() => {
      const ns = Array.from(document.querySelectorAll('[data-node-id]'));
      if (ns.length < 2) return null;
      const p = (n) => { const r = n.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + 10 }; };
      return { a: p(ns[0]), b: p(ns[1]) };
    });
    if (two) {
      await page.keyboard.down('Shift');
      await page.mouse.click(two.b.x, two.b.y);
      await page.keyboard.up('Shift');
      await page.waitForTimeout(1000);
      say(J(await countIn(page, [CANVAS_CONTAINERS[3]])));
    }

    say('\n===== 画布页 · 状态四：打开 Agent 面板，量它顶端那一排 =====');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const opened = await page.evaluate(() => {
      const c = Array.from(document.querySelectorAll('button,[role="button"]'))
        .find((b) => /收起 Agent 面板|Collapse Agent/.test(b.getAttribute('aria-label') || ''));
      if (c) return { alreadyOpen: true };
      const o = Array.from(document.querySelectorAll('button,[role="button"]'))
        .find((b) => /Agent|智能体/.test(b.getAttribute('aria-label') || '') &&
                     !/Collapse|收起/.test(b.getAttribute('aria-label') || ''));
      if (!o) return { err: '顶栏找不到 Agent 按钮' };
      const r = o.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    say('[打开 Agent]', J(opened));
    if (opened.x) { await page.mouse.click(opened.x, opened.y); await page.waitForTimeout(2200); }
    const row = await page.evaluate(() => {
      const c = Array.from(document.querySelectorAll('button,[role="button"]'))
        .find((b) => /收起 Agent 面板|Collapse Agent/.test(b.getAttribute('aria-label') || ''));
      if (!c) return null;
      for (let up = 0; up < 6; up++) {
        let p = c.parentElement;
        for (let i = 0; i < up; i++) p = p && p.parentElement;
        if (!p) break;
        const n = p.querySelectorAll('button,[role="button"]').length;
        if (n >= 6 && !p.querySelector('.td-canvas-dock') && !p.querySelector('.td-canvas-topbar')) {
          // ★ **只报告，不打标记**——理由见 countIn 里 resolve='agent-row' 那段注释。
          return { up, buttons: n, tag: p.tagName.toLowerCase(), cls: (p.className || '').slice(0, 50) };
        }
      }
      return null;
    });
    say('[Agent 面板行容器]', J(row));
    say(J(await countIn(page, [{ name: 'Agent 面板顶端那一行', resolve: 'agent-row' }])));

    // ─────────────────────────────────────────────────────────────
    // 第五段：「数出来的那些，到底点不点得着？」
    //
    // ★ 上面几种数法都在回答「有多少个像按钮的东西」，
    //   **没有一种在回答「点下去有没有反应」**——而手册那句话说的正是「可点的东西」。
    //   M249 就是在这里抓到自己手册的一条错：顶栏「11 个可点」只在面板打开时成立。
    // ★ 判据用**捕获阶段的 pointerdown 落点**：它问「真按下时事件落在谁身上」，
    //   不依赖我的任何几何假设——**前三种数法都依赖「我以为的范围」**。
    // ★ **阳性对照强制先跑**：同一个监听器按在顶栏主页按钮上，落点必须是它自己；
    //   对照不成立，下面所有「落点是 section」都只能说明监听器坏了。
    say('\n===== 画布页 · 第五段：数出来的按钮，真按下去事件落在谁身上 =====');
    // ★ 先重载拿干净状态：前四段是多选、开面板、Escape 连着做的，
    //   **实测带着那串状态进来时 `.td-canvas-dock` 里一个按钮都没有**，
    //   于是「左侧把手找不到」这个结论会是假的。**量之前先把状态复位。**
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2200);
    say('[已重载] Dock 按钮数 =', await page.evaluate(() =>
      document.querySelectorAll('.td-canvas-dock button').length));

    await page.evaluate(() => {
      window.__m249hits = [];
      document.addEventListener('pointerdown', (e) => {
        const t = e.target;
        const path = [];
        for (let n = t, i = 0; i < 4 && n; i++, n = n.parentElement) {
          path.push(n.tagName.toLowerCase() +
            (n.getAttribute('aria-label') ? '「' + n.getAttribute('aria-label') + '」' : ''));
        }
        window.__m249hits.push({ x: Math.round(e.clientX), y: Math.round(e.clientY),
                                 target: path[0] || null, path });
      }, true);
    });
    const press = async (label, pt) => {
      if (!pt) { say('[' + label + '] 没找到目标，跳过'); return null; }
      await page.evaluate(() => { window.__m249hits = []; });
      await page.mouse.move(pt.x, pt.y);
      await page.waitForTimeout(250);
      await page.mouse.down();
      await page.waitForTimeout(120);
      await page.mouse.up();
      await page.waitForTimeout(400);
      const hits = await page.evaluate(() => window.__m249hits);
      say('[' + label + '] 按 (' + pt.x + ',' + pt.y + ') → 落点 ' +
          (hits.length ? hits[0].path.join(' < ') : '（一个事件都没有）'));
      return hits;
    };
    const where = (re) => page.evaluate((r) => {
      const rx = new RegExp(r);
      const b = Array.from(document.querySelectorAll('button,[role="button"]'))
        .find((x) => rx.test(x.getAttribute('aria-label') || ''));
      if (!b) return null;
      const q = b.getBoundingClientRect();
      // ★ 可见宽度要**夹进视口**算，不能只判「rect 与视口有交集」（M249 自己栽过：
      //   第一版判 `q.x < innerWidth` 对 rect=(1593,0,16,1000) 返回 true，
      //   而它的**中心 x=1601 已经在 1600 宽的视口之外**，连鼠标都放不上去）。
      const vis = Math.max(0, Math.min(q.right, window.innerWidth) - Math.max(q.left, 0));
      return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2),
               rect: [q.x, q.y, q.width, q.height].map(Math.round),
               viewportW: window.innerWidth,
               visibleWidthPx: Math.round(vis),
               centerInsideViewport: (q.x + q.width / 2) < window.innerWidth,
               pointerEvents: getComputedStyle(b).pointerEvents,
               parentPointerEvents: b.parentElement ? getComputedStyle(b.parentElement).pointerEvents : null };
    }, re);

    // 阳性对照：主页按钮。**它必须收到事件**，否则后面全是无效读数。
    const ctl = await where('^主页$');
    say('[阳性对照目标]', J(ctl));
    const ctlHit = await press('阳性对照 · 顶栏主页按钮', ctl);
    const ctlOk = !!(ctlHit && ctlHit[0] && /主页/.test(ctlHit[0].path.join(' ')));
    say('[阳性对照是否成立]', ctlOk);
    if (!ctlOk) say('★★ 阳性对照不成立：下面所有「落点不是它」的读数一律作废 ★★');
    // ★★ **阳性对照自己把被测状态改掉了**（M249 踩过）：那个「主页」按钮是**导航**，
    //   按一下就离开画布，`.td-canvas-dock` 里的按钮当场归零——
    //   于是后面「左侧把手不在 DOM 里」读起来像是产品没有它，**其实是我自己走开了**。
    //   **阳性对照跑完必须把状态复位**，否则它污染的正是它要验证的那段序列。
    say('[复位] 阳性对照点完已离开画布，重新回画布页');
    await page.goto(APP + CANVAS, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2200);
    say('[复位后] Dock 按钮数 =', await page.evaluate(() =>
      document.querySelectorAll('.td-canvas-dock button').length));
    await page.evaluate(() => {
      window.__m249hits = [];
      document.addEventListener('pointerdown', (e) => {
        const t = e.target;
        const path = [];
        for (let n = t, i = 0; i < 4 && n; i++, n = n.parentElement) {
          path.push(n.tagName.toLowerCase() +
            (n.getAttribute('aria-label') ? '「' + n.getAttribute('aria-label') + '」' : ''));
        }
        window.__m249hits.push({ x: Math.round(e.clientX), y: Math.round(e.clientY), path });
      }, true);
    });

    const rhClosed = await where('调整右侧面板宽度');
    say('[右侧把手几何 · 面板收起态]', J(rhClosed));
    await press('右侧把手（面板收起态）', rhClosed);

    // ★ 左侧把手**只在左侧面板打开时才在 DOM 里**（实测面板关着时根本没有这个按钮），
    //   所以先把 Dock 的「资产」点开；点一次没出来就再点一次（它可能本来就是开着的）。
    say('\n[动作] 点开左侧面板（否则左侧把手不在 DOM 里）');
    const openLeft = await where('^资产$');
    say('[左侧面板开关]', J(openLeft));
    if (openLeft) { await page.mouse.click(openLeft.x, openLeft.y); await page.waitForTimeout(1400); }
    let lh = await where('调整左侧面板宽度');
    if (!lh && openLeft) {
      await page.mouse.click(openLeft.x, openLeft.y);
      await page.waitForTimeout(1400);
      lh = await where('调整左侧面板宽度');
    }
    say('[左侧把手几何]', J(lh));
    if (!lh) {
      // ★ **找不到就把现场打出来**，绝不静默跳过——「没找到」和「量了没有」必须分清。
      say('[左侧把手为什么不在] 现场 =', J(await page.evaluate(() => ({
        asides: Array.from(document.querySelectorAll('aside')).map((a) => {
          const r = a.getBoundingClientRect();
          return { rect: [r.x, r.y, r.width, r.height].map(Math.round),
                   pe: getComputedStyle(a).pointerEvents, cls: (a.className || '').slice(0, 40) };
        }),
        dockLabels: Array.from(document.querySelectorAll('.td-canvas-dock button'))
          .map((b) => b.getAttribute('aria-label')),
        allPanelWidthBtns: Array.from(document.querySelectorAll('button'))
          .map((b) => b.getAttribute('aria-label')).filter((s) => s && /宽度|resize/i.test(s)),
      }))));
    }
    await press('左侧把手', lh);

    say('\n[动作] 打开 Agent 面板后再按一次右侧把手');
    // ★ 顶栏那个按钮的 aria-label 实测是「**打开 Agent**」，不是「Agent」——
    //   `^Agent$` 一条都没匹配上，面板根本没开，后两行读数就全是收起态的复述（M249 踩过）。
    const openBtn = await where('Agent');
    if (openBtn) { await page.mouse.click(openBtn.x, openBtn.y); await page.waitForTimeout(2400); }
    const rhOpen = await where('调整右侧面板宽度');
    say('[右侧把手几何 · 面板打开态]', J(rhOpen));
    await press('右侧把手（面板打开态）', rhOpen);

    // 还原：把面板关回去，别把状态留给下一个探针
    const closeBtn = await where('收起 Agent 面板');
    if (closeBtn) { await page.mouse.click(closeBtn.x, closeBtn.y); await page.waitForTimeout(1500); }
    say('[已还原] 面板关闭指令发出 =', !!closeBtn);
  } catch (e) {
    say('[出错]', e && e.message);
    process.exitCode = 1;
  } finally {
    await ctx.close();
  }
})();

module.exports = { CANVAS_CONTAINERS, DESTRUCTIVE };
