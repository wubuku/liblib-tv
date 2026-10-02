// 批次 110 · c 轮：换**真正的**播放 URL 再拦一次，并顺手做「解除拦截 → 重试」那一半。
//
// b 轮的收获（比成功更有价值）：
//   · 我拦的 key 是**上传时的存储 key**（`ooHx1IfRMfIKm8GlcVBdIOFE9UxdJqfdDnCfEL`），
//     拦截**确实触发了**（`Network.loadingFailed` 里有一条 `blockedReason: "inspector"`）
//   · 可是节点里 `<audio src>` 用的是**另一个 key**：
//     `oERcOtFfdQDiV1DIHmFBfRExqfYiGndCM8df8E`
//   ⇒ 📌 **上传时的存储 key 与播放时的取流 key 不是同一个。**
//     照着上传日志去拦播放，**永远拦不到**。
//   · 🔑 而且那个播放 URL 上带着 **`mime_type=audio_mpeg`** —— 源文件是 **WAV**，
//     说明**服务端把它转码成了 MPEG 容器**再分发（时长 `4.032` 与自造 4 秒 WAV 一致）
//   · b 轮拦截**形同虚设**：媒体照常加载（`readyState 4`、`error null`、`duration 4.032`）
//     ⇒ 这是批次 105 那条「**拦截命中 ≠ 注入生效**」的**第二次**应验，
//       而且这次更隐蔽：拦截**报了命中**、媒体**却完好无损**
//
// 本轮两件事：
//   ① **先解除 b 轮那条错误拦截**（第一动作，绝不能忘）
//   ② 用**真 key** + **关浏览器缓存** 重来一次，并读「解除后重试」这一半
//      —— 这正是 `media-playback.md` 挂了两轮多的「重试播放」两个分支
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', self: 'node_pp3bhjpexx' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b110c.json', import.meta.url), JSON.stringify(out, null, 1));

const readNode = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const aud = n.querySelector('audio');
  const btns = Array.from(n.querySelectorAll('button')).map((x) => { const r = x.getBoundingClientRect();
    return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
      box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; });
  return {
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    audio: aud ? { srcHead: (aud.getAttribute('src') || '').slice(0, 150), readyState: aud.readyState,
      networkState: aud.networkState,
      error: aud.error ? { code: aud.error.code, message: (aud.error.message || '').slice(0, 140) } : null,
      duration: Number.isFinite(aud.duration) ? aud.duration : String(aud.duration),
      paused: aud.paused, currentTime: aud.currentTime } : null,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    buttons: btns,
  };
}, SELF);

const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');

out.hits = [];
const onReq = (e) => { if (e.type !== 'Media') return; out.hits.push({ k: 'req', url: e.request.url.slice(0, 200) }); save(); };
const onFail = (e) => { out.hits.push({ k: 'failed', type: e.type, reason: e.blockedReason || null, err: e.errorText || null, cancel: !!e.canceled }); save(); };
cdp.on('Network.requestWillBeSent', onReq);
cdp.on('Network.loadingFailed', onFail);

let unblocked = false;
const clearAll = async () => { try { await cdp.send('Network.setBlockedURLs', { urls: [] }); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }); unblocked = true; log('\n✅ 拦截与缓存开关已全部解除'); } catch (e) { log('🔴 解除失败：', e.message); } };
process.on('exit', () => { if (!unblocked) try { require('node:child_process'); } catch {} });

// ---- ① 第一动作：解除 b 轮那条错误拦截 ----
log('=== ① 先解除 b 轮的错误拦截 ===');
await clearAll();
out.afterUnblock = await readNode();
log('解除后节点：', JSON.stringify(out.afterUnblock.audio));
save();

