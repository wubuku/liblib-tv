// 批次 97 · b 轮：两件事，一件只读、一件要自建节点。
//
// Part 1（**只读**，用画布上别人的音频节点）：
//   🔑 **手柄能不能拖**。a 轮清点出音频节点 `flow-node-source-handle` **31/31 都有**
//      （时间线是 0/2）⇒ 结构上有。但批次 91 钉过：**元素本体 `pe` 恒 `none`，
//      真热区在 `::before`（40×80）**。所以「有手柄」≠「能拖」，必须测 `::before` 的 `pe`。
//   🔑 **空音频节点那条 aria 的三态变化**。a 轮读到逐字
//      `暂无音频. No resources: 0 ready, 0 processing, 0 failed. Not selected.`
//      —— 结尾那个 `Not selected.` 显然**会随选中态变**，这正是本页缺失的状态契约。
//
// Part 2（**自建一个音频节点**，测完按 id 删净）：
//   🔑 **样音播放的完整时序**。本页「仍未验证」明写：只测到 0.9s 仍为 `Play`、3.4s 已为 `Pause`，
//      **没有测到它什么时候停**。本轮密集采样 `Play`↔`Pause` 翻转，找到播放时长。
//   🔑 **同时选用多个音色**。本页「仍未验证」第二条。
//   ⚠️ **只在自建节点上做** —— 点 `Add` 会改节点的说明文案，绝不能碰别人建的那 31 个。
//   ⚠️ 不点「生成」（扣费边界）。点 `Play`/`Add` 批次 32 已证不扣积分，仍每步回读积分。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
let SELF = null;

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

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { zoom: await zoomLabel(), scale: await scaleNow() };
log('适配：', JSON.stringify(out.fit));

// ================= Part 1（只读） =================
const findExcl = (cls) => p.evaluate((c) => {
  const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
  const rows = [];
  for (const n of document.querySelectorAll(c)) {
    const r = n.getBoundingClientRect();
    if (r.width < 16 || r.height < 16) continue;
    if (r.right < 60 || r.bottom < 60 || r.left > 1180 || r.top > 640) continue;
    let self = 0, tot = 0, goodPt = null;
    for (let i = 1; i <= 3; i++) for (let j = 1; j <= 3; j++) {
      const x = Math.round(r.x + (r.width * i) / 4), y = Math.round(r.y + (r.height * j) / 4);
      if (x < 1 || y < 1 || x > 1279 || y > 719) continue;
      tot++;
      const e = document.elementFromPoint(x, y);
      const o = e && e.closest('.react-flow__node');
      if (o && o.getAttribute('data-id') === n.getAttribute('data-id')) { self++; if (!e.closest(INTERACTIVE) && !goodPt) goodPt = { x, y }; }
    }
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      w: Math.round(r.width), h: Math.round(r.height), self, tot, goodPt });
  }
  return rows.filter((r) => r.self === r.tot && r.tot >= 9 && r.goodPt).sort((x, y) => y.w * y.h - x.w * x.h);
}, cls);

out.cands = await findExcl('.react-flow__node-audio');
const TID = out.cands[0]?.id;
out.pick = out.cands[0] || null;
log('独占音频节点：', TID, JSON.stringify(out.pick));

