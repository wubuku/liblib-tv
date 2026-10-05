// 批次 168-a —— **检验一条刚刚被我写进手册的规律，看它是不是被过度推广了。**
//
// 🔑 靶子：批次 165–167 连着三批测出「对话框两侧各留 16 ⇒ 余量 32」，
//    很容易顺手推广成「所有面板都留 32px 余量」。
//    而**纯静态读 CSS 就看见反例**（零浏览器成本）：
//        .w-workspace-help-center{width:min(360px,calc(100vw - 32px))}   ← 横向 32
//        .h-workspace-help-center{height:min(648px,calc(100vh - 76px))}  ← **纵向 76**
//    ⇒ 「帮助中心」面板的纵向余量是 **76，不是 32**。本轮去把它打出来。
//
// 📐 可证伪的预测（两个门槛各取两侧一档）：
//   宽 = min(360, 视口宽 − 32)　　门槛 **392 / 391**
//   高 = min(648, 视口高 − 76)　　门槛 **724 / 723**
//   余量**对称**：高被夹住时上下各 38。CSS 里另有 `--workspace-chrome-top-bar-height:40px`，
//   但**相关不等于因果** ⇒ 只记读数，不替它编理由。
//
// ⛔ 只读：顶栏头像 → 用户菜单 →「帮助中心」，只开面板读数，不点任何设置项。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 高档 = [[1280, 800], [1280, 724], [1280, 723], [1280, 720], [1280, 600], [1280, 400]];
const 宽档 = [[1280, 720], [900, 720], [392, 720], [391, 720], [360, 720]];
const rec = { 批次: '168a', 目的: '验证 帮助中心 面板 宽=min(360,100vw−32) / 高=min(648,100vh−76)，检验「所有面板都 32px 余量」这条推广' };
let 断言过 = true, 断言数 = 0, 断言预期 = 6;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b168a.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读 = () => {
  let e = document.querySelector('.w-workspace-help-center');
  let 找法 = 'class .w-workspace-help-center';
  if (!e) {
    const 候选 = Array.from(document.querySelectorAll('[role=dialog],aside,section')).filter((x) => /帮助中心/.test(x.innerText || ''));
    e = 候选.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length)[0] || null;
    找法 = '按内文「帮助中心」找的最短容器';
  }
  if (!e) return { 找到: false, 视口: [innerWidth, innerHeight] };
  const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
  const 滚 = e.querySelector('[data-testid="shortcut-help-scroll-region"]') || e.querySelector('[role=region]');
  return {
    找到: true, 找法, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth, position: cs.position, overflow: cs.overflow },
    内联: e.getAttribute('style'),
    classList: (typeof e.className === 'string' ? e.className : '').split(/\s+/).filter(Boolean).slice(0, 12),
    滚动区: 滚 ? { 盒: [Math.round(滚.getBoundingClientRect().width), Math.round(滚.getBoundingClientRect().height)], scrollH: 滚.scrollHeight, clientH: 滚.clientHeight } : null,
    逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
  };
};

