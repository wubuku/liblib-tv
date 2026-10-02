// 批次 110 · b 轮：对**本轮自建、且从没播过**的那个音频节点做故障注入 —— 第一次真正拦住它的媒体请求。
//
// a 轮的读数给了本轮一切前提：
//   · SELF = `node_pp3bhjpexx`，**从没播过**
//   · 节点里 **`audio: null`、`nVideo: 0`、`nImg: 0`** ⇒ **`<audio>` 元素是点播放之后才插进来的**
//   · 媒体 URL **没有扩展名**，长这样：
//     `https://v3-dreamina-de.jianying.com/<hash>/6abfffea/video/tos/cn/tos-cn-v-148450/
//      ooHx1IfRMfIKm8GlcVBdIOFE9UxdJqfdDnCfEL/?a=513695&ch=0&…`
//     ⇒ 定位靠 **TOS key**（`ooHx1IfRMfIKm8GlcVBdIOFE9UxdJqfdDnCfEL`），不是靠 `.wav`
//   ⚠️ 画布上还有 68 个别人的音频节点，它们也一直在发 `type=Media` 请求
//     （a 轮抓到 key `oEBAAYfDNI5rBuqHTqyuFv76fBmSmEpAFgCgIg` 的那些**不是本轮的**）
//     ⇒ **拦截必须按 key 精确匹配，不能按 `/audio|video|media/` 这类宽 pattern**
//
// 🔴 边界：只拦本轮那一个 key；本轮结束前**必定解除**。
// 📌 批次 105 教训：**断言必须带命中计数**，且命中之后还要看被注入对象状态有没有变。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', self: 'node_pp3bhjpexx', key: 'ooHx1IfRMfIKm8GlcVBdIOFE9UxdJqfdDnCfEL' };
const SELF = out.self, KEY = out.key;
const save = () => writeFileSync(new URL('./_tmp-b110b.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
const readNode = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const aud = n.querySelector('audio');
  const btns = Array.from(n.querySelectorAll('button')).map((x) => { const r = x.getBoundingClientRect();
    return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'), w: Math.round(r.width), h: Math.round(r.height) }; });
  return {
    aria: n.getAttribute('aria-label'),
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    audio: aud ? { src: aud.getAttribute('src'), currentSrc: (aud.currentSrc || '').slice(0, 160), preload: aud.getAttribute('preload'),
      readyState: aud.readyState, networkState: aud.networkState,
      error: aud.error ? { code: aud.error.code, message: (aud.error.message || '').slice(0, 120) } : null,
      duration: Number.isFinite(aud.duration) ? aud.duration : String(aud.duration),
      paused: aud.paused, currentTime: aud.currentTime, ended: aud.ended } : null,
    nAudio: n.querySelectorAll('audio').length,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    buttons: btns,
  };
}, SELF);
const playBtn = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  for (const x of n.querySelectorAll('button')) {
    const a = x.getAttribute('aria-label') || '';
    if (/^Play |^Pause /.test(a)) { const r = x.getBoundingClientRect();
      return { aria: a, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }
  }
  return null;
}, SELF);

const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');
out.hits = { request: 0, failed: 0, mine: 0, mineFailed: 0, others: 0, samples: [] };
cdp.on('Network.requestWillBeSent', (e) => {
  const u = e.request.url || '';
  if (e.type !== 'Media') return;
  out.hits.request++;
  if (u.includes(KEY)) { out.hits.mine++; if (out.hits.samples.length < 8) out.hits.samples.push({ k: 'req', url: u.slice(0, 200) }); }
  else out.hits.others++;
  save();
});
cdp.on('Network.loadingFailed', (e) => {
  out.hits.failed++;
  if (e.type === 'Media' || e.blockedReason) {
    if (out.hits.samples.length < 12) out.hits.samples.push({ k: 'failed', type: e.type, reason: e.blockedReason, err: e.errorText, cancel: e.canceled });
  }
  save();
});

out.start = await status();
out.before = await readNode();
out.pb0 = await playBtn();
log('起点：', JSON.stringify(out.start));
log('注入前节点：', JSON.stringify(out.before, null, 1).slice(0, 900));
log('播放钮：', JSON.stringify(out.pb0));
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 装拦截：只按 key 精确匹配 ----
const pattern = `*${KEY}*`;
await cdp.send('Network.setBlockedURLs', { urls: [pattern] });
out.blockPattern = pattern;
log('\n已设拦截：', pattern);
save();

// ---- 点播放 ----
if (!out.pb0) { log('🔴 找不到播放钮 ⇒ 中止'); await cdp.send('Network.setBlockedURLs', { urls: [] }); await b.close(); process.exit(3); }
await p.mouse.move(out.pb0.x, out.pb0.y); await p.waitForTimeout(350);
await p.mouse.click(out.pb0.x, out.pb0.y);
log('已点播放，开始采…');
save();

out.timeline = [];
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1500);
  const s = await readNode();
  out.timeline.push({ k, ms: k * 1500, innerText: s.innerText, audio: s.audio, hits: { ...out.hits } });
  log(`  #${String(k).padStart(2)} ${k * 1500}ms  账="${s.innerText}"`);
  log(`        audio=${s.audio ? JSON.stringify({ readyState: s.audio.readyState, networkState: s.audio.networkState, error: s.audio.error, paused: s.audio.paused, currentTime: s.audio.currentTime, duration: s.audio.duration }) : 'null'}  命中=${JSON.stringify({ req: out.hits.request, mine: out.hits.mine, failed: out.hits.failed, others: out.hits.others })}`);
  save();
  if (k === 6) await p.screenshot({ path: '/tmp/b110-b-blocked.png' });
}

out.after = await readNode();
out.pbAfter = await playBtn();
log('\n注入后节点：', JSON.stringify(out.after, null, 1));
log('播放钮（注入后）：', JSON.stringify(out.pbAfter));
out.hitCheck = { requests: out.hits.request, mineRequests: out.hits.mine, failed: out.hits.failed, mineInjected: out.hits.mine > 0 };
log('\n命中计数：', JSON.stringify(out.hitCheck));
out.samples = out.hits.samples;
log('样本：', JSON.stringify(out.samples, null, 1));
save();
await p.screenshot({ path: '/tmp/b110-b-blocked-full.png' });
log('\n截图 /tmp/b110-b-blocked.png（14s 时点）与 /tmp/b110-b-blocked-full.png');
save();
log('\n⚠️ 拦截仍在生效，c 轮务必解除');
log('DONE b');
process.exit(0);
