// 批次 113 · b 轮：结清「音色库样音的确切时长」这条老账。
//
// 老账原文（`audio-node-voice.md:224-232`）：
//   批次 32 记的是「0.9s 仍为 `Play`、3.4s 已为 `Pause`」。
//   批次 97 用 MutationObserver 监听所有 `aria-label` 变化（逐条记时间戳），连采 30 秒，
//   **结果：observer 记到 0 条**，轮询也只读到起手那一次 `Play`，30 秒一直是 `Play`。
//   ⇒ 两条读数互相矛盾，批次 97 记 VOID。
//
// 🔴 批次 97 那个判据有个**结构性漏洞**（这轮要正面戳破）：
//   它只 `observe(attributes: aria-label)`。如果「Play 按钮」和「Pause 按钮」
//   **是两个不同的元素**（React 条件渲染换了整个子树），那么**属性一次都不会变** ——
//   observer 记到 0 条**完全符合预期**，它压根没在看「元素被换掉」这条路。
//   ⇒ 批次 97 的「0 条」是**判据的盲区**，不是产品行为的读数。
//
// 🔴 本轮的做法（两条臂，只差「音频来源」这一个变量）：
//   臂 1（**阳性对照**）：自建节点的**带媒体**音频 → 点 `Play` ⇒ 批次 104 独立观测过会翻转
//   臂 2（**靶子**）：音色库**样音** `Play 生动解说` ⇒ 批次 97 记 30s 不翻转
//   同轮、同判据、同会话、只差一个变量 ⇒ 臂 2 若是「不翻转」，就是**可判定的结论**，
//   不再是 VOID。
//
// 🔴 判据同时读三条互不相同的通道（都不共享假设）：
//   ① testid：`audio-simple-player`（暂停）↔ `audio-simple-player-active`（播放）—— 批次 110 定的
//   ② aria 文本：`Play <名>` ↔ `Pause <名>`
//   ③ `MutationObserver` **同时**听 `attributes` + `childList` + `characterData`（补上 97 的盲区）
//   ④ 轮询兜底（250ms/次）—— 不共享 observer 的任何假设
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const WAV = '/tmp/jimeng-b104-test.wav';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b113b.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 🔑 「当前有没有在播放」的四通道快照。**不预设判据在哪个属性里** —— 全读。
const snap = (label) => p.evaluate((lbl) => {
  const r = {};
  // ① testid 家族
  r.tids = Array.from(new Set(Array.from(document.querySelectorAll('[data-testid^="audio-simple-player"]'))
    .map((e) => e.getAttribute('data-testid'))));
  // ② 所有带 Play/Pause 字样的按钮（画布上的 + 音色库里的）
  r.pp = Array.from(new Set(Array.from(document.querySelectorAll('[aria-label]'))
    .map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), inNode: !!e.closest('.react-flow__node') }))
    .filter((x) => /^(Play|Pause|播放|暂停)\b/.test(x.a))
    .map((x) => `${x.a}#${x.t || '-'}${x.inNode ? '@node' : ''}`)));
  // ③ innerText 里的播放状态句
  const body = (document.body.innerText || '');
  r.textFlags = ['播放中', '正在播放', '暂停', '试听'].filter((k) => body.includes(k));
  // ④ 页面里所有 <audio> 的 paused / src 尾段（不播的时候可能压根不在 DOM）
  r.audios = Array.from(document.querySelectorAll('audio')).map((a) => ({
    paused: a.paused, t: a.getAttribute('data-testid'),
    src: (a.currentSrc || a.src || '').slice(-40), ct: (a.currentTime || 0).toFixed(2), dur: (a.duration || 0).toFixed(2) }));
  r.at = Date.now();
  r.lbl = lbl;
  return r;
}, label);

