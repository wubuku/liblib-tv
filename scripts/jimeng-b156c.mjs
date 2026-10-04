// 批次 156-c —— 找出「工具」按钮到底怎么标的
//
// 🔴 156-b 的收获与卡点：平移 + 选中都成功（目标节点屏上 `341×192@560,380`），
//    浮动工具条读出来是 **`959×40`、12 个按钮**，但**其中 10 个的 `aria-label` 逐字为空**，
//    只有「全屏」「下载」有 aria ⇒ 按 aria 找「工具」必然找不到。
//    （12 项这个数与 AUDIT 批次 145 记的「有素材图片节点 12 项、含『工具』」对得上。）
//
// 🎯 本轮只回答一个问题：**这 12 个按钮各自靠什么标识自己** ——
//    `title` / `data-toolbar-value` / `data-testid` / svg path / 悬停提示逐字。
//    手段：逐个 `mouse.move` 过去读悬停层 + dump 属性表。**一个按钮都不点。**
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156c', 目的: '找出图片节点浮动工具条 12 个按钮的标识方式' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const 写transform = (t) => p.evaluate((s) => { const e = document.querySelector('.react-flow__viewport'); if (e) e.style.transform = s; }, t);
const 取平移 = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : [0, 0]; };
const 取缩放 = (t) => { const m = /scale\(([\d.]+)\)/.exec(t || ''); return m ? parseFloat(m[1]) : 0.6; };

const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  const s = 取缩放(起点transform);
  const IMG = 'node_gref4sw056';
  const cp = await canvasPos(p);
  const [nx, ny] = cp[IMG] || [0, 0];
  await 写transform('translate(' + (560 - nx * s) + 'px, ' + (380 - ny * s) + 'px) scale(' + s + ')');
  await p.waitForTimeout(1400);

  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  rec.落点 = 落;
  if (!落.__err) {
    const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
      const n = h && h.closest('.react-flow__node'); return !!(n && n.getAttribute('data-id') === i); }, [落.x, 落.y, IMG]);
    rec.归属 = 归属;
    if (归属) {
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
      rec.选中数 = await selCount(p);

      // dump 有面积那一条工具条的全部按钮属性
      rec.按钮表 = await p.evaluate(() => {
        const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).find((e) => e.getBoundingClientRect().width > 0);
        if (!bar) return null;
        const r = bar.getBoundingClientRect();
        return {
          条盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          class逐字: bar.className,
          个数: bar.querySelectorAll('button').length,
          按钮: Array.from(bar.querySelectorAll('button')).map((b, k) => {
            const q = b.getBoundingClientRect();
            const 属性 = {};
            for (const a of Array.from(b.attributes)) 属性[a.name] = a.value;
            return { 序: k, 属性,
              盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10, Math.round(q.x), Math.round(q.y)],
              中心: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)],
              逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
              svg: b.querySelectorAll('svg').length,
              svgPath: Array.from(b.querySelectorAll('path')).map((x) => (x.getAttribute('d') || '').slice(0, 34)),
              html: b.outerHTML.slice(0, 260) };
          }),
        };
      });
      落盘();
      console.log('工具条', 串(rec.按钮表 && { 条盒: rec.按钮表.条盒, 个数: rec.按钮表.个数, class逐字: rec.按钮表.class逐字 }, 600));
      for (const b2 of ((rec.按钮表 || {}).按钮 || [])) {
        console.log('  序' + b2.序, '盒', JSON.stringify(b2.盒), '| 属性', JSON.stringify(b2.属性), '| 逐字', JSON.stringify(b2.逐字), '| svg', b2.svg, '| path', JSON.stringify(b2.svgPath.slice(0, 2)));
      }

      // 逐个悬停读 tooltip（**不点**）
      rec.悬停 = [];
      for (const b2 of ((rec.按钮表 || {}).按钮 || [])) {
        await p.mouse.move(b2.中心[0], b2.中心[1]);
        await p.waitForTimeout(700);
        const tip = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tooltip],[data-radix-popper-content-wrapper]'))
          .map((e) => { const r = e.getBoundingClientRect(); return { 逐字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
          .filter((z) => z.盒[0] > 0));
        rec.悬停.push({ 序: b2.序, 中心: b2.中心, tip });
      }
      落盘();
      console.log('\n🆕 悬停逐个读到的 tooltip：');
      for (const h of rec.悬停) console.log('  序' + h.序, JSON.stringify(h.tip));
      断言('⓪ 至少能靠悬停或属性认出「工具」那一项',
        rec.悬停.some((h) => /工具/.test(JSON.stringify(h.tip))) ||
        ((rec.按钮表 || {}).按钮 || []).some((b2) => /工具/.test(JSON.stringify(b2.属性) + b2.逐字)),
        { tooltip: rec.悬停.map((h) => h.tip) });
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
  const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
    for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
    return { __err: 'no-free-pane' }; });
  if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900);
}
await 写transform(起点transform);
await p.waitForTimeout(1500);
rec.还原后transform = await 读transform();
await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
落盘();
console.log('\n还原 transform 逐字相同 =', 起点transform === rec.还原后transform);
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
rec.断言全过 = 断言过; 落盘();
await b.close();
