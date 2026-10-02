// 批次 105 · f 轮：把故障注入**第三次**打进去（d、e 两轮都没命中）。
//
// 🔴🔴 本轮补上两条踩坑记录，都很便宜但极易复发：
//   ① **「装上拦截」≠「拦截生效」**。d、e 两轮 `blocked` 都是 0，而脚本当时并没有报警——
//      是我自己回头去数命中次数才发现的。**故障注入类断言必须带命中计数。**
//   ② 🔴 **`page.route('…去掉 query 的字符串…')` 匹配不到任何请求。**
//      Playwright 对**不含通配符**的字符串按**整条 URL 精确匹配**，
//      我把 `?a=513695&ch=0…` 整段 query 砍掉当 glob 用 ⇒ 永远不匹配。
//      本轮改用**谓词函数** `u => u.href.includes(<素材 token>)`，并额外挂一个
//      全量 `request` 监听器（只打本节点的素材 token）来交叉验证到底有没有真发请求。
//
// 目标：把 `media-playback.md` 117-119 行那个从没被对账过的「重试播放两分支」逼出来。
// ⚠️ 手册里必须原样写明：**失效是本轮用请求 abort 注入的，不是资源自然过期。**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_kk93zz7qzx' };
const SELF = out.selfId;
const TOKEN = 'oUw1dENDqBrmNYZFELi6zSISHAmffv4gxBIWdu';
let blocked = 0;
const seenReq = [];

p.on('request', (r) => { if (r.url().includes(TOKEN)) { seenReq.push({ t: Date.now(), url: r.url().slice(0, 90) }); log('  📥 真的发了请求：', r.url().slice(0, 90)); } });

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

const snap = async (tag) => {
  const s = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const v = n.querySelector('video');
    return {
      text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 280),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      video: v ? { rs: v.readyState, ns: v.networkState, dur: v.duration, ct: v.currentTime, paused: v.paused,
        err: v.error ? { code: v.error.code, msg: v.error.message } : null } : null,
      imgs: Array.from(n.querySelectorAll('img')).map((e) => ({ alt: e.alt, complete: e.complete, nw: e.naturalWidth })),
      btns: Array.from(n.querySelectorAll('button')).map((e) => ({ t: e.getAttribute('data-testid'), a: e.getAttribute('aria-label') })).slice(0, 24),
      clock: (() => { const c = n.querySelector('[data-testid="video-node-player-clock"]'); return c ? c.innerText.replace(/\s+/g, '') : null; })(),
    };
  }, SELF);
  out[tag] = { ...s, blockedSoFar: blocked, reqSeen: seenReq.length };
  log(`\n──── ${tag} （拦截命中 ${blocked} ／ 见请求 ${seenReq.length}）────`);
  log('  text   :', s.text);
  log('  clock  :', JSON.stringify(s.clock));
  log('  testids:', JSON.stringify(s.testids));
  log('  arias  :', JSON.stringify(s.arias));
  log('  video  :', JSON.stringify(s.video));
  log('  imgs   :', JSON.stringify(s.imgs));
  log('  btns   :', JSON.stringify(s.btns));
  return s;
};

const refetch = (i) => p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const v = n && n.querySelector('video');
  if (!v) return { __err: 'no-video' };
  const url = v.currentSrc || v.src;
  v.pause();
  v.removeAttribute('src'); v.load();
  v.setAttribute('src', url); v.load();
  return { ok: true };
}, i);

out.step0 = await snap('0-注入前');
log('\n>>> 装拦截（谓词函数）');
await p.route((u) => u.href.includes(TOKEN), async (route) => { blocked++; log('  🚧 命中 #' + blocked); try { await route.abort('failed'); } catch (e) { /* noop */ } });

log('>>> 强制重发');
out.refetch1 = await refetch(SELF);
await p.waitForTimeout(4500);
out.step1 = await snap('1-注入失败后');
log('\n🔴 命中 =', blocked, blocked === 0 ? '❌ 仍未命中' : '✅ 打进去了');

if (blocked > 0) {
  // 分支 A：撤拦截 + 重新触发 ⇒ 「资源可恢复」
  log('\n>>> 分支 A：撤拦截后重新 load（可恢复）');
  await p.unroute((u) => u.href.includes(TOKEN));
  await refetch(SELF);
  await p.waitForTimeout(5000);
  out.step2 = await snap('2-撤拦截后重载');

  // 分支 B：再注入 + 点播放 ⇒ 「已彻底失效」
  log('\n>>> 分支 B：再注入后点播放（彻底失效）');
  await p.route((u) => u.href.includes(TOKEN), async (route) => { blocked++; log('  🚧 命中 #' + blocked); try { await route.abort('failed'); } catch (e) { /* noop */ } });
  const pb = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const b = Array.from(n.querySelectorAll('button')).find((e) => /^Play\b/.test(e.getAttribute('aria-label') || '') || /^Pause\b/.test(e.getAttribute('aria-label') || ''));
    if (!b) return null; const r = b.getBoundingClientRect();
    return { a: b.getAttribute('aria-label'), x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, SELF);
  out.pb = pb; log('播放/暂停钮：', JSON.stringify(pb));
  if (pb) { await p.mouse.move(pb.x, pb.y); await p.waitForTimeout(350); await p.mouse.click(pb.x, pb.y); }
  await p.waitForTimeout(5000);
  out.step3 = await snap('3-再注入后点播放');
}

out.blockedTotal = blocked;
out.reqSeen = seenReq;
writeFileSync(new URL('./_tmp-b105f.json', import.meta.url), JSON.stringify(out, null, 1));
log('\n已落盘');
await b.close();
