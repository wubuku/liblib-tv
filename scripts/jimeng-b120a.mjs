// 批次 120 · a 轮：**底部状态行在 DOM 里到底是谁**（全册缺这一档）。
//
// 🔴 缺口：
//   - `00-quickstart.md` 的「界面分区速览」示意图里**画了**「底部状态行」，
//     但同一节的「界面清单」只列了左栏 / 底部 dock / 顶栏 / 右下角 / 缩放菜单
//     —— **状态行没有自己的条目**。
//   - `20-reference.md:23` 把状态行逐字抄下来了（`N nodes, N edges, N selected. Editable. Room connected. 已保存.`），
//     `20-reference.md:325` 还立了规矩「**判断连线数一律看状态行**」；
//     `navigate-canvas.md` / `connect-nodes.md` / `organize-group-layout.md` 至少 10 处拿它当判据。
//   - 但**全册从来没记过它的 testid、尺寸、位置、分段结构**，也没记过「怎么在 DOM 里找到它」。
//
// 📌 本轮要回答：
//   ① 用什么判据能从 DOM 里精确定位它？（文本反查 → 往上是哪个 testid/class？）
//   ② 它的矩形、层级、z-index、是否落在某个已知容器里？
//   ③ 逐字那段里 6 段（nodes / edges / selected / Editable / Room connected / 已保存）
//      是 6 个独立元素还是 1 个文本节点？
//   ④ 顺手清点全文档**不属于任何节点**的 chrome testid（批次 118 立规：
//      判「某个元素在不在」所有可能宿主都要扫）。
//
// ⛔ 本轮**纯只读**：不点任何按钮，不建任何节点，不改任何状态。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b120a.json', import.meta.url), JSON.stringify(out, null, 1));

const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const statusText = () => p.evaluate(() => (document.body.innerText.match(/[\d,]+ nodes?, [\d,]+ edges?, [\d,]+ selected\.[^\n]*/) || [])[0] || null);

out.start = { zoom: await zoom(), credits: await credits(), status: await statusText() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ============================================================
// ① 文本反查：谁的内含文本命中状态行那句？逐个祖先给出身份
// ============================================================
out.reverse = await p.evaluate(() => {
  const RE = /\d+ nodes?, \d+ edges?, \d+ selected\./;
  const hits = [];
  const all = document.querySelectorAll('body *');
  // 从最深命中往上收：只保留**最内层**的那些，再单独记它们的祖先链
  const inner = [];
  for (const e of all) {
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!RE.test(t)) continue;
    if (e.children.length && Array.from(e.children).some((c) => RE.test((c.textContent || '')))) continue; // 有更内层的命中 ⇒ 不是最内层
    inner.push(e);
  }
  const desc = (e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id || null,
      cls: (e.getAttribute('class') || '').toString().slice(0, 80), role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label'), lang: e.getAttribute('lang'),
      rect: [q.x, q.y, q.width, q.height].map(Math.round), z: cs.zIndex, pos: cs.position,
      自身可见: q.width > 0 && q.height > 0, 文字: (e.textContent || '').replace(/\s+/g, ' ').trim() }; };
  for (const e of inner) {
    const chain = []; let cur = e;
    for (let k = 0; k < 12 && cur && cur !== document.documentElement; k++) { chain.push(desc(cur)); cur = cur.parentElement; }
    hits.push(chain);
  }
  return { 最内层命中数: inner.length, 命中链: hits };
});
log('\n=== ① 文本反查（最内层命中 ' + out.reverse.最内层命中数 + ' 个）===');
out.reverse.命中链.forEach((chain, i) => {
  log(`\n-- 链 ${i + 1}（自内向外）--`);
  chain.forEach((d, k) => log(`  ${'  '.repeat(k)}${k === 0 ? '★ ' : ''}${d.tag} tid=${JSON.stringify(d.tid)} id=${JSON.stringify(d.id)} role=${JSON.stringify(d.role)} rect=${JSON.stringify(d.rect)} z=${d.z} pos=${d.pos} 可见=${d.自身可见}\n  ${'  '.repeat(k)}cls=${JSON.stringify(d.cls)}\n  ${'  '.repeat(k)}文字=${JSON.stringify(d.文字)}`));
});
save();

