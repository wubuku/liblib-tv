// 批次 105 · b 轮：盯住那张「不可解码但已收下」的素材，看 `processing` 会不会走到 `failed`。
//
// a 轮的重大发现（手册里从来没写过第三种状态）：
//   🔴 节点 `innerText` 逐字是
//      **`jimeng-b105-garbage 1 resource: 0 ready, 1 processing, 0 failed. Selected.`**
//      —— 这串 **resource: x ready, y processing, z failed** 是节点自报的资源账，
//      比「有没有 `<video>`」更早一步告诉你资源处在哪一步。
//      `media-playback.md` 124-133 行那张表只分了**两**栏（空节点 / 资源失效），
//      🔴 **漏了中间这一档：资源已收下、正在处理、播不了**。
//   此刻 testid 是 `video-node-uploading`、aria「正在处理上传内容…」、
//   `<video>` 0 个、`img` 0 个、节点里**唯一**的 button 是 `Rename …`。
//
// 🔴 本轮自己踩的两个坑，写在注释里免得下批再踩：
//   ① 停止条件写 `/failed/` 会被账本里的 **`0 failed`** 误命中 ⇒ 第一版 k=0 就停了。
//      必须先把数字取出来再比大小。
//   ② 30 次 × 10s 超过了后台 300s 上限，而且 `| tail` 会把 stdout 全缓冲到进程结束
//      ⇒ 进程被砍，一行都没留下。改为**每采一次就落盘**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const FILE = new URL('./_tmp-b105b.json', import.meta.url);
const out = { at: new Date().toISOString(), selfId: 'node_p0brqdj8z0', series: [] };
const SELF = out.selfId;
const save = () => writeFileSync(FILE, JSON.stringify(out, null, 1));

const snap = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  return {
    t: new Date().toISOString().slice(11, 19),
    text: n.innerText.replace(/\s+/g, ' ').trim(),
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    video: Array.from(n.querySelectorAll('video')).map((e) => ({ rs: e.readyState, dur: e.duration, err: e.error ? e.error.code : null })),
    img: n.querySelectorAll('img').length,
    btns: Array.from(n.querySelectorAll('button')).map((e) => (e.getAttribute('aria-label') || e.innerText || '').trim()).filter(Boolean).slice(0, 20),
  };
}, SELF);

const ITER = 12, EVERY = 14_000;
for (let k = 0; k < ITER; k++) {
  const s = await snap();
  s.k = k;
  const m = (s.text || '').match(/(\d+) resource: (\d+) ready, (\d+) processing, (\d+) failed/);
  s.ledger = m ? { res: +m[1], ready: +m[2], processing: +m[3], failed: +m[4] } : null;
  out.series.push(s);
  save();
  log(`[${s.t}] k=${k} 账本=${JSON.stringify(s.ledger)} video=${s.video.length} img=${s.img} testid=${s.testids.find((x) => /upload|play|error|fail/i.test(x)) || '-'} text="${(s.text || '').slice(0, 100)}"`);
  if ((s.ledger && (s.ledger.ready || s.ledger.failed)) || s.video.length) { log('  ⇒ 状态已变'); break; }
  await p.waitForTimeout(EVERY);
}
out.final = out.series[out.series.length - 1];
log('\n最后读数：', JSON.stringify(out.final, null, 1));
save();
await b.close();
