// 批次 113 · b3 轮：**只补臂 2**（音色库样音）。
//
// 为什么又要拆一轮：b2 轮臂 2 挂在找按钮上，而按钮的真实 aria 是
//   **`音色: 音色库`**（逐字，前面还有「音色: 」三字），不是 `音色库`。
//   —— 这已经是本轮第三次「判据猜错宿主」了（前两次：`testid: null` 的反查、
//   `tid` 正则传不进 evaluate）。所以脚本里不再手写 aria，而是**先扫一遍
//   面板上所有按钮的 aria 逐字**，再从**读到的清单**里挑。
//
// 臂 1（阳性对照）已在 b2 轮成立，这里不再重跑，只把它的读数一并记进 out 对照表。
//   臂 1：4 秒 wav 播完，t=62ms 就从 `Play` 翻成 `Pause`，t=+5092ms 自动翻回 `Play`。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b3',
  // b2 轮臂 1 的阳性对照读数（本轮直接引用，不重跑）
  arm1FromB2: { flips: 18, mo: 294, secs: 14, flipAtMs: 62, autoStopAtMs: 5092,
    tids: ['audio-simple-player-active'], aria: 'Pause jimeng-b104-test', audio: 'audio-playback-media',
    nodeTids: ['flow-node-media-stroke','flow-node-target-handle','flow-node-title','flow-node-selected-tag','flow-node-source-handle','flow-node-source-connection-menu-button','audio-node-result','audio-result-gallery','audio-simple-player','audio-timeline-visual','audio-playback-waveform','audio-waveform-base','audio-waveform-progress','audio-waveform-playhead','audio-waveform-playhead-line','audio-waveform-playhead-cap','audio-duration','audio-duration-accessible'],
    durs: [{ tid: 'audio-duration', txt: '00:00:04 00 : 00 : 04', rect: [587,440,62,15] },
           { tid: 'audio-duration-accessible', txt: '00:00:04', rect: [587,439,1,1] }] } };
const save = () => writeFileSync(new URL('./_tmp-b113b3.json', import.meta.url), JSON.stringify(out, null, 1));

const SELF = 'node_cp2dh7fn7d';
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

const snap = (lbl) => p.evaluate((l) => {
  const r = { at: Date.now(), lbl: l };
  r.tids = Array.from(new Set(Array.from(document.querySelectorAll('[data-testid^="audio-simple-player"]')).map((e) => e.getAttribute('data-testid'))));
  r.pp = Array.from(new Set(Array.from(document.querySelectorAll('[aria-label]'))
    .map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), inNode: !!e.closest('.react-flow__node') }))
    .filter((x) => /^(Play|Pause)\b/.test(x.a || ''))
    .map((x) => `${x.a}#${x.t || '-'}${x.inNode ? '@node' : ''}`)));
  r.audios = Array.from(document.querySelectorAll('audio')).map((a) => ({ paused: a.paused, t: a.getAttribute('data-testid'), ct: +(a.currentTime || 0).toFixed(2), dur: +(a.duration || 0).toFixed(2), srcTail: (a.currentSrc || a.src || '').slice(-30) }));
  return r;
}, lbl);
const installMo = (tag) => p.evaluate((tg) => {
  window.__b3 = { tag: tg, t0: Date.now(), ev: [] };
  const hit = (s) => /play|pause|audio|生动|解说|试听/i.test(String(s));
  const desc = (n) => { if (!n) return null; if (n.nodeType === 3) return (n.nodeValue || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    if (n.nodeType !== 1) return `#${n.nodeName}`;
    const t = n.getAttribute && n.getAttribute('data-testid'), a = n.getAttribute && n.getAttribute('aria-label');
    return `${n.tagName}${t ? '#' + t : ''}${a ? '[' + a.replace(/\s+/g, ' ').trim().slice(0, 30) + ']' : ''}`; };
  const mo = new MutationObserver((list) => { for (const rec of list) { const e = { t: Date.now() - window.__b3.t0, type: rec.type };
    if (rec.type === 'childList') { const ad = Array.from(rec.addedNodes).map(desc).filter((x) => x && hit(x));
      const r2 = Array.from(rec.removedNodes).map(desc).filter((x) => x && hit(x));
      if (ad.length || r2.length) e.ch = { added: ad.slice(0, 4), removed: r2.slice(0, 4) }; }
    else if (rec.type === 'attributes') { e.attr = rec.attributeName; e.on = desc(rec.target);
      if (rec.attributeName === 'aria-label' || rec.attributeName === 'data-testid') e.new = String(rec.target.getAttribute(rec.attributeName) || '').replace(/\s+/g, ' ').trim().slice(0, 50); }
    else if (rec.type === 'characterData') e.txt = desc(rec.target);
    if (e.ch || e.attr || e.txt) window.__b3.ev.push(e); } });
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true });
  window.__b3.mo = mo; return { tag: tg };
}, tag);
const readMo = (tag) => p.evaluate((tg) => (window.__b3 && window.__b3.tag === tg ? { n: window.__b3.ev.length, ev: window.__b3.ev } : { n: -1, ev: [] }), tag);

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');

