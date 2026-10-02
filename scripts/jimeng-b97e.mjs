// 批次 97 · e 轮：两件事，都要建节点，护栏照旧（b 轮事故换来的）。
//
// ① 🔑 **试听时序必须用 MutationObserver，不能用轮询**。
//    d 轮按 200ms 轮询 120 次（24 秒），`Play`→`Pause` **一次都没翻到**，
//    而批次 32 实测「0.9s 仍为 Play、3.4s 已为 Pause」—— **两条读数互相矛盾**。
//    最可能的原因不是「没播」，而是**翻转变换快于轮询间隔**（或者点击没触发，两种都得分清）。
//    ⇒ 判据换成：在页面里挂 `MutationObserver` 监听 `aria-label` 属性变化，
//       **逐条记下时间戳**。这样**再快的翻转也漏不掉**，且能区分
//       「从来没播」（零条记录）与「播了但极快」（有记录）。
//
// ② ⚠️ **自建节点的 canvas 尺寸不稳定**：d 轮自建的「音频 33」在 60% 下量到屏上
//    `184×184` ⇒ canvas **306.67**，而画布上另外 31 个音频节点恒 `320×320`。
//    本轮建完立刻 / 2s / 5s / 10s 各量一次，看它是**会稳定下来**还是**真的更小**。
//    （这关系到批次 79 那条「canvas 恒 320×320」要不要加限定词。）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await setZoom(60);
log('缩放：', await zoomLabel(), 'scale =', await scaleNow());

// ---------- 护栏：建前 id 集合 ----------
const idsBefore = new Set(await allIds());
log('建前 id 数：', idsBefore.size);

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '音频' && x.w > 0 && x.h > 0));
log('左栏音频入口：', JSON.stringify(rail));

