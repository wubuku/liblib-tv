// 批次 140 b 轮前置诊断：画布上**文本节点**的 aria-label / testid 真身是什么。
// （b 轮第一版的候选过滤器用 `/文本|文字|text/i` 匹配 aria-label，候选数 0 —— 先查真身。）
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = {};
try {
  await keyGuard(p);
  await settle(p, R);
  rec.全部节点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      className: String(n.className || '').slice(0, 90),
      innerText前20: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      canvas: { w: n.offsetWidth, h: n.offsetHeight },
      在视口可用区: r.right > 8 && r.x < innerWidth - 330 && r.bottom > 70 && r.y < innerHeight - 80 };
  }));
  rec.统计 = {
    总数: rec.全部节点.length,
    有文本aria: rec.全部节点.filter((n) => /文本|文字|text/i.test(n.aria || '')).length,
    视口可用区内: rec.全部节点.filter((n) => n.在视口可用区).length,
    视口可用区且有文本aria: rec.全部节点.filter((n) => n.在视口可用区 && /文本|文字|text/i.test(n.aria || '')).length,
    aria样本: [...new Set(rec.全部节点.map((n) => n.aria))].slice(0, 25),
    class样本: [...new Set(rec.全部节点.map((n) => n.className.split(' ').slice(1, 3).join(' ')))].slice(0, 15),
  };
  rec.视口 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 400); }
fs.writeFileSync(new URL('./_tmp-b140b-diag.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 统计: rec.统计, 视口: rec.视口 }, null, 1));
await b.close();
