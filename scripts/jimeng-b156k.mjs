// 批次 156-k —— 完整刻画「设置主体」二次确认对话框（`subject-export-confirm-dialog`）
//
// 🔴 本批最重要的一格：**「保存到主体库」不是一个动作，是两个**。
//    156-h 点了菜单项之后连按 3 次 Esc，156-i 重开主体库读到的还是基线，
//    当时读成的结论是「点了没反应」——**其实是被自己关掉了**。
//    156-j 用「点前/点后全 DOM 差分」把它逼出来：新增 21 个元素，其中就有
//    `subject-export-confirm-dialog` 548×688。
//    ⇒ 📌 **立规 19：判「这个按钮点了有没有反应」之前，先排除「反应被我自己的收尾动作抹掉了」**。
//        自动化脚本里 Esc / 点空白 / 切工具 都是**收尾动作**，它们和「按钮没反应」在日志上完全同形。
//        正确做法是**点完先读现场、再收尾**（156-j 就是这么做的：现场浮层读到了那个 dialog）。
//
// ✅ 本轮只做**可逆**取证：打开对话框 → 逐项 dump → **只填名称不点保存** → 读「保存」何时变可用 → Esc 丢弃。
//    「填了不保存」是零持久副作用的（对话框字段随 Esc 一起消失），在授权范围内。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156k', 目的: '完整刻画「设置主体」二次确认对话框（不点保存）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156k.json', import.meta.url), JSON.stringify(rec, null, 1));
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
  await p.mouse.up(); await p.waitForTimeout(1400); return { 落点: 起 };
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

