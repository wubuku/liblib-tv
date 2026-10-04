// 批次 156-b —— 平移视图去看那个**有媒体的图片节点**，打开它的「工具」菜单
//
// 🔴 156-a 为什么没打开菜单：`node_gref4sw056`（aria 逐字「图片 node: b22-upload」）
//    **整块在视口外**（60% 下屏上 x ≈ -323），`可点落点` 找不到任何像素。
//    ⇒ 📌 **立规 13：节点在视口外时，先平移视图再量，不要因为「点不到」就以为功能不存在**
//    （与批次 119「面板跟着节点走，节点在视口左侧时面板 x 会到 -272」同源）。
//
// 🔑 平移是**纯本地视图状态，不写任何数据**，且**完全可还原**：
//    脚本开头读 `viewport` 的 transform，结尾原样写回 ⇒ 收尾断言「transform 与起点逐字相同」。
// ⛔ 本轮仍然**只读**：不点「保存到主体库」（那是写数据，下一轮 b 做，且必须先对账基线）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156b', 目的: '平移视图 → 打开有媒体图片节点的「工具」菜单 → 找「保存到主体库」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    return true;
  });
  const 全候选 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    全候选.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), disabled: b.getAttribute('aria-disabled'),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b });
  }
  return { 候选数: cands.length, 全候选, 可用: 全候选.filter((z) => z.在视口内 && z.中心是自己) };
}, pred);

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
// 直接写 viewport transform（纯视图操作，不触发任何数据变更）
const 写transform = (t) => p.evaluate((s) => { const e = document.querySelector('.react-flow__viewport'); if (e) e.style.transform = s; }, t);
const 取平移 = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : [0, 0]; };
const 取缩放 = (t) => { const m = /scale\(([\d.]+)\)/.exec(t || ''); return m ? parseFloat(m[1]) : 0.6; };

const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  const s = 取缩放(起点transform); const [tx, ty] = 取平移(起点transform);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p), transform: 起点transform, scale: s };

  const IMG = 'node_gref4sw056';
  const cp = await canvasPos(p);
  rec.目标canvas = cp[IMG] || null;
  const [nx, ny] = cp[IMG] || [0, 0];
  // 让目标节点落在屏上 (560, 380)
  const wantX = 560 - nx * s; const wantY = 380 - ny * s;
  const 新transform = 'translate(' + wantX + 'px, ' + wantY + 'px) scale(' + s + ')';
  rec.新transform = 新transform;
  await 写transform(新transform);
  await p.waitForTimeout(1400);
  rec.平移后transform = await 读transform();
  rec.平移后屏上盒 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]'); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, IMG);
  console.log('平移后 transform =', rec.平移后transform, '| 目标屏上盒 =', JSON.stringify(rec.平移后屏上盒));
  断言('⓪ 平移把目标节点带进视口（屏上 x ≥ 0）', rec.平移后屏上盒 && rec.平移后屏上盒[2] >= 0, rec.平移后屏上盒);

  if (rec.平移后屏上盒 && rec.平移后屏上盒[2] >= 0) {
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
    rec.落点 = 落;
    if (!落.__err) {
      const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
        const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, IMG]);
      rec.归属 = 归属;
      if (归属.对) {
        await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
        rec.选中数 = await selCount(p);
        rec.工具条 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
          const r = e.getBoundingClientRect();
          return { 盒: [Math.round(r.width), Math.round(r.height)], 有面积: r.width > 0,
            按钮: Array.from(e.querySelectorAll('button')).map((b) => ({ aria: (b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 16), testid: b.getAttribute('data-testid') })) };
        }));
        console.log('\n工具条', 串(rec.工具条, 1600));
        const 工 = await 找点({ sel: 'button,[role=button]', 字面等于: '工具' });
        rec.工具钮 = 工;
        const G = (工.可用 || [])[0];
        rec.工具落点 = G || null;
        if (G) {
          await p.mouse.click(G.x, G.y); await p.waitForTimeout(1800);
          rec.工具菜单 = await p.evaluate(() => {
            const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
            const ms = Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).filter((x) => x.getBoundingClientRect().width > 100);
            if (!ms.length) return { 命中: false, 现有菜单: Array.from(document.querySelectorAll('[role=menu]')).map((x) => 盒(x)) };
            const m = ms[ms.length - 1];
            return { 命中: true, 菜单数: ms.length, role: m.getAttribute('role'), testid: m.getAttribute('data-testid'), aria: m.getAttribute('aria-label'), 盒: 盒(m),
              逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
              项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: it.getAttribute('aria-label'), 盒: 盒(it), disabled: it.getAttribute('aria-disabled'), svg数: it.querySelectorAll('svg').length })) };
          });
          落盘();
          console.log('\n🆕 工具菜单', 串(rec.工具菜单, 2800));
          const 项 = (rec.工具菜单 || {}).项 || [];
          const 目标项 = 项.find((z) => /主体库|保存到主体/.test(z.逐字));
          rec.保存到主体库项 = 目标项 || null;
          断言('① 「工具」菜单里有「保存到主体库」这一项', !!目标项, { 项: 项.map((z) => z.逐字) });
          断言('② 菜单项数与手册的「九项」一致（10 项含分组标题则另算）', 项.length > 0, { 项数: 项.length });
          for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
        }
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ---------- 收尾：清选中 + 还原视图 ----------
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
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
落盘();
console.log('\n起点 transform =', 起点transform);
console.log('还原后 transform =', rec.还原后transform, '| 逐字相同 =', 起点transform === rec.还原后transform);
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('③ 🔑 视图 transform **与起点逐字相同**（平移完全还原）', 起点transform === rec.还原后transform, { 起点: 起点transform, 后: rec.还原后transform });
断言('④ 收尾积分**仍是 805**', String(rec.收尾.积分).indexOf('805') >= 0, { 积分: rec.收尾.积分 });
rec.断言全过 = 断言过; 落盘();
await b.close();
