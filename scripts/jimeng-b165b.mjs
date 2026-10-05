// 批次 165-b —— 165-a 量出机制之后，**用它预测一个边界再去打那个边界**。
//
// 🔑 165-a 的读数：模态是**定尺** `801×620`（三个视口逐层一致），但计算样式里有一项跟着视口走：
//     1280×720 → max-height 688px ｜ 1440×900 → 868px ｜ 1680×1050 → 1018px
//     ⇒ **max-height = 视口高 − 32**（差值三档都是 32）
//   而 `height` 在这三档都没被触发（620 < 688/868/1018）⇒ 1280×720 下「高 = 视口−100」纯属**巧合**。
//
// 📐 由这条机制推出两个**可证伪的预测**：
//   P1（垂直）高度上限生效的门槛在 **620 + 32 = 652**：
//      H ≥ 652 → 高度仍是 620；H < 652 → 高度应恰好等于 H − 32（651 应读出 619）。
//      ⇒ 测 [720 / 660 / 652 / 651 / 640 / 600 / 520] 七档，**边界前后各取一档**。
//   P2（水平）`max-width: none` 且宽度写死 801px ⇒ **窗口不够宽时不缩、只会溢出**：
//      视口 700 宽时对话框应仍是 801 宽，左余量应变成**负数**。
//      ⇒ 测 [1280 / 900 / 801 / 700] 四档。
//
// ⛔ 全程只读：只开「资产库」模态再 Esc 关掉。不建节点、不上传、不点任何提交类按钮。
// 🔴 收尾：把共享页签视口**复位**到 1280×720。
//   （165-a 实测：给新页签发 override 会**把浏览器窗口一起改掉**，关掉页签也不会自动还原 ——
//     共享页签一度掉到 800×873。「换个页签就不污染共享会话」这句话已被证伪。）
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 高度档 = [[1280, 720], [1280, 660], [1280, 652], [1280, 651], [1280, 640], [1280, 600], [1280, 520]];
const 宽度档 = [[1280, 720], [900, 720], [801, 720], [700, 720]];
const rec = { 批次: '165b', 目的: '用 165-a 的机制（max-height = 视口高−32）预测并验证高度门槛与宽度溢出' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165b.json', import.meta.url), JSON.stringify(rec, null, 1));

// 🔴 页面内函数不能用外部闭包常量（165-a 自身失误 1），全部内联。
const 量 = () => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false, 视口: [innerWidth, innerHeight] };
  const v = document.querySelector('[data-testid="canvas-asset-library-viewport"]');
  const f = document.querySelector('[data-testid="canvas-asset-library-footer"]');
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; };
  return {
    有: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    maxHeight: cs.maxHeight, maxWidth: cs.maxWidth, minWidth: cs.minWidth,
    内容区: 盒(v), 内容区overflow: v ? getComputedStyle(v).overflow : null,
    内容区可滚: v ? [v.scrollHeight, v.clientHeight] : null,
    页脚: 盒(f), 页脚在视口内: f ? f.getBoundingClientRect().bottom <= innerHeight + 0.5 : null,
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 130),
  };
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
console.log('共享页签起点', JSON.stringify(rec.共享起点));

let p2 = null;
const 走一档 = async (s2, w, h, tag) => {
  await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  const 钮 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  let 模态 = null;
  if (钮) {
    await p2.mouse.click(钮[0], 钮[1]);
    for (let k = 0; k < 8 && !(模态 && 模态.有); k++) { await p2.waitForTimeout(650); 模态 = await p2.evaluate(量); }
    await p2.keyboard.press('Escape'); await p2.waitForTimeout(900);
  }
  const 行 = { 档: tag, 视口: [w, h], 按钮落点: 钮, 模态 };
  console.log(`  [${tag}] 视口 ${w}×${h} → 盒 ${JSON.stringify(模态 && 模态.盒)} maxH ${模态 && 模态.maxHeight} 余量 ${JSON.stringify(模态 && 模态.余量)}`);
  落盘();
  return 行;
};

