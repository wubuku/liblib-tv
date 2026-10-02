// 批次 113 · c 轮诊断 2：**只读**。上一轮查明 `.tiptap.ProseMirror`（`646×28@117,529`）
// 内部按 5px 网格打 `elementFromPoint`，1661 次落在 `SPAN`、535 次落在它自己的父容器
// `DIV.relative.col-start-1` 上，而编辑器自己的子元素只有 `P` + `BR`。
// ⇒ 有个 **SPAN 盖在编辑器上面**。这一轮把这个 SPAN 的完整祖先链、几何、来源问出来。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c-diag2' };
const save = () => writeFileSync(new URL('./_tmp-b113cdiag2.json', import.meta.url), JSON.stringify(out, null, 1));

out.spanProbe = await p.evaluate(() => {
  const e = document.querySelector('.tiptap.ProseMirror');
  const r = e.getBoundingClientRect();
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
  const hit = document.elementFromPoint(cx, cy);
  const o = { editorRect: [r.x, r.y, r.width, r.height].map(Math.round), at: [cx, cy], hit: null, chain: [], sameAsEditor: false };
  if (!hit) return o;
  const tag = (n) => n.tagName + (n.getAttribute('data-testid') ? '#' + n.getAttribute('data-testid') : '')
    + (n.getAttribute('aria-label') ? '[' + n.getAttribute('aria-label') + ']' : '')
    + (n.getAttribute('class') ? '.' + n.getAttribute('class').toString().split(' ').slice(0, 3).join('.') : '');
  o.hit = tag(hit);
  o.sameAsEditor = hit === e || e.contains(hit);
  let n = hit; let d = 0;
  while (n && d++ < 30) { const b = n.getBoundingClientRect(); const cs = getComputedStyle(n);
    o.chain.push({ d, el: tag(n).slice(0, 90), rect: [b.x, b.y, b.width, b.height].map(Math.round),
      pe: cs.pointerEvents, pos: cs.position, z: cs.zIndex, ov: cs.overflow, op: cs.opacity,
      parentIsEditor: n.parentElement === e || (e.contains(n.parentElement)),
      inToolbar: !!n.closest('[data-testid="node-toolbar"]'), inNode: !!n.closest('.react-flow__node') });
    n = n.parentElement; }
  // 编辑器里有没有任何一点能命中自己
  let selfHits = 0, tried = 0; const miss = [];
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 1)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 3) { tried++;
      const el = document.elementFromPoint(x, y);
      if (el && (el === e || e.contains(el))) selfHits++; else if (miss.length < 6) miss.push([x, y, el ? tag(el).slice(0, 60) : '(null)']); }
  o.selfHits = selfHits; o.tried = tried; o.missSamples = miss;
  // 覆盖层的兄弟：在 editor 父容器里，与编辑器同级、且矩形与编辑器相交的元素
  const pr = e.parentElement;
  o.siblings = Array.from(pr.children).map((c) => { const cb = c.getBoundingClientRect();
    return { el: tag(c).slice(0, 80), rect: [cb.x, cb.y, cb.width, cb.height].map(Math.round),
      overlap: !(cb.right < r.left || cb.left > r.right || cb.bottom < r.top || cb.top > r.bottom),
      pe: getComputedStyle(c).pointerEvents, pos: getComputedStyle(c).position, z: getComputedStyle(c).zIndex }; });
  return o;
});
log('编辑器 rect =', JSON.stringify(out.spanProbe.editorRect), '｜中心', JSON.stringify(out.spanProbe.at));
log('中心命中 =', out.spanProbe.hit, '｜是编辑器自己吗 =', out.spanProbe.sameAsEditor);
log(`\n自命中点：${out.spanProbe.selfHits} / ${out.spanProbe.tried}（步长 1×3）`);
log('打不中的样本：'); (out.spanProbe.missSamples || []).forEach((m) => log('   ' + JSON.stringify(m)));
log('\n命中元素的祖先链：');
(out.spanProbe.chain || []).forEach((c) => log(`   d=${c.d} ${JSON.stringify(c)}`));
log('\n编辑器的兄弟元素：');
(out.spanProbe.siblings || []).forEach((c) => log('   ' + JSON.stringify(c)));
save();
log('\nDONE diag2');
process.exit(0);
