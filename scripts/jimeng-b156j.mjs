// 批次 156-j —— 「保存到主体库」点下去到底发生了什么：**不猜，比差分**
//
// 156-i 的结果：点完 8 秒 + 重新开库，主体库**逐字等于 156-a 的基线**（仍是「没有可用主体」、
// `canvas-subject-import-empty` 仍在、零 <img>）⇒ **共享数据没被改，也就不需要撤回**（这本身是好消息）。
//
// 🔴 但「主体库没变」有**三种互斥解释**，156-i 分不开：
//    (a) 点击是**静默无操作**（功能坏了 / 需要别的前置）；
//    (b) 写到了**别处**（账号级主体库 / Room），这个面板只是**导入源**不是**目的地**；
//    (c) 需要**二次确认**（弹了什么东西被我的 3 次 Esc 关掉了）。
//    156-h 的轮询只数 `[data-state=open]`，**toast / role=status / 任何新 testid 都会被漏掉** ——
//    而 156-h 点完确实按了 3 次 Esc ⇒ (c) 完全可能发生却被自己抹掉了。
//
// ✅ 本轮：不预设反馈形态，直接做 **DOM 差分** —— 点前/点后各取一次「页面上出现过的一切」签名，
//    再逐项差。命中 (a)/(b)/(c) 哪个由数据说话。
//    ⚠️ 收尾**不按 Esc**，先把现场读干净再说。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156j', 目的: '点「保存到主体库」后做全 DOM 差分，分开 静默无操作/写到别处/需二次确认' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156j.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const tx = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
const 读节点 = (id) => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, id);
const 空点 = (ya, yb, xa, xb, s) => p.evaluate(([y1, y2, x1, x2, st]) => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = y1; y < y2; y += st) for (let x = x1; x < x2; x += st) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
}, [ya, yb, xa, xb, s]);
const 拖 = async (dx, dy) => {
  if (!dx && !dy) return { 跳过: 0 };
  const 起 = await 空点(130, 600, 400, 880, 10); if (起.__err) return 起;
  await p.mouse.move(起.x, 起.y); await p.mouse.down();
  for (let k = 1; k <= 12; k++) { await p.mouse.move(起.x + Math.round(dx * k / 12), 起.y + Math.round(dy * k / 12)); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(1400); return { 落点: 起, 请求: [dx, dy] };
};
const 切工具 = async (想要) => {
  const g = () => p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    if (!b) return null; const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  const b = await g(); if (!b) return { 错: 'no-toggle' };
  if (b.aria === 想要) return { 已就位: true };
  await p.mouse.click(b.盒[2] + b.盒[0] / 2, b.盒[3] + b.盒[1] / 2); await p.waitForTimeout(1300);
  const 后 = await g(); return { 前: b, 后, 成功: !!(后 && 后.aria === 想要) };
};

// 🔑 签名：把「页面上出现过的一切可见物」压成一个可比较的集合。不预设反馈形态。
const 签名 = (阶段) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 有面积 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 集 = [];
  const 加 = (类, e) => { const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    集.push({ 类, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), state: e.getAttribute('data-state'),
      aria: (e.getAttribute('aria-label') || '').slice(0, 40), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      盒: 盒(e) }); };
  // ① 所有可能的「反馈位」：toast / status / alert / 浮层 / 模态 / 菜单
  for (const e of document.querySelectorAll('[data-sonner-toast],[data-sonner-toaster],[role=status],[role=alert],[role=alertdialog],[role=dialog],[data-state=open],[class*=toast],[class*=Toast],[class*=notification],[class*=Notification],[class*=message],[class*=Message],[class*=snackbar],[class*=banner],[class*=tip]')) 加('反馈', e);
  // ② 全部可见 testid（覆盖任何我没想到的入口）
  for (const e of document.querySelectorAll('[data-testid]')) 加('testid', e);
  // ③ 文本命中关键词的可见元素
  for (const e of document.querySelectorAll('div,span,p,li,button,[role=menuitem]')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length > 120) continue;
    if (!/保存|成功|失败|已添加|已保存|主体库|toast|Saved|success/i.test(t)) continue;
    if (!有面积(e)) continue;
    // 只留「叶子」节点，避免把整页根节点都收进来
    if (e.children.length && Array.from(e.children).some((c) => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) continue;
    加('关键词', e);
  }
  return { 阶段: tag, 总数: 集.length, 集 };
}, 阶段);

const 差 = (A, B) => {
  const key = (z) => [z.类, z.role || '', z.testid || '', z.state || '', z.aria || '', z.逐字 || ''].join('');
  const ma = new Map(A.集.map((z) => [key(z), z])); const mb = new Map(B.集.map((z) => [key(z), z]));
  const 新增 = B.集.filter((z) => !ma.has(key(z)));
  const 消失 = A.集.filter((z) => !mb.has(key(z)));
  const 变位 = A.集.map((z) => { const w = mb.get(key(z)); return w && w.盒 && z.盒 && (w.盒[0] !== z.盒[0] || w.盒[1] !== z.盒[1]) ? { 前: z, 后: w } : null; }).filter(Boolean);
  return { 新增, 消失, 变位 };
};

