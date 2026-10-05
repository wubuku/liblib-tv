// 批次 165-g —— 顺着「窄视口」这条线，撞到一个**眼睛先看见、断言却没看见**的东西。
//
// 🔑 起因：165-c 拍的极窄档截图（400×720）里，资产库顶部的**搜索框压在二级页签上**
//   （「视频 / 音频 / 文档」三个页签被盖掉半截）。而 165-c 的断言 ⑤ 判的是
//   「页签条 vs 动作组是否重叠」—— 读出 **false**（页签条右缘 272 < 动作组左缘 285）⇒ **通过**。
//   ⇒ 📌 **这条断言问错了对象**：真正压在页签上的是**搜索框**，不是动作组。
//      它从一开始就没进过断言。
//
// 📐 本轮把「看起来重叠」变成 DOM 级读数，三件事：
//   ① 定位搜索框（先按 testid，再退到 aria `Search Dreamina assets`），量它与页签条的**相交面积**；
//   ② **命中测试**：逐个二级页签的中心点调 `document.elementFromPoint`，
//      看拿到的是页签自己还是搜索框 —— 「盖住」的硬证据不是面积，是**点不中**；
//   ③ 对照档 1280 / 900 / 700 / 400，确认这是**窄视口特有**而不是一直如此。
//
// ⛔ 只读：只开资产库模态再 Esc；新页签里跑，共享页签不动，收尾复位 1280×720。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 档 = [[1280, 720], [900, 720], [700, 720], [400, 720]];
const rec = { 批次: '165g', 目的: '窄视口下搜索框是否压住二级页签：用相交面积 + 命中测试定性' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165g.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读 = () => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false };
  const 区 = document.querySelector('[data-testid="canvas-asset-library-operation-area"]');
  // 搜索框：先 testid，再退到 aria，最后退到区内的 input
  const 输入 = 区 ? Array.from(区.querySelectorAll('input')) : [];
  const s = 输入[0] || null;
  const 宿主 = s ? (s.closest('[data-testid]') || s.parentElement) : null;
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); return { x: +q.x.toFixed(1), y: +q.y.toFixed(1), w: +q.width.toFixed(1), h: +q.height.toFixed(1) }; };
  const 页签条 = document.querySelector('[data-testid="canvas-asset-library-navigation-controls"]');
  const 动作组 = document.querySelector('[data-testid="canvas-asset-library-query-action-group"]');
  // 二级页签：页签条内 role=tab 的元素
  const 二级 = 页签条 ? Array.from(页签条.querySelectorAll('[role=tab],button')) : [];
  const 相交 = (a, b) => {
    if (!a || !b) return null;
    const x = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
    const y = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
    return { w: +x.toFixed(1), h: +y.toFixed(1), 面积: +(x * y).toFixed(0) };
  };
  const s盒 = 盒(宿主);
  const 页签盒 = 盒(页签条);
  return {
    有: true, 视口: [innerWidth, innerHeight],
    搜索: { testid: 宿主 ? 宿主.getAttribute('data-testid') : null,
      aria: s ? s.getAttribute('aria-label') : null, 占位: s ? s.getAttribute('placeholder') : null,
      盒: s盒, 类名: 宿主 ? (typeof 宿主.className === 'string' ? 宿主.className.slice(0, 80) : null) : null },
    页签条盒: 页签盒, 动作组盒: 盒(动作组),
    相交搜索与页签条: 相交(s盒, 页签盒),
    相交搜索与动作组: 相交(s盒, 盒(动作组)),
    二级页签: 二级.map((t) => {
      const q = t.getBoundingClientRect();
      const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
      const 命中 = document.elementFromPoint(cx, cy);
      return {
        逐字: (t.innerText || '').trim().slice(0, 6), aria: t.getAttribute('aria-label'),
        盒: [+cx.toFixed(1), +cy.toFixed(1), Math.round(q.width), Math.round(q.height)],
        中心命中的是: 命中 ? { 标签: 命中.tagName, testid: 命中.getAttribute('data-testid'), aria: 命中.getAttribute('aria-label'), 逐字: (命中.innerText || '').trim().slice(0, 8), 在搜索内: !!(s && (命中 === s || (宿主 && 宿主.contains(命中)))) } : null,
        中心命中本页签: 命中 ? !!(命中 === t || t.contains(命中)) : null,
      };
    }),
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

let p2 = null;
try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);
  rec.读数 = [];
  for (const [w, h] of 档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1500);
    const 钮 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    let 读数 = null;
    if (钮) {
      await p2.mouse.click(钮[0], 钮[1]);
      for (let k = 0; k < 8 && !(读数 && 读数.有); k++) { await p2.waitForTimeout(650); 读数 = await p2.evaluate(读); }
      await p2.keyboard.press('Escape'); await p2.waitForTimeout(900);
    }
    rec.读数.push({ 视口: [w, h], 读数 });
    const 被盖 = (读数 ? 读数.二级页签.filter((z) => z.中心命中本页签 === false) : []);
    console.log(`\n[${w}×${h}] 搜索盒 ${JSON.stringify(读数 && 读数.搜索 && 读数.搜索.盒)} ｜ 与页签条相交 ${JSON.stringify(读数 && 读数.相交搜索与页签条)}`);
    console.log('   二级页签中心命中：' + (读数 ? 读数.二级页签.map((z) => `${z.逐字}:${z.中心命中本页签 ? '✅自己' : '❌' + (z.中心命中的是 ? z.中心命中的是.标签 + '/' + (z.中心命中的是.aria || '') : '')}`).join('  ') : ''));
    if (被盖.length) console.log('   ⛔ 被盖页签 =', JSON.stringify(被盖.map((z) => z.逐字)));
    落盘();
  }
  const 宽档 = rec.读数.find((z) => z.视口[0] === 1280), 窄档 = rec.读数.find((z) => z.视口[0] === 400);
  rec.判定 = {
    宽档相交: 宽档.读数.相交搜索与页签条, 窄档相交: 窄档.读数.相交搜索与页签条,
    宽档被盖数: 宽档.读数.二级页签.filter((z) => z.中心命中本页签 === false).length,
    窄档被盖数: 窄档.读数.二级页签.filter((z) => z.中心命中本页签 === false).length,
    窄档搜索testid: 窄档.读数.搜索.testid, 窄档搜索aria: 窄档.读数.搜索.aria,
  };
  断言('① 1280 档：搜索框与页签条**不相交**，四个页签中心全部命中自己',
    宽档.读数.相交搜索与页签条.面积 === 0 && rec.判定.宽档被盖数 === 0, rec.判定);
  断言('② 400 档：搜索框与页签条**有相交**，且确有页签点不中（真被盖）',
    窄档.读数.相交搜索与页签条.面积 > 0 && rec.判定.窄档被盖数 > 0, rec.判定);
  断言('③ 700 档是分界参考档（读数如实记下，不断言哪一边）', !!窄档.读数.有, null);
  console.log('\n判定 =', JSON.stringify(rec.判定, null, 1));
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
} finally {
  try { if (p2) await p2.close(); } catch (e) {}
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('④ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 300); }
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
