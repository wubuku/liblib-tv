// 批次 200 a 轮：隔离批次 199 指出的那个**未排查变量** —— 「点第一条结果」在不同视口下
// 未必是同一个节点。
//
// 背景链：
//   批次 197：六档视口下「落点Y − 高/2」在 1280 宽三档是 −100 上下、其余三档是 0
//   批次 198：找到了 ty 的两组分支，并否掉了「初始平移随宽度变」
//   批次 199：留下一个没排查的变量 —— 批次 197 记过 **1600×900 那档结果行数是 13 条、
//             其余档是 10 条**，而两轮都点的是「第一条」
//             ⇒ 不同视口下「第一条」**未必是同一个节点**
//
// 📌 立规 77 的配套：固定点第 N 条这类操作，**要先把点的对象的 id 读出来**，别假定它不变。
//
// 🔴 本轮做法（把那个变量**显式化**）：
//   每档不只点「第一条」，而是**把前 3 条的 testid 全部读出来**，并**分别点**其中
//   **同一个 testid**（若存在）在 6 档视口下的落点。
//   ⇒ 若「同一个 testid」的落点跨视口**一致**，那变量就不是「点的对象变了」；
//   ⇒ 若**不一致**，那就定位到了。
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 视口集 = [
  { 名: '1000x720', w: 1000, h: 720 }, { 名: '1200x720', w: 1200, h: 720 },
  { 名: '1280x600', w: 1280, h: 600 }, { 名: '1280x720', w: 1280, h: 720 },
  { 名: '1280x840', w: 1280, h: 840 }, { 名: '1600x900', w: 1600, h: 900 },
];
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b200a', 假设: '「点的第一条」在不同视口下未必是同一个节点；把前 3 条的 testid 全读出来并对同一个 testid 逐档取景' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

out.档 = {};
for (const v of 视口集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: v.w, height: v.h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!搜索钮) { out.档[v.名] = { 中止: '找不到搜索钮' }; continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1400);
    await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
      if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
        e.dispatchEvent(new Event('input', { bubbles: true })); } });
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2200);

    // 📌 前 5 条的 testid 全部读出来（不假定顺序稳定）
    const 前5 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]'))
      .slice(0, 5).map((e, i) => ({ 第几条: i + 1, testid: e.getAttribute('data-testid'),
        aria: e.getAttribute('aria-label'), 屏上: (() => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); })() })));
    const 总条数 = await p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length);
    log(`\n=== ${v.名} === 总条数 ${总条数}`);
    for (const r of 前5) log(`   第${r.第几条}条 ${r.testid} :: ${r.aria}`);

    const 逐条取景 = [];
    for (const target of 前5.slice(0, 3)) {
      // 关掉面板重开，保证每次都是从同一起点起（避免上一条的影响）
      await p.keyboard.press('Escape'); await p.waitForTimeout(800);
      const pt = await p.evaluate((tid) => {
        const e = document.querySelector(`[data-testid="${tid}"]`); if (!e) return null;
        const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, target.testid);
      if (!pt) { 逐条取景.push({ testid: target.testid, 跳过: '面板重开后该行不在（可能不在首页）' }); continue; }
      await p.mouse.click(pt[0], pt[1]);
      // 连采 5 帧，等收敛
      const 帧 = [];
      for (let k = 0; k < 5; k++) {
        帧.push(await p.evaluate((tid) => {
          const id = tid.replace('canvas-search-result-node_', 'node_');
          const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
          const r = n.getBoundingClientRect();
          const vp = document.querySelector('.react-flow__viewport');
          const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
          return { 中心: [Math.round((r.x + r.width / 2) * 10000) / 10000, Math.round((r.y + r.height / 2) * 10000) / 10000],
            屏上: [r.x, r.y, r.width, r.height].map((q) => Math.round(q * 10000) / 10000),
            vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
        }, target.testid));
        await p.waitForTimeout(600);
      }
      const 末 = 帧[帧.length - 1];
      逐条取景.push({ testid: target.testid, 第几条: target.第几条, aria: target.aria,
        末中心: 末.中心, 末屏上: 末.屏上, 末vp: 末.vp,
        中心X取值: [...new Set(帧.map((f) => f.中心 && f.中心[0]))], 中心Y取值: [...new Set(帧.map((f) => f.中心 && f.中心[1]))] });
      log(`   点「${target.testid}」→ 中心 ${JSON.stringify(末.中心)} | vp ${JSON.stringify(末.vp)} | X取值 ${JSON.stringify([...new Set(帧.map((f) => f.中心 && f.中心[0]))])}`);
    }
    out.档[v.名] = { 总条数, 前5, 逐条取景 };
  } catch (e) { out.档[v.名] = { 出错: e.message }; log(v.名, '🔴', e.message); }
  finally { await p.close(); }
}

fs.writeFileSync('/tmp/b200a.json', JSON.stringify(out, null, 1));
out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
await b.close();
