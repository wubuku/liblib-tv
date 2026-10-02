// 批次 97 · d 轮：Part 2 重做（试听时序 + 多音色选用）。
//
// 🔴 **这轮的护栏是 b 轮事故换来的，写在最前面**：
//   b 轮「建节点」**其实失败了**（节点数 39→39 没变，适配态下左栏点不动），
//   而脚本靠「取最后一个音频节点」去猜「我建的是哪个」⇒ 猜到了**别人的节点**并删了它。
//   ⇒ 三条硬防护，**任一不满足就立即停止、绝不进入删除分支**：
//     ① 建前把**全画布 id 集合**存下来；
//     ② 建后取**差集**，且必须**恰好只有一个**新 id（别人同时建节点会让差集 >1 ⇒ 判失败）；
//     ③ 那个新 id 必须**同时**是 `.react-flow__node-audio.selected`
//        （建节点会自动选中，**别人的节点不会因为我的点击而变成选中**）。
//   ⇒ **`SELF` 只允许来自这个差集**，任何「取最后一个」「取 selected 的」写法都删掉了。
//
// 另外两处 b 轮的错误选择器：
//   `[aria-label^="Add "]` 匹配到 **39 个 `Add tags`**（每个节点上的标签按钮）——
//   音色按钮的 aria 是 `Add <音色名>`，必须**排除 `Add tags`**，且限定在音色库浮层内。
//   `Play ` 同理，要限定在 `[aria-label="全音色"]` 网格内。
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

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await setZoom(60);
out.beforeZoom = await zoomLabel();
log('归位后缩放：', out.beforeZoom);

// ---------- 护栏 ①：建前 id 集合 ----------
const idsBefore = new Set(await allIds());
out.idsBeforeCount = idsBefore.size;
log('建前 id 数：', idsBefore.size);

// 定位左栏「音频」入口（**60% 下**，b 轮在 23% 适配态下点不动）
out.rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '音频' && x.w > 0 && x.h > 0));
log('左栏音频入口：', JSON.stringify(out.rail));

