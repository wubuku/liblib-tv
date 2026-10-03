// 批次 142 诊断：组卡片的**标题可点区**现在到底在哪 / 为什么扫不到。
//
// 🔴 救援脚本（`jimeng-b139-rescue.mjs`）的解组步骤卡住了：标题落点扫描返回
//   `no-title-point` ⇒ **组清不掉、成员也删不掉**（共享画布上留了 1 组 + 78 节点）。
//   两个可疑点：
//   ① `document.querySelector('.react-flow__node-group')` **可能返回影子** ——
//      影子带 `pointer-events: none`、没有标题，点它当然没反应（批次 139 已记：一个组匹配 2 个元素）。
//   ② 标题行在卡片**上沿之外约 28px**，若被顶栏遮住或卡片在视口下缘，扫不到。
// 本轮把这两件事分开量，并把标题周围一圈的命中物全部 dump 出来。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = {};
try {
  await keyGuard(p);
  await settle(p, R);
  rec.状态行 = await R.status();
  rec.zoom = await R.zoom();
  rec.视口 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));

  rec.组元素 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group')).map((g) => {
    const r = g.getBoundingClientRect(); const s = getComputedStyle(g);
    return { id: g.getAttribute('data-id'), 是影子: /^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      pe: s.pointerEvents, zIndex: s.zIndex, 逐字: (g.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
  }));

  // 标题带候选：真身 + 其内所有非空文本子元素
  rec.标题候选 = await p.evaluate(() => {
    const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
    if (!g) return { __err: 'no-真身' };
    const r = g.getBoundingClientRect();
    const 候选 = [];
    for (const e of g.querySelectorAll('*')) {
      if (!(e.textContent || '').trim()) continue;
      const er = e.getBoundingClientRect();
      if (er.width < 1 || er.height < 1) continue;
      候选.push({ tag: e.tagName, cls: String(e.className || '').slice(0, 60),
        逐字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        屏上: { x: Math.round(er.x), y: Math.round(er.y), w: Math.round(er.width), h: Math.round(er.height) },
        pe: getComputedStyle(e).pointerEvents });
    }
    return { 卡片: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      在视口内: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
      候选数: 候选.length, 候选: 候选.slice(0, 12) };
  });

  // 卡片上方 60px 内的命中物分布
  rec.上方命中扫描 = await p.evaluate(() => {
    const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
    if (!g) return null;
    const r = g.getBoundingClientRect();
    const 统计 = {};
    for (let y = Math.max(Math.round(r.y) - 60, 0); y <= Math.round(r.y) + 4; y += 4) {
      for (let x = Math.round(r.x); x <= Math.round(r.x) + Math.min(r.width, 400); x += 8) {
        const h = document.elementFromPoint(x, y);
        const k = h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 46) : 'null';
        统计[k] = (统计[k] || 0) + 1;
      }
    }
    return 统计;
  });
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b142-diag.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1).slice(0, 3000));
await b.close();
