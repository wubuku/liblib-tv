// 批次 77：`duplicate-delete-history.md` 逐类型复测（该页最新只到批次 30，是全册最陈旧的页面之一）
//
// 页面上的三组断言，逐条对：
//   A 右键菜单**逐类型**的条目数与容器尺寸（空视频 7/200×292 基线；文本/时间线/导演台 同基线；
//     空图片 8/200×332；主体 8/200×332；有资源图片 9/200×372）
//   B 「下载」禁用原因分两种（媒体一种、主体/时间线/导演台一种；**文本不禁用、直接可用**）
//   C ⌘D 副本命名追加序号 ` (2)` —— ⚠️ 批次 30 只在**视频**节点上精确复测过，
//     页面却把它写成了通用规则 ⇒ 本批在**文本 / 主体 / 图片**上各测一次。
//
// 纪律：
//   · 只**读**右键菜单，绝不点「保存到主体库」（写共享数据、撤不回）与「下载」；
//   · 所有临时节点建一个删一个，收尾按 id 精确删除并回读确认；
//   · ⌘D 产生的副本用 ⌘Z 撤销（验证「⌘Z 可撤销副本」这条页面断言）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const OUT = new URL('./_tmp-b77.json', import.meta.url);
const TYPES = ['视频', '文本', '图片', '音频', '时间线', '主体', '导演台'];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };

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
/** 右键菜单全量读数（**只读**，不点任何条目） */
const readCtxMenu = () => p.evaluate(() => {
  const ms = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const el = ms[ms.length - 1]; if (!el) return { none: true };
  const r = el.getBoundingClientRect();
  return { aria: el.getAttribute('aria-label'), role: el.getAttribute('role'), testid: el.getAttribute('data-testid'),
    box: `${Math.round(r.width)}x${Math.round(r.height)}`,
    items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => { const q = x.getBoundingClientRect(); const cs = getComputedStyle(x);
      const lines = (x.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
      const sr = Array.from(x.querySelectorAll('.sr-only')).map((s) => (s.innerText || '').trim()).filter(Boolean);
      return { name: lines[0], sub: lines.slice(1), srOnly: sr, dis: x.getAttribute('aria-disabled'), cursor: cs.cursor,
        color: cs.color, box: `${Math.round(q.width)}x${Math.round(q.height)}` }; }) };
});
async function openCtxMenu(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return false;
  await p.mouse.click(box.x, box.y, { button: 'right' });
  await p.waitForTimeout(1000);
  return true;
}
async function ctxDelete(id) {
  if (!await openCtxMenu(id)) return false;
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1500);
  if (!(await ids()).includes(id)) return true;
  if (!ok) { await esc(1); await openCtxMenu(id);
    await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
    await p.waitForTimeout(1500); }
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString(), created: [], menus: {}, dup: [] };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  for (const kind of TYPES) {
    const pre = await ids();
    const rail = await p.evaluate((k) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => new RegExp('^' + k + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, kind);
    if (!rail) { log(`🔴 ${kind}: 左栏无入口`); continue; }
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2400);
    const created = (await ids()).filter((x) => !pre.includes(x));
    if (created.length !== 1) { log(`🔴 ${kind} 新建 ${created.length} 个`); await esc(2); continue; }
    const id = created[0]; mine = id; out.created.push(id);
    await esc(1);
    // —— A/B：右键菜单逐项读数
    await openCtxMenu(id);
    const menu = await readCtxMenu();
    out.menus[kind] = menu;
    log(`\n── ${kind} 菜单 ${menu.box}｜${(menu.items || []).length} 项｜aria ${menu.aria}`);
    for (const it of (menu.items || [])) log(`   ${it.dis === 'true' || it.cursor === 'not-allowed' ? '🔘' : '✅'} ${it.name}${it.sub.length ? '｜' + it.sub.join(' / ') : ''}${it.srOnly.length ? '｜sr-only: ' + it.srOnly.join(' / ') : ''}｜${it.cursor}`);
    await esc(1);

    // —— C：⌘D 副本命名（先断言真正选中，页面明确写过「0 selected 时按 ⌘D 无反应」）
    if (['文本', '主体', '图片'].includes(kind)) {
      if (!(await selectNode(id))) { log(`   ⛔ ${kind} 没选中 ⇒ ⌘D 读数作废（页面已记：未选中时无反应）`); }
      else {
        const g = await keyGuard(p);            // ⌘D 是字母类按键 ⇒ 过安全守卫
        if (!g.safe) log(`   ⛔ 焦点不安全（${g.where}）⇒ 跳过 ⌘D`);
        else {
          const before = await ids();
          const n0 = before.length;
          await p.keyboard.press('Meta+d'); await p.waitForTimeout(1500);
          const after = await ids();
          const created2 = after.filter((x) => !before.includes(x));
          let dupInfo = { kind, createdCount: created2.length, n0, n1: after.length };
          if (created2.length === 1) {
            dupInfo.dupId = created2[0];
            dupInfo.dupTitle = await p.evaluate((v) => (document.querySelector(`.react-flow__node[data-id="${v}"] .flow-node-title,[data-testid="node-title"]`) || document.querySelector(`.react-flow__node[data-id="${v}"]`)).innerText.trim().split('\n')[0], created2[0]);
            dupInfo.origTitle = await p.evaluate((v) => document.querySelector(`.react-flow__node[data-id="${v}"]`).innerText.trim().split('\n')[0], id);
            const geo = await p.evaluate(([a, c]) => { const f = (x) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(x.style.transform || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
              const A = document.querySelector(`.react-flow__node[data-id="${a}"]`), C = document.querySelector(`.react-flow__node[data-id="${c}"]`);
              const g2 = (e) => e ? { box: [Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)] } : null;
              return { orig: f(A), dup: f(C), origBox: g2(A), dupBox: g2(C) }; }, [id, created2[0]]);
            dupInfo.dx = geo.orig && geo.dup ? Math.round((geo.dup[0] - geo.orig[0]) * 100) / 100 : null;
            dupInfo.dy = geo.orig && geo.dup ? Math.round((geo.dup[1] - geo.orig[1]) * 100) / 100 : null;
            dupInfo.sameBox = geo.origBox && geo.dupBox ? geo.origBox.box.join('x') === geo.dupBox.box.join('x') : null;
            log(`   ⌘D → 新增 ${created2.length} 个｜原「${dupInfo.origTitle}」副本「${dupInfo.dupTitle}」｜dx=${dupInfo.dx} dy=${dupInfo.dy}｜同尺寸 ${dupInfo.sameBox}`);
            // ⌘Z 撤销副本（页面断言：⌘Z 可撤销副本）
            await p.keyboard.press('Meta+z'); await p.waitForTimeout(1300);
            dupInfo.afterUndo = { nodes: (await ids()).length, gone: !(await ids()).includes(created2[0]) };
            log(`   ⌘Z 后：${dupInfo.afterUndo.gone ? '✅ 副本已撤销' : '🔴 副本仍在'}｜节点数 ${dupInfo.afterUndo.nodes}`);
          } else log(`   ⌘D → 新增 ${created2.length} 个（不是 1 ⇒ 不作断言）`);
          out.dup.push(dupInfo);
          await esc(2);
        }
      }
    }
    log(`   清理 ${id} ${(await ctxDelete(id)) ? '✅' : '🔴 仍在'}`); mine = null;
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
    led.per_batch = { ...(led.per_batch || {}), 77: out.created }; led.updated_at = new Date().toISOString().slice(0, 10);
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('ledger 追加', out.created.length, '个 id'); } catch (e) { log('ledger 更新失败', e.message); }
  await b.close();
}
