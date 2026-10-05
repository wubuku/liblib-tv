// 批次 165-a —— 把「宽 = 视口−480、高 = 视口−100」这条**待验猜测**测成事实或否掉。
//
// 🔑 靶子（SOURCE_OBSERVATIONS §4.05.4 第 1 条 / assets-and-upload.md:93 与 :393）：
//   模态在 1280×720 下量到 `801×620@240,50`，余量「左 240 / 右 239 / 上 50 / 下 50」。
//   当时写下的推断是「宽 = 视口−480、高 = 视口−100」，并**自己标注为待验猜测**，
//   理由是「换视口会污染共享会话里钉死的 1280×720」。
//
// 🆕 本批的解法（不污染共享会话）：
//   **在同一个浏览器上下文里新开一个页签**（共享 cookie ⇒ 同一登录态），
//   只对**新页签**发 `Emulation.setDeviceMetricsOverride`，共享页签的视口**一个像素都不动**。
//   ⇒ 「换分辨率污染共享会话」这个阻塞理由在本轮**不成立**。
//
// 📐 同时做第二件事：量到数值只说明「是什么」，**读它自己的样式表**才能说明「为什么」。
//   走 document.styleSheets 找管辖 `canvas-asset-library-dialog` 的规则，把 width/height
//   声明逐字取出来 —— 若声明里是 `vw/vh/calc/min()`，定律就有了机制解释；
//   若是一个固定 px，那 1280 下那个「差 480 / 差 100」就是**巧合**。
//
// ⛔ 全程只读：只开「资产库」这一个模态再 Esc 关掉。
//    不建节点、不上传、不点「确认/保存」、不点任何生成按钮、不动积分。
// 🔴 收尾硬要求：关掉自己开的页签，并断言**共享页签**的视口/节点数/积分/浮层与起点逐项一致。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 视口表 = [[1280, 720], [1440, 900], [1680, 1050]];
const rec = { 批次: '165a', 目的: '第二个视口样本：判定「宽=视口−480 / 高=视口−100」这条猜测成立与否' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165a.json', import.meta.url), JSON.stringify(rec, null, 1));

const 层清单 = ['canvas-asset-library-surface', 'canvas-asset-library-operation-area',
  'canvas-asset-library-navigation-controls', 'canvas-asset-library-query-action-group',
  'canvas-asset-library-viewport', 'canvas-asset-library-footer',
  'canvas-asset-library-import-status', 'canvas-asset-library-box-selection'];

// 🔴 批次 165-a 自身失误 1：上面那个 `层清单` 是 **Node 侧**的 const，
//    `p.evaluate` 的函数体在浏览器里跑，**闭包不跨进程** ⇒ 第一轮直接 ReferenceError。
//    ⇒ 页面内函数用到的每个常量都必须**内联进函数体**，不能靠闭包带进去。
const 量模态 = () => {
  const 层清单 = ['canvas-asset-library-surface', 'canvas-asset-library-operation-area',
    'canvas-asset-library-navigation-controls', 'canvas-asset-library-query-action-group',
    'canvas-asset-library-viewport', 'canvas-asset-library-footer',
    'canvas-asset-library-import-status', 'canvas-asset-library-box-selection'];
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false, 视口: [innerWidth, innerHeight] };
  const r = d.getBoundingClientRect();
  const cs = getComputedStyle(d);
  const 盒 = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; };
  return {
    有: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    计算样式: { width: cs.width, height: cs.height, maxWidth: cs.maxWidth, maxHeight: cs.maxHeight,
      minHeight: cs.minHeight, position: cs.position, resize: cs.resize, overflow: cs.overflow },
    层: Object.fromEntries(层清单.map((t) => { const e = document.querySelector(`[data-testid="${t}"]`); return [t, e ? 盒(e) : null]; })),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
  };
};
const 读规则 = () => {
  const 命中 = [];
  const 走 = (rules) => {
    for (const rule of rules) {
      if (rule.cssRules) { 走(rule.cssRules); continue; }
      if (!rule.selectorText) continue;
      if (!/asset-library-(dialog|surface|viewport|footer)\b/.test(rule.selectorText)) continue;
      const css = rule.style.cssText;
      if (!/width|height|inset|position/.test(css)) continue;
      命中.push({ 选择器: rule.selectorText.slice(0, 220), 声明: css.slice(0, 320) });
    }
  };
  for (const s of document.styleSheets) { try { 走(s.cssRules); } catch (e) { /* 跨域样式表读不到，跳过 */ } }
  return 命中;
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

// 🔴 共享视口轨迹：用来**归因**「视口被谁改了」。
//   上一轮跑完发现共享页签从 1280×720 变成 1920×873（本轮只对新页签发过 override），
//   在归因之前不能写成「是我改的」也不能写成「不是我改的」⇒ 只能把时间线记下来。
rec.共享轨迹 = [];
const 轨迹 = async (标签) => {
  const v = await shared.evaluate(() => [innerWidth, innerHeight]);
  rec.共享轨迹.push({ 标签, 视口: v });
  console.log('  共享视口 · ' + 标签 + ' = ' + JSON.stringify(v));
  return v;
};
await 轨迹('起点');

let p2 = null;
try {
  // ============ ① 在共享上下文里新开页签（同登录态），只改它的视口 ============
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);                       // 批次 29 教训：reload 后至少 6.5s 才断言
  rec.新页签 = await p2.evaluate(() => ({
    视口: [innerWidth, innerHeight], url: location.href,
    有画布壳: !!document.querySelector('.react-flow__wrapper, [rf__wrapper]'),
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    body前120: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
  }));
  console.log('新页签就绪', JSON.stringify(rec.新页签));
  await 轨迹('新页签加载后');
  // 📌 壳选择器 `.react-flow__wrapper, [rf__wrapper]` 实测读出 false（与共享页签不同），
  //    判据改用**看得见的读数**（节点数 / 状态行 / 积分），不靠一个读不到的选择器。
  断言('ⓑ 新页签的**数据**与共享页签逐项一致（节点数/状态行/积分）',
    rec.新页签.节点数 === rec.共享起点.节点数 && rec.新页签.状态行 === rec.共享起点.状态行 &&
    String(rec.新页签.积分) === String(rec.共享起点.积分), { 新页签: rec.新页签, 共享起点: rec.共享起点 });
  断言('⓪ 新页签 body 上确实画出了这一份画布（不是登录页/空壳）',
    /76 nodes/.test(rec.新页签.body前120 || ''), rec.新页签.body前120);
  落盘();

  const s2 = await p2.context().newCDPSession(p2);
  rec.读数 = [];
  for (const [w, h] of 视口表) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1600);
    await 轨迹('对新页签 override ' + w + '×' + h + ' 之后');
    const 实视口 = await p2.evaluate(() => [innerWidth, innerHeight]);
    // 点开资产库模态（按 aria-label，不靠坐标记忆）
    const 钮 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    const 行 = { 视口: 实视口, 按钮落点: 钮, 规则: await p2.evaluate(读规则), 模态: null };
    if (钮) {
      await p2.mouse.click(钮[0], 钮[1]);
      // 🔴 批次 153 教训：开模态后**不许**调 settle()（它会连按 Esc 把模态关掉），只等
      let 模态 = null;
      for (let k = 0; k < 8 && !(模态 && 模态.有); k++) { await p2.waitForTimeout(700); 模态 = await p2.evaluate(量模态); }
      行.模态 = 模态;
      if (w === 1440 && 模态 && 模态.有) {
        await p2.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/123-asset-library-1440x900.png', import.meta.url).pathname });
        行.截图 = 'screenshots/123-asset-library-1440x900.png';
      }
      await p2.keyboard.press('Escape');
      await p2.waitForTimeout(1200);
      行.关后浮层 = await p2.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
        .filter((m) => m.getBoundingClientRect().width > 1).length);
    }
    rec.读数.push(行);
    console.log(`\n[${w}×${h}] 视口实测 ${JSON.stringify(实视口)}`);
    console.log('  模态盒 =', JSON.stringify(行.模态 && 行.模态.盒), '余量 =', JSON.stringify(行.模态 && 行.模态.余量));
    console.log('  样式 =', JSON.stringify(行.模态 && 行.模态.计算样式));
    落盘();
  }

  // ============ ② 判定：三个视口下宽/高各自是什么函数 ============
  const 宽 = rec.读数.map((z) => (z.模态 && z.模态.有 ? z.模态.盒[0] : null));
  const 高 = rec.读数.map((z) => (z.模态 && z.模态.有 ? z.模态.盒[1] : null));
  rec.判定 = { 视口: 视口表, 宽序列: 宽, 高序列: 高 };
  断言('① 三个视口都量到了模态', rec.读数.every((z) => z.模态 && z.模态.有), rec.判定);
  断言('② 宽度**不随**视口变（推翻「宽 = 视口−480」）', new Set(宽).size === 1, rec.判定);
  断言('③ 高度**不随**视口变（推翻「高 = 视口−100」）', new Set(高).size === 1, rec.判定);
  断言('④ 水平居中在三个视口都成立（左余量 ≈ 右余量，差 ≤ 1）',
    rec.读数.every((z) => z.模态 && z.模态.有 && Math.abs(z.模态.余量.左 - z.模态.余量.右) <= 1), rec.读数.map((z) => z.模态 && z.模态.余量));
  断言('⑤ 垂直居中在三个视口都成立（上余量 ≈ 下余量，差 ≤ 1）',
    rec.读数.every((z) => z.模态 && z.模态.有 && Math.abs(z.模态.余量.上 - z.模态.余量.下) <= 1), rec.读数.map((z) => z.模态 && z.模态.余量));
  const 规则集 = rec.读数[0].规则 || [];
  rec.规则数 = 规则集.length;
  断言('⑥ 读到了管辖该模态的样式规则（读得到 = 同源样式表）', 规则集.length > 0, { 规则数: 规则集.length });
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
} finally {
  try { if (p2) { await 轨迹('关闭新页签之前'); await p2.close(); rec.已关新页签 = true; } } catch (e) { rec.关页签异常 = String(e).slice(0, 300); }
  await 轨迹('关闭新页签之后');
  try {
    rec.共享收尾 = await 读共享(shared);
    console.log('共享页签收尾', JSON.stringify(rec.共享收尾));
    // 📌 判据分两层：**数据**不变量严格比；**视口**单独归因（它可能被别的会话改动，
    //    把它并进同一条断言会让「别人的改动」记成「我的失败」，反之亦然）。
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('⑦ 共享页签的**数据**一个都没变（状态行/节点数/选中/浮层/积分）',
      rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异, 起点: rec.共享起点, 收尾: rec.共享收尾 });
    断言('⑧ 页签数回到 1（自己开的那一个已关）', ctx.pages().length === 1, { 页签数: ctx.pages().length });
    // 共享视口若已偏离手册约定的 1280×720，按仓库约定复位，并**如实标注归因未知**
    if (rec.共享收尾.视口[0] !== 1280 || rec.共享收尾.视口[1] !== 720) {
      const { pinViewport } = await import('./jimeng-safe-keys.mjs');
      rec.复位 = await pinViewport(shared);
      rec.复位归因 = '未知：本批只对新页签发过 override，但无法证明不是本批引起的';
      console.log('已把共享视口复位到', JSON.stringify(rec.复位));
      await 轨迹('复位之后');
    } else {
      rec.复位 = '起点即为 1280×720，无需复位';
    }
  } catch (e) { rec.共享收尾异常 = String(e).slice(0, 400); }
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