if (!rail.length) { log('🔴 找不到入口 ⇒ 停止（不建不删）'); }
else {
  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(700);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(2600);

  const idsAfter = await allIds();
  const created = idsAfter.filter((id) => !idsBefore.has(id));
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const newSel = selIds.filter((id) => !idsBefore.has(id));
  out.guard = { before: idsBefore.size, after: idsAfter.length, created, selIds, newSel };
  log('护栏：', JSON.stringify(out.guard));
  const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不删任何东西');
  if (!SELF) { log('停止。'); }
  else {
    // ---------- ② 尺寸稳定性：立刻 / 2s / 5s / 10s ----------
    out.sizeSeries = [];
    for (const wait of [0, 2000, 3000, 5000]) {
      if (wait) await p.waitForTimeout(wait);
      const m = await p.evaluate((c) => {
        const n = document.querySelector(`.react-flow__node[data-id="${c.id}"]`);
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { screen: `${Math.round(r.width * 100) / 100}×${Math.round(r.height * 100) / 100}`,
          translate: n.style.transform, scale: (() => { const e = document.querySelector('.react-flow__viewport');
            const mm = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return mm ? Number(mm[1]) : null; })() }; }, { id: SELF });
      if (m) { m.canvasW = m.scale ? Math.round((parseFloat(m.screen.split('×')[0]) / m.scale) * 100) / 100 : null;
        out.sizeSeries.push(m);
        log(`   尺寸 +${wait}ms：屏上 ${m.screen}｜canvas 宽 ${m.canvasW}｜scale ${m.scale}`); }
    }
    // 对照：一个已有的音频节点同时刻读数
    out.controlSize = await p.evaluate(() => {
      const n = document.querySelector('.react-flow__node-audio');
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const e = document.querySelector('.react-flow__viewport');
      const mm = e && /scale\(([\d.]+)\)/.exec(e.style.transform || '');
      const s = mm ? Number(mm[1]) : null;
      return { aria: n.getAttribute('aria-label'), screen: `${Math.round(r.width)}×${Math.round(r.height)}`,
        canvas: s ? Math.round((r.width / s) * 100) / 100 : null, scale: s }; });
    log('对照（已有音频节点）：', JSON.stringify(out.controlSize));

    // ---------- ① 试听：MutationObserver 记时序 ----------
    const opened = await p.evaluate(() => {
      const f = document.querySelector('[data-testid="audio-generation-form"]');
      if (!f) return false;
      const e = Array.from(f.querySelectorAll('[aria-label^="音色:"]'))[0];
      if (!e) return false; e.click(); return true; });
    await p.waitForTimeout(1800);
    out.gridOpen = await p.evaluate(() => document.querySelectorAll('[aria-label="全音色"]').length);
    log('音色库：', out.gridOpen, '（点开=', opened, '）');

    const target = await p.evaluate(() => { const g = document.querySelector('[aria-label="全音色"]');
      if (!g) return null; const e = g.querySelector('[aria-label^="Play "]'); return e ? e.getAttribute('aria-label') : null; });
    out.playTarget = target;
    log('试听目标：', target);

    if (target) {
      const name = target.replace(/^Play /, '');
      // 挂 observer
      await p.evaluate((n) => {
        window.__obs = []; window.__t0 = performance.now();
        const obs = new MutationObserver((muts) => {
          for (const m of muts) {
            const el = m.target;
            if (el.tagName === 'BUTTON' && /^Play |^Pause /.test(el.getAttribute('aria-label') || '')) {
              window.__obs.push({ t: Math.round(performance.now() - window.__t0), aria: el.getAttribute('aria-label') });
            }
          }
        });
        obs.observe(document.body, { subtree: true, attributes: true, attributeFilter: ['aria-label'] });
        window.__obsOn = true;
      }, name);
      await p.waitForTimeout(300);
      const clicked = await p.evaluate((n) => { const e = document.querySelector(`[aria-label="全音色"] [aria-label="Play ${n}"]`);
        if (!e) return false; e.click(); return true; }, name);
      out.playClicked = clicked;
      log('点试听：', clicked);
      // 采样 30 秒：既用 observer 记录，也用高频轮询做交叉核对
      const t0 = Date.now();
      out.poll = [];
      for (let k = 1; k <= 150; k++) {
        await p.waitForTimeout(200);
        const a = await p.evaluate((n) => {
          if (document.querySelector(`[aria-label="全音色"] [aria-label="Pause ${n}"]`)) return 'Pause';
          if (document.querySelector(`[aria-label="全音色"] [aria-label="Play ${n}"]`)) return 'Play';
          return 'none'; }, name);
        if (!out.poll.length || out.poll[out.poll.length - 1].aria !== a) {
          out.poll.push({ t: Date.now() - t0, aria: a }); log(`   轮询 t=${Date.now() - t0}ms → ${a}`); }
        if (a === 'Play' && k > 2) break;
      }
      out.observed = await p.evaluate(() => { if (window.__obsOn) { window.__obsOn = false; } return window.__obs || []; });
      out.creditsAfterPlay = await credits();
      log('MutationObserver 记到 ' + out.observed.length + ' 条：', JSON.stringify(out.observed));
      log('试听后积分：', out.creditsAfterPlay);
      // 关掉音色库
      await p.evaluate(() => { const f = document.querySelector('[data-testid="audio-generation-form"]');
        const e = Array.from(f.querySelectorAll('[aria-label^="音色:"]'))[0]; if (e) e.click(); });
      await p.waitForTimeout(900);
    }

    // ---------- 收尾：只删 SELF ----------
    out.cleanup = { target: SELF, attempts: [] };
    for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
    for (let attempt = 1; attempt <= 3; attempt++) {
      const pt = await p.evaluate((i) => {
        const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (let a = 1; a <= 3; a++) for (let c = 1; c <= 3; c++) {
          const x = Math.round(r.x + (r.width * a) / 4), y = Math.round(r.y + (r.height * c) / 4);
          if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
          const e = document.elementFromPoint(x, y);
          if (e && e.closest('.react-flow__node') === n && !e.closest(INTERACTIVE)) return { x, y }; }
        return null; }, SELF);
      if (!pt) { await setZoom(60); await p.keyboard.press('Meta+0'); await p.waitForTimeout(1900); continue; }
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200);
      const isSel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        return n ? n.classList.contains('selected') : false; }, SELF);
      if (!isSel) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }
      await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
      await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
      await p.waitForTimeout(1500);
      const res = await p.evaluate((i) => {
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        if (!n || !n.classList.contains('selected')) return 'target-not-selected';
        const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return 'no-menu';
        const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
          .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
        if (!it) return 'no-item'; it.click(); return 'clicked'; }, SELF);
      await p.waitForTimeout(1900);
      const still = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
      out.cleanup.attempts.push({ attempt, res, still });
      log(`  删除尝试 ${attempt}：${res}｜SELF仍在=${still}`);
      if (!still) break;
    }
    const idsNow = await allIds();
    out.selfLeft = idsNow.includes(SELF);
    out.missing = idsAfter.filter((id) => !idsNow.includes(id));
    log('自建残留：', out.selfLeft, '｜本轮消失的 id：', JSON.stringify(out.missing));
  }
}

for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b97e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