try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);

  // ============ P1：高度门槛（预测门槛 652） ============
  rec.高度读数 = [];
  for (const [w, h] of 高度档) rec.高度读数.push(await 走一档(s2, w, h, '高度'));
  const 预测高 = (h) => (h >= 652 ? 620 : h - 32);
  const 实高 = rec.高度读数.map((z) => (z.模态 && z.模态.有 ? z.模态.盒[1] : null));
  rec.P1 = { 预测: 高度档.map(([, h]) => ({ 视口高: h, 预测高: 预测高(h) })), 实测高: 实高 };
  console.log('P1 预测 vs 实测 =', JSON.stringify(rec.P1));
  断言('P1 七档实测高度与机制预测逐档相同（含 652/651 边界两侧）',
    rec.高度读数.every((z, i) => z.模态 && z.模态.有 && z.模态.盒[1] === 预测高(z.视口[1])), rec.P1);
  断言('P1 边界成立：652 档仍是 620，651 档掉到 619',
    rec.高度读数.find((z) => z.视口[1] === 652).模态.盒[1] === 620 &&
    rec.高度读数.find((z) => z.视口[1] === 651).模态.盒[1] === 619, rec.P1);
  断言('P1 高度被压矮时页脚仍在视口内（不被挤出屏幕）',
    rec.高度读数.every((z) => z.模态 && z.模态.有 && z.模态.页脚在视口内 === true),
    rec.高度读数.map((z) => ({ 视口: z.视口, 页脚: z.模态 && z.模态.页脚, 在内: z.模态 && z.模态.页脚在视口内 })));
  // 压矮档拍一张证据图（手册说明「窗口很矮时资产库会被压矮」）
  const 矮档 = rec.高度读数.find((z) => z.视口[1] === 520);
  if (矮档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 520, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1400);
    const b2 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (b2) {
      await p2.mouse.click(b2[0], b2[1]); await p2.waitForTimeout(2600);
      await p2.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/123-asset-library-short-viewport.png', import.meta.url).pathname });
      rec.矮档图 = 'screenshots/123-asset-library-short-viewport.png';
      await p2.keyboard.press('Escape'); await p2.waitForTimeout(900);
    }
  }
  落盘();

  // ============ P2：宽度溢出（预测：写死 801，不缩、只会溢出） ============
  rec.宽度读数 = [];
  for (const [w, h] of 宽度档) rec.宽度读数.push(await 走一档(s2, w, h, '宽度'));
  const 档700 = rec.宽度读数.find((z) => z.视口[0] === 700);
  const 档801 = rec.宽度读数.find((z) => z.视口[0] === 801);
  rec.P2 = { 实测宽: rec.宽度读数.map((z) => (z.模态 && z.模态.有 ? z.模态.盒[0] : null)),
    余量: rec.宽度读数.map((z) => z.模态 && z.模态.余量) };
  console.log('P2 =', JSON.stringify(rec.P2));
  断言('P2 四档宽度都仍是 801（`max-width: none` ⇒ 不会被压窄）',
    rec.P2.实测宽.every((x) => x === 801), rec.P2);
  断言('P2 视口 700 宽时左余量为**负**（溢出而不是缩放）',
    档700 && 档700.模态 && 档700.模态.有 && 档700.模态.余量.左 < 0, 档700 && 档700.模态 && 档700.模态.余量);
  断言('P2 视口 801 宽时余量为 0（刚好铺满）',
    档801 && 档801.模态 && 档801.模态.有 && Math.abs(档801.模态.余量.左) <= 1, 档801 && 档801.模态 && 档801.模态.余量);
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
} finally {
  try { if (p2) await p2.close(); } catch (e) { rec.关页签异常 = String(e).slice(0, 200); }
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('⑦ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    断言('⑧ 页签数回到 1', ctx.pages().length === 1, { 页签数: ctx.pages().length });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 400); }
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