// ---- ② 取出**真正的**播放 key ----
const realUrl = out.afterUnblock.audio ? out.afterUnblock.audio.srcHead : null;
log('\n=== ② 播放 URL ===\n ', realUrl);
const m = realUrl ? realUrl.match(/tos-cn-v-148450\/([A-Za-z0-9]+)\//) : null;
out.realKey = m ? m[1] : null;
log('播放取流 key =', out.realKey, out.realKey ? '✅' : '🔴 提取不到');
save();
if (!out.realKey) { log('⛔ 取不到 key ⇒ 中止'); await clearAll(); process.exit(3); }

// ---- ③ 关缓存 + 拦真 key，然后强制重新取流 ----
log('\n=== ③ 关缓存 + 拦真 key ===');
await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
out.blockPattern = `*${out.realKey}*`;
await cdp.send('Network.setBlockedURLs', { urls: [out.blockPattern] });
log('已设：', out.blockPattern, '｜缓存已关');
out.hits = [];   // 计数清零，从这里开始算
save();

const reloadAudio = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const a = n && n.querySelector('audio');
  if (!a) return { __err: 'no-audio' };
  const before = { readyState: a.readyState, networkState: a.networkState, error: a.error ? a.error.code : null, src: (a.getAttribute('src') || '').slice(0, 120) };
  a.load();
  return { before, after: { readyState: a.readyState, networkState: a.networkState } };
}, SELF);
out.reload = await reloadAudio();
log('强制 load()：', JSON.stringify(out.reload));
save();

out.phase1 = [];
for (let k = 1; k <= 12; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode();
  out.phase1.push({ k, ms: k * 1200, audio: s.audio, innerText: s.innerText, n: out.hits.length });
  log(`  阻断中 #${String(k).padStart(2)}  audio=${JSON.stringify(s.audio)}`);
  log(`        账="${s.innerText}"  事件数=${out.hits.length}`);
  save();
}
out.afterBlock = await readNode();
log('\n=== 阻断中的最终读数 ===');
log(JSON.stringify(out.afterBlock, null, 1));
log('\n事件样本：', JSON.stringify(out.hits.slice(0, 10), null, 1));
out.blockedHits = out.hits.filter((h) => h.k === 'failed' && h.reason).length;
out.mineBlocked = out.hits.some((h) => h.k === 'failed' && h.reason && h.type === 'Media');
log('拦截命中（blockedReason 非空）=', out.blockedHits, '｜有 Media 被拦 =', out.mineBlocked);
save();
await p.screenshot({ path: '/tmp/b110-c-blocked.png' });
log('截图 /tmp/b110-c-blocked.png');
save();

// ---- ④ 解除拦截 → 「重试播放」这一半 ----
log('\n=== ④ 解除拦截，重试 ===');
await cdp.send('Network.setBlockedURLs', { urls: [] });
out.hits = [];
out.retry = await reloadAudio();
log('重试 load()：', JSON.stringify(out.retry));
out.phase2 = [];
for (let k = 1; k <= 12; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode();
  out.phase2.push({ k, ms: k * 1200, audio: s.audio, innerText: s.innerText, n: out.hits.length });
  log(`  重试中 #${String(k).padStart(2)}  audio=${JSON.stringify(s.audio)}`);
  log(`        账="${s.innerText}"  事件数=${out.hits.length}`);
  save();
}
out.afterRetry = await readNode();
log('\n=== 重试后的最终读数 ===');
log(JSON.stringify(out.afterRetry, null, 1));
save();
await p.screenshot({ path: '/tmp/b110-c-retry.png' });
log('截图 /tmp/b110-c-retry.png');

await clearAll();
out.verdict = {
  blocked_media: out.mineBlocked,
  error_code_while_blocked: out.afterBlock.audio && out.afterBlock.audio.error ? out.afterBlock.audio.error.code : null,
  readyState_while_blocked: out.afterBlock.audio ? out.afterBlock.audio.readyState : null,
  error_code_after_retry: out.afterRetry.audio && out.afterRetry.audio.error ? out.afterRetry.audio.error.code : null,
  readyState_after_retry: out.afterRetry.audio ? out.afterRetry.audio.readyState : null,
  duration_after_retry: out.afterRetry.audio ? out.afterRetry.audio.duration : null,
};
log('\n=== 判定 ===', JSON.stringify(out.verdict, null, 1));
save();
log('\nDONE c');
process.exit(0);
