// 批次 165-d —— 165-c 把**规律**测准了（宽 = min(801, 视口−32)，门槛 833/832），
// 但连着两次**机制假设都被自己的读数否掉**：
//   假设 1（165-b）：`max-width: none` ⇒ 不会缩、只会溢出　→ **否**，实测会缩（769 / 668 / 368）
//   假设 2（165-c）：祖先是 flex 容器、我方 flex-shrink 生效　→ **否**，
//        祖先只有 BODY（`display: block`）；我方 class 逐字是
//        `fixed left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col`
// 🔴 顺带**订正 165-c 自己的一处误读**：窄视口下量到的「左右各 16px 余量」
//    **不是边距，是居中的结果** —— (400−368)/2 = 16、(832−800)/2 = 16。
//    「16 = 32/2」是**必然**，不能拿它反推「容器有 16px 内边距」。
//
// 📐 本轮只问一件事：**那个 32 是什么单位**。两个可证伪的读法：
//   ① 样式表里把声明逐字抓出来（165-a 试过 `styleSheets[].cssRules`，
//      跨域样式表直接抛异常 ⇒ 这条路不通；改成 `fetch(href)` 拿原始 CSS 文本再搜 `801`）。
//   ② **改根字号再看**：把 `html` 的 font-size 从 16px 改成 20px。
//      若 32 是 `2rem`，钳位应变成 40 ⇒ 500 宽视口下宽度应从 468 变成 460；
//      高度侧同理。若**纹丝不动**，那 32 就是写死的 px，与字号无关。
//      ⇒ 这是一个**能区分 rem 与 px 的判据**，不是又一轮「看起来像」。
//
// ⛔ 只读 + 注入的样式**当场撤掉**：只改新页签的 `html` 字号，
//    共享页签一个像素都不动，收尾照旧复位 1280×720。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const rec = { 批次: '165d', 目的: '那个 32 到底是 rem 还是写死的 px：改根字号做区分判据' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165d.json', import.meta.url), JSON.stringify(rec, null, 1));

// 页面内函数：常量内联（165-a 教训 1）
const 量 = () => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false };
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  return {
    有: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    用到宽: cs.width, maxHeight: cs.maxHeight,
    根字号: getComputedStyle(document.documentElement).fontSize,
    cls: (typeof d.className === 'string' ? d.className : '').slice(0, 120),
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
const 开模态 = async (p, wait = 2400) => {
  const 钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!钮) return null;
  await p.mouse.click(钮[0], 钮[1]); await p.waitForTimeout(wait);
  return await p.evaluate(量);
};
const 关模态 = async (p) => { await p.keyboard.press('Escape'); await p.waitForTimeout(900); };

