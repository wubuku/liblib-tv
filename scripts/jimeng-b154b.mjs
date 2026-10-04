// 批次 154-b —— **纯只读地面真相探针**（唯一副作用是「建 1 个图片节点 + 删掉它」）
//
// 🎯 为什么需要这一轮：b154 主脚本尾部的点扫描把盒格式 `[w,h,x,y]` 按 `[x,y,w,h]` 解构，
//    于是「点『展开图片生成器』」实际点到了 (52,42) 的**画布标题**。
//    更要命的是：点击**之前**读到的 `node-toolbar` 已经是 680×208 / 7 个按钮 / 带「生成」。
//    ⇒ 「生成表单需不需要先点展开」这件事，**我根本没验过**，却已经往下推了两步。
//
// 🔑 本轮只回答三个纯度量问题，一个展开按钮都不点：
//    Q-a  建完图片节点（已选中）后，`generation-form` 在不在？在哪个祖先链里？
//    Q-b  `node-toolbar` 有几个实例？每个实例的**每一个按钮**的 testid / aria / 逐字文案 /
//        自身矩形 / 矩形中心 `elementFromPoint` 命中的祖先链 —— 用来区分
//        「DOM 里有一个按钮」与「这个按钮真的在屏上、真的可点」。
//    Q-c  「展开图片生成器」与「生成」分别挂在哪个实例、中心点命中谁。
//
// ⛔ 红线：本轮**不点任何按钮**（只 `mouse.move`），不按任何键，不生成、不扣费。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '154b', 目的: '只读：新建图片节点后生成表单是否默认在场 + 工具条按钮逐个可点性' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b154b.json', import.meta.url), JSON.stringify(rec, null, 1));
// 🔑 **scratch 截图绝不写进 `screenshots/`** —— 那里每个 png 都会被 gate-a 的
//    「screenshot file missing from manifest」当成漏登记。本批踩过：写到 screenshots/ 直接让两道门变红。
const 出图 = new URL('./_tmp_b154b-shots/', import.meta.url);
fs.mkdirSync(出图, { recursive: true });

// 🔑 矩形一律用**具名对象**在 evaluate 内现取现用，绝不跨边界传数组再解构
const 探工具条 = () => ({
  实例: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e, k) => {
    const r = e.getBoundingClientRect();
    return {
      序: k,
      盒: { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10 },
      有面积: r.width > 0 && r.height > 0,
      祖先链: (() => { const c = []; let n = e; for (let i = 0; i < 6 && n; i++) { n = n.parentElement; if (!n || n === document.body) break;
        c.push(n.tagName.toLowerCase() + (n.getAttribute('data-testid') ? '{' + n.getAttribute('data-testid') + '}' : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.split(/\s+/)[0] : '')); } return c; })(),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((b) => {
        const q = b.getBoundingClientRect();
        const cx = Math.round(q.x + q.width / 2); const cy = Math.round(q.y + q.height / 2);
        return {
          testid: b.getAttribute('data-testid'),
          aria: b.getAttribute('aria-label'),
          逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          盒: { w: Math.round(q.width * 10) / 10, h: Math.round(q.height * 10) / 10, x: Math.round(q.x * 10) / 10, y: Math.round(q.y * 10) / 10 },
          有面积: q.width > 0 && q.height > 0,
          中心: { x: cx, y: cy },
          中心命中: (() => { const h = document.elementFromPoint(cx, cy); if (!h) return null;
            const btn = h.closest('button,[role=button]');
            return { 标签: h.tagName.toLowerCase(), 是自己: btn === b,
              是谁: btn ? (btn.getAttribute('data-testid') || btn.getAttribute('aria-label') || (btn.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) || btn.tagName.toLowerCase()) : null }; })(),
        };
      }),
    };
  }),
});

const 探testid = (ids) => ({
  读: Object.fromEntries(ids.map((n) => [n, Array.from(document.querySelectorAll('[data-testid="' + n + '"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { 盒: { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10 },
      role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
      祖先链: (() => { const c = []; let n = e; for (let i = 0; i < 6 && n; i++) { n = n.parentElement; if (!n || n === document.body) break;
        c.push(n.tagName.toLowerCase() + (n.getAttribute('data-testid') ? '{' + n.getAttribute('data-testid') + '}' : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.split(/\s+/)[0] : '')); } return c; })() };
  })])),
});

const 五项 = ['generation-form', 'generation-mention-panel', 'generation-mention-submenu',
  'generation-source-picker-chip', 'generation-source-picker-close'];
