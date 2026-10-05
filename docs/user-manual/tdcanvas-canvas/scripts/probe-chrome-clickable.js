/* probe-chrome-clickable.js —— M257：左下缩放条与左侧 Dock 的控件，是不是每个都真能点到
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-chrome-clickable.js
 *
 * ── 这条要回答两个问题，而它们是同一个形状 ──────────────────────────
 * ① **左下缩放条 6 个控件**（小地图 / 隐藏连线 / 网格吸附 / 重置视图 / 缩放滑杆 / 快捷键）
 * ② **左侧 Dock 那 N 个按钮**（8 恒有 + 有选中时多 1）
 * 两者都在 `left-3` / `left-4` 的左下角，而**左侧节点面板是 `left-14` 起、默认开着**
 * （`use-canvas-side-panel-store.ts:19` 的 `initialOpen()` 只在 localStorage 记着 "0" 时才算关）。
 * ★ 几何上两者**必然重叠**——所以这不是「会不会」的问题，是「盖住几个」的问题。
 *
 * ── 判据 ──────────────────────────────────────────────────────────
 * 逐个控件问 `document.elementFromPoint(中心x, 中心y)`，
 * **并要求返回的最上层元素落在该控件自己的子树里**——
 * 这就是「这一格归它」与「这一格归别人」的分界（M255 的 F74，本批第二次应用）。
 * ★ **阳性对照**：面板关掉时，**每一个**控件都必须命中自己；
 *   对照不成立的话，上面所有「落点不是它」都只能说明判据坏了（F61 的延续）。
 *
 * ── ★ 三个写这支探针时踩到的坑，都留在代码里 ────────────────────────
 * ⓪ **「6 个控件」的第 6 个没有 `data-canvas-view-control` 属性**——`canvas-zoom-controls.tsx:100`
 *    那个「快捷键」按钮只有 `aria-label`（`canvas-zoom-controls.tsx:50 / 63 / 76 / 80` 四个才有属性）。
 *    只按属性选会量到 **5 个**，**而少掉的那个恰好是读者找帮助的入口**——
 *    **按「属性齐全」去枚举控件，等于按实现细节挑，漏谁由实现决定，不由你决定。**
 * ① **容器要用「里面有没有 minimap」反查**。`[data-canvas-no-zoom]` 在页面上不止一处，
 *    第一版直接 `querySelector` 选中的是**侧面板自己**——
 *    于是量出来的是「面板里的 12 个东西」，**看起来还挺合理**，差点当成结论。
 * ② **「当前有没有选中」不能用类名 `z-50`**（F75 的第四次复发）：
 *    `canvas-node.tsx:311` 的三目是 `isGroup ? "z-[5]" : isSelected ? "z-50" : "z-10"`，
 *    **实测 Ctrl+A 全选四个节点之后没有一个节点的类名带 `z-50`**。
 *    可靠的是产品自己给的信号：`tool-delete` 只在 `{selectedCount ? … : null}` 时渲染
 *    （`canvas-toolbar.tsx:258-261`），**它在 Dock 里出现 ⇔ 有选中**。
 * ③ ★★ **画布只渲染视口内的节点**（台账 F79，`project.tsx:617` 的 `visibleNodes` + 280px padding）。
 *    所以 `[data-node-id]` 数到 0 **不等于画布上没有节点**——
 *    侧面板的「画布元素 N」才是真值。**这一条把前三支按节点找点的探针全废过一次**
 *    （详见 F79，本探针在取点前先 `waitNodes` 轮询，并且把侧面板计数一起打出来对账）。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const APP = process.env.APP_URL || 'http://localhost:3000';
const CANVAS = process.env.CANVAS_URL || '';
const PROFILE = process.env.PROFILE || '/tmp/m244-profile';
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

/** 逐个控件问「这一格归谁」 */
const PROBE_CONTROLS = (sel) => Array.from(document.querySelectorAll(sel)).map((el) => {
  const r = el.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const top = document.elementFromPoint(cx, cy);
  const who = top ? top.tagName + '.' + String(top.className || '').split(' ').slice(0, 2).join('.') : 'null';
  return {
    id: el.getAttribute('data-canvas-view-control') || el.getAttribute('data-canvas-tool')
        || (el.getAttribute('aria-label') || '').slice(0, 10) || el.tagName,
    kind: el.tagName === 'INPUT' ? '滑杆' : '按钮',
    x: Math.round(cx), w: Math.round(r.width),
    self: !!(top && el.contains(top)),
    inPanel: !!(top && top.closest('aside.td-canvas-side-panel')),
    who,
  };
});