const IMG = 'node_gref4sw056';
const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null; let 拖动量 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  await 切工具('抓手工具');
  const bf = await 读节点(IMG);
  拖动量 = [560 - (bf[2] + bf[0] / 2), 380 - (bf[3] + bf[1] / 2)];
  await 拖(Math.round(拖动量[0]), Math.round(拖动量[1]));
  await 切工具('选择工具');
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  rec.落点 = 落;
  if (落.__err) throw new Error('落点失败: ' + JSON.stringify(落));
  await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
  rec.选中数 = await selCount(p);
  console.log('选中数', rec.选中数);
  断言('① 点中带媒体的图片节点（选中数 1）', rec.选中数 === 1, { 选中数: rec.选中数 });

  // ===== 右键 → 逐字确认九项 → 记「点前」签名 =====
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1600);
  rec.菜单 = await p.evaluate(() => {
    const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return { 命中: false };
    const r = d.getBoundingClientRect();
    return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      项: Array.from(d.querySelectorAll('[role=menuitem]')).map((it) => { const ir = it.getBoundingClientRect();
        return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: it.getAttribute('aria-label'),
          盒: [Math.round(ir.width), Math.round(ir.height), Math.round(ir.x), Math.round(ir.y)] }; }) };
  });
  const 项 = (rec.菜单 || {}).项 || [];
  const 保存项 = 项.find((z) => /保存到主体库/.test(z.逐字));
  rec.保存项 = 保存项 || null;
  console.log('右键菜单', 串(rec.菜单, 1500));
  断言('② 右键菜单 200×372 九项、含可点的「保存到主体库」', (rec.菜单 || {}).盒[0] === 200 &&
    (rec.菜单 || {}).盒[1] === 372 && 项.length === 9 && !!保存项, { 盒: (rec.菜单 || {}).盒, 项数: 项.length });
  if (!保存项) throw new Error('菜单里没有「保存到主体库」');
  rec.保存项aria = 保存项.aria;

  const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 4; yy <= y + h - 4; yy += 2)
    for (let xx = Math.ceil(x) + 4; xx <= x + w - 4; xx += 2) { const el = document.elementFromPoint(xx, yy);
      const mi = el && el.closest('[role=menuitem]'); if (mi && (mi.innerText || '').indexOf('保存到主体库') >= 0) return { x: xx, y: yy }; }
    return { __err: 'no-point' }; }, 保存项.盒);
  rec.保存落点 = lp;

  const 前 = await 签名('点前');
  rec.点前总数 = 前.总数;
  console.log('点前签名元素数', 前.总数);

  // ===== 点！然后高频探 10 秒，**不按任何键** =====
  await p.mouse.click(lp.x, lp.y);
  rec.采样 = [];
  for (let i = 0; i < 20; i++) {
    await p.waitForTimeout(500);
    const s = await 签名('t' + ((i + 1) / 2));
    rec.采样.push({ 毫秒: (i + 1) * 500, 总数: s.总数, 与点前差: 差(前, s) });
    if (i % 4 === 0 || (i + 1) === 20) 落盘();
  }
  const 后 = await 签名('点后');
  rec.总差 = 差(前, 后);
  rec.后总数 = 后.总数;
  rec.采样轨迹 = rec.采样.map((z) => ({ 毫秒: z.毫秒, 总数: z.总数, 新增: z.与点前差.新增.length, 消失: z.与点前差.消失.length }));
  落盘();
  console.log('\n🆕 总差：新增', rec.总差.新增.length, '| 消失', rec.总差.消失.length, '| 变位', rec.总差.变位.length);
  console.log('新增', 串(rec.总差.新增, 2200));
  console.log('消失', 串(rec.总差.消失, 1400));
  console.log('轨迹', JSON.stringify(rec.采样轨迹));

  rec.点后可见反馈 = await p.evaluate(() => Array.from(document.querySelectorAll('body *'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      cls: (e.className || '').toString().slice(0, 70), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
      盒: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })() }))
    .filter((z) => /保存|成功|失败|已添加|已保存到|Saved|success/i.test(z.逐字) && z.盒[0] < 900));
  console.log('点后关键词元素', 串(rec.点后可见反馈, 1800));

  断言('③ 点后 10 秒内，页面上出现过**任何**新反馈元素（toast/模态/状态文本）', rec.总差.新增.length > 0,
    { 新增数: rec.总差.新增.length, 新增: rec.总差.新增.slice(0, 6) });
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ===== 收尾：先读现场，再归位 =====
rec.现场浮层 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-state=open],[role=dialog],[role=alertdialog]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
    state: e.getAttribute('data-state'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }).filter((z) => z.盒[0] > 0));
console.log('现场浮层', 串(rec.现场浮层, 1200));
try {
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  const t = await p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return b ? b.getAttribute('aria-label') : null; });
  if (t !== '抓手工具') await 切工具('抓手工具');
  if (拖动量) await 拖(-Math.round(拖动量[0]), -Math.round(拖动量[1]));
  let t2 = await 读transform(); const a = tx(起点transform) || []; let b2 = tx(t2) || [];
  for (let k = 0; k < 4 && a.length === 2 && b2.length === 2; k++) {
    const ex = a[0] - b2[0]; const ey = a[1] - b2[1];
    if (Math.abs(ex) < 0.05 && Math.abs(ey) < 0.05) break;
    await 拖(-Math.round(ex), -Math.round(ey)); t2 = await 读transform(); b2 = tx(t2) || [];
  }
  rec.归位后transform = t2;
  await 切工具('选择工具');
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const e = await 空点(90, 600, 360, 930, 8); if (e.__err) break;
    await p.mouse.click(e.x, e.y); await p.waitForTimeout(800);
  }
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), transform: await 读transform() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
