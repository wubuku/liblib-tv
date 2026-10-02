// 批次 110 · e 轮：手册那句「资源已彻底失效则进入**无时长空载态（时间显示 00:00 / 00:00）**」到底成不成立。
//
// d 轮已把「可恢复」那一支关掉：
//   点「重试播放音频」（拦截已解除）→ **1.2 秒内**恢复：
//   `<audio>` 回来（`readyState 4`、`duration 4.032`）、`paused:false`、`currentTime` 已在走、
//   按钮变 **`Pause jimeng-b104-test`**（= **恢复后直接开始播**，不是回到暂停态）、
//   资源账**仍然纹丝不动** `1 resource: 1 ready, 0 processing, 0 failed.`
//   并且**确实重新发了请求**（同一 key 换了 CDN 节点；前一个 `net::ERR_ABORTED` 是切 CDN 时的正常放弃）
//   🆕 两个新 testid：播放中多出 **`audio-simple-player-active`**（未播态是 `audio-simple-player`）
//      和 **`audio-playback-media`**（这就是 `<audio>` 元素本身）
//
// 本轮测「**彻底失效**」那一支：拦截**一直挂着**的情况下点「重试播放音频」。
// 顺带正面回答：失败态到底显不显示时长。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e', self: 'node_pp3bhjpexx' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b110e.json', import.meta.url), JSON.stringify(out, null, 1));

const readNode = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const aud = n.querySelector('audio');
  const r = n.getBoundingClientRect();
  // 时长相关的所有可见文字（含 sr-only），逐条列出
  const durEls = Array.from(n.querySelectorAll('[data-testid^="audio-duration"]')).map((e) => {
    const b = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), text: (e.textContent || '').trim(),
      box: `${Math.round(b.x)},${Math.round(b.y)} ${Math.round(b.width)}×${Math.round(b.height)}` }; });
  const btn = (re) => { for (const x of n.querySelectorAll('button')) { const a = x.getAttribute('aria-label') || '';
    if (re.test(a)) { const br = x.getBoundingClientRect();
      return { aria: a, x: Math.round(br.x + br.width / 2), y: Math.round(br.y + br.height / 2),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; } } return null; };
  return {
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    audio: aud ? { readyState: aud.readyState, networkState: aud.networkState,
      error: aud.error ? { code: aud.error.code, message: (aud.error.message || '').slice(0, 140) } : null,
      duration: Number.isFinite(aud.duration) ? aud.duration : String(aud.duration), paused: aud.paused } : null,
    durEls, testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    retryBtn: btn(/^重试播放/), playBtn: btn(/^Play |^Pause /),
    // 失败态那个区域的逐字文字
    errEl: (() => { const e = n.querySelector('[data-testid="audio-playback-error"]');
      if (!e) return null; const br = e.getBoundingClientRect();
      return { text: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(),
        html: e.outerHTML.slice(0, 400),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; })(),
  };
}, SELF);

const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');
out.hits = [];
cdp.on('Network.requestWillBeSent', (e) => { if (e.type === 'Media') { out.hits.push({ k: 'req', url: e.request.url.slice(0, 190) }); save(); } });
cdp.on('Network.loadingFailed', (e) => { if (e.type === 'Media') { out.hits.push({ k: 'failed', reason: e.blockedReason || null, err: e.errorText || null }); save(); } });
let unblocked = false;
const clearAll = async () => { try { await cdp.send('Network.setBlockedURLs', { urls: [] }); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }); unblocked = true; } catch (e) { log('解除失败', e.message); } };

out.step0 = await readNode();
log('=== 起点（d 轮恢复后，正在播）===');
log('  账：', out.step0.innerText);
log('  时长元素：', JSON.stringify(out.step0.durEls));
save();

// ---- 先暂停，免得它自己播完 ----
if (out.step0.playBtn && /^Pause/.test(out.step0.playBtn.aria)) {
  await p.mouse.click(out.step0.playBtn.x, out.step0.playBtn.y); await p.waitForTimeout(1200);
  log('已暂停：', (await readNode()).innerText);
  save();
}

