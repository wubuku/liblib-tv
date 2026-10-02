// 批次 116 · b 轮：读 `生成模式` 下拉的全部选项，并逐个切换读**面板控件的逐字差异**。
//
// a 轮的关键发现（靶子因此更准了）：
//   视频面板**没有「创作类型」下拉**（那是音频面板的 `创作类型: 音频生成`）。
//   手册说的「全能参考」是 **`生成模式` 下拉的当前值**：
//     `生成模式: 全能参考`（`80×32@434,615`）
//   ⇒ 「首尾帧」与「全能参考」**是同一个下拉的两个选项**，不是两个独立功能。
//   另发现一个手册未记的**合并控件**：
//     `视频尺寸选项: 16:9 · 720P · 1, Standard-only model`（`129×32@303,615`）
//     —— 比例、分辨率、时长数字被合进**一个** aria。
//
// 🔴 判据：切模式后**逐字对比整个控件清单**（aria + 尺寸 + 位置），
//    不是「有没有变」。并**每一步读积分**（批次 63 已证改设置不扣费，这里复核）。
// 🔴 不点「生成」，不点任何上传入口之外的扣费控件。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SELF = process.env.SELF_ID;
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b116b.json', import.meta.url), JSON.stringify(out, null, 1));

const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));

// 主面板（按面积筛，避开那个高度恒 0 的同 testid 元素 —— 批次 85 已记）
const readPanel = (lbl) => p.evaluate((l) => {
  const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .map((e) => ({ e, r: e.getBoundingClientRect() })).filter((x) => x.r.width > 1 && x.r.height > 1);
  if (!tbs.length) return { at: Date.now(), lbl: l, __err: 'no-panel' };
  tbs.sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
  const tb = tbs[0].e, r = tbs[0].r;
  const rect = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  return { at: Date.now(), lbl: l, nTb: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    panel: { rect: rect(tb), text: (tb.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 320), svgs: tb.querySelectorAll('svg').length },
    btns: Array.from(tb.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'),
      exp: e.getAttribute('aria-expanded'), rect: rect(e) })).filter((x) => x.aria),
    inputs: Array.from(tb.querySelectorAll('input,textarea,[contenteditable]')).map((e) => ({ tag: e.tagName,
      tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), rect: rect(e) })) };
}, lbl);

// 落点：按 aria 前缀现算，限定在按钮内部
const ptOf = (reStr) => p.evaluate((src) => {
  const re = new RegExp(src);
  const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .map((e) => ({ e, r: e.getBoundingClientRect() })).filter((x) => x.r.width > 1 && x.r.height > 1);
  for (const { e: tb } of tbs) for (const el of tb.querySelectorAll('button,[role=button]')) {
    if (!re.test(el.getAttribute('aria-label') || '')) continue;
    const r = el.getBoundingClientRect(); if (r.width < 1) continue;
    for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
      for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) {
        if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const h = document.elementFromPoint(x, y); if (h && (h === el || el.contains(h)))
          return { x, y, aria: el.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; } }
  return { __err: 'no-clickable' };
}, reStr);

out.nodeExists = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
log('节点存在？', out.nodeExists);
if (!out.nodeExists) { log('⛔ 中止'); await b.close(); process.exit(3); }

// ---- 0. 确保宿主节点选中且**生成面板开着** ----
// ⚠️ 上一轮脚本崩在读基线之前，Esc 已经把整个生成面板关掉了；
//    面板不在 ⇒ 所有「按 aria 找控件」的落点都会返回 no-clickable。
const ensurePanel = async (tag) => {
  for (let round = 0; round < 3; round++) {
    const st = await p.evaluate(() => {
      const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
        .map((e) => ({ e, r: e.getBoundingClientRect() })).filter((x) => x.r.width > 1 && x.r.height > 1);
      return { nPanel: tbs.length, nAll: document.querySelectorAll('[data-testid="node-toolbar"]').length,
        hasGM: !!document.querySelector('button[aria-label^="生成模式"]') }; });
    if (st.nPanel > 0 && st.hasGM) { log(`  [${tag}] 面板已开（第 ${round + 1} 轮）`, JSON.stringify(st)); return st; }
    // 点画布空白取消选中
    const blank = await p.evaluate(() => { const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true; if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
      if (el.closest('[role="menu"],[data-testid="node-toolbar"]')) return true; return false; };
      for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
    if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(1100); }
    // 再点宿主
    const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
      const r = n.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
        for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
          const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
      return { __err: 'unreachable' }; }, SELF);
    if (pt.x) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800); }
    log(`  [${tag}] 第 ${round + 1} 轮尝试后：`, JSON.stringify(await p.evaluate(() => ({
      nPanel: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().height > 1).length,
      hasGM: !!document.querySelector('button[aria-label^="生成模式"]') }))));
  }
  return { __err: 'panel-never-opened' };
};
out.ensure0 = await ensurePanel('start');
if (out.ensure0.__err) { log('⛔ 面板开不出来 ⇒ 中止'); await b.close(); process.exit(4); }

out.credits0 = await credits();
log('起始积分：', out.credits0);

