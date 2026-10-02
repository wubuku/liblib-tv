// 批次 80 · A：edit-text-node.md（**全册最陈旧任务页，停在批次 40**）的三处可测缺口。
// 纯本地操作：不生成、不发送、不耗积分、不需要授权。
//
// 缺口 1 页面第 133 行：「复制 ⌘C / 复制副本 ⌘D / 粘贴 ⌘V / 下载 / 撤销 / 删除」——**只列 6 项**，
//        而批次 77 逐类型复测时文本节点右键菜单是 **7 项 200×292**。⇒ 漏了一项。
// 缺口 2 页面第 138 行只说「不要点击空白（会提交）」，**完全没写按 Esc 会怎样** ——
//        这是提交还是撤销？读者最可能踩的一步，页面没答案。
// 缺口 3 页面第 104 行明写「改名提交动作**未执行**，保持画布原状」⇒ 补做。
//
// 纪律：只用**自建**文本节点；按字母键前先断言焦点在 `.ProseMirror`（keyGuard 的精神，
//       这里手工做同样的前置断言）；不按 ⌘D / ⌘C（会造副本）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, stable: true }; } return { scale: await scaleOf(), stable: false }; };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
let mine = null;
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); };
try {
  const z0 = await settle(); log('开场', JSON.stringify(z0), '|', await status()); out.z0 = z0;
  // —— 建自建文本节点
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常：' + JSON.stringify(made));
  mine = made[0]; log('新建', mine);

  // ============ 缺口 1：文本节点右键菜单逐项 ============
  const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    for (const f of [[0.5, 0.18], [0.3, 0.5], [0.7, 0.5], [0.5, 0.35]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
      const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
  if (!pt) throw new Error('右键落点找不到');
  await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1200);
  out.menu = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return { found: false };
    const r = m.getBoundingClientRect();
    const items = Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => { const b = e.getBoundingClientRect();
      const sr = e.querySelector('.sr-only');
      return { text: (e.innerText || '').split('\n')[0].trim(), box: `${Math.round(b.width)}x${Math.round(b.height)}`,
        disabled: e.getAttribute('aria-disabled') === 'true', cursor: getComputedStyle(e).cursor,
        srOnly: sr ? (sr.textContent || '').trim().slice(0, 40) : null }; });
    return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      aria: m.getAttribute('aria-label'), count: items.length, items };
  });
  log('右键菜单', JSON.stringify(out.menu, null, 1));
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);   // ⚠️ 只按一次（连按会连带取消选中）
  log('Esc 一次后 selected =', await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return n ? /(^|\s)selected(\s|$)/.test(n.className) : null; }, mine));

  // ============ 缺口 2：编辑态按 Esc 是提交还是撤销 ============
  // 双击节点主体进入编辑（双击**标题行**也会进编辑，所以点主体更稳）
  const body = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height * 0.62) }; }, mine);
  await p.mouse.dblclick(body.x, body.y); await p.waitForTimeout(1200);
  const ed = await p.evaluate(() => { const e = document.querySelector('.ProseMirror[contenteditable="true"]');
    return { found: !!e, focused: document.activeElement === e, innerHTML: e ? e.innerHTML : null }; });
  out.edit = { entered: ed };
  log('编辑态', JSON.stringify(ed));
  if (!ed.found) throw new Error('没进编辑态 ⇒ 后续读数作废(VOID)');
  // 打字前再断言焦点在编辑器里（keyGuard 的手工版）
  const MARK = '批次80Esc测试';
  const f0 = await p.evaluate(() => { const e = document.querySelector('.ProseMirror[contenteditable="true"]');
    const ok = document.activeElement === e || (e && e.contains(document.activeElement)); return { ok, active: document.activeElement.tagName + '.' + (document.activeElement.className || '').slice(0, 30) }; });
  log('打字前焦点断言', JSON.stringify(f0));
  if (!f0.ok) throw new Error('焦点不在编辑器 ⇒ 拒绝打字（防误触画布快捷键）');
  await p.keyboard.type(MARK); await p.waitForTimeout(600);
  out.edit.afterType = await p.evaluate(() => { const e = document.querySelector('.ProseMirror[contenteditable="true"]');
    return { innerHTML: e ? e.innerHTML : null, innerText: e ? (e.innerText || '').trim() : null }; });
  log('打字后', JSON.stringify(out.edit.afterType));
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  // ⚠️ 自伤修正：这一段第一版误写成 `p.evaluate((v) => {... MARK_LITERAL ...})` ——
  //    `MARK_LITERAL` 是 Node 侧变量，页面里不存在 ⇒ 每次读数都抛 ReferenceError。
  //    标记串必须**当参数传进去**（见下一段）。
  out.edit.afterEsc = await p.evaluate(([v, mark]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const e = document.querySelector('.ProseMirror[contenteditable="true"]');
    const ed = e ? e.closest('.react-flow__node') : null;
    return { editorStillOpen: !!e, editorBelongsTo: ed ? ed.getAttribute('data-id') : null,
      nodeInnerText: n ? (n.innerText || '').split('\n').filter(Boolean).slice(0, 4) : null,
      nodeHasMark: n ? ((n.innerText || '').includes(mark) || (n.innerHTML || '').includes(mark)) : null,
      status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected/) || ['?'])[0] };
  }, [mine, MARK]);
  log('Esc 之后', JSON.stringify(out.edit.afterEsc));

  // ============ 缺口 3：行内重命名的提交动作 ============
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  // 重新选中（点标题行最安全 —— 批次 77 的前置条件）
  const trow = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 15) }; }, mine);
  await p.mouse.click(trow.x, trow.y); await p.waitForTimeout(1000);
  out.rename = { selectedBefore: await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine) };
  const rb = await p.evaluate(() => { const el = document.querySelector('button[aria-label^="Rename"]'); if (!el) return null;
    const r = el.getBoundingClientRect(); return { aria: el.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  out.rename.button = rb; log('Rename 钮', JSON.stringify(rb));
  if (rb) {
    await p.mouse.click(rb.x, rb.y); await p.waitForTimeout(900);
    out.rename.afterClick = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
      const inp = n.querySelector('input'); const t = n.querySelector('[data-testid=flow-node-title]');
      return { inputFound: !!inp, inputValue: inp ? inp.value : null, focused: document.activeElement === inp,
        titleText: t ? (t.innerText || '').trim() : null, active: document.activeElement.tagName }; }, mine);
    log('点 Rename 后', JSON.stringify(out.rename.afterClick));
    if (out.rename.afterClick.inputFound) {
      await p.fill('input', '').catch(() => {});
      await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const i = n.querySelector('input');
        if (i) { i.focus(); } }, mine);
      await p.keyboard.press('Meta+A'); await p.waitForTimeout(200);
      await p.keyboard.type('改名测试80'); await p.waitForTimeout(400);
      out.rename.beforeEnter = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
        const i = n.querySelector('input'); return { value: i ? i.value : null }; }, mine);
      await p.keyboard.press('Enter'); await p.waitForTimeout(1400);
      out.rename.afterEnter = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
        const t = n.querySelector('[data-testid=flow-node-title]'); const i = n.querySelector('input');
        return { inputStillThere: !!i, titleText: t ? (t.innerText || '').trim() : null,
          aria: n.getAttribute('aria-label'), nodeInnerTextHead: (n.innerText || '').split('\n').filter(Boolean).slice(0, 2) }; }, mine);
      log('Enter 之后', JSON.stringify(out.rename.afterEnter));
    }
  }
  // ============ 顺带：工具条尺寸是否随画布缩放变化（延伸 78/79 的口径）============
  out.toolbarByZoom = [];
  for (const pct of [60, 100]) {
    await setZoom(pct);
    const zz = await settle();
    const r = await p.evaluate(() => { const el = document.querySelector('[data-testid="node-toolbar"]');
      if (!el) return null; const b = el.getBoundingClientRect();
      return { screen: `${Math.round(b.width)}x${Math.round(b.height)}`, n: el.querySelectorAll('button,[role="button"]').length }; });
    out.toolbarByZoom.push({ pct, scale: zz.scale, ...r });
    log('node-toolbar @', pct + '%', 'scale', zz.scale, JSON.stringify(r));
  }
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(450); }
  if (mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await status(), zoomLabel: await labelOf(), scale: zf.scale, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 80: [...new Set([...(led.per_batch?.['80'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b80.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
