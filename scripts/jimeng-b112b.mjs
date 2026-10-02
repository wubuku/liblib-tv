// 批次 112 · b 轮：把 a 轮撞出来的**「预览不可用」**这一档读全，并修正 a 轮那个错的判据。
//
// a 轮的四格结果（**没有造出 `failed`**）：
//   ① 0 字节 png        ⇒ **连节点都没建出来**（客户端就拒了）
//   ② 纯文本改 .png      ⇒ **连节点都没建出来**
//   ③ 截断 png（33 字节）⇒ 建出节点，最终落到 **「预览不可用」**（新档位！）
//   ④ CRC 合法、IDAT 垃圾 ⇒ 资源账 **`1 ready`**，`imgs: 1`，正常渲染 ⇒ **服务端容忍了**
//
// 🔴🔴 a 轮自己的判据错了 14 次：`ledger()` 只读 `n.innerText`，
//   而**图片节点的资源账不在 `innerText` 里**，它在 **`aria-label`** 上：
//   a 轮读到的 `1 resource: 1 ready, 0 processing, 0 failed.` **全部来自 aria**。
//   ⇒ 「读数为 null」又是判据的问题，**不是产品没有账**。
//   📌 **同一个字段名，在不同节点类型上落在不同的属性里** —— 必须逐类型验过才知道读哪儿。
//
// 本轮两件事：
//   ① 用**正确的判据**（`aria-label` 优先，回落 `innerText`）重测截断 png
//   ② 把「预览不可用」这一档读全，并测它的 **「重试」** 按钮
//      （对应批次 110 的「重试播放」：**它会不会改资源账**？）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b112b.json', import.meta.url), JSON.stringify(out, null, 1));

const FILE = '/tmp/jimeng-b112-truncated.png';
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// ✅ 修正后的判据：**aria-label 优先，回落 innerText**；先取数字再比大小
const readNode = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const inner = (n.innerText || '').replace(/\s+/g, ' ').trim();
  // 节点根上的 aria 与内部所有 aria 全都看一眼，账在哪就取哪
  const allAria = [n.getAttribute('aria-label'), ...Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label'))]
    .filter(Boolean).map((s) => s.replace(/\s+/g, ' ').trim());
  const ledgerRe = /(\d+) resources?: (\d+) ready, (\d+) processing, (\d+) failed/;
  let src = null, m = null;
  for (const a of allAria) { const mm = a.match(ledgerRe); if (mm) { src = 'aria'; m = mm; break; } }
  if (!m) { const mi = inner.match(ledgerRe); if (mi) { src = 'innerText'; m = mi; } }
  const btn = (re) => { for (const x of n.querySelectorAll('button')) { const ar = x.getAttribute('aria-label') || '';
    if (re.test(ar)) { const br = x.getBoundingClientRect();
      return { aria: ar, x: Math.round(br.x + br.width / 2), y: Math.round(br.y + br.height / 2),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; } } return null; };
  return {
    cls: n.className, rootAria: n.getAttribute('aria-label'),
    innerText: inner.slice(0, 200),
    ledgerSource: src,
    n: m ? m[1] : null, ready: m ? Number(m[2]) : null, processing: m ? Number(m[3]) : null, failed: m ? Number(m[4]) : null,
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(allAria)),
    buttons: Array.from(n.querySelectorAll('button')).map((x) => { const br = x.getBoundingClientRect();
      return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; }),
    imgs: n.querySelectorAll('img').length,
    previewUnavailable: !!n.querySelector('[data-testid="image-preview-unavailable"]'),
    previewEl: (() => { const e = n.querySelector('[data-testid="image-preview-unavailable"]');
      if (!e) return null; const br = e.getBoundingClientRect();
      return { text: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(),
        html: e.outerHTML.slice(0, 420),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; })(),
    retryBtn: btn(/^Retry |^重试/), replaceBtn: btn(/^替换媒体/),
  };
}, id);

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const idsBefore = await allIds();
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0)[0] || null);
if (!rail) { log('🔴 找不到上传入口'); await b.close(); process.exit(3); }
const onFc = async (fc) => { try { await fc.setFiles(FILE); } catch (e) { log('  setFiles 失败：', e.message); } };
p.on('filechooser', onFc);
await p.mouse.move(rail.x + rail.w / 2, rail.y + rail.h / 2); await p.waitForTimeout(500);
await p.mouse.click(rail.x + rail.w / 2, rail.y + rail.h / 2);
// 🔴 **不要在这里 `p.off`** —— `filechooser` 事件是**异步**触发的，
//    摘早了监听器就永远收不到，`setFiles` 不会执行 ⇒ 一个节点都建不出来。
//    （第一版就栽在这一格：差集恒空，读成「截断 png 建不出节点」，而 a 轮明明建出来了。）
let SELF = null;
for (let k = 1; k <= 14; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length) { SELF = diff[0]; log(`#${k} 差集 = ${JSON.stringify(diff)}`); break; }
}
p.off('filechooser', onFc);
const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
out.self = SELF; out.selIds = selIds;
out.guardrail2 = { diffN: SELF ? 1 : 0, ok: !!SELF && selIds.includes(SELF) };
log('SELF =', SELF, '｜护栏② =', out.guardrail2.ok);
save();
if (!SELF) { log('🔴 没建出节点 ⇒ 中止'); await b.close(); process.exit(3); }