// ---- 1. 扫面板上所有按钮的 aria 逐字（不再手写猜） ----
out.selfState = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  return { selected: n.classList.contains('selected') }; }, SELF);
log('SELF 选中？', JSON.stringify(out.selfState));
out.panelButtons = await p.evaluate(() => { const tb = document.querySelector('[data-testid="node-toolbar"]'); if (!tb) return null;
  return Array.from(tb.querySelectorAll('button,[role=button]')).map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'), exp: e.getAttribute('aria-expanded'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }).filter((x) => x.aria); });
log('\n面板按钮 aria 逐字：'); (out.panelButtons || []).forEach((x) => log('   ' + JSON.stringify(x)));
save();

// ---- 2. 从读到的清单里挑「音色」那个 ----
const voice = (out.panelButtons || []).find((x) => /音色/.test(x.aria || ''));
out.voiceBtn = voice;
log('\n挑中的音色按钮：', JSON.stringify(voice));
if (!voice) { log('🔴 面板里没有音色按钮 ⇒ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(voice.rect[0] + voice.rect[2] / 2, voice.rect[1] + voice.rect[3] / 2);
await p.waitForTimeout(2200);
out.libExpanded = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label*="音色"]')) {
  if (e.getAttribute('aria-expanded') !== null) return { aria: e.getAttribute('aria-label'), exp: e.getAttribute('aria-expanded') }; } return null; });
log('展开后：', JSON.stringify(out.libExpanded));
out.libOpen = await p.evaluate(() => { const e = document.querySelector('[aria-label="全音色"]'); if (!e) return { present: false };
  const r = e.getBoundingClientRect(); return { present: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
log('音色库面板：', JSON.stringify(out.libOpen));
out.voiceNames = await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[aria-label^="Add "]')).map((e) => (e.getAttribute('aria-label') || '').slice(4)))));
log('音色名：', JSON.stringify(out.voiceNames));
save();

// ---- 3. 扫页面上所有 `Play <名>` 按钮（画布上的 + 音色库里的），区分作用域 ----
out.allPlay = await p.evaluate(() => Array.from(document.querySelectorAll('[aria-label]')).map((e) => {
  const a = e.getAttribute('aria-label') || ''; if (!/^Play\s+\S/.test(a)) return null;
  const r = e.getBoundingClientRect(); if (r.width < 1) return null;
  return { aria: a, tid: e.getAttribute('data-testid'), inNode: !!e.closest('.react-flow__node'),
    inLib: !!e.closest('[aria-label="全音色"]'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}).filter(Boolean));
log('\n页面上所有 `Play <名>`：'); out.allPlay.forEach((x) => log('   ' + JSON.stringify(x)));
save();

// ---- 4. 挑音色库里那个（inLib / 不在节点里），现算落点 ----
const target = await p.evaluate((cands) => {
  for (const t of cands) { if (t.inNode) continue;
    const el = document.querySelector(`[aria-label="${t.aria.replace(/"/g, '\\"')}"]`); if (!el) continue;
    const r = el.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    if (cx < 4 || cy < 4 || cy > innerHeight - 4 || cx > innerWidth - 4) continue;
    const h = document.elementFromPoint(cx, cy); if (!h || !(h === el || el.contains(h))) continue;
    return { ok: true, aria: t.aria, tid: t.tid, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], hit: h.tagName };
  }
  return { __err: 'no-clickable' };
}, out.allPlay);
out.target = target;
log('\n靶子落点：', JSON.stringify(target));
if (target.__err) { log('🔴 拿不到可点落点 ⇒ 中止'); await b.close(); process.exit(3); }

// ---- 5. 点 + 连采 30s（批次 97 记的就是 30s） ----
out.before = await snap('before');
out.moInstall = await installMo('arm2');
const t0 = Date.now();
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);
log('已点样音 Play，连采 30s…');
const s = []; const s0 = Date.now();
while (Date.now() - s0 < 30000) { s.push(await snap('w')); await p.waitForTimeout(250); }
out.elapsed = Date.now() - t0;
out.samples = s;
out.mo = await readMo('arm2');

const seq = []; for (const x of s) { const k = x.tids.join('|') + '::' + x.pp.join('|') + '::' + JSON.stringify(x.audios.map((a) => [a.paused, a.ct]));
  if (!seq.length || seq[seq.length - 1].k !== k) seq.push({ k, t: x.at, i: s.indexOf(x) }); }
out.seq = seq.map((x) => ({ t: x.t, i: x.i, tids: x.k.split('::')[0], pp: x.k.split('::')[1], au: x.k.split('::')[2] }));
log('\n=== 臂 2 取值序列（折叠后）===');
out.seq.forEach((x) => log(`   t=${x.t} (#${x.i}) tids=${x.tids} pp=${x.pp} au=${x.au}`));
log('observer 记到', out.mo.n, '条');
out.mo.ev.slice(0, 30).forEach((e) => log('   ' + JSON.stringify(e)));

// 采样期间的 aria 全景：把出现过的所有 Play/Pause 逐字列一遍（防止折叠把细节吃掉）
out.seenAria = Array.from(new Set(s.flatMap((x) => x.pp)));
log('\n采样期间出现过的所有 Play/Pause 逐字：', JSON.stringify(out.seenAria));
out.seenAudio = s.filter((x) => x.audios.length).map((x) => ({ t: x.t, a: x.audios }));
log('采样期间页面上出现过的 <audio>：', JSON.stringify(out.seenAudio.slice(0, 10)));
out.nAudioSamples = out.seenAudio.length;

out.compare = { arm1_flips: 18, arm1_mo: 294, arm1_secs: 14, arm2_flips: out.seq.length - 1, arm2_mo: out.mo.n, arm2_secs: Math.round(out.elapsed / 1000) };
log('\n=== 两臂对照 ===', JSON.stringify(out.compare));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE b3');
process.exit(0);