// ---- 1. 展开「生成模式」下拉，读全部选项（只读）----
log('\n=== 展开「生成模式」下拉 ===');
const gm = await ptOf('^生成模式');
out.gmBtn = gm;
log('按钮：', JSON.stringify(gm));
if (gm.__err) { log('⛔ 找不到「生成模式」'); await b.close(); process.exit(4); }
await p.mouse.click(gm.x, gm.y); await p.waitForTimeout(1500);
out.listbox = await p.evaluate(() => { const c = [];
  for (const el of document.querySelectorAll('[role="listbox"]')) { const r = el.getBoundingClientRect(); if (r.width < 1) continue;
    c.push({ aria: el.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round),
      inTb: !!el.closest('[data-testid="node-toolbar"]'),
      groups: Array.from(el.querySelectorAll('[role="group"]')).map((g) => g.getAttribute('aria-label')),
      options: Array.from(el.querySelectorAll('[role="option"]')).map((o) => { const q = o.getBoundingClientRect();
        return { t: (o.innerText || '').replace(/\s+/g, ' ').trim(), sel: o.getAttribute('aria-selected'),
          rect: [q.x, q.y, q.width, q.height].map(Math.round), svgs: o.querySelectorAll('svg').length,
          desc: Array.from(o.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')) }; }) }); }
  return c; });
log('下拉读数：'); log(JSON.stringify(out.listbox, null, 1));
const modes = ((out.listbox || []).find((l) => l.inTb && l.options.length) || { options: [] }).options;
out.modes = modes.map((m) => m.t);
log('\n模式逐字：', JSON.stringify(out.modes));
// ⚠️ Esc 会把**整个生成面板**一起关掉（手册已记），所以 Esc 之后必须**重新选中节点**。
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
out.panelAfterEsc = await p.evaluate(() => document.querySelectorAll('[data-testid="node-toolbar"]').length);
log('Esc 后 node-toolbar 元素数：', out.panelAfterEsc);
{
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    if (n.classList.contains('selected')) return { already: true };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
      for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable' }; }, SELF);
  log('重新选中落点：', JSON.stringify(pt));
  if (pt && pt.x) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800); }
  // 若还没选中，点画布空白取消后再点回来
  const stillSel = await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.classList.contains('selected'), SELF);
  if (!stillSel) {
    const blank = await p.evaluate(() => { const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true; if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a')) return true; return false; };
      for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
    if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(1200);
      const pt2 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
          for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
            const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
        return null; }, SELF);
      if (pt2) { await p.mouse.click(pt2.x, pt2.y); await p.waitForTimeout(1800); } }
  }
  out.panelReopened = await p.evaluate(() => document.querySelectorAll('[data-testid="node-toolbar"]').length);
  log('重开后 node-toolbar 元素数：', out.panelReopened);
}
save();

// ---- 2. 逐个模式切换，读面板逐字差异 ----
out.perMode = [];
out.baseline = await readPanel('baseline');
if (out.baseline.__err || !out.baseline.btns) { log('⛔ 基线面板读不到 ⇒ 中止', JSON.stringify(out.baseline)); await b.close(); process.exit(4); }
log('\n基线控件数：', out.baseline.btns.length, '｜面板文字：', JSON.stringify(out.baseline.panel.text));

for (const mode of out.modes) {
  log(`\n──────── 切到「${mode}」 ────────`);
  const ens = await ensurePanel('mode-' + mode);
  if (ens.__err) { log('  ⛔ 面板开不出来 ⇒ 中止'); break; }
  const c0 = await credits();
  // 展开下拉
  const btn = await ptOf('^生成模式');
  if (btn.__err) { log('  ⛔ 下拉按钮点不到'); break; }
  await p.mouse.click(btn.x, btn.y); await p.waitForTimeout(1300);
  // 落点：限定在该 option 内部
  const opt = await p.evaluate((m) => { const el = Array.from(document.querySelectorAll('[role="option"]'))
      .find((o) => (o.innerText || '').replace(/\s+/g, ' ').trim() === m);
    if (!el) return { __err: 'gone' };
    const r = el.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); if (!h || !(h === el || el.contains(h))) return { __err: 'hit', tag: h ? h.tagName : null };
    return { x: cx, y: cy, sel: el.getAttribute('aria-selected') }; }, mode);
  if (opt.__err) { log('  ⛔ 拿不到 option 落点', JSON.stringify(opt)); out.perMode.push({ mode, fail: opt }); save(); continue; }
  await p.mouse.click(opt.x, opt.y);
  await p.waitForTimeout(1800);
  const panel = await readPanel('mode-' + mode);
  const c1 = await credits();
  // 与基线逐字对比
  const key = (x) => `${x.aria}|${x.rect.join('×')}`;
  const baseKeys = (out.baseline.btns || []).map(key);
  const nowKeys = (panel.btns || []).map(key);
  const added = nowKeys.filter((k) => !baseKeys.includes(k));
  const removed = baseKeys.filter((k) => !nowKeys.includes(k));
  const rec = { mode, optSel: opt.sel, credits0: c0, credits1: c1, 扣费: c0 !== c1,
    panelRect: panel.panel && panel.panel.rect, panelText: panel.panel && panel.panel.text, svgs: panel.panel && panel.panel.svgs,
    nBtns: (panel.btns || []).length, added, removed,
    btns: (panel.btns || []).map((x) => ({ aria: x.aria, rect: x.rect })),
    inputs: panel.inputs };
  out.perMode.push(rec);
  log('  积分：', c0, '→', c1, c0 === c1 ? '（未变）' : '🔴 变了');
  log('  面板：', JSON.stringify(rec.panelRect), 'svg', rec.svgs, '｜控件', rec.nBtns, '个');
  log('  面板文字：', JSON.stringify(rec.panelText));
  log('  相对基线：', added.length ? `+${JSON.stringify(added)}` : '（无新增）', removed.length ? `-${JSON.stringify(removed)}` : '（无移除）');
  save();
}
out.creditsEnd = await credits();
log('\n末次积分：', out.creditsEnd, '｜起始：', out.credits0, '⇒ 切换模式', out.credits0 === out.creditsEnd ? '不扣费' : '⚠️ 变了');
save();
log('\nDONE b');
process.exit(0);
