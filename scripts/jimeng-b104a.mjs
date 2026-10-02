// 批次 104 · a 轮：上传一个 `.wav`，造出**带媒体的音频节点**。
//
// 🎯 这正是批次 101 在视频侧做过一遍的事，而且**这一页把同一个错又犯了一遍**：
//   `audio-node-voice.md` 第 289-290 行写「造出带媒体的音频节点**需要生成、属扣费边界**，
//   本手册未执行」，
//   第 325 行把「**有媒体音频节点的波形与播放控件**」列为未验证。
//   🔴 **但根本不需要生成** —— 批次 102 刚测出 `accept` 白名单里有 **17 种音频扩展名**
//      （`mp3` `m4a` `wav` `flac` `aac` `wma` …），**上传通道一样能建出带媒体的音频节点**，
//      而上传**免费**。
//   ⇒ 「需要生成」被当成了「必须扣费」，实际是**素材限制**。和批次 101 一模一样的错。
//
// 素材：脚本现造的 4 秒单声道 WAV（44100Hz / 16bit）。
// 内容是**为肉眼/读数判据设计的**：每秒一段、段内 0.44s 有声 0.56s 静音，共 4 段，
// 且**四段的基频不同**（440 / 523 / 587 / 659 Hz）⇒
//   · 波形上能一眼数出走到了第几段
//   · 时间读数与 `currentTime` 可逐档互校
//
// 🔴 三重护栏（批次 97 事故后立的）：删前 id 集合 → 差集**恰好一个**且**同时是 .selected**
//                              → 事后核对消失的 id **恰好只有 SELF**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const WAV = '/tmp/jimeng-b104-test.wav';

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
out.creditsBefore = await credits();
log('上传前 id 数：', idsBefore.length, '｜积分', out.creditsBefore);

// ---- 触发 filechooser：必须用全局 on（批次 102 结论） ----
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('左栏上传入口：', JSON.stringify(rail));
if (!rail.length) { log('🔴 找不到上传入口'); writeFileSync(new URL('./_tmp-b104a.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

let seen = null;
p.on('filechooser', async (fc) => {
  const info = await fc.element().evaluate((n) => ({
    acceptTokens: (n.getAttribute('accept') || '').split(',').length, multiple: n.hasAttribute('multiple') })).catch((e) => ({ err: e.message }));
  seen = { isMultiple: fc.isMultiple(), ...info };
  log('  filechooser：', JSON.stringify(seen));
  try { await fc.setFiles(WAV); log('  setFiles：', WAV); } catch (e) { log('  setFiles 失败：', e.message); }
});
const r0 = rail[0];
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

let created = [];
for (let k = 1; k <= 24; k++) {
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
  // 等资源处理完再读结构（批次 64：图片要 5 秒以上）
  await p.waitForTimeout(4000);
  out.selfInfo = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'node-null' };
    const r = n.getBoundingClientRect();
    return { aria: n.getAttribute('aria-label'), cls: n.className, transform: n.style.transform,
      screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      media: Array.from(n.querySelectorAll('audio,video')).map((e) => ({ tag: e.tagName, paused: e.paused,
        dur: e.duration, ct: e.currentTime, muted: e.muted, vol: e.volume, src: (e.currentSrc || e.src || '').slice(0, 60) })),
      canvasEls: Array.from(n.querySelectorAll('canvas')).length,
      svgs: Array.from(n.querySelectorAll('svg')).length };
  }, SELF);
  log('\nSELF 结构：', JSON.stringify(out.selfInfo, null, 1));
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('本轮终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b104a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