const installMo = (tag) => p.evaluate((tg) => {
  window.__b = { tag: tg, t0: Date.now(), ev: [] };
  const hit = (s) => /play|pause|audio|生动|试听|解说/i.test(String(s));
  const mo = new MutationObserver((list) => {
    for (const rec of list) {
      const e = { t: Date.now() - window.__b.t0, type: rec.type };
      const desc = (n) => {
        if (!n) return null;
        if (n.nodeType === 3) return (n.nodeValue || '').replace(/\s+/g, ' ').trim().slice(0, 40);
        if (n.nodeType !== 1) return `#${n.nodeName}`;
        const t = n.getAttribute && n.getAttribute('data-testid');
        const a = n.getAttribute && n.getAttribute('aria-label');
        return `${n.tagName}${t ? '#' + t : ''}${a ? '[' + a.replace(/\s+/g, ' ').trim().slice(0, 30) + ']' : ''}`;
      };
      if (rec.type === 'childList') {
        const a = Array.from(rec.addedNodes).map(desc).filter((x) => x && hit(x));
        const r = Array.from(rec.removedNodes).map(desc).filter((x) => x && hit(x));
        if (a.length || r.length) e.ch = { added: a.slice(0, 4), removed: r.slice(0, 4) };
      } else if (rec.type === 'attributes') {
        e.attr = rec.attributeName; e.on = desc(rec.target);
        if (rec.attributeName === 'aria-label' || rec.attributeName === 'data-testid') e.new = String(rec.target.getAttribute(rec.attributeName) || '').replace(/\s+/g, ' ').trim().slice(0, 50);
      } else if (rec.type === 'characterData') {
        e.txt = desc(rec.target);
      }
      if (e.ch || e.attr || e.txt) window.__b.ev.push(e);
    }
  });
  // 🔴 关键：三条通道**全开**。批次 97 只开了 attributes，那是它记到 0 条的结构性原因。
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true, attributeOldValue: true });
  window.__b.mo = mo;
  return { tag: tg, channels: ['childList', 'attributes(aria-label,data-testid)', 'characterData'] };
}, tag);

const readMo = (tag) => p.evaluate((tg) => (window.__b && window.__b.tag === tg ? { n: window.__b.ev.length, ev: window.__b.ev } : { n: -1, ev: [] }), tag);

// 连采：observer 在页面里跑，Node 侧只做轮询兜底
const watch = async (tag, ms, step = 250) => {
  const s = [];
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    s.push(await snap(tag));
    await p.waitForTimeout(step);
  }
  return s;
};

out.start = { nodes: await nodeN(), credits: await credits() };
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
log('起点：', JSON.stringify(out.start), '｜id 数', idsBefore.length);
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ================= 阶段 1：左栏上传 wav，造一个带媒体的音频节点（阳性对照的弹药） =================
log('\n=== 阶段 1：左栏「上传」→ wav ===');
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('上传入口：', JSON.stringify(rail));
if (!rail.length) { log('🔴 找不到上传入口 ⇒ 中止'); await b.close(); process.exit(3); }

let fcSeen = null;
const onFc = async (fc) => { fcSeen = { multiple: fc.isMultiple() }; log('  filechooser：', JSON.stringify(fcSeen));
  try { await fc.setFiles(WAV); log('  setFiles ok'); } catch (e) { log('  setFiles 失败：', e.message); out.setFilesErr = e.message; } };
p.on('filechooser', onFc);

const r0 = rail[0];
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
log('已点上传，等文件选择器…');
await p.waitForTimeout(2500);

// 护栏②：上传后差集必须**恰好一个**且**同时 .selected**
let T1 = null;
for (let k = 1; k <= 20; k++) {
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) {
    const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    out.guardrail2 = { diff, sel, ok: sel.includes(diff[0]) };
    if (sel.includes(diff[0])) { T1 = diff[0]; log(`  #${k} 护栏② 通过：${diff[0]}｜selected=${JSON.stringify(sel)}`); break; }
    log(`  #${k} 差集=${JSON.stringify(diff)} 但 selected=${JSON.stringify(sel)} ⇒ 不认`);
  } else if (diff.length > 1) { log(`  #${k} 差集超过一个：${JSON.stringify(diff)} ⇒ 中止`); break; }
  await p.waitForTimeout(1200);
}
out.fileChooser = fcSeen; out.t1 = T1;
log('T1 =', T1, T1 ? '✅' : '🔴');
save();
if (!T1) { log('🔴 没造出带媒体节点 ⇒ 中止'); await b.close(); process.exit(3); }

// 等资源 ready（不是 processing）
log('\n=== 等资源 ready ===');
out.readyLog = [];
for (let k = 1; k <= 24; k++) {
  const st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    const inner = (n.innerText || '').replace(/\s+/g, ' ').trim();
    return { inner, tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))) }; }, T1);
  out.readyLog.push({ k, t: k * 1.5, inner: (st.inner || '').slice(0, 140), tids: st.tids });
  if (st.inner && /1 ready/.test(st.inner) && !/processing/.test(st.inner)) { log(`  #${k} ready：`, JSON.stringify(st.inner.slice(0, 100))); out.readyAt = k * 1.5; break; }
  if (k % 4 === 0) log(`  #${k}：`, JSON.stringify((st.inner || '').slice(0, 90)));
  await p.waitForTimeout(1500);
}
save();

