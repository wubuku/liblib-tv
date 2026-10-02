// 批次 78：`media-playback.md`（全册最薄页，82 行）里那句可测的断言 ——
//   「空节点上没有播放控件可点，**无从测起**」
// 以及「无时长空载态（时间显示 00:00 / 00:00）」被归因为「资源已彻底失效」。
// 这两句都可以在**空视频节点**上直接验，而且与「有没有能播的视频」无关。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const OUT = new URL('./_tmp-b78.json', import.meta.url);
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
async function selectNode(id) {
  for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.15, 0.2], [0.85, 0.2], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18], [0.25, 0.45]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      return { x, y, inNode: !!(document.elementFromPoint(x, y) || {}).closest?.(`.react-flow__node[data-id="${vid}"]`) }; }, [id, fx, fy]);
    if (!pt || !pt.inNode) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true;
  } return false;
}
/** 节点卡片内所有可交互元素 + 时间读数 + 进度条（**只读，不点**） */
const probeCard = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const items = Array.from(n.querySelectorAll('button,[role="button"],input,[data-testid]'))
    .map((e) => { const q = e.getBoundingClientRect();
      return { tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        aria: e.getAttribute('aria-label'), text: (e.innerText || '').trim().split('\n')[0].slice(0, 18),
        title: e.getAttribute('title'), disabled: e.getAttribute('aria-disabled') || e.disabled || null,
        box: `${Math.round(q.width)}x${Math.round(q.height)}`,
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2),
        visible: q.width > 1 && q.height > 1 }; });
  const txt = (n.innerText || '').replace(/\s+/g, ' ');
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text: txt.slice(0, 220),
    timeLike: txt.match(/\d{1,2}:\d{2}(?:\s*\/\s*\d{1,2}:\d{2})?/g),
    playish: items.filter((x) => /play|pause|muted|full ?screen|播放|暂停|静音|全屏/i.test(`${x.aria} ${x.text} ${x.title} ${x.testid}`)),
    visibleItems: items.filter((x) => x.visible).map((x) => `${x.tag}|${x.testid || ''}|${x.role || ''}|${x.aria || ''}|${x.text || ''}|${x.box}|${x.disabled || ''}`),
    allItems: items.length };
}, id);
async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500); return !(await ids()).includes(id);
}
const out = { startedAt: new Date().toISOString(), created: [] };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  // —— 对照组 1：**静息态**（不选中）
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2600);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常 ' + JSON.stringify(created));
  mine = created[0]; out.created.push(mine);
  const idle = await probeCard(mine);
  log(`\n══ 静息态 ${idle.box}\n   文本: ${idle.text}\n   时间样式: ${JSON.stringify(idle.timeLike)}｜元素总数 ${idle.allItems}｜可见 ${idle.visibleItems.length}\n   可见项:`);
  for (const s of idle.visibleItems) log('     ' + s);
  out.idle = idle;
  // —— 选中态
  await esc(1);
  if (!(await selectNode(mine))) { log('🔴 没选中'); } else {
    const sel = await probeCard(mine);
    log(`\n══ 选中态 ${sel.box}｜selected=${await selCount()}\n   文本: ${sel.text}\n   时间样式: ${JSON.stringify(sel.timeLike)}｜元素总数 ${sel.allItems}｜可见 ${sel.visibleItems.length}\n   可见项:`);
    for (const s of sel.visibleItems) log('     ' + s);
    log('   播放相关命中:', JSON.stringify(sel.playish, null, 1));
    out.selected = sel;
    // —— 悬停态（页面说「选中即出现播放控件」，悬停会不会也出现？）
    await esc(1);
    const hov = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, mine);
    await p.mouse.move(hov.x, hov.y); await p.waitForTimeout(900);
    const hv = await probeCard(mine);
    log(`\n══ 悬停态｜可见 ${hv.visibleItems.length} 项｜时间样式 ${JSON.stringify(hv.timeLike)}`);
    out.hover = hv;
    if (sel.box) {
      const clip = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
        return { x: Math.max(0, Math.round(r.x - 24)), y: Math.max(0, Math.round(r.y - 24)),
          width: Math.min(1280, Math.round(r.width + 48)), height: Math.min(720, Math.round(r.height + 48)) }; }, mine);
      await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip });
      log('📷 78-empty-video-node-card.png', JSON.stringify(clip));
    }
  }
  log('\n积分（全程）:', await credit());
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  if (mine && (await ids()).includes(mine)) log('清理', mine, (await ctxDelete(mine)) ? '✅ deleted' : '🔴 仍在');
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  log('终态', JSON.stringify(out.end));
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); led.ids = [...new Set([...(led.ids || []), ...out.created])].sort();
    led.per_batch = { ...(led.per_batch || {}), 78: out.created }; writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } catch {}
  await b.close();
}
