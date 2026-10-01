// 批次 63 侦察：生成面板上「模型 / 比例 / 时长」三个维度的控件与价格读数在哪。
//
// 手册 `prepare-generation.md:415` 挂着：
//   「未验证：切换模型/比例/时长后**价格如何具体变化**（避免误触发扣费前置动作）」
// 这个理由是批次 61、62 连续两次推翻过的**同一个滥用标签**——
// 「改宿主节点的设置」不是扣费，「点生成」才是。批次 61 实测八轮积分 805→805。
//
// 本轮**全程不点生成**。先侦察控件结构，再逐维度实测。
//
// 🔑 纪律：全部在**自建的临时节点**上做 —— 共享画布上那 6 个是别人的，
// 改它们的模型会污染别人的数据。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b63-recon.json', import.meta.url);
const MINE = [];
const D = (e) => { const r = e.getBoundingClientRect();
  return { tag: e.tagName, tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
    aria: e.getAttribute('aria-label'), cls: String(e.className || '').slice(0, 44),
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const canvasPos = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 620; y += 20) for (let x = 90; x <= 1240; x += 20) {
  if (x > 1140 && y > 590) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty(); if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length)); i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length)) === 0; };
const makeNode = async (kind) => { await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await nodeIds();
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3200);
  const made = (await nodeIds()).filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] }; };
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await reset();
  const ok = await p.evaluate((vid) => { const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return false;
    const r = e.getBoundingClientRect();
    for (let fy = 0.12; fy <= 0.9; fy += 0.08) for (let fx = 0.12; fx <= 0.9; fx += 0.08) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const t = document.elementFromPoint(x, y); if (!t || !t.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (t.closest('button,a,[role="button"],input,textarea,select')) continue;
      e.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y })); return true; }
    return false; }, id);
  await p.waitForTimeout(900);
  if (await p.evaluate((v) => document.querySelector(`.react-flow__node[data-id="${v}"].selected`) !== null, id)) {
    const done = await p.evaluate(() => { const e = document.querySelector('.react-flow__node[data-id="'+document.querySelector('.react-flow__node.selected').getAttribute('data-id')+'"]');
      if (!e) return false; const r = e.getBoundingClientRect();
      e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); return true; });
    if (done) { await p.waitForTimeout(800);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1300); }
  }
  await reset();
  return (await p.evaluate((v) => !document.querySelector(`.react-flow__node[data-id="${v}"]`), id)) ? 'deleted' : 'STILL-THERE';
};
const priceOf = () => p.evaluate(() => { const t = document.body.innerText;
  const m = t.match(/Current price[^\n]*/); const o = t.match(/Original price[^\n]*/); const d = t.match(/Discount[^\n]*/);
  return { current: m ? m[0] : null, original: o ? o[0] : null, discount: d ? d[0] : null }; });

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 63 侦察：生成面板的模型/比例/时长控件 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf());
out.start = { status: await statusLine(), credit: c0, zoom: await zoomOf() };

try {
  const v = await makeNode('视频');
  console.log('\n建临时视频节点:', JSON.stringify(v));
  if (!v.id) throw new Error('建节点失败: ' + JSON.stringify(v));
  out.nodeId = v.id; MINE.length = 0; MINE.push(v.id);

  await reset();
  await p.waitForTimeout(1200);
  const form = await p.evaluate(() => { const f = document.querySelector('form[data-testid="generation-form"]'); if (!f) return null;
    const r = f.getBoundingClientRect();
    return { aria: f.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      text: (f.innerText || '').replace(/\n{2,}/g, '\n').trim(),
      buttons: Array.from(f.querySelectorAll('button,[role="button"]')).map(D),
      testids: Array.from(f.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')) }; });
  console.log('\n=== 生成面板 form ===');
  console.log('aria:', form && form.aria, '| box:', form && form.box);
  console.log('全文:\n' + (form ? form.text.split('\n').map((s) => '  | ' + s).join('\n') : '(读不到)'));
  console.log('按钮:'); for (const x of (form ? form.buttons : [])) console.log('  ', JSON.stringify(x));
  console.log('testid 清单:', JSON.stringify(form ? [...new Set(form.testids)] : []));
  console.log('价格:', JSON.stringify(await priceOf()));
  out.form = form; out.priceBaseline = await priceOf();

  // 逐个候选控件点开，看弹什么
  const CAND = (await form.buttons).map((x) => x);
  for (const c of CAND) {
    const label = c.aria || c.text;
    if (!label || /生成|发送|停止|清空|复制|删除|参考|上传|资产库|画布选择/.test(label)) continue;
    console.log(`\n--- 点候选控件「${label}」 ${c.box} ---`);
    const hit = await p.evaluate((box) => { const [w, h, x, y] = box.split('x').map(Number).concat(); return null; }, '');
    const pt = { x: (() => { const [, , , xx, yy] = c.box.match(/(\d+)x(\d+)@(-?\d+),(-?\d+)/).map(Number); return Math.round(xx + w / 2); })(),
                 y: (() => { const m2 = c.box.match(/(\d+)x(\d+)@(-?\d+),(-?\d+)/); return Math.round(Number(m2[4]) + Number(m2[2]) / 2); })() };
    const land = await p.evaluate(([x, y]) => { const t = document.elementFromPoint(x, y); const o = t && t.closest('button,[role="button"]');
      return { tag: t && t.tagName, aria: o && o.getAttribute('aria-label'), text: o && (o.innerText || '').trim().slice(0, 20), ok: !!o }; }, [pt.x, pt.y]);
    console.log('  落点:', JSON.stringify(land));
    if (!land.ok) { console.log('  跳过（落点不是按钮）'); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
    const pops = await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[data-testid*="popover"],[data-testid*="model"],[data-testid*="picker"],[data-testid*="dropdown"],[data-testid*="size"],[data-testid*="duration"],[data-testid*="ratio"]'))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .map((e) => ({ ...D(e), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) })));
    console.log('  弹出层:', pops.length, '个');
    for (const q of pops) { console.log(`    tid=${q.tid} role=${q.role} ${q.box}`); console.log(`      text=${q.text}`); }
    console.log('  价格:', JSON.stringify(await priceOf()));
    out[`pop_${label}`] = { box: c.box, land, pops, price: await priceOf() };
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
    const left = await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).length);
    if (left) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  console.log('\n=== 收尾 ===');
  for (const id of MINE) console.log('删', id, '->', await deleteById(id));
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const s = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  await reset();
  const fin = await canvasPos();
  let dev = 0;
  for (const [id, base] of Object.entries(BASE.nodes)) { const cur = fin[id];
    const d = cur && base.canvas ? [Math.round((cur[0] - base.canvas[0]) * 100) / 100, Math.round((cur[1] - base.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev);
  console.log('剩余待删:', JSON.stringify(MINE.filter((id) => fin[id])));
  out.end = { status: await statusLine(), zoom: await zoomOf(), credit: await credit(), dev, mineLeft: MINE.filter((id) => fin[id]) };
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('写入', OUT.pathname);
  await b.close();
}