// ============================================================
// ② 逐段拆解：6 段是不是独立元素
// ============================================================
out.segments = await p.evaluate((RE) => {
  const re = new RegExp(RE);
  const all = Array.from(document.querySelectorAll('body *'));
  const inner = all.filter((e) => re.test((e.textContent || '').replace(/\s+/g, ' ')) && !(e.children.length && Array.from(e.children).some((c) => re.test((c.textContent || '')))));
  if (!inner.length) return { __err: 'no-hit' };
  const host = inner[0];
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const kids = (host) => Array.from(host.children).map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.getAttribute('class') || '').toString().slice(0, 60), rect: r(e), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim() }));
  // 往下钻到「再分就只剩纯文本」为止
  const deep = [];
  let cur = host;
  for (let k = 0; k < 5; k++) {
    deep.push({ 层: k, tag: cur.tagName, tid: cur.getAttribute('data-testid'), cls: (cur.getAttribute('class') || '').toString().slice(0, 60), 文字: (cur.textContent || '').replace(/\s+/g, ' ').trim(), 子元素数: cur.children.length, 子: kids(cur) });
    if (cur.children.length !== 1) break;
    cur = cur.firstElementChild;
  }
  return { hostRect: r(host), hostText: (host.textContent || '').replace(/\s+/g, ' ').trim(), deep };
}, '\\d+ nodes?, \\d+ edges?, \\d+ selected\\.');
log('\n=== ② 逐段拆解 ===');
if (out.segments.__err) log('  ', out.segments.__err);
else {
  out.segments.deep.forEach((L) => { log(`  层${L.层} <${L.tag}> tid=${JSON.stringify(L.tid)} 子元素数=${L.子元素数} rect=${JSON.stringify(L.rect || '')}`); log(`      cls=${JSON.stringify(L.cls)}`); log(`      文字=${JSON.stringify(L.文字)}`);
    L.子.forEach((c) => log(`        └ <${c.tag}> tid=${JSON.stringify(c.tid)} ${JSON.stringify(c.rect)} ${JSON.stringify(c.文字)}`)); });
}
save();

// ============================================================
// ③ 全文档 chrome testid 清点：不属于任何 .react-flow__node 的
// ============================================================
out.chrome = await p.evaluate(() => {
  const map = {};
  for (const e of document.querySelectorAll('[data-testid]')) {
    const inNode = !!e.closest('.react-flow__node');
    const q = e.getBoundingClientRect();
    const k = e.getAttribute('data-testid');
    (map[k] = map[k] || { 总数: 0, 节点内: 0, 节点外: [], 在节点外样例: null });
    map[k].总数++;
    if (inNode) map[k].节点内++;
    else { map[k].节点外.push([q.x, q.y, q.width, q.height].map(Math.round)); if (!map[k].在节点外样例) map[k].在节点外样例 = [q.x, q.y, q.width, q.height].map(Math.round); }
  }
  const list = Object.entries(map).map(([k, v]) => ({ tid: k, 总数: v.总数, 节点内: v.节点内, 节点外: v.节点外.length, 节点外矩形样例: v.在节点外样例 }))
    .sort((a, b) => b.总数 - a.总数);
  return { testid总数: list.length, 列表: list };
});
log('\n=== ③ 全文档 data-testid 清点（共 ' + out.chrome.testid总数 + ' 种，节点外单列）===');
out.chrome.列表.forEach((d) => log(`   ${String(d.总数).padStart(4)} (节点内 ${String(d.节点内).padStart(3)} / 节点外 ${String(d.节点外).padStart(2)})  ${d.tid}${d.节点外 ? '  ' + JSON.stringify(d.节点外矩形样例) : ''}`));
save();

// ============================================================
// ④ 落点自检：elementFromPoint 命中状态行内部？（同一次 evaluate 内现算）
// ============================================================
out.hitTest = await p.evaluate((RE) => {
  const re = new RegExp(RE);
  const all = Array.from(document.querySelectorAll('body *'));
  const host = all.find((e) => re.test((e.textContent || '').replace(/\s+/g, ' ')) && !(e.children.length && Array.from(e.children).some((c) => re.test((c.textContent || '')))));
  if (!host) return { __err: 'no-host' };
  const q = host.getBoundingClientRect();
  const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
  const el = document.elementFromPoint(cx, cy);
  return { 中心: [Math.round(cx), Math.round(cy)], 命中标签: el ? el.tagName + ' tid=' + el.getAttribute('data-testid') : null,
    命中即目标: el === host, 命中被目标包含: host.contains(el), 命中文字: el ? (el.textContent || '').replace(/\s+/g, ' ').trim() : null };
}, '\\d+ nodes?, \\d+ edges?, \\d+ selected\\.');
log('\n=== ④ 落点自检 ===');
log('  ', JSON.stringify(out.hitTest));
save();

out.end = { zoom: await zoom(), credits: await credits(), status: await statusText() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
