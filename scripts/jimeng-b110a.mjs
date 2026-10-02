// 批次 110 · a 轮：造一个**从没播过**的音频节点，并把它的媒体 URL 抓出来。
//
// 本批要关的：
//   ① `media-playback.md:198` 「重试播放」两分支 —— 三态记「无法验证」已挂了两轮多
//   ② `20-reference.md` 那行 `2 resources: 1 ready, 0 processing, 1 failed.` ← 抄写，未实测
//
// 批次 105 四轮注入全空的结论与它留下的线索：
//   d `load()` 不发请求 ｜ e 摘 src 再挂回仍不发 ｜ f 谓词路由命中 1 次但打在 cache hit 上
//   ｜ g CDP 关缓存后连 `request` 事件都不发
//   ⇒ 「**拦截命中 ≠ 注入生效**」；它建议「换一个**从没播过**的节点，
//      或换 `Network.setBlockedURLs` 这种更靠底层的手段」
// **本轮两样都用。**
//
// 🔴 边界：只对**本轮自建**节点的媒体请求动手；不写持久数据、不扣费；
//    拦截随时可关，b/c 轮结束必关。
// 📌 判据纪律：每个断言都要带**命中计数**（批次 105 教训），且命中之后还要看被注入对象状态有没有变。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a', file: '/tmp/jimeng-b104-test.wav' };
const save = () => writeFileSync(new URL('./_tmp-b110a.json', import.meta.url), JSON.stringify(out, null, 1));

const WAV = out.file;
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});

// ---- 网络抓包：整轮都开着，好抓到媒体 URL ----
const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');
out.reqs = [];
cdp.on('Network.requestWillBeSent', (e) => {
  const u = e.request.url || '';
  if (!/jimeng-b104-test|\.wav|\.mp4|audio|video|media|tos|byteimg/i.test(u)) return;
  out.reqs.push({ t: Date.now(), method: e.request.method, url: u.slice(0, 240), type: e.type || null,
    initiator: (e.initiator && e.initiator.type) || null });
});
log('网络监听已开');

out.start = await status();
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 上传（批次 109 已证免费：805 → 805） ----
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
const r0 = rail[0];
p.on('filechooser', async (fc) => { try { await fc.setFiles(WAV); log('  setFiles ok'); } catch (e) { log('  setFiles 失败：', e.message); } });
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

let SELF = null;
for (let k = 1; k <= 24; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length) { out.diffAt = k * 1200; out.diff = diff; log(`  #${k} 差集 = ${JSON.stringify(diff)}`); SELF = diff[0]; }
  if (SELF) {
    const info = await p.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      return n ? { t: (n.innerText || '').replace(/\s+/g, ' ').trim(), sel: n.classList.contains('selected') } : null;
    }, SELF);
    if (info && !/processing|正在上传/.test(info.t)) { log(`  #${k} 已 ready：${info.t}`); out.ready = info; break; }
  }
  save();
}
out.selfId = SELF;
log('SELF =', SELF, SELF ? '✅' : '🔴');

const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
out.selIds = selIds;
out.guardrail2 = { diffN: (out.diff || []).length, ok: (out.diff || []).length === 1 && selIds.includes(SELF) };
log('护栏② 差集恰好一个且同时 selected =', out.guardrail2.ok);
save();

// ---- 节点结构 + <audio> 元素（**不播**，只读） ----
out.selfInfo = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const aud = n.querySelector('audio');
  const vids = n.querySelectorAll('video');
  const imgs = n.querySelectorAll('img');
  const btns = Array.from(n.querySelectorAll('button')).map((x) => { const xr = x.getBoundingClientRect();
    return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
      box: `${Math.round(xr.x)},${Math.round(xr.y)} ${Math.round(xr.width)}×${Math.round(xr.height)}` }; });
  return {
    id: i, cls: n.className, aria: n.getAttribute('aria-label'),
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    transform: n.style.transform,
    audio: aud ? { src: aud.getAttribute('src'), currentSrc: aud.currentSrc, preload: aud.getAttribute('preload'),
      readyState: aud.readyState, networkState: aud.networkState, error: aud.error ? { code: aud.error.code, message: aud.error.message } : null,
      duration: aud.duration, paused: aud.paused, currentTime: aud.currentTime,
      box: (() => { const ar = aud.getBoundingClientRect(); return `${Math.round(ar.x)},${Math.round(ar.y)} ${Math.round(ar.width)}×${Math.round(ar.height)}`; })() } : null,
    nVideo: vids.length, nImg: imgs.length,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    buttons: btns,
  };
}, SELF);
log('\n=== 本轮自建音频节点（未播） ===');
log(JSON.stringify(out.selfInfo, null, 1));
save();

out.reqsSoFar = out.reqs.slice();
log('\n=== 抓到的相关请求 ===');
out.reqs.forEach((r, i) => log(`  [${i}] ${r.method} type=${r.type} init=${r.initiator}\n      ${r.url}`));
out.mediaUrls = out.reqs.map((r) => r.url).filter((u) => /\.(wav|mp4|m4a|mp3)(\?|$)/i.test(u));
log('\n媒体直链候选：', JSON.stringify(out.mediaUrls));
save();

out.end = await status();
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
