// 批次 171 h 轮：修 g 轮。新页签的初始视图与共享页签不同 ⇒ 第一档就「选不中节点」。
//
// 正解：**每档先把 `.react-flow__viewport` 的 transform 钉成已知值**（共享页签当前值，逐字照抄），
//   再挑一个「完全在 x>170（左栏右侧）且在屏上」的节点，点标题选中，把 Add tags 算到屏中央，点开，读数。
// 📌 改 transform 只动视图态；收尾 pinViewport 复位共享页签，transform 复原成原值。
//
// 预测：宽 = min(224, 100vw−32)，门槛 256 ⇒ 256→224 / 250→218 / 220→188 / 200→168 / 180→148 / 160→128；
//   高恒 44；vw<256 时 scrollW > clientW ⇒ 横向滚动、末尾颜色被裁。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171i' };

// 共享页签当前 transform（逐字照抄）
const 基准transform = await p.evaluate(() => document.querySelector('.react-flow__viewport').getAttribute('style'));
rec.基准transform = 基准transform;
console.log('基准 transform:', 基准transform);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const 定视口 = async (w, h) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(700);
  await tab.evaluate((t) => { document.querySelector('.react-flow__viewport').setAttribute('style', t); }, 基准transform);
  await tab.waitForTimeout(500);
  const vp = await tab.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

/** 任取一个带标题的节点，用 transform 把它挪到视口中央，再点标题选中。
 *  🔴 h 轮教训：先筛「整块在屏内」再点 ⇒ 窄视口下几乎没有节点满足（1280 时可见节点 x=345~559，
 *     400 宽时要求 x+178 ≤ 392 ⇒ 全被否掉）⇒ 8 档全报「选不中」。
 *     **顺序错了：应先把节点挪进屏，再判断能不能点。** */
const 选节点 = async (w, h) => {
  const id = await tab.evaluate(() => {
    const n = document.querySelector('.react-flow__node [data-testid="flow-node-title"]');
    return n ? n.closest('.react-flow__node').getAttribute('data-id') : null;
  });
  if (!id) return null;
  const mv = await 挪到中央(`[data-testid="flow-node-title"]`, id, w, h, '标题');
  if (!mv) return null;
  await tab.waitForTimeout(300);
  const hit = await tab.evaluate(([i, cx, cy]) => {
    const e = document.elementFromPoint(cx, cy);
    return { tag: e && e.tagName, testid: e && e.getAttribute('data-testid'),
      在节点内: !!(e && e.closest('.react-flow__node')),
      在把手上: !!(e && e.closest('[data-testid="flow-node-target-handle"],[data-testid="flow-node-source-handle"]')) };
  }, [id, mv.中心[0], mv.中心[1]]);
  if (!hit.在节点内 || hit.在把手上) return { id, 失败: '标题被挡', hit, mv };
  await tab.mouse.click(mv.中心[0], mv.中心[1]);
  await tab.waitForTimeout(700);
  const sel = await tab.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"].selected`), id);
  return sel ? { id, pt: mv.中心 } : { id, 失败: '点了没选中', hit };
};

/** 把某个元素（用选择器找）挪到视口中央：改 `.react-flow__viewport` 的 transform（只动视图态）。 */
const 挪到中央 = (sel, id, w, h, 标签) => tab.evaluate(([s, i, vw, vh, lb]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = document.querySelector(s);
  const vp = document.querySelector('.react-flow__viewport');
  if (!n || !e || !vp) return { 失败: lb + ' 找不到元素' };
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(vp.getAttribute('style'));
  if (!m) return { 失败: 'transform 解析不了', style: vp.getAttribute('style') };
  const sc = parseFloat(m[3]);
  const r = e.getBoundingClientRect();
  const dx = (vw / 2 - (r.x + r.width / 2)) / sc;
  const dy = (vh / 2 - (r.y + r.height / 2)) / sc;
  vp.setAttribute('style', `transform: translate(${parseFloat(m[1]) + dx}px, ${parseFloat(m[2]) + dy}px) scale(${m[3]});`);
  const t2 = e.getBoundingClientRect();
  return { 盒: [Math.round(t2.x), Math.round(t2.y), Math.round(t2.width), Math.round(t2.height)],
    中心: [Math.round(t2.x + t2.width / 2), Math.round(t2.y + t2.height / 2)] };
}, [sel, id, w, h, 标签]);

