// 批次 120 · c 轮：钉死「状态行」到底是什么。
//
// a/b 两轮已经拿到的事实：
//   · 那句 `N nodes, N edges, N selected. Editable. Room connected. 已保存.`
//     在**全文档只有一个宿主**：`SPAN#:modern-js-r1:`，class **`sr-only`**、
//     rect **`[-1,-1,1,1]`**、`clip: rect(0px,0px,0px,0px)`、`position:absolute`
//   · 它**没有任何 `aria-live` / `role=status`**（自己和 5 层祖先全 null）
//   · 全文档 171 种 testid 里**没有底部状态行**；底部只有 dock 4 项 + 侧边 launcher + 小地图 portal
//   · 两条**不共享假设**的旁证都看不到可见状态行：
//     本轮实时截图（y 660–720 条带）＋ 批次早期真实截图 `09-connect-nodes-edge-created.png` 底部 150px
//
// 🔑 c 轮要钉的四件事：
//   ① `:modern-js-r1:` 的文字**会不会随画布状态变**？选一个节点 → 读 → 取消选中 → 读。
//   ② `navigate-canvas.md:307` 那句「提示条存在时**状态行末尾多出**两行」——
//      多出来的到底是「状态行长了」还是**两个 sr-only 元素被 innerText 拼在了一起**？
//      ⇒ 同轮读三条互不相同的读数：`:modern-js-r1:` 自身 textContent /
//        `back-to-content-overlay` 自身 innerText / `document.body.innerText`。
//   ③ 提示条元素与状态行元素**是不是同一个祖先**、谁包含谁。
//   ④ 选中态下底部条带会不会**长出**一个可见状态行？（不成立也得有读数）
//
// ⛔ 只读 + 一次「选中→取消选中」往返；不建节点、不改任何持久状态。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b120c.json', import.meta.url), JSON.stringify(out, null, 1));
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));

// ---- 三条互不相同的读数，一次 evaluate 全拿 ----
const triple = () => p.evaluate(() => {
  const r1 = document.getElementById(':modern-js-r1:');
  const hint = document.querySelector('[data-testid="back-to-content-overlay"]');
  const main = document.querySelector('[aria-label="Canvas workspace"]');
  const txt = (e) => (e ? (e.textContent || '').replace(/\s+/g, ' ').trim() : null);
  const inr = (e) => (e ? (e.innerText || '').replace(/\s+/g, ' ').trim() : null);
  const cs = hint ? getComputedStyle(hint) : null;
  return {
    'r1.textContent': txt(r1),
    'hint.innerText': inr(hint),
    'hint.textContent': txt(hint),
    'MAIN.innerText': inr(main),
    'body.innerText 命中': (document.body.innerText.match(/[\d,]+ nodes?, [\d,]+ edges?, [\d,]+ selected\.[^\n]*/) || [])[0] || null,
    'body.innerText 含提示条': /当前视窗没有内容/.test(document.body.innerText),
    'MAIN.innerText 含提示条': /当前视窗没有内容/.test(inr(main) || ''),
    hint样式: cs ? { display: cs.display, visibility: cs.visibility, opacity: cs.opacity, position: cs.position, clip: cs.clip, pointerEvents: cs.pointerEvents } : null,
    hint矩形: hint ? (() => { const q = hint.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); })() : null,
    包含关系: { r1在hint内: hint ? hint.contains(r1) : null, hint在r1内: r1 ? r1.contains(hint) : null,
      r1在MAIN内: main ? main.contains(r1) : null, hint在MAIN内: main ? main.contains(hint) : null,
      r1与hint共同祖先: (() => { let cur = r1; while (cur && !(hint && cur.contains(hint))) cur = cur.parentElement; return cur ? (cur.tagName + ' tid=' + cur.getAttribute('data-testid')) : null; })() },
  };
});