// ---- 装拦截 → 强制重新取流 → 回到失败态 ----
const KEY = 'oERcOtFfdQDiV1DIHmFBfRExqfYiGndCM8df8E';
out.key = KEY;
log('\n=== 装拦截并强制重新取流 ===');
await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
await cdp.send('Network.setBlockedURLs', { urls: [`*${KEY}*`] });
out.hits = [];
const forced = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const a = n && n.querySelector('audio');
  if (!a) return { __err: 'no-audio' };
  a.load();
  return { ok: true, readyState: a.readyState, networkState: a.networkState };
}, SELF);
log('强制 load()：', JSON.stringify(forced));
save();

out.phase0 = [];
for (let k = 1; k <= 8; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode();
  out.phase0.push({ k, innerText: s.innerText, audio: s.audio, durEls: s.durEls, errEl: s.errEl, n: out.hits.length });
  log(`  回失败态 #${k}  账="${s.innerText}"`);
  log(`        时长元素=${JSON.stringify(s.durEls)}  拦截命中=${out.hits.filter((h) => h.reason).length}`);
  if (s.retryBtn) { log('  ⇒ 已在失败态'); out.backToFailedAt = k * 1200; break; }
  save();
}
out.inFail = await readNode();
log('\n=== 失败态读数（拦截仍在） ===');
log(JSON.stringify(out.inFail, null, 1));
log('\n失败态元素逐字：', JSON.stringify(out.inFail.errEl, null, 1));
save();
await p.screenshot({ path: '/tmp/b110-e-failed.png' });
log('截图 /tmp/b110-e-failed.png');

// ---- 关键一格：拦截**仍在**时点「重试播放音频」 ----
log('\n=== 关键：拦截仍在，点「重试播放音频」 ===');
out.hits = [];
const rb = out.inFail.retryBtn;
if (!rb) { log('🔴 没有重试钮 ⇒ 中止'); await clearAll(); process.exit(3); }
const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
await p.mouse.move(rb.x, rb.y); await p.waitForTimeout(400);
await p.mouse.click(rb.x, rb.y);
log('已点「重试播放音频」（拦截仍生效）');
out.phase1 = [];
for (let k = 1; k <= 12; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode();
  out.phase1.push({ k, ms: k * 1200, innerText: s.innerText, audio: s.audio, durEls: s.durEls, errEl: s.errEl, n: out.hits.length });
  log(`  #${String(k).padStart(2)} ${String(k * 1200).padStart(5)}ms  账="${s.innerText}"`);
  log(`        audio=${JSON.stringify(s.audio)}  时长元素=${JSON.stringify(s.durEls)}  拦截命中=${out.hits.filter((h) => h.reason).length}  重试钮=${s.retryBtn ? '有' : '无'}`);
  save();
}
out.afterRetryWhileBlocked = await readNode();
log('\n=== 「拦截仍在时点重试」的最终读数 ===');
log(JSON.stringify(out.afterRetryWhileBlocked, null, 1));
out.phase1Hits = out.hits.slice();
log('\n事件：', JSON.stringify(out.phase1Hits.slice(0, 10), null, 1));
save();
await p.screenshot({ path: '/tmp/b110-e-retry-blocked.png' });
log('截图 /tmp/b110-e-retry-blocked.png');

// ---- 收：解除拦截，再点一次重试，确认能恢复 ----
log('\n=== 收尾：解除拦截后再点一次重试 ===');
await clearAll();
out.hits = [];
const rb2 = out.afterRetryWhileBlocked.retryBtn;
if (rb2) {
  await p.mouse.click(rb2.x, rb2.y);
  for (let k = 1; k <= 8; k++) {
    await p.waitForTimeout(1200);
    const s = await readNode();
    out.phase2 = out.phase2 || [];
    out.phase2.push({ k, innerText: s.innerText, audio: s.audio });
    log(`  #${k} 账="${s.innerText}"`);
    if (s.audio && !s.retryBtn) { out.recoveredAgain = true; break; }
  }
}
out.final = await readNode();
log('\n终点账：', out.final.innerText);
log('终点时长元素：', JSON.stringify(out.final.durEls));
save();

out.verdict = {
  fail_state_text: out.inFail.innerText,
  fail_has_duration_element: out.inFail.durEls.length,
  fail_error_aria: (out.inFail.arias || []).find((x) => /重试/.test(x)) || null,
  retry_while_blocked_still_fails: !!(out.afterRetryWhileBlocked.retryBtn),
  recovered_after_unblock: !!out.recoveredAgain,
};
log('\n=== 判定 ===', JSON.stringify(out.verdict, null, 1));
await clearAll();
save();
log('\nDONE e');
process.exit(0);