const 拾取2 = ['canvas-source-picker-canvas-frame', 'canvas-source-picker-canvas-mask'];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ---------- Q-a0：**建之前**的地面真相（同一个 testid 家族在场吗？）
  rec.建前 = { 工具条: await p.evaluate(探工具条), 五项: await p.evaluate(探testid, 五项) };
  落盘();

  const 基线 = (await idsOf(p)).length;
  const 建 = await 建N个(p, '图片', 1, null, 基线);
  rec.建 = { ids: 建.ids, 护栏: 建.护栏, 护栏全过: 建.护栏.every((h) => h.通过) };
  落盘();
  if (!建.ids || !建.ids.length) throw new Error('没建成');
  const id = 建.ids[0];

  // ---------- Q-a：建完（已选中）**一个按钮都不点**
  rec.选中数 = await selCount(p);
  const 节点盒 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]'); const r = n.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, id);
  rec.节点盒 = 节点盒;
  // 只 move，不 click
  await p.mouse.move(节点盒.cx, 节点盒.cy); await p.waitForTimeout(1500);
  rec.Qa_悬停后 = { 工具条: await p.evaluate(探工具条), 五项: await p.evaluate(探testid, 五项) };
  落盘();
  await p.screenshot({ path: new URL('./_b154b-默认态.png', 出图).pathname });
  rec.截图 = 'scratch（不入库，落在 scripts/_tmp_b154b-shots/）';

  // ---------- Q-b：把鼠标**移出画布**再看一次 —— 分辨「悬停才出现」与「选中就在」
  await p.mouse.move(8, 8); await p.waitForTimeout(1500);
  rec.Qb_移出后 = { 工具条: await p.evaluate(探工具条), 五项: await p.evaluate(探testid, 五项), 选中: await selCount(p) };
  落盘();

  // ---------- 收尾：把自建节点删掉（右键 → 上下文菜单 →「删除 ⌫」）
  const 清零 = async () => {
    for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
      const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
        for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
        return { __err: 'no-free-pane' }; });
      if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
    }
    return selCount(p);
  };
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  rec.落点 = 落;
  if (!落.__err) {
    const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
      const n = h && h.closest('.react-flow__node'); return !!(n && n.getAttribute('data-id') === i); }, [落.x, 落.y, id]);
    rec.归属 = 归属;
    if (归属) {
      await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
      const del = await p.evaluate(() => {
        const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
          .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
        if (!els.length) return { __err: 'no-delete-item' };
        const e = els[0]; const r = e.getBoundingClientRect();
        for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
          for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
            const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
        return { __err: 'no-point' };
      });
      rec.删除项 = del;
      if (!del.__err) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R); }
    }
  }
  const 后 = await idsOf(p);
  rec.消失 = 前.filter((x) => !后.includes(x));
  const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 后.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
rec.小地图 = await R.minimap();
落盘();
console.log('起点', JSON.stringify(rec.起点));
console.log('\n建前工具条实例数', rec.建前.工具条.实例.length, '| 五项命中', JSON.stringify(Object.fromEntries(Object.entries(rec.建前.五项.读).map(([k, v]) => [k, v.length]))));
console.log('\n悬停后工具条实例数', rec.Qa_悬停后.工具条.实例.length, '| 五项命中', JSON.stringify(Object.fromEntries(Object.entries(rec.Qa_悬停后.五项.读).map(([k, v]) => [k, v.length]))));
console.log('\n--- 悬停后 工具条实例逐个 ---');
for (const inst of rec.Qa_悬停后.工具条.实例) {
  console.log('  序' + inst.序, '盒', JSON.stringify(inst.盒), '有面积', inst.有面积, '按钮数', inst.按钮.length, '祖先链', inst.祖先链.slice(0, 3).join(' < '));
  for (const btn of inst.按钮) console.log('     ·', JSON.stringify(btn.testid), '|', JSON.stringify(btn.aria), '|', JSON.stringify(btn.逐字), '| 盒', JSON.stringify(btn.盒), '| 中心命中', JSON.stringify(btn.中心命中));
}
console.log('\n--- 移出画布后 ---');
console.log('  实例数', rec.Qb_移出后.工具条.实例.length, '选中', rec.Qb_移出后.选中, '五项命中', JSON.stringify(Object.fromEntries(Object.entries(rec.Qb_移出后.五项.读).map(([k, v]) => [k, v.length]))));
console.log('\n五项详情(悬停后)', JSON.stringify(rec.Qa_悬停后.五项.读['generation-form'], null, 1));
console.log('\n消失', JSON.stringify(rec.消失), '| 收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图), '| 异常', rec.异常 || '无');
await b.close();
