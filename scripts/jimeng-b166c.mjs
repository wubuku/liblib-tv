// 批次 166-c —— 把「项目信息对话框 800×546」这个**假契约**换成一条真定律。
//
// 🔑 166-b 的读数推翻了手册的记法：该对话框 classList 里**没有任何高度类名**，
//    只有 `w-workspace-project-info{width:800px}`、`max-h-[80vh]`、`max-w-[calc(100vw-32px)]`。
//    四个直接子分别是 68 / 36 / **382（`flex: 1 1 0%`）** / 60 —— 68+36+382+60 = **546**。
//    ⇒ 546 **不是常量**，是「三段固定 ＋ 一段被内容撑开」的**内容高度**。
//
// 📐 由此推出两个**可证伪的预测**（高度侧 + 宽度侧，各带一个门槛）：
//   P1 高 = min(内容高度 546, 80vh)
//      视口 720 → 546（546 < 576，未触顶）｜ 600 → **480**（0.8×600，触顶）
//      ｜ 500 → **400** ｜ 400 → **320** ｜ 300 → **240**
//      ⇒ 门槛在 546/0.8 = **682.5**：视口高 ≥ 683 走 546，以下走 0.8×高。
//      边带补一档 **690 / 680** 把门槛夹出来。
//   P2 宽 = min(800, 100vw − 32)
//      视口 ≥ 832 → 800；831 → 799；700 → 668。
//
// ⛔ 只读：新页签里开对话框读数再 Esc；共享页签不动，收尾复位 1280×720。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 高档 = [[1280, 720], [1280, 690], [1280, 680], [1280, 600], [1280, 500], [1280, 400], [1280, 300]];
const 宽档 = [[1280, 720], [900, 720], [832, 720], [831, 720], [700, 720]];
const rec = { 批次: '166c', 目的: '项目信息对话框：验证 高=min(546,80vh) 与 宽=min(800,100vw−32)' };
let 断言过 = true, 断言数 = 0, 断言预期 = 6;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b166c.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读 = () => {
  const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
  if (!d) return { 有: false, 视口: [innerWidth, innerHeight] };
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  const 子 = Array.from(d.children).map((c) => { const q = c.getBoundingClientRect(), s = getComputedStyle(c);
    return { 盒: [Math.round(q.width), Math.round(q.height)], flex: s.flex, grow: s.flexGrow, minH: s.minHeight }; });
  return { 有: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth },
    子, 子高合计: 子.reduce((s, z) => s + z.盒[1], 0),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) };
};

const 读共享 = async (p) => p.evaluate(() => ({
  视口: [innerWidth, innerHeight],
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  节点数: document.querySelectorAll('.react-flow__node').length,
  选中: document.querySelectorAll('.react-flow__node.selected').length,
  浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
}));

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
const ctx = b.contexts()[0];
const shared = ctx.pages().find((x) => x.url().includes('ai-canvas'));
rec.共享起点 = await 读共享(shared);
console.log('共享起点', JSON.stringify(rec.共享起点));

let p2 = null;
const 走一档 = async (s2, w, h, tag) => {
  await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  // 更多 → 项目信息
  const 更多 = await p2.evaluate(() => { const c = Array.from(document.querySelectorAll('button,[role=button]'));
    const e = c.find((x) => (x.getAttribute('aria-label') || '').includes('更多')); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  let 读数 = null;
  if (更多) {
    await p2.mouse.click(更多[0], 更多[1]); await p2.waitForTimeout(1300);
    const 项 = await p2.evaluate(() => { const it = Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim() === '项目信息');
      if (!it) return null; const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (项) { await p2.mouse.click(项[0], 项[1]);
      for (let k = 0; k < 8 && !(读数 && 读数.有); k++) { await p2.waitForTimeout(600); 读数 = await p2.evaluate(读); }
    } else { await p2.keyboard.press('Escape'); await p2.waitForTimeout(600); }
    for (let k = 0; k < 3; k++) { await p2.keyboard.press('Escape'); await p2.waitForTimeout(500); }
  }
  const 行 = { 档: tag, 视口: [w, h], 读数 };
  console.log(`  [${tag}] ${w}×${h} → 盒 ${JSON.stringify(读数 && 读数.盒)} maxH ${读数 && 读数.计算.maxHeight} 子高合计 ${读数 && 读数.子高合计}`);
  落盘();
  return 行;
};

try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);
  rec.高档 = [];
  for (const [w, h] of 高档) rec.高档.push(await 走一档(s2, w, h, '高度'));
  const 预测高 = (h) => Math.min(546, Math.round(0.8 * h));
  rec.P1 = { 预测: 高档.map(([, h]) => ({ 视口高: h, 预测高: 预测高(h) })),
    实测: rec.高档.map((z) => (z.读数 && z.读数.有 ? z.读数.盒[1] : null)) };
  console.log('P1 =', JSON.stringify(rec.P1));
  断言('① 七档实测高度与 min(546, 80vh) 逐档相同（含 690/680 门槛两侧）',
    rec.高档.every((z) => z.读数 && z.读数.有 && z.读数.盒[1] === 预测高(z.视口[1])), rec.P1);
  断言('② 门槛成立：690 档读出 546，680 档读出 544（0.8×680）',
    rec.高档.find((z) => z.视口[1] === 690).读数.盒[1] === 546 &&
    rec.高档.find((z) => z.视口[1] === 680).读数.盒[1] === 544, rec.P1);
  const 触顶档 = rec.高档.find((z) => z.视口[1] === 600);
  断言('③ 触顶档（600 高）里「可伸缩的那一段」确实变矮：382 → 316',
    触顶档.读数.有 && 触顶档.读数.子.length === 4 &&
    触顶档.读数.子[2].盒[1] === 316 && 触顶档.读数.子[2].grow === '1',
    触顶档.读数.有 ? 触顶档.读数.子 : null);

  rec.宽档 = [];
  for (const [w, h] of 宽档) rec.宽档.push(await 走一档(s2, w, h, '宽度'));
  const 预测宽 = (w) => Math.min(800, w - 32);
  rec.P2 = { 预测: 宽档.map(([w]) => 预测宽(w)), 实测: rec.宽档.map((z) => (z.读数 && z.读数.有 ? z.读数.盒[0] : null)) };
  console.log('P2 =', JSON.stringify(rec.P2));
  断言('④ 五档实测宽度与 min(800, 100vw−32) 逐档相同（含 832/831 边界）',
    rec.宽档.every((z) => z.读数 && z.读数.有 && z.读数.盒[0] === 预测宽(z.视口[0])), rec.P2);
  断言('⑤ 四个直接子高度之和始终等于对话框高度（546 是「三段固定＋一段 flex」）',
    rec.高档.filter((z) => z.读数 && z.读数.有).every((z) => z.读数.子高合计 === z.读数.盒[1]),
    rec.高档.filter((z) => z.读数 && z.读数.有).map((z) => ({ 视口高: z.视口[1], 盒高: z.读数.盒[1], 子合计: z.读数.子高合计 })));
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1000);
  console.log('异常', rec.异常);
  断言过 = false;
} finally {
  try { if (p2) await p2.close(); } catch (e) {}
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('⑥ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 300); }
  if (断言数 < 断言预期) { console.log(`⛔ 断言只跑了 ${断言数}/${断言预期} 条 —— 中途崩了，不能当全绿`); 断言过 = false; }
  rec.断言执行数 = 断言数; rec.断言预期数 = 断言预期; rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
