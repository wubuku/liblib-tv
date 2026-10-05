// 批次 165-c —— 165-b 把 P2 **证伪了**：模态在窄视口下**会被压窄**（801 → 769 → 668），
// 而不是像我预测的那样「溢出」。这轮把真实的水平定律与它的门槛测出来，并找出机制。
//
// 🔑 165-b 的读数（视口宽 → 对话框宽）：1280→801 ｜ 900→801 ｜ 801→**769** ｜ 700→**668**
//    769 = 801 − 32 ｜ 668 = 700 − 32 ⇒ 猜「宽 = min(801, 视口宽 − 32)」，
//    **门槛在 801 + 32 = 833**（≥833 走定尺 801，≤832 走「视口−32」）。
//    而垂直侧 165-b 已实测同一个 32：门槛 620 + 32 = 652。**两侧同一个 32，很像同一个容器内边距。**
//
// 📐 本轮两件事：
//   ① 打宽度门槛：[900 / 833 / 832 / 700 / 400] 五档，验证 833/832 这对边界；
//   ② 读**祖先链**的 computed style：对话框自己写着 `width: 801px` 且 `max-width: none`，
//      却在窄容器里被压窄 ⇒ 嫌疑是**祖先是 flex 容器、自身 flex-shrink 生效**。
//      把父链的 display / padding / flex 一层层读出来，让机制说话而不是猜。
//
// ⛔ 只读：只开资产库模态再 Esc。收尾把共享视口复位到 1280×720。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 宽度档 = [[900, 720], [833, 720], [832, 720], [700, 720], [400, 720]];
const rec = { 批次: '165c', 目的: '宽度定律的门槛（833/832）与「为什么会被压窄」的祖先链机制' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165c.json', import.meta.url), JSON.stringify(rec, null, 1));

// 🔴 页面内函数不得依赖外部闭包常量（165-a 自身失误 1），常量全部内联。
const 量 = () => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 有: false, 视口: [innerWidth, innerHeight] };
  const r = d.getBoundingClientRect();
  const cs = getComputedStyle(d);
  // ---- 祖先链：每层的盒 + display + padding + flex ----
  const 链 = [];
  let e = d;
  for (let i = 0; i < 5 && e && e !== document.documentElement; i++) {
    const q = e.getBoundingClientRect(), s = getComputedStyle(e);
    链.push({
      层: i, 标签: e.tagName, testid: e.getAttribute('data-testid'), cls: (typeof e.className === 'string' ? e.className : '').slice(0, 70),
      盒: [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)],
      display: s.display, position: s.position, padding: s.padding, flex: s.flex, flexDirection: s.flexDirection,
      overflow: s.overflow, width: s.width, maxWidth: s.maxWidth, height: s.height, maxHeight: s.maxHeight,
      justifyContent: s.justifyContent, alignItems: s.alignItems,
    });
    e = e.parentElement;
  }
  const 自有 = { width: cs.width, maxWidth: cs.maxWidth, flex: cs.flex, flexShrink: cs.flexShrink, flexBasis: cs.flexBasis, minWidth: cs.minWidth, height: cs.height, maxHeight: cs.maxHeight, boxSizing: cs.boxSizing };
  // 顶部两组的「有没有互相压住 / 有没有超出对话框」——
  const g = (t) => document.querySelector(`[data-testid="${t}"]`);
  const b = (x) => { if (!x) return null; const q = x.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const 页签条 = g('canvas-asset-library-navigation-controls'), 动作组 = g('canvas-asset-library-query-action-group'), 区 = g('canvas-asset-library-operation-area');
  return {
    有: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    自有样式: 自有, 祖先链: 链,
    顶部: { 区: b(区), 页签条: b(页签条), 动作组: b(动作组),
      动作组右缘超出对话框: 动作组 ? Math.round(动作组.getBoundingClientRect().right) > Math.round(r.right) : null,
      两组是否重叠: (页签条 && 动作组) ? (页签条.getBoundingClientRect().right > 动作组.getBoundingClientRect().left) : null },
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110),
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
try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);
  rec.读数 = [];
  for (const [w, h] of 宽度档) {
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
    const 行 = { 视口: [w, h], 按钮落点: 钮, 模态 };
    rec.读数.push(行);
    console.log(`  [${w}×${h}] 盒 ${JSON.stringify(模态 && 模态.盒)} 预测宽 ${w >= 833 ? 801 : w - 32} 余量 ${JSON.stringify(模态 && 模态.余量)}`);
    落盘();
  }
  // 极窄档拍一张：顶部两组是否还各归其位
  await s2.send('Emulation.setDeviceMetricsOverride', { width: 400, height: 720, deviceScaleFactor: 2, mobile: false });
  await p2.waitForTimeout(1400);
  const b2 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (b2) {
    await p2.mouse.click(b2[0], b2[1]); await p2.waitForTimeout(2600);
    await p2.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/123-asset-library-narrow-400.png', import.meta.url).pathname });
    rec.窄档图 = 'screenshots/123-asset-library-narrow-400.png';
    await p2.keyboard.press('Escape'); await p2.waitForTimeout(900);
  }

  // ============ 判定 ============
  const 预测宽 = (w) => (w >= 833 ? 801 : w - 32);
  rec.判定 = { 档: 宽度档.map(([w]) => w), 预测: 宽度档.map(([w]) => 预测宽(w)),
    实测: rec.读数.map((z) => (z.模态 && z.模态.有 ? z.模态.盒[0] : null)) };
  console.log('判定 =', JSON.stringify(rec.判定));
  断言('① 五档实测宽与「min(801, 视口−32)」逐档相同（含 833/832 边界）',
    rec.读数.every((z) => z.模态 && z.模态.有 && z.模态.盒[0] === 预测宽(z.视口[0])), rec.判定);
  断言('② 边界成立：833 档读出 801，832 档读出 800',
    rec.读数.find((z) => z.视口[0] === 833).模态.盒[0] === 801 &&
    rec.读数.find((z) => z.视口[0] === 832).模态.盒[0] === 800, rec.判定);
  const 窄 = rec.读数.find((z) => z.视口[0] === 400);
  const 宽 = rec.读数.find((z) => z.视口[0] === 900);
  rec.机制 = { 宽视口: 宽.模态.自有样式, 窄视口: 窄.模态.自有样式, 窄视口祖先链: 窄.模态.祖先链.slice(0, 3) };
  断言('③ 对话框自身声明的仍是 `width: 801px`（两个视口都一样）',
    宽.模态.自有样式.width === '801px' && 窄.模态.自有样式.width === '801px', rec.机制);
  断言('④ 祖先是 flex 容器、自身 flex-srink 生效（机制成立）',
    /flex/.test(窄.模态.祖先链[1] && 窄.模态.祖先链[1].display || '') &&
    parseFloat(窄.模态.自有样式.flexShrink) > 0, rec.机制);
  断言('⑤ 极窄（400）时顶部两组仍**没有互相重叠**',
    窄.模态.顶部.两组是否重叠 === false, 窄.模态.顶部);
  console.log('极窄档顶部读数 =', JSON.stringify(窄.模态.顶部));
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 1200);
  console.log('异常', rec.异常);
} finally {
  try { if (p2) await p2.close(); } catch (e) { rec.关页签异常 = String(e).slice(0, 200); }
  try {
    rec.共享收尾 = await 读共享(shared);
    const 不变量 = ['状态行', '节点数', '选中', '浮层', '积分'];
    rec.数据不变量差异 = 不变量.filter((k) => JSON.stringify(rec.共享收尾[k]) !== JSON.stringify(rec.共享起点[k]));
    断言('⑥ 共享页签数据一个都没变', rec.数据不变量差异.length === 0, { 差异键: rec.数据不变量差异 });
    断言('⑦ 页签数回到 1', ctx.pages().length === 1, { 页签数: ctx.pages().length });
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位到', JSON.stringify(rec.复位));
  } catch (e) { rec.收尾异常 = String(e).slice(0, 400); }
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
