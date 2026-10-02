// 批次 89 · A：审计 `30-concepts.md`（普查停在 **69**，落后 20 批）。
//
// 这页最新的一节是批次 69 的「「元素不存在」这个结论，要先排掉**三种条件错**」：
//   ① 搜的范围  ② 等的时机  ③ 用的标签
// 但**批次 82 与 88 又各自撞出了第四、第五种**，而且这两种比前三种更隐蔽 ——
// 它们不是「查得不够」，是**判据自己写错了却报出干净的 0**。
//
// 本轮三个可证伪预测：
//
// 🔑 **P1（跨状态验证批次 83 的高度公式）**
//     批次 83 立下节点汇总面板公式 `高 = 4 + 40×类型行数 + 12 + 36`，
//     当时 n=6 得出 200×292。**但共享画布此后被别人加了十几个音频节点**，
//     类型行数 n 可能已变 ⇒ 若公式是对的结构，**高度必须跟着 n 一起变**。
//     这是一次真正的泛化检验：公式要么跨状态成立，要么它其实只拟合了一个 n。
//
// 🔑 **P2（「a || b」短路的普适性 —— 它有多常见？）**
//     批次 88 因 `innerText || aria-label` 短路而连续两轮读到「找不到」。
//     那种写法只在**两者都为空**时等价于「或」。本轮统计：
//     全画布上「innerText 与 aria-label 都非空且不相等」的元素有多少个？
//     ⇒ 若这类元素成百上千，这个坑不是个例而是**默认踩**。
//
// 🔑 **P3（「一个 testid 覆盖多语义」是不是只有 node-toolbar 一个）**
//     批次 85 发现 `[data-testid="node-toolbar"]` 既是生成面板 680×208
//     又是文本浮动工具条 192×40。本轮做**全量普查**：把当前 DOM 里每个 testid
//     按「出现过的不同(标签, class, 尺寸)」分组，凡是组数 > 1 的都要看。
//     ⇒ 可证伪：若除 `node-toolbar` 外还有别的 testid 呈现多签名，
//       那么「拿 testid 当语义」是**系统性**错误，不是个别疏漏。
//
// ⛔ 只读为主：点「节点 N」开关面板是只读的；**不点任何扣费按钮**、
//        不建节点、不删他人节点、不按 F、不进导演台。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const scale = async () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const R = (n) => Math.round(n * 100) / 100;

out.start = { scale: await scale(), zoom: await zoomPct(), sel: await selCount(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));

// ══════════════════ P1：节点汇总面板高度公式的跨状态验证 ══════════════════
const trig = 'button[aria-label^="Canvas node summary"]';
out.p1 = {};
if (await p.evaluate((s) => !!document.querySelector(s), trig)) {
  await p.click(trig);
  await p.waitForTimeout(900);
  out.p1.panel = await p.evaluate(() => {
    const R = (n) => Math.round(n * 100) / 100;   // ⚠️ Node 侧的 R 在 evaluate 里不可见（批次 89 自伤①）
    const e = document.querySelector('[data-testid="canvas-node-summary-popover"]');
    if (!e) return { found: false };
    const r = e.getBoundingClientRect();
    // 逐行读：每一行取 aria 与文字
    const rows = Array.from(e.querySelectorAll('[aria-label^="Canvas node summary"]')).map((n) => {
      const rr = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), text: (n.innerText || '').replace(/\s+/g, ' ').trim(), w: R(rr.width), h: R(rr.height), y: R(rr.top) };
    });
    const all = Array.from(e.querySelectorAll('*')).filter((n) => n.getBoundingClientRect().height > 0)
      .map((n) => ({ tag: n.tagName, role: n.getAttribute('role'), aria: n.getAttribute('aria-label'),
        cls: (n.className && String(n.className).slice(0, 40)) || '', t: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }))
      .filter((x) => x.t);
    return { found: true, w: R(r.width), h: R(r.height), x: R(r.x), y: R(r.y), rows, all };
  });
  if (out.p1.panel?.found) {
    const n = out.p1.panel.rows.length;
    const pred = 4 + 40 * n + 12 + 36;
    out.p1.verdict = { typeRows: n, measuredH: out.p1.panel.h, formula_n: pred,
      formula_usesTypeRowsOnly: out.p1.panel.h === pred, formula_usesAllRows: out.p1.panel.h === 4 + 40 * (n + 1) + 12 + 36 };
    log('P1：类型行数 n =', n, '｜面板', out.p1.panel.w + '×' + out.p1.panel.h, '｜公式 4+40n+12+36 =', pred);
    log('P1 判定：', JSON.stringify(out.p1.verdict));
  } else log('P1：面板未找到 —— 🔴 记 VOID，不记「不存在」');
  await p.keyboard.press('Escape');
  await p.waitForTimeout(500);
} else log('P1：找不到「节点 N」触发器');

// ══════════════════ P2：a || b 短路的普适性 ══════════════════
out.p2 = await p.evaluate(() => {
  const both = [], shadow = [];
  for (const e of document.querySelectorAll('*')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const a = e.getAttribute('aria-label');
    if (t && a && t !== a) {
      const rec = { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (String(e.className || '')).slice(0, 44),
        inner: t.slice(0, 44), aria: a.slice(0, 44) };
      both.push(rec);
      if (t.length > 1) shadow.push(rec);   // innerText 为真值 ⇒ || 永远读不到 aria
    }
  }
  const uniq = (arr) => { const m = new Map(); for (const r of arr) { const k = `${r.tag}|${r.tid}|${r.cls}|${r.aria}`; if (!m.has(k)) m.set(k, r); } return [...m.values()]; };
  return { total: both.length, shadow: shadow.length, shadowUniq: uniq(shadow).length, sample: uniq(shadow).slice(0, 14) };
});
log('P2：innerText 与 aria-label 都非空且不相等的元素 =', out.p2.total, '｜其中 innerText 为真值（会被 || 短路）=', out.p2.shadow, '去重', out.p2.shadowUniq);

// ══════════════════ P3：testid 多语义普查 ══════════════════
out.p3 = await p.evaluate(() => {
  const R = (n) => Math.round(n);   // ⚠️ 同上：取整必须在浏览器上下文里自带
  const m = new Map();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const k = e.getAttribute('data-testid');
    const r = e.getBoundingClientRect();
    const sig = `${e.tagName}|${(String(e.className || '')).slice(0, 36)}|${R(r.width)}x${R(r.height)}`;
    if (!m.has(k)) m.set(k, new Set());
    m.get(k).add(sig);
  }
  const multi = [];
  for (const [k, s] of m) if (s.size > 1) multi.push({ tid: k, sigs: [...s] });
  return { totalTestids: m.size, multiCount: multi.length, multi: multi.sort((a, b) => b.sigs.length - a.sigs.length).slice(0, 12) };
});
log('P3：DOM 里 testid 共', out.p3.totalTestids, '个｜签名 >1 的有', out.p3.multiCount, '个');
for (const m of out.p3.multi) log('   🔴', m.tid, '→', m.sigs.length, '种：', m.sigs.slice(0, 3).join('  /  '));

out.end = { sel: await selCount(), credits: await credits(), zoom: await zoomPct(), status: await status() };
log('终点：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
writeFileSync('_tmp-b89a.json', JSON.stringify(out, null, 2));
log('已写 _tmp-b89a.json');
await b.close();
