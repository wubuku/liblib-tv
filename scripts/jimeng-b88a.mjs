// 批次 88 · A：审计 `director-node.md`（普查停在 71）。
//
// 这一页经批次 57/68 两次取证，质量很高，**不需要重复它已做过的**。
// 本轮打的是**别的批次造出来的弹药**：
//
// 🔑 **批次 85 刚证明 `[data-testid="node-toolbar"]` 一个 testid 覆盖两类面板**：
//     生成面板（空视频/图片/音频，`680×208`，不随缩放）
//     ＋ 文本节点浮动工具条（`192×40`@60%，随缩放）。
//     而本页第 21 行写着「**选中它（导演台）没有浮动工具条**（与主体、时间线节点一致）」。
//     ⇒ **可证伪预测 P1**：选中导演台时 `node-toolbar` 计数为 **0**
//       （或只剩那个高度 0 的占位），**不出现 680×208、也不出现 192×40**。
//       若成立 ⇒ `node-toolbar` 的类型表要补一行「导演台 / 主体 / 时间线：无」。
//
// 🔑 **批次 78 钉过「标题行在节点矩形上方 31–33 canvas px」**。
//     本页第 33 行写 `Rename 导演台`「顶边在卡片顶边上方 **32px**、与卡片顶齐平」，
//     且给了屏上坐标 `39×32@564,232`。
//     ⇒ **可证伪预测 P2**：这个 32 到底是**屏上**还是 **canvas**？
//       在 60% 下，屏上 32 px = canvas 53.3 px；canvas 32 px = 屏上 19.2 px。
//       一次双缩放测量就能定。
//
// 🔑 **批次 86 证明 `.sr-only` 到处都是**、批次 85 证明后代选择器会捞进节点。
//     本页的「静息态 / 选中态元素差分」正是靠差集做的 —— 沿用同一手法复核。
//
// ⛔ 绝不点：**「进入导演台」**（会跳进 3D 工作台，未获单独授权）、
//        `Rename 导演台`、两个连接手柄、任何扣费按钮。
//        也**不按 F**（该页自己写明「按 F 会不会跳进 3D 工作台恰恰是未知的，不冒险」）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => { const l = await p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
    return e ? e.getAttribute('aria-label') : null; }); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const titlePointXY = async (id) => { const sc = await readScale();
  return await p.evaluate((arg) => { const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); const tries = [];
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) {
      const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * arg.scale));
      if (x < 0 || y < 0 || y > 716) continue;
      const h = document.elementFromPoint(x, y); if (!h || !n.contains(h)) continue;
      tries.push({ k, f, x, y, txt: (h.innerText || h.getAttribute('aria-label') || '').trim().slice(0, 16) }); }
    const withTxt = tries.filter((t) => t.txt); const pick = withTxt[0] || tries[0] || null;
    return { scale: arg.scale, nodeBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, pick }; }, { v: id, scale: sc.scale }); };

/** 🔑 可见元素签名快照（差集用）。 */
const snap = () => p.evaluate(() => { const o = [];
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    o.push({ k: `${e.tagName}|${String(e.className||'').split(' ')[0]}|${Math.round(r.width)}x${Math.round(r.height)}|${e.getAttribute('data-testid')||''}|${e.getAttribute('aria-label')||''}|${(e.innerText||'').trim().split('\n')[0].slice(0,16)}`,
      tag: e.tagName, cls: String(e.className||'').split(' ')[0], w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y), testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      role: e.getAttribute('role'), t: (e.innerText || '').trim().split('\n')[0].slice(0, 22) }); }
  return o; });
const diffAdd = (A, B) => { const m = new Set(A.map((r) => r.k)); return B.filter((r) => !m.has(r.k)); };

/** 导演台节点的全量描述（限定在该节点 DOM 内，避免后代污染）。 */
const describe = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { err: '节点不在' };
  const r = n.getBoundingClientRect();
  const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); const scale = m ? Number(m[1]) : null;
  const info = (e) => { if (!e) return null; const rr = e.getBoundingClientRect();
    return { tag: e.tagName, box: `${Math.round(rr.width)}x${Math.round(rr.height)}@${Math.round(rr.x)},${Math.round(rr.y)}`,
      canvas: scale ? `${Math.round(rr.width/scale)}x${Math.round(rr.height/scale)}` : null,
      aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'), cls: String(e.className||'').split(' ').slice(0,2).join('.'),
      cursor: getComputedStyle(e).cursor, t: (e.innerText || '').trim().slice(0, 24) }; };
  const enter = Array.from(n.querySelectorAll('*')).find((e) => /进入导演台/.test(e.innerText || '') && e.children.length === 0)
    || n.querySelector('[aria-label="进入导演台"]');
  const rename = Array.from(n.querySelectorAll('*')).find((e) => /Rename 导演台/.test(e.innerText || e.getAttribute('aria-label') || ''));
  const title = n.querySelector('[class*="node-title"], .flow-node-title');
  const tags = Array.from(n.querySelectorAll('*')).find((e) => /Add tags/i.test((e.getAttribute('aria-label') || '') + (e.innerText || '')));
  const handles = Array.from(n.querySelectorAll('.react-flow__handle, [class*="handle"]'))
    .map((e) => { const rr = e.getBoundingClientRect();
      return { cls: String(e.className||'').split(' ').slice(0,2).join('.'), testid: e.getAttribute('data-testid'),
        box: `${Math.round(rr.width)}x${Math.round(rr.height)}@${Math.round(rr.x)},${Math.round(rr.y)}` }; });
  return { nodeBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    nodeCanvas: scale ? `${Math.round(r.width/scale)}x${Math.round(r.height/scale)}` : null, scale,
    nodeClass: n.className, nodeAria: (n.parentElement || {}).getAttribute ? n.parentElement.getAttribute('aria-label') : null,
    enter: info(enter), rename: info(rename), title: info(title), addTags: info(tags),
    handleCount: handles.length, handles,
    // 页面说 Rename 顶边「在卡片顶边上方 32px、与卡片顶齐平」→ 直接算差
    renameOffset: (() => { if (!rename) return null; const rr = rename.getBoundingClientRect();
      return { screenDy: Math.round(rr.y - r.y), screenDx: Math.round(rr.x - r.x),
        canvasDy: scale ? Math.round((rr.y - r.y) / scale) : null, canvasDx: scale ? Math.round((rr.x - r.x) / scale) : null }; })(),
    // P1：node-toolbar 计数
    nodeToolbars: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => { const rr = e.getBoundingClientRect();
      return `${Math.round(rr.width)}x${Math.round(rr.height)}`; }),
    // 节点外的浮层（画布级）
    outerFloat: Array.from(document.querySelectorAll('[data-testid^="selection-context-toolbar"]')).length };
}, id);

