// 批次 89 · C：把批次 83 的高度公式从「拟合一个点」变成「跨两个 n 验证」。
//
// b 轮已经把 n 查清了 —— 节点按 **aria 前缀**分组，当前 6 组：
//   视频 node 1 ｜ 文本 node 3 ｜ 时间线 node 1 ｜ **外部 node 1**（= 导演台）｜
//   音频 node 13 ｜ 图片 node 1
// ⇒ 4 + 40×6 + 12 + 36 = **292**，与实测 `200×292@73,47` 严丝合缝。
//
// ⚠️ 但 b 轮也暴露了这批数据的**弱点**：别的会话加了 13 个音频节点，
//     **n 一点没变**（因为 n 是**类型数**，不是节点数）—— 这不是跨状态检验。
//
// ⇒ 本轮做**真正的跨状态检验**：画布上目前 **0 个主体节点**，
//     从左栏造 1 个 ⇒ n 变 7。
//   **可证伪预测 P1a**：面板高度从 `200×292` 变成 **`200×332`（恰好 +40）**。
//   若不是 +40 ⇒ 公式错（它其实拟合的是那一个 n）。
//   **可证伪预测 P1b**：新节点 aria 前缀是「主体 node」而不是「外部 node」
//   —— 若导演台的「外部」是因为它是唯一没有专属类型名的那类，那主体就该有。
//
// 🔑 **顺带解掉一个记了 6 个批次的悬案**：批次 83 记下「节点汇总面板多出一类逐字
//     『**外部 1**』，与五种媒体类型并列，机制未查明」。
//     b 轮线索指向：导演台节点的 aria 逐字是 **`外部 node: 导演台`**，
//     class 也是 `react-flow__node-external`（批次 88 复核过 class 这一半）。
//     ⇒ **P1c**：面板里那一行的来源就是导演台，数量 1 = 导演台节点数。
//
// 🔑 **P3 续查**：a 轮把签名算成 `标签|class|宽×高`，`flow-node-title` 裂成 13 种
//     —— 那是**标题文字长度不同**，不是语义不同。本轮改成结构签名（只看 标签+class）
//     并把**差异尾部打出来**。
//     另有一个真正像 `node-toolbar` 的候选：`flow-node-selected-tag` 同签名三种尺寸
//     （24×24 / 28×28 / 29×29）⇒ **P3b** 24×24 是 `Add tags` 钮，28×28 是色板？
//
// ⛔ 绝不点：任何扣费按钮、「保存到主体库」、发送/生成。
//     自建的节点**按 id 精确删除**（右键菜单 →「删除」），绝不用 Delete 键。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });

// 打开节点汇总面板并量它（🔴 a 轮 900ms 不够，b 轮 1600ms 才在 —— 本页「等的时机」那条的现场复现）
const readPanel = async (tag) => {
  const trig = 'button[aria-label^="Canvas node summary"]';
  await p.click(trig);
  await p.waitForTimeout(1800);
  const r = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-node-summary-popover"]');
    if (!e) return { found: false };
    const b = e.getBoundingClientRect();
    // 面板内的行：取 aria 为 "Canvas node summary" 的元素（类型行）
    const rows = Array.from(e.querySelectorAll('[aria-label="Canvas node summary"]')).map((n) => {
      const rr = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), text: (n.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(rr.top), h: Math.round(rr.height) };
    });
    const allText = Array.from(e.querySelectorAll('*')).map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.length < 30);
    return { found: true, w: Math.round(b.width), h: Math.round(b.height), x: Math.round(b.x), y: Math.round(b.y), rows, allText: [...new Set(allText)] };
  });
  if (r.found) { r.n = r.rows.length; r.pred = 4 + 40 * r.n + 12 + 36; r.hit = r.h === r.pred; log(`  ${tag}：面板 ${r.w}×${r.h}｜类型行 n=${r.n}｜公式 4+40n+12+36=${r.pred}｜${r.hit ? '✅ 命中' : '🔴 不符'}`); }
  else log(`  ${tag}：🔴 面板没出现 —— 记 VOID，不记「不存在」`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(700);
  return r;
};

