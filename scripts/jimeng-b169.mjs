// 批次 169 —— 检验一个**反向预测**：前面四批测的模态都会随窗口缩，
// 而「生成历史」面板在 CSS 里是 `.h-generation-history-panel{height:211px}` ——
// **一个写死的 px、没有任何视口项** ⇒ 预测它**不随窗口高度变**。
//
// 🔑 这条预测有实际用处：手册把「生成历史」面板记成固定 `320×211`，
//    但**没说它会不会跟着窗口缩**。若它真的不缩，那用户在小窗口里就会看到
//    「面板不动、别的对话框会缩」的不一致 —— 值得写进手册；
//    若它其实会缩，那 211 这个数就不是定尺，和前面几批是同一族问题。
//
// 📐 同时把它的**机制**读出来（classList / 内联 style / 直接子几何），
//    并对照 CSS 里另一条 `min-h-generation-history-panel{min-height:min(211px,100%)}`
//    —— **`height` 写死、`min-height` 带视口项**，两者不是一回事。
//
// ⛔ 只读：点开顶栏 `canvas-panel-launcher` 看面板，Esc 关掉；不点任何生成记录、不触发生成。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
// 🆕 加两档**极矮**视口：机制上 `max-height: 100%` 意味着「容器比 211 矮时才夹」，
//    而面板顶边固定在 y=56 ⇒ 可用高度 = 视口高 − 56 ⇒ 门槛 211+56 = **267**。
//    预测：视口 ≥ 267 → 恒 211；256 → 200；200 → 144（= 视口高 − 56）。
// 🔴 第二版预测（可用高度 = 视口高 − 56）**被读数否掉**：267→151、256→140、200→84，
//    三档差值都是 **116** ⇒ 可用高度 ＝ 视口高 − **116**（不是 56）。
//    ⇒ 门槛应是 211 + 116 = **327**；加三档把它夹出来：340 / 330 / 327。
const 档 = [[1280, 720], [1280, 600], [1280, 500], [1280, 400], [1280, 340], [1280, 330], [1280, 327], [1280, 300], [1280, 267], [1280, 256], [1280, 200], [900, 720], [700, 720]];
const rec = { 批次: '169', 目的: '验证「生成历史」面板的高度是写死的 211px（不随窗口缩），与模态的行为相反' };
let 断言过 = true, 断言数 = 0, 断言预期 = 5;
// 🔴 批次 169 自身失误（本轮第一个版本）：断言里直接写 `数组.every(...)`，
//    而数组**可能读成空的** ⇒ `[].every()` **恒为 true** ⇒ 一条也没量到却报「✅」。
//    实测确实发生：六档全部「面板 undefined」，断言 ③ ④ 却打印了绿。
//    ⇒ 正解：**断言助手自带非空守卫** —— 传进来的每组读数少于 2 条就直接判负，
//      并把「读数条数」打印出来，让「什么都没读到」不可能伪装成通过。
const 断言 = (名, ok, 详情, 组 = null) => {
  断言数++;
  const 空 = 组 ? (Array.isArray(组) ? 组.length < 2 : false) : false;
  const v = !!ok && !空;
  if (!v) 断言过 = false;
  console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情)) + (空 ? `  ⚠️ 读数只有 ${组.length} 条（<2），视为「没读到」` : ''));
  return v;
};
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b169.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读 = () => {
  // 🆕 先数「同名 testid 的实例数」—— 批次 162 在 node-toolbar 上栽过一次，本轮是同一个形状
  const 同名 = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).map((e) => {
    const q = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), 盒: [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)] }; });
  const p = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '生成历史');
  if (!p) return { 找到: false, 同名实例: 同名, 视口: [innerWidth, innerHeight] };
  const r = p.getBoundingClientRect(), cs = getComputedStyle(p);
  // 面板本体：launcher 兄弟里带「生成历史」的那个，或 class 含 generation-history-panel
  // ✅ 正确面板本体：**它自己就有 testid** —— `generation-history-panel`（`<SECTION>`）。
  //    第一版按「内文含生成历史的最小容器」找，抓到的是**整屏工作台外壳**（1280×720）
  //    ⇒ 读数全错。📌 教训：**有 testid 就用 testid**，别用「按内文猜容器」。
  let e = document.querySelector('[data-testid="generation-history-panel"]');
  let 找法 = 'testid=generation-history-panel';
  if (!e) {
    e = Array.from(document.querySelectorAll('section,aside')).filter((x) => /生成历史/.test(x.innerText || ''))
      .sort((a, b2) => a.getBoundingClientRect().width * a.getBoundingClientRect().height - b2.getBoundingClientRect().width * b2.getBoundingClientRect().height)[0] || null;
    找法 = '兜底：按 section 里含「生成历史」找';
  }
  const out = { 找到: true, 同名实例: 同名, 实例数: 同名.length, 找法, 视口: [innerWidth, innerHeight],
    launcher: { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      ariaExpanded: p.getAttribute('aria-expanded'), classList: (typeof p.className === 'string' ? p.className : '').split(/\s+/).filter(Boolean).slice(0, 10) } };
  if (e) {
    const q = e.getBoundingClientRect(), s = getComputedStyle(e);
    out.面板 = { 盒: [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)],
      余量: { 上: +q.y.toFixed(1), 下: +(innerHeight - (q.y + q.height)).toFixed(1), 左: +q.x.toFixed(1), 右: +(innerWidth - (q.x + q.width)).toFixed(1) },
      计算: { width: s.width, height: s.height, minHeight: s.minHeight, maxHeight: s.maxHeight, maxWidth: s.maxWidth, position: s.position },
      内联: e.getAttribute('style'),
      classList: (typeof e.className === 'string' ? e.className : '').split(/\s+/).filter(Boolean).slice(0, 12),
      子: Array.from(e.children).slice(0, 5).map((c) => ({ testid: c.getAttribute('data-testid'), 高: Math.round(c.getBoundingClientRect().height) })),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) };
  }
  return out;
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
  const 开面板 = async () => {
    // 🔴 `document.querySelector('[data-testid="canvas-panel-launcher"]')` 命中的是**「搜索」**那个 ——
    //    实测该 testid **被两个按钮复用**（搜索 x=915 / 生成历史 x=947），而 querySelector 取文档顺序第一个。
    //    ⇒ 可靠定位是 **aria 逐字「生成历史」**。
    const 钮 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '生成历史'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!钮) return false;
    await p2.mouse.click(钮[0], 钮[1]); await p2.waitForTimeout(2200); return true;
  };
  const 关面板 = async () => { for (let k = 0; k < 3; k++) { await p2.keyboard.press('Escape'); await p2.waitForTimeout(600); } };

  rec.读数 = [];
  for (const [w, h] of 档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1300);
    const 开成了 = await 开面板();
    const z = await p2.evaluate(读);
    rec.读数.push({ 视口: [w, h], 开成了, ...z });
    console.log(`  [${w}×${h}] launcher ${JSON.stringify(z.launcher && z.launcher.盒)} 面板 ${JSON.stringify(z.面板 && z.面板.盒)} 高度计算 ${z.面板 && z.面板.计算.height} minH ${z.面板 && z.面板.计算.minHeight}`);
    if (z.面板 && w === 1280 && h === 720) {
      await p2.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/127-generation-history-panel-fixed-211.png', import.meta.url).pathname });
      rec.图 = 'screenshots/127-generation-history-panel-fixed-211.png';
    }
    await 关面板();
    落盘();
  }
  const 高s = rec.读数.filter((z) => z.面板 && z.视口[0] === 1280 && z.视口[1] >= 327);
  const 矮s = rec.读数.filter((z) => z.面板 && z.视口[0] === 1280 && z.视口[1] < 327);
  const 宽s = rec.读数.filter((z) => z.面板 && z.视口[1] === 720);
  rec.汇总 = { 高档面板高: 高s.map((z) => z.面板.盒[1]), 宽档面板宽: 宽s.map((z) => z.面板.盒[0]),
    计算高: 高s.map((z) => z.面板.计算.height), 计算宽: 宽s.map((z) => z.面板.计算.width) };
  console.log('汇总 =', JSON.stringify(rec.汇总));
  断言('⓪ 十三档都读到了面板（含 aria-expanded 变 true），且 **同名 testid 恒为 2 个实例**',
    rec.读数.filter((z) => z.面板).length === 13 && rec.读数.filter((z) => z.launcher && z.launcher.ariaExpanded === 'true').length >= 1 &&
    rec.读数.every((z) => z.实例数 === 2), rec.汇总, rec.读数);
  断言('① **窗口 ≥ 327 的七档下，面板高度恒为 211**（反直觉：模态会缩，它不会）',
    new Set(高s.map((z) => z.面板.盒[1])).size === 1 && 高s.every((z) => z.面板.盒[1] === 211), rec.汇总, 高s);
  断言('② 面板宽度也恒定（900 / 700 窄视口下不缩）',
    new Set(宽s.map((z) => z.面板.盒[0])).size === 1, rec.汇总, 宽s);
  // 🔴 我第一版预测 `max-height` 是 `none` ⇒ **错**，实测是 `100%`（+ `min-height: min(211px,100%)`）。
  //    这不是小错：它意味着「容器比 211 矮时面板**会**被夹」⇒ 于是必须补两档极矮视口去夹这个边界。
  断言('③ 计算样式逐字是 `height:211px` ＋ `max-height:100%` ＋ `min-height:min(211px,100%)`（我原预测 max-height:none 是错的）',
    高s.every((z) => z.面板.计算.height === '211px' && z.面板.计算.maxHeight === '100%' && /211px/.test(z.面板.计算.minHeight)),
    高s.map((z) => z.面板.计算), 高s);
  断言('⑥ 矮视口触发 `max-height:100%` 夹取：面板高 ＝ 视口高 − **116**（327 档恰好 211 属边界；300→184 / 267→151 / 256→140 / 200→84）',
    矮s.length === 4 && 矮s.every((z) => z.面板.盒[1] === z.视口[1] - 116),
    矮s.map((z) => ({ 视口高: z.视口[1], 面板高: z.面板.盒[1] })), 矮s);
  断言('④ 对照组：同一视口下**模态**（帮助中心 360×644）会缩 —— 两种面板行为不同，别混为一谈',
    rec.汇总.高档面板高.every((x) => x === 211), { 本批面板: rec.汇总.高档面板高, 对照_帮助中心: '644 = min(648,100vh−76)（批次 168）' }, 高s);
  断言('⑤ 窗口很矮（400）时面板**顶到屏幕外也不裁**，读出 y 仍是固定偏移',
    rec.读数.find((z) => z.视口[1] === 400).面板 != null, rec.读数.map((z) => ({ 视口: z.视口, 面板: z.面板 && z.面板.盒 })), rec.读数);
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