/** 把选中节点的 Add tags 按钮挪到视口正中（复用 挪到中央）。 */
const 挪按钮到中央 = (id, w, h) => 挪到中央('[data-testid="flow-node-selected-tag"]', id, w, h, 'AddTags');

const 读 = () => tab.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const btns = Array.from(e.querySelectorAll('button')).map((b) => {
    const q = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      完全在可视区内: q.left >= r.left - 0.5 && q.right <= r.right + 0.5 };
  });
  return { 布局宽: e.offsetWidth, 布局高: e.offsetHeight, 变换后: [Math.round(r.width), Math.round(r.height)],
    computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth },
    scrollW: e.scrollWidth, clientW: e.clientWidth, 可横向滚动: e.scrollWidth > e.clientWidth + 0.5,
    内边距: cs.padding, 间隙: cs.gap, 按钮数: btns.length,
    按钮: btns, 被裁: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria) };
});

rec.档位 = [];
for (const [w, h] of [[1280, 720], [400, 720], [300, 720], [256, 720], [250, 720], [220, 720], [200, 720], [180, 720], [160, 720]]) {
  await 定视口(w, h);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const n = await 选节点(w, h);
  if (!n || n.失败) { rec.档位.push({ 视口: [w, h], 打开: false, 原因: n && n.失败 || '选不中', 细节: n }); console.log(`  ${w}×${h}: ❌ ${n && n.失败 || '选不中'}`, JSON.stringify(n && n.hit || '')); continue; }
  const mv = await 挪按钮到中央(n.id, w, h);
  if (!mv || mv.失败) { rec.档位.push({ 视口: [w, h], 打开: false, 原因: '挪不动', mv }); console.log(`  ${w}×${h}: ❌ ${JSON.stringify(mv)}`); continue; }
  await tab.waitForTimeout(300);
  await tab.mouse.click(mv.中心[0], mv.中心[1]);
  let last = -1, stable = 0;
  for (let i = 0; i < 20; i++) {
    await tab.waitForTimeout(200);
    const ww = await tab.evaluate(() => { const e = document.querySelector('.max-w-canvas-tag-selector'); return e ? e.offsetWidth : -1; });
    if (ww > 0 && ww === last) { stable++; if (stable >= 2) break; } else stable = 0;
    last = ww;
  }
  const d = await 读();
  if (!d) { rec.档位.push({ 视口: [w, h], 打开: false, 原因: '点了没开' }); console.log(`  ${w}×${h}: ❌ 点了没开`); continue; }
  const 预测宽 = Math.min(224, Math.max(0, w - 32));
  rec.档位.push({ 视口: [w, h], 打开: true, 布局: [d.布局宽, d.布局高], computed: d.computed,
    滚动: d.可横向滚动, scrollW: d.scrollW, clientW: d.clientW, 按钮数: d.按钮数, 被裁: d.被裁, 预测宽, 按钮: d.按钮 });
  console.log(`  ${w}×${h}: 布局 ${d.布局宽}×${d.布局高}（预测宽 ${预测宽} ${d.布局宽 === 预测宽 ? '✅' : '❌'}）` +
    ` scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 按钮数=${d.按钮数} 被裁=${JSON.stringify(d.被裁)}`);
  if (w === 200) {
    await tab.evaluate(() => {
      const e = document.querySelector('.max-w-canvas-tag-selector');
      const r = e.getBoundingClientRect();
      const d2 = document.createElement('div');
      d2.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
        `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d2);
    });
    await tab.waitForTimeout(250);
    await tab.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/134-node-tag-selector-clamped-200px.png', import.meta.url).pathname });
    rec.图 = 'screenshots/134-node-tag-selector-clamped-200px.png';
    await tab.evaluate(() => document.querySelectorAll('div[style*="2147483646"]').forEach((e) => e.remove()));
  }
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
}
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)),
  'transform:', await p.evaluate(() => document.querySelector('.react-flow__viewport').getAttribute('style')));
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b171i.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
