// 批次 113 · c 轮前置诊断：**只读，不点任何东西**。
// 现象：`.tiptap.ProseMirror` 可见（`646×28@117,529`），
//      但在它内部按 5px 网格打 `elementFromPoint` 打不中自己 ⇒ 必有东西盖在上面。
// 要查清：盖住它的是什么、`pointer-events` 是什么链、真正能点进去的坐标在哪。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c-diag' };
const save = () => writeFileSync(new URL('./_tmp-b113cdiag.json', import.meta.url), JSON.stringify(out, null, 1));

out.probe = await p.evaluate(() => {
  const e = document.querySelector('.tiptap.ProseMirror');
  if (!e) return { __err: 'no-editor' };
  const r = e.getBoundingClientRect();
  const o = { rect: [r.x, r.y, r.width, r.height].map(Math.round), hits: {}, chain: [] };
  // 命中统计
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 4) {
      const el = document.elementFromPoint(x, y);
      if (!el) { o.hits['(null)'] = (o.hits['(null)'] || 0) + 1; continue; }
      const t = el.tagName + (el.getAttribute('data-testid') ? '#' + el.getAttribute('data-testid') : '')
        + (el.getAttribute('aria-label') ? '[' + el.getAttribute('aria-label') + ']' : '')
        + '.' + ((el.getAttribute('class') || '').toString().split(' ').slice(0, 2).join('.'));
      o.hits[t] = (o.hits[t] || 0) + 1;
    }
  // 自己这一串的 pointer-events
  const chain = []; let n = e;
  while (n && n !== document.body) { const cs = getComputedStyle(n);
    chain.push({ tag: n.tagName, tid: n.getAttribute('data-testid'), cls: (n.getAttribute('class') || '').toString().slice(0, 40),
      pe: cs.pointerEvents, ov: cs.overflow, z: cs.zIndex, pos: cs.position, ad: n.getAttribute('aria-disabled') });
    n = n.parentElement; }
  o.chain = chain;
  // 自己内部的子元素与它们占的范围
  o.kids = Array.from(e.querySelectorAll('*')).map((k) => { const kr = k.getBoundingClientRect();
    const cs = getComputedStyle(k);
    return { tag: k.tagName, tid: k.getAttribute('data-testid'), cls: (k.getAttribute('class') || '').toString().slice(0, 34),
      rect: [kr.x, kr.y, kr.width, kr.height].map(Math.round), pe: cs.pointerEvents, txt: (k.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; });
  // 提示词输入区这一行的其它控件（谁在 529..557 这个 y 带里）
  o.band = [];
  for (const el of document.querySelectorAll('button,[role=button],[aria-label],[data-testid]')) {
    const br = el.getBoundingClientRect();
    if (br.width < 1 || br.height < 1) continue;
    if (br.top < r.y - 6 || br.top > r.y + r.height + 6) continue;
    if (br.right < r.x || br.left > r.x + r.width) continue;
    o.band.push({ tag: el.tagName, tid: el.getAttribute('data-testid'), aria: el.getAttribute('aria-label'),
      rect: [br.x, br.y, br.width, br.height].map(Math.round), pe: getComputedStyle(el).pointerEvents,
      hitAt: (() => { const h = document.elementFromPoint(Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2));
        return h ? h.tagName + (h.getAttribute('data-testid') ? '#' + h.getAttribute('data-testid') : '') : null; })() });
  }
  return o;
});
log('rect =', JSON.stringify(out.probe.rect));
log('\n命中统计（elementFromPoint 落在谁身上）：');
Object.entries(out.probe.hits).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => log(`   ${String(v).padStart(4)}  ${k}`));
log('\n自己这一串的 pointer-events 链：');
out.probe.chain.forEach((c) => log('   ' + JSON.stringify(c)));
log('\n内部子元素：');
out.probe.kids.forEach((k) => log('   ' + JSON.stringify(k)));
log('\n同 y 带里的其它控件（谁在抢）：');
out.probe.band.forEach((k) => log('   ' + JSON.stringify(k)));
save();
log('\nDONE diag');
process.exit(0);
