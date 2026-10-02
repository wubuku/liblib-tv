// 批次 105 · c 轮：再造一个**能正常播**的视频节点，作为故障注入的靶子。
//
// 为什么还要再造一个：a 轮那张「不可解码的垃圾 mp4」根本没走到能播的那一步——
// 它**永远停在 `processing`**（12:57 上传 → 13:08 十一分钟，账本逐位不动：
//   `1 resource: 0 ready, 1 processing, 0 failed`，
//   testid 恒为 `video-node-uploading`、aria 恒为「正在处理上传内容…」、
//   `<video>` 0 个、`img` 0 个、节点里唯一的 button 是 `Rename …`）。
// ⇒ 它是**第三种状态**，不是手册 124-133 行那张表里的「资源失效」。
//   「失效」那栏要的是**曾经 ready、后来请求失败**，所以必须先有一个 ready 的节点。
//
// 素材：复用批次 101 那支 6 秒 H.264（640×360/25fps，**上传免费**，805 → 805）。
//
// 🔴 三重护栏：存 id 集合 → 差集**恰好一个**且**同时是 .selected** → 事后核对消失的 id 恰好只有 SELF。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const GOOD = '/tmp/jimeng-b101-test-avc1.mp4';

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

let seen = null;
p.on('filechooser', async (fc) => {
  seen = { isMultiple: fc.isMultiple() };
  try { await fc.setFiles(GOOD); log('  setFiles：', GOOD); } catch (e) { log('  setFiles 失败：', e.message); }
});
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
if (!rail.length) { log('🔴 找不到上传入口'); writeFileSync(new URL('./_tmp-b105c.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
const r0 = rail[0];
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

let created = [];
for (let k = 1; k <= 30; k++) {
  await p.waitForTimeout(1500);
  created = (await allIds()).filter((id) => !idsBefore.includes(id));
  if (created.length) { out.gotAtMs = k * 1500; break; }
}
const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const newSel = selIds.filter((id) => !idsBefore.includes(id));
out.guard = { before: idsBefore.length, after: (await allIds()).length, created, selIds, newSel };
log('护栏：', JSON.stringify(out.guard));
out.creditsAfter = await credits();
log('上传后积分：', out.creditsAfter, '（上传前', out.creditsBefore, '）');

const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
out.selfId = SELF;
out.chooser = seen;
log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');

if (SELF) {
  // 等 ready（批次 101：资源要几秒到几十秒不等，这里按账本轮询而不是死等）
  const snap = () => safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const v = n.querySelector('video');
    return { text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      video: v ? { rs: v.readyState, dur: v.duration, ct: v.currentTime, paused: v.paused, err: v.error ? v.error.code : null,
        src: (v.currentSrc || v.src || '') } : null };
  }, SELF);
  for (let k = 0; k < 16; k++) {
    const s = await snap();
    const m = (s.text || '').match(/(\d+) resource: (\d+) ready, (\d+) processing, (\d+) failed/);
    s.ledger = m ? { ready: +m[2], processing: +m[3], failed: +m[4] } : null;
    out['poll' + k] = s;
    log(`  轮 ${k} 账本=${JSON.stringify(s.ledger)} video=${s.video ? `rs=${s.video.rs} dur=${s.video.dur}` : 'null'}`);
    if (s.video && s.video.dur) { log('  ⇒ ready'); break; }
    await p.waitForTimeout(6000);
  }
  const fin = await snap();
  out.final = fin;
  log('\n靶子节点读数：', JSON.stringify(fin, null, 1));
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('本轮终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b105c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
