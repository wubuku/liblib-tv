// 批次 105 · a 轮：造一个**有资源但播不了**的视频节点。
//
// 🎯 `media-playback.md:201` 挂着本页最后一项「未验证」：
//   「资源失效后的『重试播放』与空载态（需要一张会失效的素材，本轮未造）」。
//   而 117-133 行**已经把失效态该长什么样写成了表格**（控件齐全、时间读数 `00:00 / 00:00`、
//   卡片中央是失败态提示），却只有一句「异常态行为部分来自历史观察记录」——
//   🔴 **那张表是照着「历史观察」写的，从来没人造出过失效素材去对账。**
//
// 手法：不是去改 DOM 的 `src`（那是自欺欺人），而是**真造一张过不了解码的素材**——
//   `/tmp/jimeng-b105-garbage.mp4`：合法 `ftyp` 头（`file` 命令都认它是 ISO Media MP4）
//   + 1MB 伪随机字节。扩展名在批次 102 的 111 条白名单里、容器嗅探也过，
//   所以它能**真的走完上传通道**拿到 CDN 地址；只是 `<video>` 解不出帧 ⇒ 这才是
//   「资源在、但播不了」的真状态。
//
// 🔴 三重护栏（批次 97 事故后立的）：存 id 集合 → 差集**恰好一个**且**同时是 .selected**
//                              → 事后核对消失的 id **恰好只有 SELF**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const BAD = '/tmp/jimeng-b105-garbage.mp4';

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
out.creditsBefore = await credits();
log('上传前 id 数：', idsBefore.length, '｜积分', out.creditsBefore);

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('左栏上传入口：', JSON.stringify(rail));

let seen = null;
p.on('filechooser', async (fc) => {
  const info = await fc.element().evaluate((n) => ({
    acceptTokens: (n.getAttribute('accept') || '').split(',').length, multiple: n.hasAttribute('multiple') })).catch((e) => ({ err: e.message }));
  seen = { isMultiple: fc.isMultiple(), ...info };
  log('  filechooser：', JSON.stringify(seen));
  try { await fc.setFiles(BAD); log('  setFiles：', BAD); } catch (e) { log('  setFiles 失败：', e.message); }
});
if (rail.length) {
  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
}

let created = [];
for (let k = 1; k <= 30; k++) {
  await p.waitForTimeout(1500);
  const now = await allIds();
  created = now.filter((id) => !idsBefore.includes(id));
  if (created.length) { out.gotAtMs = k * 1500; break; }
}
const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const newSel = selIds.filter((id) => !idsBefore.includes(id));
out.guard = { before: idsBefore.length, after: (await allIds()).length, created, selIds, newSel };
log('护栏：', JSON.stringify(out.guard));
out.creditsAfter = await credits();
log('上传后积分：', out.creditsAfter, '（上传前', out.creditsBefore, '）');
out.chooser = seen;

const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
out.selfId = SELF;
log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');

if (SELF) {
  // 资源处理可能要一会儿（批次 64：图片要 5 秒以上）；这里连采样 8 次看它稳没稳
  await p.waitForTimeout(6000);
  const sample = async () => safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const r = n.getBoundingClientRect();
    const media = Array.from(n.querySelectorAll('video,audio')).map((e) => ({
      tag: e.tagName, paused: e.paused, dur: e.duration, ct: e.currentTime,
      rs: e.readyState, ns: e.networkState, err: e.error ? { code: e.error.code, msg: e.error.message } : null,
      src: (e.currentSrc || e.src || '').slice(0, 90) }));
    return { aria: n.getAttribute('aria-label'),
      screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 300),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      media, imgs: n.querySelectorAll('img').length, videoEls: n.querySelectorAll('video').length };
  }, SELF);
  out.t0 = await sample();
  log('\nSELF 结构（+6s）：', JSON.stringify(out.t0, null, 1));
  await p.waitForTimeout(8000);
  out.t1 = await sample();
  log('\nSELF 结构（+14s）：', JSON.stringify(out.t1, null, 1));
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('本轮终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b105a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