try {
  out.zoom0 = await setZoom(60); out.credits0 = await credits();
  log('起始', JSON.stringify(out.zoom0), out.credits0);

  // ══════ 建一个导演台节点 ══════
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^导演台$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rail) throw new Error('左栏找不到「导演台」');
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine.push(made[0]);
  const id = made[0];

  out.grids = [];
  // ══════ 档 1：60% — 静息态 ══════
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  out.grids.push({ tag: '静息@60%', sel: await selCount(), ...(await describe(id)) });
  log('静息@60%', JSON.stringify(out.grids[0], null, 1));
  const A60 = await snap();

  // ══════ 档 2：60% — 选中态 ══════
  const t = await titlePointXY(id);
  log('标题落点', JSON.stringify(t));
  if (t && t.pick) { await p.mouse.click(t.pick.x, t.pick.y); await p.waitForTimeout(2000); }
  out.grids.push({ tag: '选中@60%', sel: await selCount(), titlePoint: t, ...(await describe(id)) });
  log('选中@60%', JSON.stringify(out.grids[1], null, 1));
  const B60 = await snap();
  out.diff60 = diffAdd(A60, B60);
  log(`60% 静息→选中：新增 ${out.diff60.length} 个`);
  out.diff60.slice(0, 12).forEach((r) => log('   +', JSON.stringify({ tag: r.tag, cls: r.cls, box: `${r.w}x${r.h}@${r.x},${r.y}`, testid: r.testid, aria: r.aria, t: r.t })));
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);

  // ══════ 档 3：100% — 验 canvas 320×320 与 rename 偏移的量纲 ══════
  out.zoom1 = await setZoom(100); log('切到', JSON.stringify(out.zoom1));
  await p.waitForTimeout(1000);
  const t1 = await titlePointXY(id);
  if (t1 && t1.pick) { await p.mouse.click(t1.pick.x, t1.pick.y); await p.waitForTimeout(2000); }
  out.grids.push({ tag: '选中@100%', sel: await selCount(), titlePoint: t1, ...(await describe(id)) });
  log('选中@100%', JSON.stringify(out.grids[2], null, 1));
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);

  // ══════ 判读 ══════
  const rest60 = out.grids[0], sel60 = out.grids[1], sel100 = out.grids[2];
  out.verdict = {};
  out.verdict.P1_noToolbar = { idle: rest60.nodeToolbars, selected: sel60.nodeToolbars,
    ok: rest60.nodeToolbars.every((s) => /x0$|^0x/.test(s)) && sel60.nodeToolbars.every((s) => /x0$|^0x/.test(s)) };
  log('P1 选中导演台后 node-toolbar =', JSON.stringify(sel60.nodeToolbars), '| 预测成立 =', out.verdict.P1_noToolbar.ok);
  out.verdict.P2_renameOffset = { at60: sel60.renameOffset, at100: sel100 ? sel100.renameOffset : null,
    pageSays: '顶边在卡片顶边上方 32px' };
  log('P2 rename 偏移 60%:', JSON.stringify(sel60.renameOffset), ' 100%:', JSON.stringify(out.verdict.P2_renameOffset.at100));
  out.verdict.nodeCanvas = { at60: rest60.nodeCanvas, at100: sel100 ? sel100.nodeCanvas : null, pageSays: 'canvas 恒 320×320' };
  log('节点 canvas 60%:', rest60.nodeCanvas, ' 100%:', out.verdict.nodeCanvas.at100, '| 页面称恒 320×320');
  out.credits1 = await credits();
  log('积分', out.credits0, '→', out.credits1);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const v of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(v); a++) {
      const q = await p.evaluate((x) => { const n = document.querySelector(`.react-flow__node[data-id="${x}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const X = Math.round(r.x + r.width * f[0]), Y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(X, Y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x: X, y: Y }; } return null; }, v);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(950);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1400);
    }
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), credits: await credits(), leftover: left };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 88: [...new Set([...(led.per_batch?.['88'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b88a.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
