// 批次 72 · A2：把入口 2 的菜单读到**逐项状态**（不靠标题判定方向），
// 顺带解决一个**量纲疑点**：手册同页里手柄有两个尺寸说法，对不上。
//
// 背景 1（方向判定）：b72a 已证明「从手柄拖到空白松手」**自动**弹出
//   canvas-context-menu / aria 逐字「添加节点」/ 200×316 —— 但只记了菜单项**名字**，
//   没记**可连性**。而批次 71 的铁律是：标题跟按钮走，**判定方向要靠可连项**。
//   尺子用视频源：after ⊕ 只有「视频」可连（其余六项禁用），
//   before ⊕ 则是 文本/图片/视频/音频 四项可连 —— 两者**不可能混淆**。
//
// 背景 2（量纲疑点）：`connect-nodes.md` 里手柄尺寸有两个互不相容的说法 ——
//   「入口」小节写「约 **60×120** 热区」，「原子步骤」写「实测约 **44×88**（60% 缩放下量得 43×87）」。
//   若两者都是 60% 下的屏上像素，换算成 canvas 应为 100×200 与 73×147，**差了 28%**；
//   若「60×120」本来就是 canvas 口径，则它与我实测的 34×68 屏上（≈56.7×113.3 canvas）吻合，
//   而「44×88@60%」那一处就是**把别的缩放档的读数记成了 60%**（批次 68 同款错误）。
//   本轮量多种节点类型 + 直接读 transform 比例，给出可判定的结论。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b72a2.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(380); } };
const BLOCK = ['button', '[role="button"]', 'input', 'textarea', '[role="menu"]', '[role="listbox"]', '[role="dialog"]',
  '[data-testid="node-toolbar"]', '[data-testid="workspace-bottom-dock-frame"]', '[data-testid="canvas-fixed-toolbar-left-rail"]',
  '[data-testid="canvas-top-bar-actions"]', '[data-testid="canvas-panel-launcher"]', '[data-testid="canvas-feature-sidecar"]'].join(',');

/** 节点 → 其两个手柄的**屏上**尺寸 + 换算出的 canvas 尺寸 + 缩放比例 */
const handleGeom = (id) => p.evaluate(([vid, scale]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
  const pick = (side) => n.querySelector(`.react-flow__handle-${side}`);
  const one = (side) => { const h = pick(side); if (!h) return null; const r = h.getBoundingClientRect();
    const cs = getComputedStyle(h);
    return { side, w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
      canvasW: Math.round((r.width / scale) * 10) / 10, canvasH: Math.round((r.height / scale) * 10) / 10,
      pe: cs.pointerEvents, op: cs.opacity,
      glyphX: h.style.getPropertyValue('--octo-flow-node-handle-glyph-x'), glyphY: h.style.getPropertyValue('--octo-flow-node-handle-glyph-y'),
      clsShort: String(h.className).split(' ').slice(0, 2).join('.') }; };
  const tr = getComputedStyle(n).transform;
  return { handles: [one('left'), one('right')], nodeTransform: tr, nodeScaleVar: n.style.getPropertyValue('--octo-flow-node-scale') || null };
}, [id, 0.6]);

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

const out = { startedAt: new Date().toISOString(), geom: {} };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  // —— 顺手把他人节点的缩放比例读出来（用它的 transform matrix a 值），作为换算依据
  const scaleProbe = await p.evaluate(() => { const n = document.querySelector('.react-flow__node');
    const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(n).transform); return m ? parseFloat(m[1]) : null; });
  log('节点 transform matrix a（=缩放）:', scaleProbe);

  for (const kind of ['视频', '文本', '图片']) {
    const pre = await ids();
    const rail = await p.evaluate((k) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => new RegExp('^' + k + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, kind);
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2400);
    const created = (await ids()).filter((x) => !pre.includes(x));
    if (created.length !== 1) { log(`🔴 ${kind} 新建 ${created.length} 个`); created.forEach(() => {}); await esc(2); continue; }
    const id = created[0];
    out.geom[kind] = await handleGeom(id);
    log(`\n── ${kind} ${id} 手柄:`, JSON.stringify(out.geom[kind]));

    if (kind === '视频') {
      // —— 不选中，直接拖右手柄到空白
      const h = out.geom[kind].handles.find((x) => x.side === 'right');
      const at = await p.evaluate(([id2, side]) => { const el = document.querySelector(`.react-flow__node[data-id="${id2}"] .react-flow__handle-${side}`);
        const r = el.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, [id, 'right']);
      await p.mouse.move(at.cx, at.cy); await p.waitForTimeout(700);
      const grab = await p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); return { onHandle: !!(el && el.closest('[class*="react-flow__handle"]')) }; }, [at.cx, at.cy]);
      if (!grab.onHandle) throw new Error('落点不在手柄上，拒绝拖拽');
      const blank = await p.evaluate((BLOCK) => {
        for (let y = 150; y < 640; y += 16) for (let x = 140; x < 1170; x += 16) {
          const el = document.elementFromPoint(x, y); if (!el || el.closest('.react-flow__node') || el.closest(BLOCK)) continue;
          return { x, y }; } return null; }, BLOCK);
      log('   空白落点', JSON.stringify(blank));
      await p.mouse.down(); await p.waitForTimeout(220);
      for (let i = 1; i <= 8; i++) { await p.mouse.move(Math.round(at.cx + ((blank.x - at.cx) * i) / 8), Math.round(at.cy + ((blank.y - at.cy) * i) / 8)); await p.waitForTimeout(90); }
      await p.mouse.up(); await p.waitForTimeout(1500);
      // —— 读**逐项状态**：这是判定方向的唯一硬证据
      const menu = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
        if (!ms.length) return { none: true };
        const el = ms[ms.length - 1]; const r = el.getBoundingClientRect();
        return { aria: el.getAttribute('aria-label'), testid: el.getAttribute('data-testid'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => ({ name: (x.innerText || '').trim().split('\n')[0],
            reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
            dis: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor, color: getComputedStyle(x).color })) }; });
      out.entry2Menu = menu;
      log('   入口 2 菜单:', menu.aria, menu.box);
      for (const it of (menu.items || [])) log(`     ${it.dis === 'true' || it.cursor === 'not-allowed' ? '🔘' : '✅'} ${it.name}｜${it.reason || '—'}｜${it.cursor}｜${it.color}`);
      await esc(1);
    }
    mine = id;
    log('   清理', id, (await ctxDelete(id)) ? '✅' : '🔴 仍在');
    mine = null;
  }
  log('\n积分:', await credit());
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
