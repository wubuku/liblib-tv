/**
 * probe-bottom-bar.js —— 量「左侧面板开着时，左下角那一排到底哪几项点得到」（M307）。
 *
 * `20-reference.md` 的「鼠标与键位」那节是全库字数最多、图最少的一节（实测
 * 1828 中文字、0 张图），而它最反直觉的一条是纯文字的：
 *
 * > **面板开着时 6 项里只有「打开小地图」点得到，收起面板后 6/6 全通。**
 *
 * ★ **★ 本探针把「点得到」量出来，而不是照抄那句话**：★★
 * ★ **★ 判据是 `elementFromPoint` 落在该项自己身上**（★★ **被面板盖住时它落的是
 * ★ **★ 面板自己，★ **★ 所以「盖住」与「点不到」在机器上是同一件事**）。
 *
 * 用法：
 *   node scripts/probe-bottom-bar.js
 *   TD_SHOT=screenshots/xx.png node scripts/probe-bottom-bar.js
 *
 * ── 纪律 ──
 * 1. 自己开干净画布，全程只建不删。
 * 2. **每一项的可点性都是当场 elementFromPoint 量的**，图上的 ✓/✗ 不写死。
 * 3. **断言不成立就 exit 1**：面板开着必须是 1/6，收起后必须是 6/6。
 *    ——反过来，如果哪天真变了，这张图的前提就废了，不该照旧发出去。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const BASE = process.env.TD_BASE || 'http://localhost:3000';
const VW = Number(process.env.TD_VW || 1440), VH = Number(process.env.TD_VH || 900);
const say = (...a) => console.log(a.join(' '));

/** 左下角那一排的 6 项：取实测的 aria-label 与盒模型，不写死位置。 */
const readBar = (page) => page.evaluate(() => {
  const out = [];
  document.querySelectorAll('button, input[type="range"]').forEach((e) => {
    const r = e.getBoundingClientRect();
    if (r.y > 820 && r.y < 900 && r.width > 10 && r.width < 200) {
      out.push({ al: e.getAttribute('aria-label') || '', x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
    }
  });
  return out.sort((a, b) => a.x - b.x);
});

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: VW, height: VH },
    deviceScaleFactor: process.env.TD_SHOT ? 2 : 1,
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  if (!/TDCanvas/i.test(await page.title())) throw new Error('打开的不是 TDCanvas');
  await page.getByRole('button', { name: '新建画布' }).click();
  await page.waitForTimeout(2200);
  if (!/\/canvas\//.test(page.url())) throw new Error('没跳到画布页');

  const items = await readBar(page);
  say('左下角这一排共', items.length, '项：', items.map((i) => `${i.al}@${i.x}`).join('  '));
  if (items.length !== 6) throw new Error(`这一排是 ${items.length} 项而不是 6 项，停下`);

  // ── 状态一：面板关着 ──
  const closed = await page.evaluate((items) => items.map((it) => {
    const cx = it.x + it.w / 2, cy = it.y + it.h / 2;
    const hit = document.elementFromPoint(cx, cy);
    // ★ **★ 必须用 `closest('[aria-label]')` 而不是直接读命中元素的 aria-label**：
    // ★ **★ `elementFromPoint` 返回的是**最顶层那个元素**，
    // ★ **★ 而按钮里那块 `<svg>` 图标既没有 aria-label 也没有可读名字——
    // ★ **★★ 于是第一版把「面板收起、6 项全部点得到」判成了 1/6，★★
    // ★ **★★★ 表现是「面板关着也点不到」，★★★ **而那显然不对。**
    const owner = hit && hit.closest ? hit.closest('[aria-label]') : null;
    const label = owner ? (owner.getAttribute('aria-label') || owner.tagName) : 'null';
    return { al: it.al, x: it.x, y: it.y, w: it.w, h: it.h, cx, cy, hitLabel: label, ok: label === it.al };
  }), items);
  say('面板收起时:', closed.map((c) => `${c.al}=${c.ok ? '点得到' : '点不到'}`).join('  '));
  const closedOK = closed.filter((c) => c.ok).length;
  say(`  → ${closedOK}/6`);

  // ── 状态二：面板开着 ──
  await page.locator('button[aria-label="搜索节点"]').click();
  await page.waitForTimeout(1000);
  const panel = await page.evaluate(() => {
    const e = document.querySelector('.td-canvas-side-panel');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  });
  say('侧面板实测盒模型:', JSON.stringify(panel));
  if (!panel) throw new Error('没找到侧面板，停下');
  const opened = await page.evaluate((items) => items.map((it) => {
    const cx = it.x + it.w / 2, cy = it.y + it.h / 2;
    const hit = document.elementFromPoint(cx, cy);
    // ★ **★ 必须用 `closest('[aria-label]')` 而不是直接读命中元素的 aria-label**：
    // ★ **★ `elementFromPoint` 返回的是**最顶层那个元素**，
    // ★ **★ 而按钮里那块 `<svg>` 图标既没有 aria-label 也没有可读名字——
    // ★ **★★ 于是第一版把「面板收起、6 项全部点得到」判成了 1/6，★★
    // ★ **★★★ 表现是「面板关着也点不到」，★★★ **而那显然不对。**
    const owner = hit && hit.closest ? hit.closest('[aria-label]') : null;
    const label = owner ? (owner.getAttribute('aria-label') || owner.tagName) : 'null';
    return { al: it.al, x: it.x, y: it.y, w: it.w, h: it.h, cx, cy, hitLabel: label, ok: label === it.al };
  }), items);
  say('面板开着时:', opened.map((c) => `${c.al}=${c.ok ? '点得到' : '点不到'}(${c.hitLabel})`).join('  '));
  const openOK = opened.filter((c) => c.ok).length;
  say(`  → ${openOK}/6`);

  say('页面 JS 错误:', errors.length ? errors.join(' | ') : '无');

  // ── 断言：这张图的前提（1/6 与 6/6）必须成立，否则不产出 ──
  if (openOK !== 1) throw new Error(`面板开着时实测 ${openOK}/6 点得到，不是正文说的 1/6——图的前提不成立，停下`);
  if (closedOK !== 6) throw new Error(`面板收起时实测 ${closedOK}/6，不是 6/6——图的前提不成立，停下`);
  say('★ 断言通过：面板开着 1/6、收起 6/6，与正文一致');

  if (process.env.TD_SHOT) {
    // ★ **★ 传 `opened`（带 `ok` 的实测结果）而不是 `items`（readBar 的原始项）**——
    // ★ **★ 而第一版传的是 `items`，★★ **于是 `it.ok` 全是 undefined、
    // ★ **★★★ 图上 6 个徽标全画成了 ✗。★★★ **而那正是「面板开着点不到」的样子，
    // ★ **★★★ 所以整张图读起来是「6 项全被挡」——★★ **和实测的 1/6 正好相反。**
    const info = await page.evaluate(({ items, panel, openOK, closedOK }) => {
      const ns = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('style', 'position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483000');
      const el = (tag, at) => { const n = document.createElementNS(ns, tag); for (const k in at) n.setAttribute(k, at[k]); return n; };

      // 面板的覆盖区（用实测盒模型，不写死）
      svg.appendChild(el('rect', { x: panel.x, y: panel.y, width: panel.w, height: panel.h, fill: '#ef4444', 'fill-opacity': 0.07, stroke: '#ef4444', 'stroke-width': 1.6, 'stroke-dasharray': '8 5' }));
      // 只把「压到左下角那一排」的那段画浓一点
      svg.appendChild(el('rect', { x: panel.x, y: 830, width: panel.w, height: 60, fill: '#ef4444', 'fill-opacity': 0.16 }));

      const tag = el('g', {});
      tag.appendChild(el('rect', { x: panel.x, y: 700, width: 268, height: 26, rx: 5, fill: '#0f172a', 'fill-opacity': 0.88, stroke: '#ef4444', 'stroke-width': 1.2 }));
      const tt = el('text', { x: panel.x + 10, y: 718, fill: '#fca5a5', 'font-size': 14, 'font-weight': 600 });
      tt.textContent = `左侧节点面板 实测 x ${panel.x}–${panel.x + panel.w}`;
      tag.appendChild(tt);
      svg.appendChild(tag);

      // 6 项各自：框 + 徽标（✓/✗ 来自上面那次实测）
      items.forEach((it) => {
        const g = el('g', {});
        const good = it.ok;
        g.appendChild(el('rect', { x: it.x - 2, y: it.y - 2, width: it.w + 4, height: it.h + 4, rx: 6, fill: 'none', stroke: good ? '#22c55e' : '#f87171', 'stroke-width': 2.2 }));
        const bx = it.x + it.w / 2 - 13, by = it.y - 24;
        g.appendChild(el('rect', { x: bx, y: by, width: 26, height: 20, rx: 4, fill: good ? '#22c55e' : '#f87171' }));
        const m = el('text', { x: bx + 13, y: by + 15, fill: '#052e16', 'font-size': 14, 'font-weight': 700, 'text-anchor': 'middle' });
        m.textContent = good ? '✓' : '✗';
        g.appendChild(m);
        svg.appendChild(g);
      });

      const box = el('g', {});
      const lines = [
        '面板开着：6 项里只有「打开小地图」点得到',
        `收起面板后：6 项全部点得到（${closedOK}/6）`,
        '面板实测占 x 56–336，把这一排压掉了 5 项',
      ];
      const wBox = 430, hBox = lines.length * 24 + 20;
      box.appendChild(el('rect', { x: 400, y: 620, width: wBox, height: hBox, rx: 8, fill: '#0f172a', 'fill-opacity': 0.93, stroke: '#ef4444', 'stroke-width': 1.4 }));
      lines.forEach((s, i) => {
        const t = el('text', { x: 412, y: 620 + 26 + i * 24, fill: i === 1 ? '#fde68a' : '#e2e8f0', 'font-size': 15, 'font-weight': i === 1 ? 700 : 500 });
        t.textContent = s;
        box.appendChild(t);
      });
      svg.appendChild(box);

      document.body.appendChild(svg);
      return { openOK, closedOK, panel, items: items.map((i) => i.al) };
    }, { items: opened, panel, openOK, closedOK });
    say('overlay:', JSON.stringify(info));
    await page.waitForTimeout(400);
    await page.screenshot({ path: process.env.TD_SHOT });
    say('已保存截图:', process.env.TD_SHOT);
  }
  await browser.close();
})().catch((e) => { console.error('FAIL:', e.message.split('\n')[0]); process.exit(1); });
