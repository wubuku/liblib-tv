// 批次 105 · d 轮：对那个 **ready** 的视频节点做**故障注入**，把「资源失效」这一档逼出来。
//
// ⚠️ 先把话说清楚（这是本轮唯一的合成成分，手册里必须原样写明）：
//   **失效不是自然发生的**，是本轮用 Playwright 的 `page.route` 把**那一条媒体请求**
//   `abort()` 掉制造出来的。理由：a 轮那张真·不可解码素材证明后端会把它**永远挂在
//   `processing`**（11 分钟账本逐位不动），自然过期这条路在当前环境里等不到。
//   ⇒ 下面所有读数都是**客户端对「资源请求失败」的真实反应**，
//      但**不能**据此声称「后端资源过期时长这样」——那是另一个问题，本轮没测。
//
// 要验的是 `media-playback.md` 117-119 行那个两分支：
//   「重试播放后：**资源可恢复**则正常播放；**资源已彻底失效**则进入无时长空载态
//     （时间显示 00:00 / 00:00，无法播放）」
//   ——🔴 这句话本手册至今只有「来自历史观察记录」一句背书，从没被对账过。
//
// 顺序：开播 → 取 `currentSrc` → 装拦截 → 逼 `<video>` 重新 load → 读失败态
//       → 撤拦截 + 重试（看可恢复分支）→ 再装拦截 + 重试（看空载分支）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_kk93zz7qzx' };
const SELF = out.selfId;

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// ---- 通用读数器：一个节点此刻长什么样 ----
const snap = async (tag) => {
  const s = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const v = n.querySelector('video');
    const desc = (e) => e ? `${e.tagName.toLowerCase()}${(e.getAttribute('class') || '').split(' ').filter((c) => /preview|player|surface|error|fail|retry|play/i.test(c)).join('.')}` : null;
    return {
      text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 260),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      video: v ? { rs: v.readyState, ns: v.networkState, dur: v.duration, ct: v.currentTime, paused: v.paused,
        err: v.error ? { code: v.error.code, msg: v.error.message } : null, src: v.currentSrc || v.src } : null,
      imgs: Array.from(n.querySelectorAll('img')).map((e) => ({ cls: e.className, complete: e.complete, w: e.naturalWidth, h: e.naturalHeight, alt: e.alt })),
      btns: Array.from(n.querySelectorAll('button')).map((e) => ({ t: e.getAttribute('data-testid'), a: e.getAttribute('aria-label'), x: e.innerText.trim() })).slice(0, 24),
    };
  }, SELF);
  out[tag] = s;
  log(`\n──── ${tag} ────`);
  log('  text     :', s.text);
  log('  testids  :', JSON.stringify(s.testids));
  log('  arias    :', JSON.stringify(s.arias));
  log('  video    :', JSON.stringify(s.video));
  log('  imgs     :', JSON.stringify(s.imgs));
  log('  btns     :', JSON.stringify(s.btns));
  return s;
};

out.step0 = await snap('0-注入前');

// ---- 1. 开播，取真实媒体 URL ----
const playBtn = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const b = Array.from(n.querySelectorAll('button')).find((e) => /^Play\b/.test(e.getAttribute('aria-label') || ''));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { aria: b.getAttribute('aria-label'), x: r.x + r.width / 2, y: r.y + r.height / 2 };
}, SELF);
log('\n播放钮：', JSON.stringify(playBtn));
out.playBtn = playBtn;
if (playBtn) {
  await p.mouse.move(playBtn.x, playBtn.y); await p.waitForTimeout(400);
  await p.mouse.click(playBtn.x, playBtn.y);
  await p.waitForTimeout(2500);
}
const afterPlay = await snap('1-开播后');
const src = afterPlay.video && afterPlay.video.src;
out.src = src;
log('\n媒体 URL：', src);

// ---- 2. 装拦截，只打这一条 ----
let blocked = 0;
if (src) {
  const glob = src.split('?')[0];
  await p.route(glob, async (route) => { blocked++; log('  🚧 拦截到媒体请求 #' + blocked); try { await route.abort('failed'); } catch (e) { log('  abort 失败', e.message); } });
  log('已装载拦截：', glob);
}
out.blocked = () => blocked;

// ---- 3. 逼 <video> 重新 load ----
const reload = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n && n.querySelector('video');
  if (!v) return { __err: 'no-video' };
  v.load();
  return { ok: true };
}, SELF);
log('\n强制 reload：', JSON.stringify(reload));
await p.waitForTimeout(3500);
out.step2 = await snap('2-注入失败后');

// ---- 4. 撤拦截 → 点重试（可恢复分支） ----
if (src) { await p.unroute(src.split('?')[0]); log('\n已撤拦截'); }
// 找「重试」类按钮
const findRetry = async () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const cands = Array.from(n.querySelectorAll('button,[role=button]'));
  const hit = cands.find((e) => /重试|retry|重播|重新/i.test((e.getAttribute('aria-label') || '') + ' ' + e.innerText));
  if (!hit) return { none: true, all: cands.map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), x: e.innerText.trim() })) };
  const r = hit.getBoundingClientRect();
  return { aria: hit.getAttribute('aria-label'), tid: hit.getAttribute('data-testid'), x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height };
}, SELF);
out.retryBtn = await findRetry();
log('重试按钮探测：', JSON.stringify(out.retryBtn));
if (out.retryBtn && out.retryBtn.x) {
  await p.mouse.move(out.retryBtn.x, out.retryBtn.y); await p.waitForTimeout(400);
  await p.mouse.click(out.retryBtn.x, out.retryBtn.y);
  await p.waitForTimeout(4000);
}
out.step3 = await snap('3-撤拦截后重试');
out.blockedTotal = blocked;

writeFileSync(new URL('./_tmp-b105d.json', import.meta.url), JSON.stringify(out, null, 1));
log('\n已落盘');
await b.close();