/** ★ 只在**缩放条那一个容器**内部枚举。
 *  直接 `page.evaluate(PROBE_CONTROLS, '[data-canvas-no-zoom] button')` 会把侧面板里的
 *  按钮一起捞进来（面板也带 `data-canvas-no-zoom`）——18 个里有一半不是缩放条的。 */
const ZOOMBAR_CONTROLS = () => {
  const mini = document.querySelector('[data-canvas-view-control="minimap"]');
  const wrap = mini && mini.closest('[data-canvas-no-zoom]');
  if (!wrap) return [];
  return Array.from(wrap.querySelectorAll('[data-canvas-view-control], input[type="range"], button')).map((el) => {
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const top = document.elementFromPoint(cx, cy);
    const who = top ? top.tagName + '.' + String(top.className || '').split(' ').slice(0, 2).join('.') : 'null';
    return {
      id: el.getAttribute('data-canvas-view-control') || (el.getAttribute('aria-label') || '').slice(0, 10) || el.tagName,
      kind: el.tagName === 'INPUT' ? '滑杆' : '按钮',
      x: Math.round(cx), w: Math.round(r.width),
      self: !!(top && el.contains(top)),
      inPanel: !!(top && top.closest('aside.td-canvas-side-panel')),
      who,
    };
  });
};

/** 侧面板的「画布元素 N」——★ 那是 store 的真值，`[data-node-id]` 不是（F79） */
const TRUTH = () => {
  const a = document.querySelector('aside.td-canvas-side-panel');
  const m = a && a.textContent.match(/画布元素\s*(\d+)/);
  return { 侧面板: m ? m[1] : '(关)', dom节点: document.querySelectorAll('[data-node-id]').length };
};

const SIDE_OPEN = () => !!document.querySelector('aside.td-canvas-side-panel');

/** 等节点真的落进 DOM（视口虚拟化会让他们一时读不到，F79） */
async function waitNodes(page, tries = 12) {
  for (let i = 1; i <= tries; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('[data-node-id]').length);
    if (n > 0) return { n, tries: i };
    await page.waitForTimeout(250);
  }
  return { n: 0, tries };
}

/** 找一个只属于某个节点的点（节点默认全叠在画布正中，两节点中心可能同坐标） */
const ANY_EXCLUSIVE_POINT = () => {
  const ns = Array.from(document.querySelectorAll('[data-node-id]'));
  const tried = [];
  for (const n of ns) {
    const id = n.getAttribute('data-node-id');
    const r = n.getBoundingClientRect();
    tried.push(id.slice(0, 10));
    for (const [fx, fy] of [[0.5, 0.06], [0.5, 0.94], [0.08, 0.5], [0.92, 0.5], [0.3, 0.06], [0.7, 0.06], [0.06, 0.08], [0.94, 0.08]]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      if (y < 80 || y > window.innerHeight - 60 || x < 0 || x > window.innerWidth) continue;
      const e = document.elementFromPoint(x, y);
      const h = e && e.closest('[data-node-id]');
      if (h && h.getAttribute('data-node-id') === id) return { id, x, y, tried };
    }
  }
  return { id: null, x: null, y: null, tried };
};