// ---- 连采，看它怎么从「正常」走到「预览不可用」 ----
out.samples = [];
const t0 = Date.now();
for (let k = 1; k <= 20; k++) {
  await p.waitForTimeout(1200);
  const s = await readNode(SELF);
  out.samples.push({ k, ms: Date.now() - t0, src: s.ledgerSource, ready: s.ready, processing: s.processing, failed: s.failed,
    imgs: s.imgs, previewUnavailable: s.previewUnavailable, innerText: s.innerText,
    arias: s.arias, testids: s.testids, screen: s.screen });
  log(`  #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms  账源=${s.ledgerSource} ready=${s.ready} processing=${s.processing} failed=${s.failed} imgs=${s.imgs} 预览不可用=${s.previewUnavailable}`);
  log(`        文字="${s.innerText}"`);
  save();
  if (s.previewUnavailable) { out.reachedAt = Date.now() - t0; log('  ⇒ 进入「预览不可用」'); break; }
}
out.settled = await readNode(SELF);
log('\n=== 「预览不可用」这一档的完整读数 ===');
log(JSON.stringify(out.settled, null, 1));
save();
await p.screenshot({ path: '/tmp/b112-b-preview-unavailable.png' });
log('\n截图 /tmp/b112-b-preview-unavailable.png');
save();

// ---- 测它的「重试」按钮（对应批次 110 的「重试播放」：会不会改资源账？） ----
const rb = out.settled.retryBtn;
out.retry = { btn: rb };
if (!rb) { log('\n⚠️ 没有「重试」按钮 ⇒ 跳过'); }
else {
  log(`\n=== 点「重试」${JSON.stringify(rb.aria)} ===`);
  const g2 = await keyGuard(p);
  log('焦点守卫：', g2.safe ? '✅' : '⛔', g2.where || '');
  if (g2.safe) {
    out.retry.before = { ready: out.settled.ready, failed: out.settled.failed, imgs: out.settled.imgs, previewUnavailable: out.settled.previewUnavailable };
    await p.mouse.move(rb.x, rb.y); await p.waitForTimeout(400);
    await p.mouse.click(rb.x, rb.y);
    out.retry.samples = [];
    for (let k = 1; k <= 12; k++) {
      await p.waitForTimeout(1200);
      const s = await readNode(SELF);
      out.retry.samples.push({ k, ms: k * 1200, ready: s.ready, processing: s.processing, failed: s.failed, imgs: s.imgs,
        previewUnavailable: s.previewUnavailable, innerText: s.innerText, testids: s.testids });
      log(`  #${String(k).padStart(2)} ready=${s.ready} failed=${s.failed} imgs=${s.imgs} 预览不可用=${s.previewUnavailable}｜"${s.innerText}"`);
      save();
    }
    out.retry.after = await readNode(SELF);
    log('\n=== 重试后 ===');
    log(JSON.stringify({ ready: out.retry.after.ready, failed: out.retry.after.failed, imgs: out.retry.after.imgs,
      previewUnavailable: out.retry.after.previewUnavailable, innerText: out.retry.after.innerText,
      testids: out.retry.after.testids }, null, 1));
    save();
    await p.screenshot({ path: '/tmp/b112-b-after-retry.png' });
    log('截图 /tmp/b112-b-after-retry.png');
  }
}
out.selfId = SELF;
out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE b（z 轮再删节点）');
process.exit(0);
