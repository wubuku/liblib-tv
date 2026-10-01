// 批次 72 · A：入口 2（从手柄拖到空白松手后再点 +）**属哪个方向？**
//
// 批次 71 在正文里明确留了一个洞：「入口 2 打开的是哪一个方向，本批未取证」。
// 本轮用**方向差异最大**的源当尺子 —— 视频源：
//   before ⊕「添加上下文」可连 4 项（文本/图片/视频/音频）
//   after  ⊕「添加节点」   可连 1 项（视频）
// ⇒ 读出来的可连项**必然**能判定方向，不靠猜标题。
//
// 三条纪律：
//   ① 拖拽前用 elementFromPoint 断言落点**真的在手柄元素上**（批次 64/65 的坑）；
//   ② **不选中节点**（选中时 handle pointer-events:none，会被 ⊕ 接管 ⇒ 拖不到手柄）；
//   ③ 拖到**空白**而非他人节点上；收尾用门 8 的 canvas 坐标比对证明没碰别人。
// 另：拖拽可能把节点带走 ⇒ 全程只在自己的临时节点上拖，且收尾按 id 精确删除。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b72a.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(380); } };

/** 全文档可交互元素指纹，用于「松手后到底多出了什么」的差分 */
const census = () => p.evaluate(() => {
  const keys = new Map();
  for (const e of document.querySelectorAll('[aria-label],[data-testid],[role="menuitem"],[role="button"],button')) {
    const q = e.getBoundingClientRect();
    const k = `${e.tagName}|${e.getAttribute('data-testid') || ''}|${e.getAttribute('role') || ''}|${e.getAttribute('aria-label') || ''}|${(e.innerText || '').trim().split('\n')[0]}`;
    if (!keys.has(k)) keys.set(k, { n: 0, vis: 0, box: `${Math.round(q.width)}x${Math.round(q.height)}`, cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) });
    const v = keys.get(k); v.n++; if (q.width > 1) { v.vis++; v.box = `${Math.round(q.width)}x${Math.round(q.height)}`; v.cx = Math.round(q.x + q.width / 2); v.cy = Math.round(q.y + q.height / 2); }
  }
  return Object.fromEntries(keys);
});
const diff = (a, c) => Object.keys(c).filter((k) => !(k in a) || c[k].vis > (a[k] ? a[k].vis : 0));

/** 「空白落点」必须避开的可交互层（沿用历批清单） */
const BLOCKERS = ['button', '[role="button"]', 'input', 'textarea', '[role="menu"]', '[role="listbox"]', '[role="dialog"]',
  '[data-testid="node-toolbar"]', '[data-testid="workspace-bottom-dock-frame"]', '[data-testid="canvas-fixed-toolbar-left-rail"]',
  '[data-testid="canvas-top-bar-actions"]', '[data-testid="canvas-panel-launcher"]', '[data-testid="canvas-feature-sidecar"]'].join(',');

