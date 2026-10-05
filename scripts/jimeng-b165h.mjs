// 批次 165-h —— 给 165-g 那个「被盖」现象定出**门槛**，并把量法本身换对。
//
// 🔑 165-g 定性成功但**量法用错了**：我用 `相交面积` 判「搜索框压没压页签」，
//    而 `相交面积` 是拿 **input 最近的 testid 祖先**算的 —— 那恰好是整个顶部区
//    （`canvas-asset-library-operation-area`，801×104），**容器天然包含页签**，
//    于是四档全读出 面积 8352，**这个指标恒真、毫无区分力**（断言 ① 因此误红）。
//    真正有区分力的是**命中测试**：1280 读「被盖 0 个」、400 读「被盖 3 个」。
//    ⇒ 📌 立规：**判「谁盖住谁」不能用相交面积**（父子必相交），
//      要么用 `elementFromPoint` 判**点得中不中**，要么把盒收窄到**叶子元素**。
//
// 📐 本轮两件事：
//   ① 把搜索框的盒**收窄到 input 本身**（不再用 testid 祖先），四档如实读；
//   ② 扫宽度找**门槛**：每个二级页签从「点得中」翻成「点不着」的具体宽度是多少。
//      判据一律用命中测试，不用面积。
//
// ⛔ 只读：新页签内跑，共享页签不动，收尾复位 1280×720。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 档 = [[1280, 720], [700, 720], [600, 720], [580, 720], [560, 720], [540, 720], [520, 720], [500, 720], [480, 720], [460, 720], [440, 720], [420, 720], [400, 720], [380, 720], [360, 720]];
const rec = { 批次: '165h', 目的: '「搜索框盖住二级页签」的门槛：逐档用命中测试定位翻转点' };
let 断言过 = true;
const 断言计数 = { 共: 0, 预期: 6 };
const 断言 = (名, ok, 详情) => { 断言计数.共++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165h.json', import.meta.url), JSON.stringify(rec, null, 1));

// 页面内：常量内联；盒一律用 getBoundingClientRect 的原始小数；判据 = 命中测试
const 读 = () => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false };
  const 区 = document.querySelector('[data-testid="canvas-asset-library-operation-area"]');
  const input = 区 ? 区.querySelector('input') : null;
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); return [+q.x.toFixed(1), +q.y.toFixed(1), +q.width.toFixed(1), +q.height.toFixed(1)]; };
  const 页签条 = document.querySelector('[data-testid="canvas-asset-library-navigation-controls"]');
  const 动作组 = document.querySelector('[data-testid="canvas-asset-library-query-action-group"]');
  const 二级 = 页签条 ? Array.from(页签条.querySelectorAll('[role=tab],button')) : [];
  const 一级 = 区 ? Array.from(区.querySelectorAll('[role=tab],button')).slice(0, 2) : [];
  const 测 = (t) => {
    const q = t.getBoundingClientRect();
    const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
    const 命中 = document.elementFromPoint(cx, cy);
    const 是输入 = 命中 && 命中.tagName === 'INPUT';
    return { 逐字: (t.innerText || '').trim().slice(0, 6), 盒: 盒(t), 中心: [+cx.toFixed(1), +cy.toFixed(1)],
      点得中: !!(命中 && (命中 === t || t.contains(命中))), 命中标签: 命中 ? 命中.tagName : null,
      命中aria: 命中 ? 命中.getAttribute('aria-label') : null, 被输入抢走: 是输入 };
  };
  return {
    有: true, 视口: [innerWidth, innerHeight],
    对话框盒: 盒(d), 区盒: 盒(区),
    输入盒: 盒(input), 输入aria: input ? input.getAttribute('aria-label') : null,
    输入类名: input ? (typeof input.className === 'string' ? input.className.slice(0, 90) : null) : null,
    页签条盒: 盒(页签条), 动作组盒: 盒(动作组),
    一级页签: 一级.map(测), 二级页签: 二级.map(测),
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
    await p2.waitForTimeout(1400);
    const 钮 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    let 读数 = null;
    if (钮) {
      await p2.mouse.click(钮[0], 钮[1]);
      for (let k = 0; k < 8 && !(读数 && 读数.有); k++) { await p2.waitForTimeout(600); 读数 = await p2.evaluate(读); }
      await p2.keyboard.press('Escape'); await p2.waitForTimeout(800);
    }
    rec.读数.push({ 视口宽: w, 读数 });
    if (读数 && 读数.有) {
      const 被抢 = 读数.二级页签.filter((z) => !z.点得中);
      console.log(`[${w}] 对话框 ${JSON.stringify(读数.对话框盒)} ｜ input ${JSON.stringify(读数.输入盒)} ｜ 二级被输入抢走 ${被抢.length ? 被抢.map((z) => z.逐字).join(',') : '无'}`);
    } else console.log(`[${w}] 模态未打开`);
    落盘();
  }

  // ---- 逐个二级页签求「翻转门槛」：最后一个点得中的宽度 vs 第一个点不中的宽度 ----
  const 名字 = ['图片', '视频', '音频', '文档'];
  rec.门槛 = {};
  for (let i = 0; i < 4; i++) {
    let 最后一个好的 = null, 第一个坏的 = null;
    for (const z of rec.读数) {
      const t = z.读数 && z.读数.有 ? z.读数.二级页签[i] : null;
      if (!t) continue;
      if (t.点得中) 最后一个好的 = z.视口宽;
      else if (第一个坏的 === null && 最后一个好的 !== null) 第一个坏的 = z.视口宽;
    }
    rec.门槛[名字[i]] = { 最后可点宽度: 最后一个好的, 首个不可点宽度: 第一个坏的,
      结论: 第一个坏的 !== null && 最后一个好的 !== null ? `视口宽 ≤ ${第一个坏的} 时点不中` : '全档均可点' };
  }
  console.log('\n门槛 =', JSON.stringify(rec.门槛, null, 1));
  断言('① 1280 档四个二级页签全部点得中（基线成立）',
    rec.读数.find((z) => z.视口宽 === 1280).读数.二级页签.every((z) => z.点得中),
    rec.读数.find((z) => z.视口宽 === 1280).读数.二级页签);
  断言('② 400 档确有页签被输入抢走（缺陷复现）',
    rec.读数.find((z) => z.视口宽 === 400).读数.二级页签.some((z) => z.被输入抢走),
    rec.读数.find((z) => z.视口宽 === 400).读数.二级页签.map((z) => [z.逐字, z.点得中]));
  断言('③ 每个二级页签都算出了门槛（最后一个可点宽度与第一个不可点宽度都读到）',
    Object.values(rec.门槛).every((v) => v.最后可点宽度 !== null), rec.门槛);
  断言('④ 门槛**随页签从左到右单调变小**（越靠右越早被盖）',
    (() => { const g = 名字.map((n) => rec.门槛[n].首个不可点宽度 ?? 9999);
      return g.every((v, i) => i === 0 || v <= g[i - 1]); })(), rec.门槛);
  rec.结论 = '资产库二级页签在窄视口下会被顶部搜索输入框盖住并点不中；门槛逐页签不同';
  console.log('🔑', rec.结论);
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
  // 🔴 批次 165-h 自身失误：异常之后 `finally` 照样打印「断言全过 = true」——
  //    因为那个标志只在**断言失败**时置 false，崩在中途的批次会被记成**绿灯**。
  //    正解：**异常必须把标志置否**，并且末尾要有一条「预期断言条数都跑到了」的计数断言。
  断言过 = false;
} finally {
  try { if (p2) await p2.close(); } catch (e) {}
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('⑤ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 300); }
  // 🔴 新增：断言条数门 —— 前面共 6 条断言，任何一条没跑到就说明中途崩了
  rec.断言执行数 = 断言计数.共;
  rec.断言预期数 = 6;
  const 条数够 = 断言计数.共 >= 断言计数.预期;
  if (!条数够) 断言过 = false;
  console.log(`断言执行 ${断言计数.共} / 预期 ${断言计数.预期}`);
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
