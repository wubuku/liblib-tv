// 批次 105 · e 轮：把故障注入**真正打进去**（d 轮打空了）。
//
// 🔴 d 轮失败的教训（写下来免得下批再踩）：
//   对一个 `readyState 4`、已完整缓冲的 `<video>` 调 `v.load()`，**根本不会重新发请求**
//   —— 浏览器直接从内存缓存喂它。证据：`out.blockedTotal === 0`，全程没有一行
//   「🚧 拦截到媒体请求」；`v.load()` 之后 `rs` 仍是 4、`ct` 仍在 2.817→3.421 往前走、
//   `err` 仍是 null。⇒ **「我装了拦截」不等于「拦截生效了」，必须数命中次数**。
//
// 本轮手法：先 `removeAttribute('src')` + `load()`，再把**同一个 URL 原样挂回去**再 `load()`
//   —— 这样浏览器一定会重新发请求，而**请求本身一个字都没改**，
//   失败完全来自网络层（`page.route(...).abort()`），不是来自 DOM。
//   ⚠️ 这一点必须在手册里写明：这轮是**故障注入**，不是「资源自然过期」。
//
// 顺带把 d 轮捞到的两条真读数固定下来（它们本身就有价值）：
//   ① 播放中节点 `innerText` 逐字含 **`Seek <名>`** 与 **`Playing video`**，
//      且 arias 里有 **`"<名>: Playing video"`** —— 播放态有一条**专门的 aria 播报**，
//      未播时没有（未播只有按钮的 `Play <名>`）。
//   ② 未播态节点里只有 **5 个** button（Rename / Add tags / Create connected node /
//      Play / 替换媒体）；**静音钮与全屏钮起播后才出现**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_kk93zz7qzx' };
const SELF = out.selfId;
let blocked = 0;

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

const snap = async (tag) => {
  const s = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const v = n.querySelector('video');
    return {
      text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 260),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      video: v ? { rs: v.readyState, ns: v.networkState, dur: v.duration, ct: v.currentTime, paused: v.paused,
        err: v.error ? { code: v.error.code, msg: v.error.message } : null } : null,
      imgs: Array.from(n.querySelectorAll('img')).map((e) => ({ alt: e.alt, complete: e.complete, nw: e.naturalWidth })),
      btns: Array.from(n.querySelectorAll('button')).map((e) => ({ t: e.getAttribute('data-testid'), a: e.getAttribute('aria-label') })).slice(0, 24),
      clock: (() => { const c = n.querySelector('[data-testid="video-node-player-clock"]'); return c ? c.innerText.replace(/\s+/g, '') : null; })(),
    };
  }, SELF);
  out[tag] = { ...s, blockedSoFar: blocked };
  log(`\n──── ${tag} （拦截命中 ${blocked} 次）────`);
  log('  text   :', s.text);
  log('  clock  :', JSON.stringify(s.clock));
  log('  testids:', JSON.stringify(s.testids));
  log('  arias  :', JSON.stringify(s.arias));
  log('  video  :', JSON.stringify(s.video));
  log('  imgs   :', JSON.stringify(s.imgs));
  log('  btns   :', JSON.stringify(s.btns));
  return s;
};

out.step0 = await snap('0-注入前');

const force = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n && n.querySelector('video');
  if (!v) return { __err: 'no-video' };
  const url = v.currentSrc || v.src;
  v.pause();
  v.removeAttribute('src'); v.load();
  v.setAttribute('src', url); v.load();      // 同一个 URL 原样挂回
  return { ok: true, url };
}, SELF);
out.force = force;
log('\n强制重发：', JSON.stringify(force).slice(0, 200));

if (force && force.url) {
  const glob = force.url.split('?')[0];
  await p.route(glob, async (route) => { blocked++; try { await route.abort('failed'); } catch (e) { /* noop */ } });
  out.routeGlob = glob;
  log('已装载拦截：', glob);
  // load() 在装拦截之前就发了，所以这里再来一次，确保命中
  await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n && n.querySelector('video');
    if (!v) return { __err: 'no-video' };
    const url = v.currentSrc || v.src;
    v.removeAttribute('src'); v.load();
    v.setAttribute('src', url); v.load();
    return { ok: true };
  }, SELF);
  await p.waitForTimeout(4000);
}
out.step1 = await snap('1-注入失败后');
log('\n🔴 拦截命中次数 =', blocked, blocked === 0 ? '（还是没有命中！）' : '✅ 确实打进去了');

writeFileSync(new URL('./_tmp-b105e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