/** 缩放条容器：按「里面有没有 minimap」反查，别直接 querySelector('[data-canvas-no-zoom]') */
const ZOOMBAR_RECT = () => {
  const mini = document.querySelector('[data-canvas-view-control="minimap"]');
  const wrap = mini && mini.closest('[data-canvas-no-zoom]');
  const side = document.querySelector('aside.td-canvas-side-panel');
  if (!wrap) return { err: '没找到缩放条容器' };
  const wr = wrap.getBoundingClientRect(), sr = side && side.getBoundingClientRect();
  return {
    缩放条: [Math.round(wr.x), Math.round(wr.right)],
    面板: sr ? [Math.round(sr.x), Math.round(sr.right)] : null,
    重叠像素: sr ? Math.round(wr.right - sr.x) : null,
  };
};

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  const rows = [];
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    OUT('[开局] ' + JSON.stringify(await page.evaluate(TRUTH)));

    for (const want of [true, false]) {
      if (await page.evaluate(SIDE_OPEN) !== want) {
        const sb = await page.$('button[data-canvas-tool="tool-search"]');
        if (sb) { await sb.click({ force: true }); await page.waitForTimeout(900); }
      }
      const open = await page.evaluate(SIDE_OPEN);
      OUT('\n################ 面板' + (open ? '开' : '关') + '（实测 ' + open + '） ################');
      OUT('[节点数] ' + JSON.stringify(await page.evaluate(TRUTH)));
      OUT('[缩放条几何] ' + JSON.stringify(await page.evaluate(ZOOMBAR_RECT)));

      const zoom = await page.evaluate(ZOOMBAR_CONTROLS);
      OUT('  --- 左下缩放条 ---');
      OUT('  可点到 ' + zoom.filter((z) => z.self).length + ' / ' + zoom.length);
      zoom.forEach((z) => OUT('    ', z.self ? '✓' : '✗', z.kind, z.id, 'x=' + z.x,
        z.self ? '' : '落点 ' + z.who + (z.inPanel ? '〔在面板内〕' : '')));
      rows.push({ open, kind: '缩放条', items: zoom });

      const dock = await page.evaluate(PROBE_CONTROLS, '.td-canvas-dock button');
      OUT('  --- 左侧 Dock（无选中态）---');
      OUT('  可点到 ' + dock.filter((z) => z.self).length + ' / ' + dock.length
          + '  tool-delete 在=' + dock.some((z) => z.id === 'tool-delete'));
      dock.filter((z) => !z.self).forEach((z) => OUT('    ✗', z.id, '落点', z.who));
      rows.push({ open, kind: 'Dock', items: dock });

      // 有选中时 Dock 多一个 tool-delete
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
      const w = await waitNodes(page);
      const p = await page.evaluate(ANY_EXCLUSIVE_POINT);
      if (p.x != null) {
        await page.mouse.click(p.x, p.y);
        await page.waitForTimeout(900);
        const d2 = await page.evaluate(PROBE_CONTROLS, '.td-canvas-dock button');
        OUT('  --- 左侧 Dock（单选态 · 节点 ' + w.n + ' 个等 ' + w.tries + ' 轮 · 点 ' + p.id.slice(0, 10) + '）---');
        OUT('  可点到 ' + d2.filter((z) => z.self).length + ' / ' + d2.length
            + '  tool-delete 在=' + d2.some((z) => z.id === 'tool-delete'));
        d2.filter((z) => !z.self).forEach((z) => OUT('    ✗', z.id, '落点', z.who));
        rows.push({ open, kind: 'Dock·单选', items: d2 });
      } else {
        OUT('  --- 左侧 Dock（单选态）--- ✗ 找不到独占点（DOM 节点 ' + w.n + '，试过 '
            + (p.tried.length ? p.tried.join(' / ') : '空') + '）——这一档不产出读数');
      }
    }

    OUT('\n===== 汇总：存在但按不到 =====');
    for (const r of rows) {
      const bad = r.items.filter((i) => !i.self);
      OUT('  面板' + (r.open ? '开' : '关') + ' · ' + r.kind + '：' + bad.length + ' / ' + r.items.length
          + (bad.length ? '  → ' + bad.map((b) => b.id).join(', ') : ''));
    }
  } catch (e) {
    OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e);
  } finally {
    try { await page.keyboard.press('Escape'); } catch (e) {}
    await ctx.close();
  }
})();