if (TID) {
  // P1-a：手柄本体与 ::before 的 pe / 几何（**批次 91 的判据**）
  out.handles = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const one = (sel) => { const e = n.querySelector(sel); if (!e) return null;
      const cs = getComputedStyle(e), bs = getComputedStyle(e, '::before'), as = getComputedStyle(e, '::after');
      const r = e.getBoundingClientRect();
      const br = (st, tag) => ({ pe: st.pointerEvents, op: st.opacity, w: st.width, h: st.height, content: st.content });
      return { cls: e.className, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        self: { pe: cs.pointerEvents, op: cs.opacity }, before: br(bs, 'before'), after: br(as, 'after') }; };
    return { src: one('.flow-node-source-handle,[data-testid="flow-node-source-handle"]'),
      tgt: one('.flow-node-target-handle,[data-testid="flow-node-target-handle"]') };
  }, TID);
  log('P1 手柄：');
  log('   source：', JSON.stringify(out.handles.src));
  log('   target：', JSON.stringify(out.handles.tgt));

  // P1-b：空音频节点那条 aria 的三态逐字
  const ariaOf = () => p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const list = Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label'));
    return { empty: list.find((a) => /No resources/.test(a)) || null, all: list,
      form: document.querySelectorAll('[data-testid="audio-generation-form"]').length,
      toolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length };
  }, TID);
  out.emptyStates = [];
  out.emptyStates.push({ state: '未选中', ...(await ariaOf()) });
  await p.mouse.click(out.pick.goodPt.x, out.pick.goodPt.y); await p.waitForTimeout(1400);
  out.emptyStates.push({ state: '选中', ...(await ariaOf()) });
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  log('P1 空节点 aria 三态：');
  out.emptyStates.forEach((s) => log(`   ${s.state}：${JSON.stringify(s.empty)}（form=${s.form} toolbar=${s.toolbar}）`));

  // P1-c：对照 —— 同一个判据在**时间线**节点上（结构上没有 source 手柄）
  out.tlHandles = await p.evaluate(() => {
    const n = document.querySelector('.react-flow__node-timeline');
    if (!n) return null;
    return { aria: n.getAttribute('aria-label'),
      src: n.querySelectorAll('.flow-node-source-handle,[data-testid="flow-node-source-handle"]').length,
      tgt: n.querySelectorAll('.flow-node-target-handle,[data-testid="flow-node-target-handle"]').length };
  });
  log('P1 时间线对照：', JSON.stringify(out.tlHandles));
}