if (!out.rail.length) { log('🔴 找不到左栏音频入口 ⇒ 停止（不建不删）'); }
else {
  const r0 = out.rail[0];
  // 悬停后再点（左栏默认可能是收起的图标态，悬停才展开为图标+文字）
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(700);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(3200);

  // ---------- 护栏 ②③：差集 + selected 双重确认 ----------
  const idsAfter = await allIds();
  const created = idsAfter.filter((id) => !idsBefore.has(id));
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected'))
    .map((e) => e.getAttribute('data-id')));
  out.guard = { idsBeforeCount: idsBefore.size, idsAfterCount: idsAfter.length, created, selIds,
    newSelected: selIds.filter((id) => !idsBefore.has(id)) };
  log('护栏读数：', JSON.stringify(out.guard));

  const SELF = created.length === 1 && out.guard.newSelected.length === 1
    && out.guard.newSelected[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('护栏判定 SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不进入后续，也不删除任何东西');

  if (SELF) {
    out.selfInfo = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), translate: n.style.transform,
        screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, SELF);
    log('自建节点：', JSON.stringify(out.selfInfo));

    // 面板读数：**音色按钮限定在 audio-generation-form 内**
    const panel = () => p.evaluate(() => {
      const form = document.querySelector('[data-testid="audio-generation-form"]');
      const inForm = (e) => !form || form.contains(e);
      const voiceBtns = Array.from(document.querySelectorAll('[aria-label^="音色:"]')).filter(inForm);
      const grid = document.querySelector('[aria-label="全音色"]');
      const gIn = (e) => grid ? grid.contains(e) : false;
      return {
        form: document.querySelectorAll('[data-testid="audio-generation-form"]').length,
        toolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
        voiceBtn: voiceBtns[0] ? voiceBtns[0].getAttribute('aria-label') : null,
        voiceExpanded: voiceBtns[0] ? voiceBtns[0].getAttribute('aria-expanded') : null,
        grid: document.querySelectorAll('[aria-label="全音色"]').length,
        // 🔑 排除 `Add tags`（那是节点标签按钮，b 轮踩过）
        playBtns: grid ? Array.from(grid.querySelectorAll('[aria-label^="Play "]')).map((e) => e.getAttribute('aria-label')) : [],
        addBtns: grid ? Array.from(grid.querySelectorAll('[aria-label^="Add "]')).map((e) => e.getAttribute('aria-label')) : [],
        addTagsTotal: document.querySelectorAll('[aria-label="Add tags"]').length,
        chips: Array.from(document.querySelectorAll('[data-testid="audio-generation-form"] span'))
          .map((s) => s.innerText.trim()).filter((t) => /^\d+(\.\d+)?s$/.test(t)),
        hint: form ? form.innerText.replace(/\s+/g, ' ').trim().slice(0, 100) : null };
    });

    out.panel0 = await panel();
    log('面板初态：', JSON.stringify(out.panel0));

    if (out.panel0.voiceBtn) {
      await p.click('[data-testid="audio-generation-form"] [aria-label^="音色:"]').catch(() => {});
      if (await p.evaluate(() => document.querySelectorAll('[aria-label="全音色"]').length) === 0)
        await p.evaluate(() => { const f = document.querySelector('[data-testid="audio-generation-form"]');
          const e = Array.from(f.querySelectorAll('[aria-label^="音色:"]'))[0]; if (e) e.click(); });
      await p.waitForTimeout(1800);
      out.panel1 = await panel();
      log('音色库打开后：', JSON.stringify({ grid: out.panel1.grid,
        play: out.panel1.playBtns.length, add: out.panel1.addBtns.length, addTags: out.panel1.addTagsTotal }));
    }

    // ---------- 🔑 试听完整时序 ----------
    out.play = {};
    if (out.panel1?.playBtns.length) {
      const full = out.panel1.playBtns[0];
      const name = full.replace(/^Play /, '');
      out.play.name = name;
      await p.evaluate((n) => { const e = document.querySelector(`[aria-label="全音色"] [aria-label="Play ${n}"]`);
        if (e) e.click(); }, name);
      out.play.timeline = [{ t: 0, aria: 'Play' }];
      const T0 = Date.now();
      let last = 'Play';
      for (let k = 1; k <= 120; k++) {
        await p.waitForTimeout(200);
        const a = await p.evaluate((n) => {
          if (document.querySelector(`[aria-label="全音色"] [aria-label="Pause ${n}"]`)) return 'Pause';
          if (document.querySelector(`[aria-label="全音色"] [aria-label="Play ${n}"]`)) return 'Play';
          return 'grid-closed'; }, name);
        const t = Date.now() - T0;
        if (a !== last) { out.play.timeline.push({ t, aria: a }); log(`   试听 t=${t}ms → ${a}`); last = a; }
        if (a === 'Play' && k > 3) break;
        if (a === 'grid-closed') break;
      }
      out.play.credits = await credits();
      log('试听结束积分：', out.play.credits, '｜翻转序列：', JSON.stringify(out.play.timeline));
    }

    // ---------- 🔑 同时选用多个音色 ----------
    out.multi = { steps: [] };
    if (out.panel1?.addBtns.length >= 2) {
      const picks = out.panel1.addBtns.slice(0, 2);
      out.multi.picks = picks;
      for (const a of picks) {
        const nm = a.replace(/^Add /, '');
        const ok = await p.evaluate((n) => { const e = document.querySelector(`[aria-label="全音色"] [aria-label="Add ${n}"]`);
          if (!e) return false; e.click(); return true; }, nm);
        await p.waitForTimeout(1700);
        const st = await panel();
        out.multi.steps.push({ name: nm, clicked: ok, chips: st.chips, hint: st.hint, addLeft: st.addBtns.length });
        log(`   选用「${nm}」→ chips=${JSON.stringify(st.chips)}｜说明首 90 字：${JSON.stringify((st.hint || '').slice(0, 90))}`);
      }
      out.multi.credits = await credits();
      log('两次选用后积分：', out.multi.credits);
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
          if (e && e.closest('.react-flow__node') === n && !e.closest(INTERACTIVE)) return { x, y };
        }
        return null; }, SELF);
      if (!pt) { await setZoom(60); await p.keyboard.press('Meta+0'); await p.waitForTimeout(1900); continue; }
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200);
      const isSel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        return n ? n.classList.contains('selected') : false; }, SELF);
      if (!isSel) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }
      await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
      await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
      await p.waitForTimeout(1500);
      const open = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-context-menu"]'));
      if (!open) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); continue; }
      // 🔑 删除前**再确认一次菜单所属**：只允许删 SELF
      const clicked = await p.evaluate((i) => {
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        if (!n || !n.classList.contains('selected')) return 'target-not-selected';
        const m = document.querySelector('[data-testid="canvas-context-menu"]');
        if (!m) return 'no-menu';
        const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
          .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
        if (!it) return 'no-item'; it.click(); return 'clicked'; }, SELF);
      await p.waitForTimeout(1900);
      const still = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
      out.cleanup.attempts.push({ attempt, open, clicked, still });
      log(`  删除尝试 ${attempt}：菜单=${open} 结果=${clicked} SELF仍在=${still}`);
      if (!still) break;
    }
    out.selfLeft = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
    // 🔑 核对：**没有误删别的节点**（建后 id 集合 vs 现在）
    const idsNow = await allIds();
    out.missing = idsAfter.filter((id) => !idsNow.includes(id));
    log('自建残留：', out.selfLeft, '｜本轮消失的 id：', JSON.stringify(out.missing),
      '（应当恰好只有 SELF：' + SELF + '）');
  }
}

// 收尾
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b97d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
