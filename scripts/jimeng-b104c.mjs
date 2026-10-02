// 批次 104 · c 轮：b 轮撞出来的三件事必须查清。
//
// b 轮的三处意外：
//   ① `audio-simple-player` 是**铺满整卡的 DIV**（`320×320` canvas）、**没有 aria-label**
//      —— 我按「testid 里有 Play 按钮」去读，读到空串。**真正的 `Play <名>` 在别的元素上。**
//   ② 点它**没有开始播放**，而是**跳到了 50%**：播放头 `left: 0% → 50%`、`<audio>.currentTime = 2`
//      （素材 4 秒）⇒ **点卡片是「跳转到点击位置」**，aria 也摆着 `Seek <名>`。
//   ③ 挂载出来的 `<audio>` 是 `paused: true` / `readyState: 0` / **`duration: null`**，
//      连采 6 次 `currentTime` 恒为 2 ⇒ **压根没播起来**。
//
// 本轮三问：
//   A 逐个列出节点里**每一个带 aria 的元素**及其几何，定位真正的播放钮与 Seek 区
//   B `<audio>` 的 `src` 是什么？`readyState` 会不会随时间变成 ≥1？（还是根本加载不了）
//   C 时间读数 `00:00:04` 到底什么格式？（它是 `00:00:04` 还是 `00:00 / 04`？）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_rezb9hd9kv' };
const SELF = out.selfId;
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// ---- A 逐个带 aria 的元素 ----
log('=== A 节点内每个带 aria 的元素 ===');
out.ariaEls = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const sc = (() => { const e = document.querySelector('.react-flow__viewport');
    const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })();
  const nodeRect = n.getBoundingClientRect();
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const ox = t ? Number(t[1]) : 0, oy = t ? Number(t[2]) : 0;
  return Array.from(n.querySelectorAll('[aria-label]')).map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
      tid: e.getAttribute('data-testid'),
      cv: `${Math.round(r.width / sc * 100) / 100}×${Math.round(r.height / sc * 100) / 100}@${Math.round((r.x - nodeRect.x) / sc + ox)},${Math.round((r.y - nodeRect.y) / sc + oy)}`,
      screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      parentTid: e.parentElement ? e.parentElement.getAttribute('data-testid') : null,
      cursor: getComputedStyle(e).cursor }; });
}, SELF);
for (const a of out.ariaEls) log(`  ${a.tag} aria=${JSON.stringify(a.aria)} role=${a.role} tid=${a.tid} 父=${a.parentTid} cursor=${a.cursor} cv=${a.cv}`);

// ---- C 时间读数的真实结构 ----
log('\n=== C 时间读数逐节点拆开 ===');
out.durTree = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const walk = (root) => { const rows = [];
    for (const e of root.querySelectorAll('*')) { const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const own = Array.from(e.childNodes).filter((c) => c.nodeType === 3).map((c) => c.textContent.trim()).filter(Boolean);
      if (own.length) rows.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.className||'').toString().slice(0,40),
        ownText: own.join('|'), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }); }
    return rows; };
  const d = n.querySelector('[data-testid="audio-duration"]');
  const a11y = n.querySelector('[data-testid="audio-duration-accessible"]');
  return { duration: d ? { text: (d.textContent||'').replace(/\s+/g,' ').trim(), leaves: walk(d) } : null,
    accessible: a11y ? { text: (a11y.textContent||'').replace(/\s+/g,' ').trim(), aria: a11y.getAttribute('aria-label'),
      cls: (a11y.className||'').toString().slice(0,60) } : null };
}, SELF);
log(JSON.stringify(out.durTree, null, 1));

// ---- B <audio> 的 src 与 readyState 随时间变化 ----
log('\n=== B <audio> 的 src / readyState 随时间 ===');
out.audio = [];
for (let k = 0; k < 6; k++) {
  const a = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('audio'); if (!v) return { none: true };
    return { src: (v.getAttribute('src') || '').slice(0, 90), currentSrc: (v.currentSrc || '').slice(0, 90),
      sourceTags: Array.from(n.querySelectorAll('source')).map((s) => (s.getAttribute('src') || '').slice(0, 60)),
      readyState: v.readyState, networkState: v.networkState, paused: v.paused, ct: v.currentTime, dur: v.duration,
      error: v.error ? { code: v.error.code, msg: (v.error.message || '').slice(0, 80) } : null,
      preload: v.getAttribute('preload'), canPlay: (() => { try { return v.canPlayType('audio/wav'); } catch (e) { return 'err'; } })() }; }, SELF);
  out.audio.push({ t: k * 1000, ...a });
  log(`  t=${k}s：${JSON.stringify(a)}`);
  if (k < 5) await p.waitForTimeout(2000);
}

writeFileSync(new URL('./_tmp-b104c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