// ================= 阶段 2：臂 1 —— 带媒体节点的播放（阳性对照） =================
log('\n=== 臂 1（阳性对照）：带媒体音频节点点 Play ===');
const playBtn = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  for (const e of n.querySelectorAll('[data-testid="audio-simple-player"],[data-testid="audio-simple-player-active"],button,[role=button]')) {
    const a = e.getAttribute('aria-label') || '';
    if (/^Play\b/.test(a) || /播放/.test(a)) { const r = e.getBoundingClientRect();
      return { aria: a, tid: e.getAttribute('data-testid'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; } }
  return { __err: 'no-play' };
}, T1);
log('播放按钮：', JSON.stringify(playBtn));
out.arm1 = { playBtn };
if (!playBtn || playBtn.__err) { log('🔴 找不到播放按钮 ⇒ 臂 1 放弃'); }
else {
  // 落点**按动作时刻现算**，只问「命中元素是否落在目标内部」
  const hitChk = await p.evaluate((t) => { const e = document.elementFromPoint(t.x + t.w / 2, t.y + t.h / 2);
    const btn = document.querySelector(`[data-testid="${t.tid}"]`) || null;
    return { tag: e ? e.tagName : null, ok: !!(e && btn && (e === btn || btn.contains(e))), txt: e ? (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) : null }; },
    { x: playBtn.x, y: playBtn.y, w: playBtn.w, h: playBtn.h, tid: playBtn.tid });
  log('  落点校验：', JSON.stringify(hitChk));
  if (!hitChk.ok) { log('🔴 落点校验不过 ⇒ 臂 1 放弃'); out.arm1.hitFail = hitChk; }
  else {
    out.arm1.before = await snap('arm1-before');
    out.arm1.moInstall = await installMo('arm1');
    const t0 = Date.now();
    await p.mouse.click(playBtn.x + playBtn.w / 2, playBtn.y + playBtn.h / 2);
    log('  已点 Play，连采 14s…');
    out.arm1.samples = await watch('arm1', 14000, 250);
    out.arm1.elapsed = Date.now() - t0;
    out.arm1.mo = await readMo('arm1');
    // 翻转判定：只看**采到过的不同取值序列**，相邻重复折叠
    const seq = (arr) => { const r = []; for (const s of arr) { const k = s.tids.join('|') + '::' + s.pp.join('|') + '::' + JSON.stringify(s.audios.map((a) => [a.paused, a.ct]));
      if (!r.length || r[r.length - 1].k !== k) r.push({ k, t: s.at }); } return r; };
    out.arm1.seq = seq(out.arm1.samples).map((x) => ({ t: x.t, tids: x.k.split('::')[0], pp: x.k.split('::')[1], au: x.k.split('::')[2] }));
    log('  ⇒ 臂 1 取值序列（折叠后）：');
    out.arm1.seq.forEach((x) => log(`     t=${x.t} tids=${x.tids} pp=${x.pp} au=${x.au}`));
    log('  ⇒ observer 记到', out.arm1.mo.n, '条');
    out.arm1.mo.ev.slice(0, 25).forEach((e) => log('     ' + JSON.stringify(e)));
    // 停掉播放（点 Pause），免得叠音干扰臂 2
    const pause = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      for (const e of n.querySelectorAll('button,[role=button]')) { const a = e.getAttribute('aria-label') || '';
        if (/^Pause\b/.test(a) || /^暂停/.test(a)) { const r = e.getBoundingClientRect();
          return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; }, T1);
    if (pause) { await p.mouse.click(pause.x, pause.y); await p.waitForTimeout(900); log('  已点 Pause 停掉'); out.arm1.paused = true; }
    else log('  ⚠️ 找不到 Pause（可能已播完自动停）');
  }
}
save();

// ================= 阶段 3：臂 2 —— 音色库样音（靶子） =================
log('\n=== 臂 2（靶子）：音色库样音 ===');
// 先确保 T1 选中，面板在
await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (n && !n.classList.contains('selected')) n.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); }, T1);
await p.waitForTimeout(600);
let libBtn = await p.evaluate(() => { for (const e of document.querySelectorAll('button,[role=button]')) {
  if ((e.getAttribute('aria-label') || '') === '音色库') { const r = e.getBoundingClientRect();
    if (r.width) return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height), exp: e.getAttribute('aria-expanded') }; } } return null; });
