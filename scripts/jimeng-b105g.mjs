// 批次 105 · g 轮：把**缓存**这个变量也掐掉，才算真的制造出一次网络失败。
//
// 🔴 f 轮的教训（很便宜但极容易骗人）：
//   路由**确实命中了**（`命中 #1`，`page.on('request')` 也看到那条 URL），
//   `route.abort('failed')` 也**确实执行了** —— 可是 4.5 秒后：
//     `<video>` 仍是 `rs:4, ns:1, dur:6, err:null`，节点 testids/arias/时钟**一个字节都没变**，
//     账本照旧 `1 ready, 0 processing, 0 failed`。
//   原因不是「注入失败」，而是**媒体早在前几轮就已经被浏览器缓存**，
//   `abort()` 打在一次 cache hit 上等于打空气。
//   ⇒ **「拦截命中」也不等于「注入生效」**——这是 d/e/f 三轮连着踩的同一个坑的第三层。
//
// 本轮：用 CDP 打开 `Network.setCacheDisabled` + `Network.clearBrowserCache`，
// 把缓存这个变量彻底掐掉，再重发一次。
//
// ⚠️ 结论口径（手册里必须原样写）：**失效是本轮用请求 abort 注入的，不是资源自然过期。**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = ctx.pages().find((x) => x.url().includes('ai-canvas'));
await p.bringToFront();
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_kk93zz7qzx' };
const SELF = out.selfId;
const TOKEN = 'oUw1dENDqBrmNYZFELi6zSISHAmffv4gxBIWdu';
let blocked = 0;
const seenReq = [];

p.on('request', (r) => { if (r.url().includes(TOKEN)) { seenReq.push(r.url().slice(0, 90)); log('  📥 请求：', r.url().slice(0, 80)); } });
p.on('requestfailed', (r) => { if (r.url().includes(TOKEN)) log('  ❌ 请求失败：', (r.failure() || {}).errorText, '|', r.url().slice(0, 60)); });

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
  log(`\n──── ${tag} （命中 ${blocked} ／ 请求 ${seenReq.length}）────`);
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

log('\n>>> CDP：关缓存 + 清缓存');
const cdp = await ctx.newCDPSession(p);
try { await cdp.send('Network.enable'); } catch (e) { log('Network.enable:', e.message); }
try { await cdp.send('Network.setCacheDisabled', { cacheDisabled: true }); log('  ✅ setCacheDisabled(true)'); } catch (e) { log('  setCacheDisabled 失败:', e.message); }
try { await cdp.send('Network.clearBrowserCache'); log('  ✅ clearBrowserCache'); } catch (e) { log('  clearBrowserCache 失败:', e.message); }
out.cdp = { cacheDisabled: true, cleared: true };

log('>>> 装拦截 + 强制重发');
await p.route((u) => u.href.includes(TOKEN), async (route) => { blocked++; log('  🚧 命中 #' + blocked); try { await route.abort('failed'); } catch (e) { /* noop */ } });
out.refetch = await refetch(SELF);
await p.waitForTimeout(5000);
out.step1 = await snap('1-缓存关掉后注入失败');
log('\n🔴 命中 =', blocked);

if (blocked > 0) {
  log('\n>>> 找「重试 / 失败」类控件');
  out.retry = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null;
    const all = Array.from(n.querySelectorAll('button,[role=button]')).map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), x: e.innerText.trim() }));
    const hit = all.find((e) => /重试|retry|重播|失败|重新/i.test((e.a || '') + e.x));
    return { all, hit: hit || null };
  }, SELF);
  log('控件清单：', JSON.stringify(out.retry, null, 1));
  log('\n>>> 分支 A：撤拦截 + 重发（可恢复？）');
  await p.unroute((u) => u.href.includes(TOKEN));
  out.refetchA = await refetch(SELF);
  await p.waitForTimeout(5000);
  out.step2 = await snap('2-撤拦截后重发');
}

out.blockedTotal = blocked;
out.reqSeen = seenReq;
try { await cdp.send('Network.setCacheDisabled', { cacheDisabled: false }); log('\n已恢复缓存设置'); } catch (e) { /* noop */ }
writeFileSync(new URL('./_tmp-b105g.json', import.meta.url), JSON.stringify(out, null, 1));
log('已落盘');
await b.close();
