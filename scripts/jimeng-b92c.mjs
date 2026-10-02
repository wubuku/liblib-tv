// 批次 92 · C：**把自建节点删干净** —— 这是本轮的收尾债，优先于任何新发现。
//
// 现状：共享画布上留了两个我建的节点（`node_z3qd75wjaf`、`node_hfn7m4kt1v`），
// 位置在别人那一片密集区（canvas ≈ (1916,956) / (1956,1036)），
// 两次扫描都是 **0 个可用落点** —— 节点被**完全盖住**（批次 89 记的是 91/100，这里是 0/100）。
//
// 🔴 **两个技术要点**：
//   ① 右键菜单在自动化下**要用 `mouse.down` + 停顿 + `mouse.up`**，
//      `mouse.click({button:'right'})` **打不开**（批次 22 早就推翻过「自动化下弹不出」的说法，
//      给的正解就是 down + 150ms 停顿）。本轮实测 `click` 确实 `menu: null`。
//   ② 盖住时**点不到，但元素还在** ⇒ 删除不该依赖「先选中」。
//      处置：逐档放大画布（节点之间会散开）→ 每档重扫落点 → 找到就选中+右键删除。
//
// ⚠️ 只删**本轮自己创建**的两个 id，逐字核对 aria 是「文本 node: 文本 N」，
//    绝不按「类型」去删（那会连别人的节点一起删）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), targets: ['node_z3qd75wjaf', 'node_hfn7m4kt1v'] };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });

const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1400); await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const a = await zoomPct(); await p.waitForTimeout(800); const c = await zoomPct();
  if (a === t0 && a === c) return true; }
  return false; };

/** 逐字核对：确实是「文本 node: 文本 N」才允许动 */
const verify = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  return { aria: n.getAttribute('aria-label'), cls: String(n.className || '').slice(0, 40) }; }, id);

const scanLanding = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  let tested = 0;
  for (let fx = 0.04; fx <= 0.96; fx += 0.04) for (let fy = 0.04; fy <= 0.96; fy += 0.04) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    tested++;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return { x, y, tested };
  }
  return { fail: true, tested, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
}, id);

/** 右键：必须 down + 停顿 + up（批次 22 的正解；click 会被吞） */
const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1100); };

out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

out.results = [];
for (const id of out.targets) {
  const rec = { id };
  if (!(await ids()).includes(id)) { rec.gone = '已不在'; out.results.push(rec); log(id, '已不在'); continue; }
  rec.verify = await verify(id);
  log(id, 'aria =', JSON.stringify(rec.verify?.aria), '← 只删「文本 node: 文本 N」，逐字核对过');
  if (!/^文本 node: 文本 \d+$/.test(rec.verify?.aria || '')) { rec.skipped = 'aria 不是文本节点，不动'; out.results.push(rec); log('  ⚠️ aria 不符，跳过'); continue; }

  let done = false;
  for (const z of [60, 100, 200, 400, 800, 100]) {
    if (!await setZoom(z)) { log(`  缩放拨不到 ${z}%`); continue; }
    const pt = await scanLanding(id);
    log(`  @${z}% 落点：${pt && !pt.fail ? `(${pt.x},${pt.y}) 已测 ${pt.tested} 点` : JSON.stringify(pt)}`);
    if (!pt || pt.fail) continue;
    // 点一下选中（确认选中的是它）
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
    const got = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (got[0] !== id) { log(`    点上去选中的是 ${JSON.stringify(got)}，放弃这一档`); await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    // 右键 → 删除
    await rightClick(pt.x, pt.y);
    const menu = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
      return Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') })); });
    rec.menuAt = { zoom: z, items: menu ? menu.map((i) => i.t) : null };
    if (!menu) { log('    菜单没出来'); continue; }
    const del = menu.find((i) => /^删除/.test(i.t) && i.dis !== 'true');
    log('    菜单：' + JSON.stringify(menu.map((i) => i.t)));
    if (!del) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
      const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) it.click(); });
    await p.waitForTimeout(1600);
    if (!(await ids()).includes(id)) { rec.deleted = true; rec.via = `zoom ${z}% + 右键删除`; done = true; log('    ✅ 已删除'); break; }
    log('    点完还在，再试');
  }
  if (!done) rec.deleted = false;
  out.results.push(rec);
}

if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
await setZoom(60);
const left = (await ids()).filter((x) => out.targets.includes(x));
out.end = { nodes: (await ids()).length, sel: await selN(), zoom: await zoomPct(), credits: await credits(), leftover: left };
log('终态：', JSON.stringify(out.end), '｜缩放归位', (await zoomPct()) === 60 ? '✅' : '🔴');
log(left.length ? `🔴 仍有残留：${left.join(' ')}` : '✅ 两个自建节点都已删净');
writeFileSync(new URL('./_tmp-b92c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