out.libBtn = libBtn;
if (!libBtn) {
  // 面板没开 ⇒ 重新点选节点让工具条出来
  const np = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 6)
      for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 6) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; } return null; }, T1);
  if (np) { await p.mouse.click(np.x, np.y); await p.waitForTimeout(1500);
    libBtn = await p.evaluate(() => { for (const e of document.querySelectorAll('button,[role=button]')) {
      if ((e.getAttribute('aria-label') || '') === '音色库') { const r = e.getBoundingClientRect();
        if (r.width) return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height), exp: e.getAttribute('aria-expanded') }; } } return null; }); out.libBtn = libBtn; }
}
log('「音色库」按钮：', JSON.stringify(libBtn));
if (!libBtn) { log('🔴 找不到「音色库」按钮 ⇒ 臂 2 放弃'); }
else {
  if (libBtn.exp === 'false') { await p.mouse.click(libBtn.x, libBtn.y); await p.waitForTimeout(1800); log('  已点开音色库'); }
  out.libOpen = await p.evaluate(() => { const e = document.querySelector('[aria-label="全音色"]'); if (!e) return { present: false };
    const r = e.getBoundingClientRect(); return { present: true, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; });
  log('  音色库面板：', JSON.stringify(out.libOpen));
  // 靶子按钮：`Play 生动解说`
  const sample = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label]')) {
    const a = e.getAttribute('aria-label') || ''; if (!/^Play\s+\S/.test(a)) continue;
    const r = e.getBoundingClientRect(); if (!r.width) continue;
    return { aria: a, tid: e.getAttribute('data-testid'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; } return null; });
  out.sampleBtn = sample;
  log('  样音按钮：', JSON.stringify(sample));
  if (!sample) { log('🔴 找不到 `Play <音色名>` 按钮 ⇒ 臂 2 放弃'); }
  else {
    const chk = await p.evaluate((t) => { const e = document.elementFromPoint(t.x + t.w / 2, t.y + t.h / 2);
      return { tag: e ? e.tagName : null, aria: e ? (e.getAttribute('aria-label') || (e.closest('[aria-label]') || {}).getAttribute?.('aria-label') || null) : null,
        ok: !!(e && (e.getAttribute('aria-label') === t.aria || (e.closest('[aria-label]') && e.closest('[aria-label]').getAttribute('aria-label') === t.aria))) }; }, sample);
    log('  落点校验：', JSON.stringify(chk));
    if (!chk.ok) { log('🔴 落点校验不过 ⇒ 臂 2 放弃'); out.arm2 = { hitFail: chk }; }
    else {
      out.arm2 = {};
      out.arm2.before = await snap('arm2-before');
      out.arm2.moInstall = await installMo('arm2');
      const t0 = Date.now();
      await p.mouse.click(sample.x + sample.w / 2, sample.y + sample.h / 2);
      log('  已点样音 Play，连采 30s（批次 97 记的就是 30s）…');
      out.arm2.samples = await watch('arm2', 30000, 250);
      out.arm2.elapsed = Date.now() - t0;
      out.arm2.mo = await readMo('arm2');
      const seq2 = []; for (const s of out.arm2.samples) { const k = s.tids.join('|') + '::' + s.pp.join('|') + '::' + JSON.stringify(s.audios.map((a) => [a.paused, a.ct]));
        if (!seq2.length || seq2[seq2.length - 1].k !== k) seq2.push({ k, t: s.at }); }
      out.arm2.seq = seq2.map((x) => ({ t: x.t, tids: x.k.split('::')[0], pp: x.k.split('::')[1], au: x.k.split('::')[2] }));
      log('  ⇒ 臂 2 取值序列（折叠后）：');
      out.arm2.seq.forEach((x) => log(`     t=${x.t} tids=${x.tids} pp=${x.pp} au=${x.au}`));
      log('  ⇒ observer 记到', out.arm2.mo.n, '条');
      out.arm2.mo.ev.slice(0, 25).forEach((e) => log('     ' + JSON.stringify(e)));
    }
  }
}
save();

// ================= 阶段 4：两臂对照 =================
log('\n=== 两臂对照 ===');
const flips = (arm) => (arm && arm.seq ? arm.seq.length - 1 : -1);
out.compare = {
  arm1_flips: flips(out.arm1), arm1_mo: out.arm1 && out.arm1.mo ? out.arm1.mo.n : null, arm1_secs: Math.round((out.arm1 && out.arm1.elapsed || 0) / 1000),
  arm2_flips: flips(out.arm2), arm2_mo: out.arm2 && out.arm2.mo ? out.arm2.mo.n : null, arm2_secs: Math.round((out.arm2 && out.arm2.elapsed || 0) / 1000),
};
log(JSON.stringify(out.compare, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);