async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500);
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString() };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  // —— 建一个**视频源**空节点（方向差异最大的尺子）
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2400);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建数异常 ' + JSON.stringify(created));
  mine = created[0];
  const nodePos0 = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); return [parseFloat(m[1]), parseFloat(m[2])]; }, mine);
  log('新建视频节点', mine, 'canvas 起点', JSON.stringify(nodePos0.map((x) => Math.round(x * 100) / 100)));

  // —— ① 先量手柄：**不选中**，悬停才显形
  const handle = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const hs = Array.from(n.querySelectorAll('.react-flow__handle, [class*="react-flow__handle"]'));
    return hs.map((h) => { const r = h.getBoundingClientRect();
      return { cls: String(h.className).split(' ').filter((c) => /handle|left|right|source|target/.test(c)).join('.'),
        box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        pe: getComputedStyle(h).pointerEvents, op: getComputedStyle(h).opacity }; });
  }, mine);
  log('节点内手柄元素:', JSON.stringify(handle, null, 1));

  const h = (handle || []).find((x) => /right|source/.test(x.cls)) || (handle || [])[0];
  if (!h) throw new Error('找不到手柄元素');
  // —— ② 悬停 → 断言落点真的是手柄（批次 64/65 的坑：合成 click / 猜坐标都翻过车）
  await p.mouse.move(h.cx, h.cy); await p.waitForTimeout(700);
  const grab = await p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y);
    return { tag: el ? el.tagName : 'null', cls: el ? String(el.className).slice(0, 90) : '', onHandle: !!(el && el.closest('[class*="react-flow__handle"]')) }; }, [h.cx, h.cy]);
  log('悬停后落点:', JSON.stringify(grab));
  if (!grab.onHandle) throw new Error('落点不在手柄上 ⇒ 拒绝拖拽（拖到别处会把节点拖走）');

  // —— ③ 找一个**空白**落点（不在任何节点/控件上）
  const blank = await p.evaluate((BLOCK) => {
    for (let y = 140; y < 640; y += 16) for (let x = 120; x < 1180; x += 16) {
      const el = document.elementFromPoint(x, y); if (!el) continue;
      if (el.closest('.react-flow__node')) continue;
      if (el.closest(BLOCK)) continue;
      return { x, y, tag: el.tagName, cls: String(el.className).slice(0, 60) };
    } return null; }, BLOCKERS);
  log('空白落点:', JSON.stringify(blank));
  if (!blank) throw new Error('找不到空白落点');

  const before0 = await census();
  // —— ④ 真拖：down → 分步 move → up
  await p.mouse.move(h.cx, h.cy); await p.waitForTimeout(300);
  await p.mouse.down(); await p.waitForTimeout(220);
  for (let i = 1; i <= 8; i++) {
    await p.mouse.move(Math.round(h.cx + ((blank.x - h.cx) * i) / 8), Math.round(h.cy + ((blank.y - h.cy) * i) / 8));
    await p.waitForTimeout(90);
  }
  await p.mouse.up(); await p.waitForTimeout(1200);
  out.afterRelease = { status: await status(), newEls: diff(before0, await census()) };
  log('松手后状态行:', out.afterRelease.status);
  log('松手后新增/变可见元素:', JSON.stringify(out.afterRelease.newEls, null, 1));

  // 节点有没有被拖走？
  const nodePos1 = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); return [parseFloat(m[1]), parseFloat(m[2])]; }, mine);
  out.nodeDelta = [Math.round((nodePos1[0] - nodePos0[0]) * 100) / 100, Math.round((nodePos1[1] - nodePos0[1]) * 100) / 100];
  log('节点自身位移:', JSON.stringify(out.nodeDelta), out.nodeDelta[0] === 0 && out.nodeDelta[1] === 0 ? '✅ 没被拖走' : '🔴 被拖走了');

  // —— ⑤ 菜单本体是否已弹出？
  const menu0 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
    if (!ms.length) return { none: true };
    const el = ms[ms.length - 1]; const r = el.getBoundingClientRect();
    return { aria: el.getAttribute('aria-label'), role: el.getAttribute('role'), testid: el.getAttribute('data-testid'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => (x.innerText || '').trim().split('\n')[0]) }; });
  log('松手瞬间的菜单:', JSON.stringify(menu0));

  // —— ⑥ 若没自动弹菜单，找那个「+」并点它
  if (menu0.none) {
    const plusInfo = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"],[aria-label*="onnected"],[aria-label*="添加"],[aria-label*="Add"]'))
      .map((e) => { const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
        return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
          text: (e.innerText || '').trim().slice(0, 12), box: `${Math.round(q.width)}x${Math.round(q.height)}`,
          cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }).filter(Boolean));
    log('松手处的可点元素:', JSON.stringify(plusInfo, null, 1));
    out.plusInfo = plusInfo;
    const cand = plusInfo.find((x) => /onnected|添加|Add|\+/.test((x.aria || '') + (x.text || '')));
    if (cand) {
      await p.mouse.click(cand.cx, cand.cy); await p.waitForTimeout(1800);
      const menu1 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
        if (!ms.length) return { none: true };
        const el = ms[ms.length - 1]; const r = el.getBoundingClientRect();
        return { aria: el.getAttribute('aria-label'), role: el.getAttribute('role'), testid: el.getAttribute('data-testid'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => ({ name: (x.innerText || '').trim().split('\n')[0],
            reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
            dis: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor })) }; });
      log('点 + 之后的菜单:', JSON.stringify(menu1, null, 1));
      out.menuAfterClick = menu1;
    } else { log('🔴 松手处没有可点的「+」⇒ 入口 2 这条路径本轮复现不出来'); }
  } else { out.menuOnRelease = menu0; }
  await esc(1);
  log('积分:', await credit());
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
  writeFileSync(OUT, JSON.stringify(out, null, 1)); await b.close();
}