const 读共享 = async (p) => p.evaluate(() => ({
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  节点数: document.querySelectorAll('.react-flow__node').length,
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
try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);

  // ---- 打开「帮助中心」：按 aria 逐字找「用户菜单」，再轮询菜单项 ----
  // 🔴 168-a 第一版用「逐个试右上角按钮」的通用循环，六个候选全试完也没打开：
  //    逐字调试读出菜单项**确实存在**（`role=menuitem` / `帮助中心`）⇒ **错在找法，不在入口**。
  //    正解：**按 aria 逐字定位「用户菜单」**，再**轮询**菜单项（通用循环只等 1300ms，不够）。
  let 已开 = false;
  const 钮 = await p2.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '用户菜单');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  rec.入口 = { 按钮aria: '用户菜单', 落点: 钮 };
  if (钮) {
    await p2.mouse.click(钮[0], 钮[1]);
    let 项 = null;
    for (let k = 0; k < 10 && !项; k++) {
      await p2.waitForTimeout(600);
      项 = await p2.evaluate(() => { const it = Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim() === '帮助中心');
        if (!it) return null; const r = it.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    }
    if (项) { await p2.mouse.click(项[0], 项[1]); await p2.waitForTimeout(2800); 已开 = !!项; }
    rec.入口.菜单项落点 = 项;
  }
  断言('⓪ 能从顶栏打开「帮助中心」', 已开, { 入口: rec.入口 });
  if (!已开) throw new Error('没打开帮助中心');

  const 基线 = await p2.evaluate(读);
  rec.基线 = 基线;
  console.log('基线 =', JSON.stringify(基线.盒), '余量', JSON.stringify(基线.余量), '｜ 找法', 基线.找法);
  console.log('  classList =', JSON.stringify(基线.classList), '｜ 内联 =', 基线.内联);
  console.log('  滚动区 =', JSON.stringify(基线.滚动区));
  断言('① 1280×720 下读出 360×644（= min(360,100vw−32) × min(648,100vh−76)，**不是** 648）',
    基线.盒[0] === 360 && 基线.盒[1] === 644, 基线.盒);
  // 🔴 第一版断言② 我预测「余量对称 38/38」⇒ **被自己的读数否掉**：
  //    classList 逐字有 `fixed right-4 top-[60px] z-40` ⇒ 这个面板是**右上角钉住**的，
  //    **不居中**：上余量恒 **60**、右余量恒 **16** ⇒ **76 = 60 + 16（上偏移 + 边距）**，
  //    不是 38+38。**规律（min(648,100vh−76)）六档全对，错的是我对 76 的解释。**
  断言('② 面板**不居中**：上余量恒 60（`top-[60px]`）、右余量恒 16（`right-4`），上下**不对称**',
    Math.abs(基线.余量.上 - 60) <= 0.5 && Math.abs(基线.余量.右 - 16) <= 0.5 &&
    Math.abs(基线.余量.下 - 16) <= 0.5, { 余量: 基线.余量, classList: 基线.classList });
  await p2.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/126-help-center-panel-360x644.png', import.meta.url).pathname });
  rec.图 = 'screenshots/126-help-center-panel-360x644.png';
  落盘();

  rec.高档 = [];
  for (const [w, h] of 高档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1200);
    const z = await p2.evaluate(读);
    rec.高档.push(z);
    console.log(`  [高 ${w}×${h}] 盒 ${JSON.stringify(z.盒)} 余量上/下 ${z.余量 && z.余量.上}/${z.余量 && z.余量.下}`);
  }
  rec.宽档 = [];
  for (const [w, h] of 宽档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1200);
    const z = await p2.evaluate(读);
    rec.宽档.push(z);
    console.log(`  [宽 ${w}×${h}] 盒 ${JSON.stringify(z.盒)} 余量左/右 ${z.余量 && z.余量.左}/${z.余量 && z.余量.右}`);
  }
  const 预测高 = (h) => Math.min(648, h - 76);
  const 预测宽 = (w) => Math.min(360, w - 32);
  rec.预测 = { 高: 高档.map(([, h]) => 预测高(h)), 高实测: rec.高档.map((z) => z.盒 && z.盒[1]),
    宽: 宽档.map(([w]) => 预测宽(w)), 宽实测: rec.宽档.map((z) => z.盒 && z.盒[0]) };
  断言('③ 高度六档与 min(648, 100vh−76) 逐档相同（含 724/723 门槛两侧）',
    rec.高档.every((z, i) => z.找到 && z.盒[1] === 预测高(高档[i][1])), rec.预测);
  断言('④ 宽度五档与 min(360, 100vw−32) 逐档相同（含 392/391 门槛两侧）',
    rec.宽档.every((z, i) => z.找到 && z.盒[0] === 预测宽(宽档[i][0])), rec.预测);
  断言('⑤ 门槛成立：724 档读出 648、723 档读出 647',
    rec.高档.find((z) => z.视口[1] === 724).盒[1] === 648 && rec.高档.find((z) => z.视口[1] === 723).盒[1] === 647, rec.预测);
  断言('⑥ 全程面板都还在（resize 不会把它关掉）',
    [...rec.高档, ...rec.宽档].every((z) => z.找到), null);
  落盘();
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 900); console.log('异常', rec.异常); 断言过 = false;
} finally {
  try { if (p2) await p2.close(); } catch (e) {}
  try {
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    rec.共享收尾 = await 读共享(shared);
    console.log('共享视口已复位', JSON.stringify(rec.复位), '｜ 数据', JSON.stringify(rec.共享收尾));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 300); }
  if (断言数 < 断言预期) { console.log(`⛔ 断言只跑了 ${断言数}/${断言预期} 条 —— 中途崩了`); 断言过 = false; }
  rec.断言执行数 = 断言数; rec.断言预期数 = 断言预期; rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
