// 批次 36：参考来源三选一的二级入口 —— 「从画布选择」首次打开（只开不选）
// 纪律：不点任何会改变画布/素材状态的项；选中前先 pan 走他人节点并断言视口内无他人节点。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { makePanner } from './jimeng-pan.mjs';
const OUT = [];
const say = (t, o) => OUT.push('### ' + t + '\n' + (typeof o === 'string' ? o : JSON.stringify(o, null, 1)));
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com'));
const cdp = await ctx.newCDPSession(page);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
await page.waitForTimeout(700);
const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
if (vp.w !== 1280 || vp.h !== 720) { console.error('VIEWPORT POLLUTED', JSON.stringify(vp)); process.exit(2); }
for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(400); }
const esc = async (n) => { for (let i = 0; i < n; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(420); } };
const credits = () => page.evaluate(() => (document.body.innerText.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null);
const allNodes = () => page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id') || '', type: Array.from(n.classList).filter((c) => c.startsWith('react-flow__node-')).join(','),
  title: (n.innerText || '').split('\n').pop().trim().slice(0, 22),
})));
const OTHERS = new Set((await allNodes()).map((n) => n.id));
say('0 他人节点（不动）', Array.from(OTHERS));

const railBtn = (name) => page.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find((x) => (x.getAttribute('aria-label') || '') === nm); if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, name);
async function makeNode(kind, cls) {
  await esc(3);
  const rb = await railBtn(kind); if (!rb) return null;
  const pre = await allNodes();
  await page.mouse.click(rb.cx, rb.cy); await page.waitForTimeout(2400);
  const post = await allNodes();
  const created = post.filter((x) => !pre.some((y) => y.id === x.id) && x.type === cls);
  if (!created.length) return null;
  MINE.push(created[0].id); return created[0].id;
}
async function selectById(id) {
  const box = await page.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null; n.scrollIntoView({ block: 'center' }); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 26) }; }, id);
  if (!box) return false;
  await page.mouse.click(box.x, box.y); await page.waitForTimeout(1700);
  let ok = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id);
  if (!ok) { await page.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return; const r = n.getBoundingClientRect(); for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) n.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 26) })); }, id);
    await page.waitForTimeout(1700); ok = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id); }
  return ok;
}
const panelReady = () => page.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1 && e.getBoundingClientRect().height > 1).length > 0);

// 先建一个空图片节点（作为参考的宿主）
const host = await makeNode('图片', 'react-flow__node-image');
say('宿主节点', host);
if (!host) { console.error('ABORT'); process.exit(4); }
// 再建一个「素材源」节点：从画布选择时它应该出现在候选列表里
const src = await makeNode('视频', 'react-flow__node-video');
say('素材源节点', src);
say('我新建的', MINE);

const ok = await selectById(host);
say('宿主选中 =', ok);
if (!ok) { say('选中失败', 'ABORT'); writeFileSync('/tmp/b36.txt', OUT.join('\n\n')); console.log('WROTE /tmp/b36.txt'); await b.close(); process.exit(5); }

// 打开 添加参考 菜单
const addBtn = await page.evaluate(() => { const tb = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1 && e.getBoundingClientRect().height > 1)[0]; const e = tb && Array.from(tb.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '添加参考'); if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, expanded: e.getAttribute('aria-expanded') }; });
say('添加参考按钮', addBtn);
if (!addBtn) { writeFileSync('/tmp/b36.txt', OUT.join('\n\n')); console.log('WROTE /tmp/b36.txt'); await b.close(); process.exit(6); }
await page.mouse.click(addBtn.cx, addBtn.cy); await page.waitForTimeout(1500);
say('添加参考菜单', await page.evaluate(() => { const m = document.querySelector('[role="menu"][aria-label="添加参考"]'); if (!m) return 'NO MENU'; const r = m.getBoundingClientRect(); return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => { const b2 = i.getBoundingClientRect(); return { text: (i.innerText || '').trim(), box: `${Math.round(b2.width)}x${Math.round(b2.height)}@${Math.round(b2.x)},${Math.round(b2.y)}`, svg: i.querySelectorAll('svg').length, disabled: i.getAttribute('aria-disabled') || '' }; }) }; }));

// 点「从画布选择」—— 只观察它打开什么，不选任何条目
const pick = await page.evaluate(() => { const m = document.querySelector('[role="menu"][aria-label="添加参考"]'); if (!m) return null; const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /从画布选择/.test(x.innerText || '')); if (!it) return null; const r = it.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
say('从画布选择 坐标', pick);
const SIG = () => page.evaluate(() => {
  const out = [];
  document.querySelectorAll('*').forEach((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 6 || r.height < 6) return;
    if (r.bottom < 0 || r.right < 0 || r.x > innerWidth || r.y > innerHeight) return;
    const role = e.getAttribute('role') || '', tid = e.getAttribute('data-testid') || '', aria = e.getAttribute('aria-label') || '';
    if (!role && !tid && !aria) return;
    if (/react-flow|workbench-shell|main-region|rf__|top-bar|fixed-toolbar|navigation|bottom-dock|sidecar|node-toolbar|context-menu/i.test(tid + ' ' + aria + ' ' + (typeof e.className === 'string' ? e.className : ''))) return;
    out.push(`${e.tagName.toLowerCase()}|${role}|${tid}|${aria}|${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}x${Math.round(r.height)}|${(e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60)}`);
  });
  return Array.from(new Set(out)).sort();
});
const S0 = await SIG();
if (pick) { await page.mouse.click(pick.cx, pick.cy); await page.waitForTimeout(2200); }
const S1 = await SIG();
say('点「从画布选择」后的 DOM 差分', { added: S1.filter((x) => !S0.includes(x)), removed: S0.filter((x) => !S1.includes(x)) });
say('打开后的浮层细节', await page.evaluate(() => {
  const R = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
  const cands = Array.from(document.querySelectorAll('[role=listbox],[role=menu],[role=dialog],[data-testid]')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 8 && r.height > 8 && r.bottom > 0 && r.right > 0 && r.x < innerWidth && r.y < innerHeight; }).filter((e) => { const t = e.getAttribute('data-testid') || ''; const a = e.getAttribute('aria-label') || ''; const c = typeof e.className === 'string' ? e.className : ''; return /react-flow|workbench|main-region|rf__|top-bar|fixed-toolbar|navigation|dock|sidecar|node-toolbar|context-menu/i.test(t + ' ' + a + ' ' + c) ? false : true; });
  return cands.map((e) => ({ tag: e.tagName.toLowerCase(), testid: e.getAttribute('data-testid') || '', role: e.getAttribute('role') || '', aria: e.getAttribute('aria-label') || '', box: R(e), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) }));
}));
say('状态', await page.evaluate(() => ({ status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0], prompt: (() => { const tb = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().height > 1)[0]; const el = tb && tb.querySelector('[contenteditable="true"]'); return el ? el.innerText.replace(/\n/g, '') : null; })() })));
say('积分', await credits());
say('我新建的节点', MINE);
writeFileSync('/tmp/b36.txt', OUT.join('\n\n'));
writeFileSync('/tmp/b36-mine.txt', MINE.join('\n'));
console.log('WROTE /tmp/b36.txt ; MINE =', JSON.stringify(MINE));
await b.close();