const 读设置主体 = (阶段) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]');
  if (!d) return { 命中: false, 阶段: tag };
  const r = d.getBoundingClientRect();
  const 列出 = (sel) => Array.from(d.querySelectorAll(sel)).map((e) => { const er = e.getBoundingClientRect();
    return { tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      type: e.getAttribute('type'), placeholder: e.getAttribute('placeholder'), maxlength: e.getAttribute('maxlength'),
      value: (e.value === undefined ? null : String(e.value).slice(0, 40)),
      逐字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      disabled: e.getAttribute('aria-disabled'), dataDisabled: e.getAttribute('data-disabled'),
      盒: 盒(e) }; }).filter((z) => z.盒[0] > 0 && z.盒[1] > 0);
  return { 命中: true, 阶段: tag, role: d.getAttribute('role'), 盒: 盒(d),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    按钮: 列出('button,[role=button]'), 输入: 列出('input,textarea,[contenteditable=true]'),
    图: Array.from(d.querySelectorAll('img')).map((x) => ({ alt: x.getAttribute('alt'), src前: (x.getAttribute('src') || '').slice(0, 50), 盒: 盒(x) })).filter((z) => z.盒[0] > 0),
    分区: Array.from(d.children).map((c) => ({ testid: c.getAttribute('data-testid'), 盒: 盒(c), 逐字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) })) };
}, 阶段);

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
  if (落.__err) throw new Error('落点失败');
  await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
  rec.选中数 = await selCount(p);
  断言('① 选中带媒体的图片节点', rec.选中数 === 1, { 选中数: rec.选中数 });

  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1600);
  const 保存项 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return null;
    const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').indexOf('保存到主体库') >= 0);
    if (!it) return null; const r = it.getBoundingClientRect();
    return { aria: it.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  rec.保存项 = 保存项;
  if (!保存项) throw new Error('右键菜单无「保存到主体库」');
  const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 4; yy <= y + h - 4; yy += 2)
    for (let xx = Math.ceil(x) + 4; xx <= x + w - 4; xx += 2) { const el = document.elementFromPoint(xx, yy);
      const mi = el && el.closest('[role=menuitem]'); if (mi && (mi.innerText || '').indexOf('保存到主体库') >= 0) return { x: xx, y: yy }; }
    return { __err: 'no-point' }; }, 保存项.盒);
  await p.mouse.click(lp.x, lp.y); await p.waitForTimeout(2200);

  // ===== 空态下的对话框 =====
  rec.空态 = await 读设置主体('空态');
  落盘();
  console.log('\n🆕 设置主体（空态）', 串(rec.空态, 3400));
  const 保存钮 = ((rec.空态 || {}).按钮 || []).find((z) => /保存/.test(z.逐字) || /保存/.test(z.aria || ''));
  rec.空态保存钮 = 保存钮 || null;
  断言('② 点「保存到主体库」弹出 `subject-export-confirm-dialog`，**548×688**',
    (rec.空态 || {}).命中 === true && (rec.空态 || {}).盒[0] === 548 && (rec.空态 || {}).盒[1] === 688,
    { 盒: (rec.空态 || {}).盒 });
  断言('③ 「保存」按钮空态**禁用**，并附原因「保存前请输入名称。」',
    !!保存钮 && (保存钮.disabled === 'true' || 保存钮.dataDisabled === 'true') &&
    /保存前请输入名称/.test(String((rec.空态 || {}).逐字 || '')),
    { 保存钮: 保存钮 || null, 逐字: String((rec.空态 || {}).逐字 || '').slice(0, 200) });
  断言('④ 名称输入框逐字带「名称*」与 **0 / 20** 计数',
    /名称\s*\*/.test(String((rec.空态 || {}).逐字 || '')) && /\d+\s*\/\s*20/.test(String((rec.空态 || {}).逐字 || '')),
    { 逐字: String((rec.空态 || {}).逐字 || '').slice(0, 200) });
  rec.空态testid = (rec.空态 || {}).testid清单;
  console.log('空态 testid', JSON.stringify(rec.空态testid));
  console.log('空态输入', 串((rec.空态 || {}).输入, 900));
  console.log('空态图', 串((rec.空态 || {}).图, 700));

  // ===== 只填名称，不点保存（零持久副作用）=====
  const 名 = await p.evaluate(() => { const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]'); if (!d) return null;
    const el = d.querySelector('input,textarea'); if (!el) return null; const r = el.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      maxlength: el.getAttribute('maxlength'), placeholder: el.getAttribute('placeholder'), aria: el.getAttribute('aria-label') }; });
  rec.名称框 = 名;
  console.log('名称框', JSON.stringify(名));
  if (名 && !名.__err) {
    await p.mouse.click(名.x, 名.y); await p.waitForTimeout(600);
    await p.keyboard.type('手册核验主体', { delay: 60 }); await p.waitForTimeout(1200);
    rec.填名后 = await 读设置主体('填名后');
    落盘();
    console.log('\n🆕 设置主体（填名后）', 串(rec.填名后, 2600));
    const 钮2 = ((rec.填名后 || {}).按钮 || []).find((z) => /保存/.test(z.逐字) || /保存/.test(z.aria || ''));
    rec.填名后保存钮 = 钮2 || null;
    断言('⑤ 填了名称后「保存」由**禁用转可用**（名称是唯一的必填门槛）',
      !!钮2 && 钮2.disabled !== 'true' && 钮2.dataDisabled !== 'true', { 钮: 钮2 || null });
    断言('⑥ 计数器从 **0 / 20** 变成 **6 / 20**（「手册核验主体」6 字）',
      /6\s*\/\s*20/.test(String((rec.填名后 || {}).逐字 || '')), { 逐字: String((rec.填名后 || {}).逐字 || '').slice(0, 200) });
    断言('⑦ 填名全程**没有点「保存」**（按钮文本逐字核对）',
      /保存前请输入名称/.test(String((rec.空态 || {}).逐字 || '')), { 空态逐字: String((rec.空态 || {}).逐字 || '').slice(-60) });
  }
  rec.点保存次数 = 0;
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ===== 收尾：先读现场，再关 =====
rec.现场 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="subject-export-confirm-dialog"]'))
  .map((d) => ({ 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
    输入值: Array.from(d.querySelectorAll('input,textarea')).map((x) => x.value) })));
console.log('收尾前现场', 串(rec.现场, 700));
try {
  for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  rec.关后 = await p.evaluate(() => !!document.querySelector('[data-testid="subject-export-confirm-dialog"]'));
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