try {
  out.start = { status: await status(), credits: await credits(), zoom: await zoomPct(), n: (await ids()).length };

  // ═══ 基线：n = 6 ═══
  log('── 基线');
  out.base = await readPanel('基线');

  // ═══ P3 续查：结构签名的差异尾部 + selected-tag 三种尺寸的归属 ═══
  log('── P3 续查');
  out.p3 = await p.evaluate(() => {
    const m = new Map();
    for (const e of document.querySelectorAll('[data-testid]')) {
      const k = e.getAttribute('data-testid');
      const c = String(e.className || '');
      if (!m.has(k)) m.set(k, { sigs: new Map(), sizes: new Map() });
      if (!m.get(k).sigs.has(c)) m.get(k).sigs.set(c, 0);
      m.get(k).sigs.set(c, m.get(k).sigs.get(c) + 1);
      const r = e.getBoundingClientRect();
      if (r.width > 0) { const s = `${Math.round(r.width)}×${Math.round(r.height)}`;
        if (!m.get(k).sizes.has(s)) m.get(k).sizes.set(s, []); m.get(k).sizes.get(s).push({ tag: e.tagName, aria: e.getAttribute('aria-label') }); }
    }
    // 对结构签名 >1 的，打出「第一个签名 vs 其余」的差异尾部
    const diff = [];
    for (const [tid, g] of m) {
      if (g.sigs.size <= 1) continue;
      const sigs = [...g.sigs.entries()];
      const base = sigs[0][0];
      const tails = sigs.slice(1).map(([s, n]) => { let i = 0; while (i < base.length && i < s.length && base[i] === s[i]) i++;
        return { n, tail: (base.slice(Math.max(0, i - 24), i) + '  ⟂  ' + s.slice(Math.max(0, i - 24), i + 34)) }; });
      diff.push({ tid, total: [...g.sigs.values()].reduce((a, c) => a + c, 0), tails });
    }
    return { multiSize: [...m.entries()].filter(([, g]) => g.sizes.size > 1).map(([tid, g]) => ({ tid, sizes: [...g.sizes.entries()].map(([s, els]) => `${s}×${els.length}${els[0].aria ? ' (aria=' + String(els[0].aria).slice(0, 28) + ')' : ''}`) })), diff };
  });
  for (const d of out.p3.diff) { log(`  🔴 [${d.tid}] n=${d.total}，签名差异尾部：`); for (const t of d.tails) log('      ', `×${t.n}`, t.tail.slice(0, 110)); }
  for (const s of out.p3.multiSize) log(`  ⚠️ [${s.tid}] 同结构多尺寸：${s.sizes.join(' ｜ ')}`);

  // ═══ 造 1 个主体节点，把 n 从 6 推到 7 ═══
  log('── 造主体节点');
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^主体$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rail) { out.make = { ok: false, why: '左栏找不到「主体」' }; log('  🔴 左栏找不到「主体」 —— 记 VOID'); }
  else {
    await p.mouse.click(rail.x, rail.y);
    await p.waitForTimeout(3600);
    const made = (await ids()).filter((x) => !pre.includes(x));
    out.make = { ok: made.length === 1, made, n_before: pre.length, n_after: (await ids()).length };
    log('  新建', made.length, '个：', made.join(' ') || '(无)', '｜画布', out.make.n_after, '节点');
    if (made.length === 1) {
      mine.push(made[0]);
      out.make.node = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        return n ? { aria: n.getAttribute('aria-label'), cls: String(n.className || ''), inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) } : null; }, made[0]);
      log('  新节点：', JSON.stringify(out.make.node));
    }
  }

  // ═══ P1a / P1c：n=7 时的高度与面板内容 ═══
  log('── 造完再量');
  out.after = await readPanel('造后');
  out.p1a = { n_before: out.base?.n, n_after: out.after?.n, h_before: out.base?.h, h_after: out.after?.h,
    pred_if_7: 4 + 40 * 7 + 12 + 36, delta: (out.base && out.after) ? out.after.h - out.base.h : null };
  log('P1a：n', out.p1a.n_before, '→', out.p1a.n_after, '｜高', out.p1a.h_before, '→', out.p1a.h_after, '｜Δ', out.p1a.delta, '｜若公式对 Δ 应为 40');
  if (out.after?.allText) log('P1c 面板内文字：', JSON.stringify(out.after.allText));
} catch (e) { out.error = String(e); log('🔴 异常：', String(e)); }

finally {
  // ═══ 收尾：按 id 精确删掉自建节点 ═══
  log('── 收尾删除');
  for (const id of mine) {
    const box = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, id);
    if (!box) { log('  ', id, '已不在画布'); continue; }
    await p.mouse.click(box.x, box.y, { button: 'right' });
    await p.waitForTimeout(900);
    const ok = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
      if (!m) return false; const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) { it.click(); return true; } return false; });
    await p.waitForTimeout(1500);
    log('  删', id, '菜单已点 =', ok);
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.end = { status: await status(), credits: await credits(), zoom: await zoomPct() };
  log('终态', JSON.stringify(out.end));
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 89: [...new Set([...(led.per_batch?.['89'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10);
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账', add.join(' ')); } } catch (e) { log('台账写入失败', String(e)); } }
  writeFileSync(new URL('./_tmp-b89c.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