// ================= Part 2（自建节点） =================
log('--- Part 2：自建一个音频节点 ---');
out.before2 = { nodes: await nodeN(), credits: await credits() };
// 左栏「音频」入口
out.railAudio = await p.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('button,[role="button"]'));
  const hit = btns.filter((e) => (e.getAttribute('aria-label') || '').match(/^音频$/) || (e.getAttribute('data-testid') || '').match(/audio/i));
  return hit.map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
      text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 10),
      screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
});
log('左栏音频入口候选：', JSON.stringify(out.railAudio));
const railBtn = out.railAudio.find((x) => x.screen && !x.screen.startsWith('0×0'));
if (!railBtn) log('⚠️ 找不到左栏音频入口 ⇒ Part 2 记 VOID');
else {
  const [gx, gy] = railBtn.screen.split('@')[1].split(',').map(Number);
  await p.mouse.click(gx, gy);
  await p.waitForTimeout(2600);
  out.after2 = { nodes: await nodeN(), credits: await credits() };
  log('建完：', JSON.stringify(out.after2), '（建前', JSON.stringify(out.before2), '）');

  // 找到新建的那个音频节点（sel===1 的那个）
  SELF = await p.evaluate(() => {
    const s = document.querySelector('.react-flow__node-audio.selected');
    if (s) return s.getAttribute('data-id');
    const a = Array.from(document.querySelectorAll('.react-flow__node-audio'));
    return a.length ? a[a.length - 1].getAttribute('data-id') : null; });
  out.selfId = SELF;
  log('自建节点 id：', SELF);

  if (SELF) {
    const panel = () => p.evaluate(() => ({
      form: document.querySelectorAll('[data-testid="audio-generation-form"]').length,
      toolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
      voiceBtn: (() => { const e = Array.from(document.querySelectorAll('[aria-label]'))
          .find((x) => (x.getAttribute('aria-label') || '').startsWith('音色:')); return e ? e.getAttribute('aria-label') : null; })(),
      voiceExpanded: (() => { const e = Array.from(document.querySelectorAll('[aria-label]'))
          .find((x) => (x.getAttribute('aria-label') || '').startsWith('音色:')); return e ? e.getAttribute('aria-expanded') : null; })(),
      grid: document.querySelectorAll('[aria-label="全音色"]').length,
      hint: (() => { const e = document.querySelector('[data-testid="audio-generation-form"]');
        if (!e) return null; const t = e.innerText.replace(/\s+/g, ' ').trim(); return t.slice(0, 90); })(),
      chips: Array.from(document.querySelectorAll('[data-testid="audio-generation-form"] span'))
        .map((s) => s.innerText.trim()).filter((t) => /^\d+s$/.test(t)).slice(0, 6),
      playBtns: document.querySelectorAll('[aria-label^="Play "]').length,
      addBtns: document.querySelectorAll('[aria-label^="Add "]').length }));

    out.panel0 = await panel();
    log('面板初态：', JSON.stringify(out.panel0));

    // 打开音色库
    if (out.panel0.voiceBtn) {
      await p.click(`[aria-label^="音色:"]`); await p.waitForTimeout(1600);
      out.panel1 = await panel();
      log('音色库打开后：', JSON.stringify(out.panel1));
    }

    // 🔑 试听完整时序：点第一个 Play，密集采样 aria
    const playName = await p.evaluate(() => { const e = document.querySelector('[aria-label^="Play "]');
      return e ? e.getAttribute('aria-label') : null; });
    out.playName = playName;
    log('试听按钮：', playName);
    if (playName) {
      const name = playName.replace(/^Play /, '');
      await p.click(`[aria-label="Play ${name}"]`);
      out.timeline = [{ t: 0, aria: 'Play（刚点下）' }];
      const T0 = Date.now();
      let last = null;
      for (let k = 1; k <= 90; k++) {
        await p.waitForTimeout(200);
        const a = await p.evaluate((nm) => {
          const play = document.querySelector(`[aria-label="Play ${nm}"]`);
          const pause = document.querySelector(`[aria-label="Pause ${nm}"]`);
          return pause ? 'Pause' : play ? 'Play' : 'none';
        }, name);
        const t = Date.now() - T0;
        if (a !== last) { out.timeline.push({ t, aria: a }); log(`   t=${t}ms → ${a}`); last = a; }
        if (a === 'Play' && k > 3) break;      // 翻回来了 ⇒ 播完
        if (a === 'none') break;
      }
      out.creditsAfterPlay = await credits();
      log('试听结束积分：', out.creditsAfterPlay, '｜翻转序列：', JSON.stringify(out.timeline));
    }

    // 🔑 同时选用多个音色：点两个不同的 Add
    out.adds = [];
    const addNames = await p.evaluate(() => Array.from(document.querySelectorAll('[aria-label^="Add "]'))
      .slice(0, 2).map((e) => e.getAttribute('aria-label')));
    out.addNames = addNames;
    log('准备选用的两个音色：', JSON.stringify(addNames));
    for (const a of addNames) {
      const nm = a.replace(/^Add /, '');
      const ok = await p.evaluate((n) => { const e = document.querySelector(`[aria-label="Add ${n}"]`);
        if (!e) return false; e.click(); return true; }, nm);
      await p.waitForTimeout(1500);
      out.adds.push({ name: nm, clicked: ok, ...(await panel()) });
      log(`   选用「${nm}」后：`, JSON.stringify(out.adds[out.adds.length - 1]));
    }
    out.creditsAfterAdd = await credits();
    log('选用后积分：', out.creditsAfterAdd);
  }
}

// ================= 收尾：删自建节点 + 三项归位 =================
out.cleanup = {};
if (SELF && (await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF))) {
  // 先 Esc 到底，再点中（独占落点 + 排除交互元素，批次 96 的判据）
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
      return null;
    }, SELF);
    if (!pt) { await p.keyboard.press('Meta+0'); await p.waitForTimeout(1800); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200);
    const isSel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      return n ? n.classList.contains('selected') : false; }, SELF);
    if (!isSel) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
    await p.waitForTimeout(1500);
    const open = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-context-menu"]'));
    if (!open) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); continue; }
    const clicked = await p.evaluate(() => {
      const m = document.querySelector('[data-testid="canvas-context-menu"]');
      const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
        .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
      if (!it) return false; it.click(); return true; });
    await p.waitForTimeout(1900);
    const still = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
    log(`  删除尝试 ${attempt}：菜单=${open} 点击=${clicked} 仍在=${still}`);
    out.cleanup[attempt] = { open, clicked, still };
    if (!still) break;
  }
}
out.selfLeft = SELF ? await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF) : null;
log('自建节点残留：', out.selfLeft);

for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = {};
for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel();
  if (zl && /, 60%$/.test(zl)) { out.restore = { ok: true, tries: k - 1 }; break; }
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  if (k === 4) out.restore = { ok: false, tries: 4 };
}
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', JSON.stringify(out.restore), out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b97b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