try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);

  // ---------- ① 抓声明：fetch 原始 CSS 文本，搜 801 ----------
  rec.样式表 = await p2.evaluate(async () => {
    const 表 = Array.from(document.styleSheets).map((s) => s.href).filter(Boolean);
    const 同源 = 表.filter((h) => { try { return new URL(h, location.href).origin === location.origin; } catch { return false; } });
    const 结果 = { 总数: 表.length, 同源数: 同源.length, href样例: 表.slice(0, 3), 抓到声明: [] };
    for (const h of 同源) {
      try {
        const txt = await (await fetch(h)).text();
        const idx = [];
        let i = -1;
        while ((i = txt.indexOf('801', i + 1)) !== -1 && idx.length < 6) {
          idx.push(txt.slice(Math.max(0, i - 110), i + 90).replace(/\s+/g, ' '));
        }
        if (idx.length) 结果.抓到声明.push({ href: h.slice(-60), 片段: idx });
      } catch (e) { /* 跨域或 CSP，跳过 */ }
    }
    return 结果;
  });
  console.log('样式表 =', JSON.stringify(rec.样式表).slice(0, 1200));
  落盘();

  // ---------- ② 区分判据：改根字号 16 → 20 ----------
  const 档 = [[500, 720, '窄宽'], [1280, 500, '窄高']];
  rec.基线 = []; rec.改字号后 = [];
  await s2.send('Emulation.setDeviceMetricsOverride', { width: 500, height: 720, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  const 基1 = await 开模态(p2); await 关模态(p2);
  await s2.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 500, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  const 基2 = await 开模态(p2); await 关模态(p2);
  rec.基线 = [{ 档: '窄宽500', 读数: 基1 }, { 档: '窄高500', 读数: 基2 }];
  console.log('基线 窄宽500 =', JSON.stringify(基1 && 基1.盒), ' 窄高500 =', JSON.stringify(基2 && 基2.盒));

  await p2.addStyleTag({ content: 'html { font-size: 20px !important; }' });
  await p2.waitForTimeout(1200);
  rec.字号已改 = await p2.evaluate(() => getComputedStyle(document.documentElement).fontSize);
  console.log('根字号改后 =', rec.字号已改);

  await s2.send('Emulation.setDeviceMetricsOverride', { width: 500, height: 720, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  const 改1 = await 开模态(p2); await 关模态(p2);
  await s2.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 500, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1500);
  const 改2 = await 开模态(p2); await 关模态(p2);
  rec.改字号后 = [{ 档: '窄宽500', 读数: 改1 }, { 档: '窄高500', 读数: 改2 }];
  console.log('改字号后 窄宽500 =', JSON.stringify(改1 && 改1.盒), ' 窄高500 =', JSON.stringify(改2 && 改2.盒));

  // 预测：若 32 = 2rem，20px 根字号 ⇒ 钳位变 40 ⇒ 500 视口下宽/高都应是 460
  rec.判定 = {
    基线宽: 基1 && 基1.盒[0], 改后宽: 改1 && 改1.盒[0], 基线高: 基2 && 基2.盒[1], 改后高: 改2 && 改2.盒[1],
    预测若rem: { 宽: 460, 高: 460 }, 预测若px: { 宽: 468, 高: 468 },
  };
  console.log('判定 =', JSON.stringify(rec.判定));

  // ---------- ③ 撤掉注入的样式并复原，确认可逆 ----------
  await p2.evaluate(() => { document.querySelectorAll('style').forEach((s) => { if ((s.textContent || '').includes('font-size: 20px')) s.remove(); }); return true; });
  await p2.waitForTimeout(900);
  await s2.send('Emulation.setDeviceMetricsOverride', { width: 500, height: 720, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1400);
  const 撤1 = await 开模态(p2); await 关模态(p2);
  rec.撤掉后 = { 根字号: await p2.evaluate(() => getComputedStyle(document.documentElement).fontSize), 读数: 撤1 };
  console.log('撤掉后 =', JSON.stringify({ 根字号: rec.撤掉后.根字号, 盒: 撤1 && 撤1.盒 }));

  断言('⓪ 根字号确实是 16 → 20 → 16 的往返，且注入可完全撤掉',
    rec.字号已改 === '20px' && rec.撤掉后.根字号 === '16px', { 改后: rec.字号已改, 撤后: rec.撤掉后.根字号 });
  断言('① 基线钳位 = 视口 − 32（500 视口 → 468），与 165-c 的定律自洽',
    基1 && 基1.盒[0] === 468 && 基2 && 基2.盒[1] === 468, { 基1: 基1 && 基1.盒, 基2: 基2 && 基2.盒 });
  const 是rem = 改1 && 改1.盒[0] === 460 && 改2 && 改2.盒[1] === 460;
  const 是px = 改1 && 改1.盒[0] === 468 && 改2 && 改2.盒[1] === 468;
  断言('② 判据**落在两侧之一**：要么 460（rem）要么 468（px），不允许第三种读数',
    是rem || 是px, rec.判定);
  rec.结论 = 是rem ? '那个 32 是 2rem（跟根字号走）' : (是px ? '那个 32 是写死的 px（与根字号无关）' : '两边都不是');
  console.log('🔑 结论 =', rec.结论);
  断言('③ 撤掉注入后钳位回到 468（可逆，没有留下副作用）',
    撤1 && 撤1.盒[0] === 468, { 撤后盒: 撤1 && 撤1.盒 });
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
} finally {
  try { if (p2) await p2.close(); } catch (e) { rec.关页签异常 = String(e).slice(0, 200); }
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('④ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    断言('⑤ 页签数回到 1', ctx.pages().length === 1, { 页签数: ctx.pages().length });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 400); }
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