const bottomVisible = () => p.evaluate(() => {
  const hits = [];
  for (const e of document.querySelectorAll('body *')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!/nodes?, \d+ edges?/.test(t)) continue;
    const q = e.getBoundingClientRect();
    if (!q.width || !q.height) continue;
    const cs = getComputedStyle(e);
    hits.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id || null, cls: (e.getAttribute('class') || '').toString().slice(0, 50),
      rect: [q.x, q.y, q.width, q.height].map(Math.round), 可见: cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.01,
      文字: t.slice(0, 70) });
  }
  // 只留最内层，避免整片祖先链刷屏
  return hits.filter((x) => !hits.some((y) => y !== x && y.rect[2] >= x.rect[2] && y.rect[3] >= x.rect[3] && y.rect[0] <= x.rect[0] && y.rect[1] <= x.rect[1]));
});

// ============================================================
out.start = { zoom: await zoom(), credits: await credits() };
out.t0 = await triple();
out.vis0 = await bottomVisible();
log('起点：', JSON.stringify(out.start));
log('\n=== ① 选中的时候 ===');
for (const [k, v] of Object.entries(out.t0)) log(`   ${k.padEnd(22)} ${JSON.stringify(v)}`);
log('   可见的含 nodes/edges 文字的元素：', JSON.stringify(out.vis0));
save();

// ============================================================
// 选一个节点 → 再读一次（三条读数 + 底部可见元素）
// ============================================================
// 落点现算：找一个**当前在视口内**、且点它不会触发扣费/生成的节点
out.pick = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('.react-flow__node[data-id]')).filter((n) => {
    const q = n.getBoundingClientRect();
    return q.width > 30 && q.height > 20 && q.left >= 0 && q.top >= 60 && q.right <= 1280 && q.bottom <= 640;
  });
  for (const n of cands) {
    const q = n.getBoundingClientRect();
    const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
    const el = document.elementFromPoint(cx, cy);
    if (el && (el === n || n.contains(el))) return { id: n.getAttribute('data-id'), 落点: [Math.round(cx), Math.round(cy)], 命中: el.tagName, 标题: (n.innerText || '').split('\n')[0] };
  }
  return null;
});
log('\n落点（现算 + elementFromPoint 自检）：', JSON.stringify(out.pick));
if (!out.pick) { log('⛔ 视口内没有可用落点，中止'); await b.close(); process.exit(3); }

await p.mouse.click(out.pick.落点[0], out.pick.落点[1]);
await p.waitForTimeout(1400);
out.t1 = await triple();
out.vis1 = await bottomVisible();
out.sel1 = await p.evaluate(() => (document.body.innerText.match(/[\d,]+ nodes?, [\d,]+ edges?, (\d+) selected\./) || [])[1]);
log('\n=== ② 选中「' + out.pick.标题 + '」之后（selected=' + out.sel1 + '）===');
for (const [k, v] of Object.entries(out.t1)) log(`   ${k.padEnd(22)} ${JSON.stringify(v)}`);
log('   可见的含 nodes/edges 文字的元素：', JSON.stringify(out.vis1));
log('   文本变化？ r1：', out.t0['r1.textContent'] !== out.t1['r1.textContent'] ? '变了' : '没变');
save();

// 取消选中
await p.mouse.click(24, 400); // 空白处（左栏右侧、dock 上方）——先自检落点
const blankOk = await p.evaluate((xy) => { const e = document.elementFromPoint(xy[0], xy[1]); return e ? e.className.toString().slice(0, 50) : null; }, [24, 400]);
log('\n取消选中的落点命中：', JSON.stringify(blankOk));
await p.waitForTimeout(1200);
out.t2 = await triple();
out.sel2 = await p.evaluate(() => (document.body.innerText.match(/[\d,]+ nodes?, [\d,]+ edges?, (\d+) selected\./) || [])[1]);
log('\n=== ③ 取消选中之后（selected=' + out.sel2 + '）===');
for (const [k, v] of Object.entries(out.t2)) log(`   ${k.padEnd(22)} ${JSON.stringify(v)}`);
save();

out.end = { zoom: await zoom(), credits: await credits(), sel: out.sel2 };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
