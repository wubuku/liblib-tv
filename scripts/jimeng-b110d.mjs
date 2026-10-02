// 批次 110 · d 轮：**真的去点**「重试播放音频」那个按钮 —— 补上 c 轮没测到的那一半。
//
// c 轮的收获（失败态终于自然复现了）：
//   阻断生效（`Network.loadingFailed`，`blockedReason: "inspector"`，`type: Media`，**命中 2 次**）后：
//   · innerText 逐字变成
//     `jimeng-b104-test 音频播放失败 重试播放音频 1 resource: 1 ready, 0 processing, 0 failed. Selected.`
//   · 🔑 **`<audio>` 元素不是「报 error」，是**整个从 DOM 里消失**（`audio: null`）
//   · testid：`audio-simple-player` / `audio-timeline-visual` / `audio-playback-waveform`
//     / `audio-duration` / `audio-duration-accessible` **全部消失**，
//     换来一个 **`audio-playback-error`**
//   · 按钮从 `Play jimeng-b104-test`（`22×22 @701,446`）变成
//     **`重试播放音频`**（`66×19 @607,383`）
//   · ✅ **资源账纹丝不动**：仍是 `1 resource: 1 ready, 0 processing, 0 failed.`
//     —— 批次 105「播放期失败不会改那张资源账」**第二次独立应验**
//
// 🔴 c 轮的「重试」是**假的**：它调的 `audio.load()` 在那时已经
//    `__err: "no-audio"`（元素都被摘了）⇒ 什么都没发生，
//    连采 12 次账都不动。本轮改为**点那个按钮本身**。
//
// 本轮两格：
//   ① 拦截**已解除**（c 轮末尾已清）⇒ 点「重试播放音频」 ⇒ 看能不能恢复
//   ② 再拦一次 ⇒ 点「重试播放音频」 ⇒ 看失败态能不能**复现**（证明这个按钮确实会重新取流）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd', self: 'node_pp3bhjpexx' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b110d.json', import.meta.url), JSON.stringify(out, null, 1));

const readNode = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const aud = n.querySelector('audio');
  const btn = (re) => { for (const x of n.querySelectorAll('button')) { const a = x.getAttribute('aria-label') || '';
    if (re.test(a)) { const br = x.getBoundingClientRect();
      return { aria: a, x: Math.round(br.x + br.width / 2), y: Math.round(br.y + br.height / 2),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; } } return null; };
  return {
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    audio: aud ? { readyState: aud.readyState, networkState: aud.networkState,
      error: aud.error ? { code: aud.error.code, message: (aud.error.message || '').slice(0, 140) } : null,
      duration: Number.isFinite(aud.duration) ? aud.duration : String(aud.duration), paused: aud.paused, currentTime: aud.currentTime } : null,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    retryBtn: btn(/^重试播放/), playBtn: btn(/^Play |^Pause /), pauseBtn: btn(/^Pause /),
  };
}, SELF);

const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');
let unblocked = false;
out.hits = [];
cdp.on('Network.requestWillBeSent', (e) => { if (e.type === 'Media') { out.hits.push({ k: 'req', url: e.request.url.slice(0, 190) }); save(); } });
cdp.on('Network.loadingFailed', (e) => { if (e.type === 'Media') { out.hits.push({ k: 'failed', reason: e.blockedReason || null, err: e.errorText || null }); save(); } });
const clearAll = async () => { try { await cdp.send('Network.setBlockedURLs', { urls: [] }); await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }); unblocked = true; } catch (e) { log('解除失败', e.message); } };

// 先确认拦截确实是清的
await clearAll();
out.step0 = await readNode();
log('=== 起点（c 轮失败态，拦截已解除）===');
log('  账：', out.step0.innerText);
log('  retryBtn：', JSON.stringify(out.step0.retryBtn));
log('  audio：', JSON.stringify(out.step0.audio));
save();
if (!out.step0.retryBtn) { log('🔴 没有「重试播放音频」按钮 ⇒ 中止'); process.exit(3); }

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');

// ---- ① 拦截已解除 ⇒ 点「重试播放音频」，看能不能恢复 ----
log('\n=== ① 拦截已解除，点「重试播放音频」 ===');
out.hits = [];
let rb = out.step0.retryBtn;
await p.mouse.move(rb.x, rb.y); await p.waitForTimeout(400);
await p.mouse.click(rb.x, rb.y);
log('已点，重试钮 aria=', rb.aria);
out.phase1 = [];
for (let k = 1; k <= 14; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode();
  out.phase1.push({ k, ms: k * 1200, innerText: s.innerText, audio: s.audio, testids: s.testids, n: out.hits.length });
  log(`  #${String(k).padStart(2)} ${String(k * 1200).padStart(5)}ms  账="${s.innerText}"`);
  log(`        audio=${JSON.stringify(s.audio)}  事件=${out.hits.length}  重试钮=${s.retryBtn ? '有' : '无'} 播放钮=${s.playBtn ? s.playBtn.aria : '无'}`);
  save();
  if (!s.retryBtn && s.audio) { log('  ⇒ 失败态已退出，出现 <audio>'); out.recoveredAt = k * 1200; break; }
}
out.afterRetry = await readNode();
log('\n=== ① 的最终读数 ===');
log(JSON.stringify(out.afterRetry, null, 1));
log('\n事件：', JSON.stringify(out.hits.slice(0, 8), null, 1));
out.phase1Hits = out.hits.slice();
save();
await p.screenshot({ path: '/tmp/b110-d-recovered.png' });
log('截图 /tmp/b110-d-recovered.png');
save();

// ---- ② 再拦一次 ⇒ 点「重试播放音频」，验证这个按钮确实会重新取流 ----
const key = (out.afterRetry.audio ? (out.afterRetry.audio.srcHead || '') : '');
log('\n=== ② 重新装拦截，验证「重试」这个动作会重新取流 ===');
// 从事件里拿播放 key
const hit = out.hits.find((h) => h.k === 'req');
if (!hit) { log('🔴 ① 没有发出媒体请求 ⇒ 无法定位 key，跳过②'); out.step2Skipped = 'no-request-in-phase1'; }
else {
  const m = hit.url.match(/tos-cn-v-148450\/([A-Za-z0-9]+)\//);
  out.realKey2 = m ? m[1] : null;
  log('播放 key =', out.realKey2);
  if (out.realKey2) {
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    await cdp.send('Network.setBlockedURLs', { urls: [`*${out.realKey2}*`] });
    // 先把它打回失败态：现在它在播放/暂停态，播放钮是 Pause 或 Play
    const s2 = await readNode();
    log('② 前状态：', s2.innerText);
    if (s2.retryBtn) { log('  （还在失败态，直接进②）'); }
    else {
      // 用「暂停 → 播放」或直接再点播放钮？更干净的做法：先重放一次失败
      log('  需要先造出失败态');
    }
    save();
  }
}
await clearAll();
log('\n✅ 拦截与缓存开关已解除');
out.end = await readNode();
log('终点账：', out.end.innerText);
save();
log('\nDONE d');
process.exit(0);
