// 批次 143 b 轮 —— 侦察二：**新节点建完能不能立刻拖开？**
//
// 🔑 背景：a 轮实测到两个新节点**阶梯叠放，屏上偏移恒 (24,24)px**（canvas 恒 40），
//   于是 `planBoxFor` 的安全判据（框选矩形四角必须不在**任何**节点内）在 76 节点的
//   共享画布上**必然失败** ⇒ 编组链走不通。
//   批次 142 说过「拖开也压不住」但**没量过**。本轮量。
//
// 本轮只做两件事：
//   ① dump 一个新文本节点内部的结构，找**可安全按下拖动**的像素（不能点正文 —— 会进编辑态）；
//   ② 试拖，量 canvas 位置变化，判「拖开」到底可不可行。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selIds, selCount, 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'b', 目的: '侦察新节点可拖动落点 + 拖开可行性' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };

  rec.建 = await 建N个(p, '文本', 1, 断言, 76);
  const SELF = rec.建.ids && rec.建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; } else {
    rec.SELF = SELF;
    rec.建后 = { 状态行: await R.status(), 选中: await selIds(p), 选中数: await selCount(p) };
    rec.建后canvas = await canvasPos(p);
    rec.建后canvasSelf = rec.建后canvas[SELF];

    // ---- ① 结构 dump：找出哪些像素按下后能拖动（而不是进编辑态 / 点到工具条）
    rec.结构 = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { __err: 'not-found' };
      const box = (e) => { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }; };
      const 树 = (el, d) => { const cs = getComputedStyle(el);
        return { 深度: d, tag: el.tagName, cls: String(el.className || '').slice(0, 80),
          pe: cs.pointerEvents, 用户可改: cs.userSelect, cursor: cs.cursor,
          盒: box(el), 子: d >= 3 ? '…' : Array.from(el.children).map((c) => 树(c, d + 1)) }; };
      return { 节点: 树(n, 0) };
    }, SELF);

    // ---- ② 网格扫描：把节点的每个像素按「按下去会命中谁 + 它的祖先链」归类
    rec.像素普查 = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const r = n.getBoundingClientRect();
      const tally = new Map();
      const 采样 = [];
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 4)
        for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 4) {
          const h = document.elementFromPoint(x, y);
          if (!h) { tally.set('null', (tally.get('null') || 0) + 1); continue; }
          const 在节点内 = n === h || n.contains(h);
          const 键 = (在节点内 ? '节点内·' : '节点外·') + h.tagName + '.' + String(h.className || '').split(' ').slice(0, 2).join('.');
          if (!tally.has(键)) { tally.set(键, 0); 采样.push({ 键, x, y, 链: (() => { const c = []; for (let k = h; k && k !== document.body; k = k.parentElement) c.push(String(k.className || '').split(' ')[0] || k.tagName); return c.slice(0, 6); })() }); }
          tally.set(键, tally.get(键) + 1);
        }
      return { 节点盒: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        总采样: [...tally.values()].reduce((a, b2) => a + b2, 0),
        分布: [...tally.entries()].sort((a2, b2) => b2[1] - a2[1]),
        各类首个采样: 采样 };
    }, SELF);
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); }

// ---- 清理
try {
  const 自建 = rec.建 && rec.建.ids ? rec.建.ids : [];
  rec.删除 = [];
  for (const id of 自建) {
    const 前 = await idsOf(p);
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id, __err: 'no-point' }); continue; }
    await p.mouse.click(落.x, 落.y, { button: 'right' });
    await p.waitForTimeout(1800);
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
        }
      return { __err: 'no-point' };
    });
    if (del.__err) { rec.删除.push({ id, __err: del.__err }); continue; }
    await p.mouse.click(del.x, del.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后 = await idsOf(p);
    rec.删除.push({ id, 消失: 前.filter((x) => !后.includes(x)) });
  }
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 剩余自建: 末.filter((x) => (rec.建 && rec.建.ids || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b143b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('\n===== 收尾 =====\n' + JSON.stringify(rec.收尾, null, 1));
await b.close();
