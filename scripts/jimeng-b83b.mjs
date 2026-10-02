// 批次 83 · B：补 a 轮三个没抓全的洞，并精测「节点 N」面板的高度公式。
//
// a 轮结论速览：
//   • 「节点 N」面板 `canvas-node-summary-popover` 实测 **200×292@73,47**、**7 行**
//     （图片1 视频1 文本3 音频13 时间线1 外部1 ＋ 查看项目信息），
//     页面写的是 **200×92 / 两行**（那是 1 节点时代）。
//     ⚠️ 页面还写「每个节点类型一行（本次实测 192×36）」——**行高 36 与 292/7 对不上**。
//   • 顶栏可点 **10** 个，页面第 18-20 行列 **12** 项：
//     「已保存」实测是 `<OUTPUT>` 非可点（页面自己标了状态，对得上），
//     但 **「标记色」在实测的 10 个里根本不存在**。
//   • 顶栏 x 坐标 `156 → 911` 中间 **755px 空白** ⇒ 实际是**两段式布局**，
//     页面「顶栏一览（左→右）」的写法暗示它们连续。
//   • **「项目」「分享」两个面板抓到 0 个候选** —— 我的候选选择器不够，
//     也可能面板压根没打开。a 轮**没有断言这一点**，是判据缺陷。
//
// 本轮：
//   ① 「标记色」到底还在不在？全顶栏 + 画布左上角扫，找带「标记/color/tag」语义的元素；
//   ② **用可见元素差集**判断「项目」「分享」面板到底有没有打开（不再靠猜选择器），
//      打开后按差集里的元素反推容器 testid；
//   ③ 精测「节点 N」每一行的真实高度，验「高度 = 40×行数 + 12」这条公式；
//   ④ 「外部」这一类到底是什么（它是 20 节点里唯一没被页面提过的类型）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const esc = async (ms = 900) => { await p.keyboard.press('Escape'); await p.waitForTimeout(ms); };
const focusCanvas = async () => { await esc(600);
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 24) for (let x = 210; x < 1240; x += 32) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); } return e; };
/** 可见元素签名快照（用于差集） */
const snap = () => p.evaluate(() => { const o = [];
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const k = `${e.tagName}|${String(e.className||'').split(' ')[0]}|${Math.round(r.width)}x${Math.round(r.height)}|${e.getAttribute('data-testid')||''}|${e.getAttribute('aria-label')||''}|${(e.innerText||'').trim().split('\n')[0].slice(0,16)}`;
    o.push({ k, tag: e.tagName, cls: String(e.className||'').split(' ')[0], w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y), testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      role: e.getAttribute('role'), t: (e.innerText||'').trim().split('\n')[0].slice(0,20) }); }
  return o; });
const diffAdd = (A, B) => { const m = new Set(A.map((r) => r.k)); return B.filter((r) => !m.has(r.k)); };
const clickTop = async (name) => { const pt = await p.evaluate((n) => {
    const bar = document.querySelector('[data-testid="canvas-top-bar"]') || document.body;
    const els = Array.from(bar.querySelectorAll('button,[role="button"],a[href]')).filter((e) => {
      const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return false;
      return ((e.getAttribute('aria-label') || '') + '|' + (e.innerText || '')).includes(n); });
    if (!els.length) return null; const e = els[0]; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, name);
  if (!pt) return { ok: false, why: `顶栏找不到「${name}」` };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1600);
  return { ok: true, at: `${pt.x},${pt.y}` }; };

try {
  await focusCanvas();

  // ══════ ① 「标记色」还在不在 ══════
  out.mark = await p.evaluate(() => {
    const found = [];
    for (const e of document.querySelectorAll('*')) {
      const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) continue;
      const blob = [e.getAttribute('aria-label'), e.getAttribute('data-testid'), e.getAttribute('title'),
        e.getAttribute('class'), (e.innerText || '').trim()].filter(Boolean).join(' ');
      if (/标记|mark\b|color|tag|label/i.test(blob) && !/marker-|\.mark\b/.test(blob.replace(/marker-[a-z-]*/g, ''))) {
        found.push({ tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          inTopBar: !!e.closest('[data-testid="canvas-top-bar"]'), cls: String(e.className || '').slice(0, 50) });
      }
    }
    // 去掉同源重复（父子同 key）
    const seen = new Set(); const uniq = [];
    for (const f of found) { const k = `${f.box}|${f.testid}|${f.aria}`; if (!seen.has(k)) { seen.add(k); uniq.push(f); } }
    return uniq.slice(0, 18);
  });
  log(`「标记色」候选 ${out.mark.length} 个：`);
  out.mark.forEach((m) => log('   ', JSON.stringify(m)));

  // ══════ ② 「项目」「分享」用差集判断有没有打开 ══════
  out.panels = {};
  for (const P of [{ key: 'project', name: '项目' }, { key: 'share', name: '分享' }]) {
    await focusCanvas();
    const A = await snap();
    const c = await clickTop(P.name);
    const B = await snap();
    const add = diffAdd(A, B);
    const rec = { click: c, added: add.length, sample: add.slice(0, 10) };
    // 找最大的新增元素 = 面板本体
    const outer = add.slice().sort((x, y) => (y.w * y.h) - (x.w * x.h))[0];
    rec.outer = outer;
    log(`${P.key}：新增 ${add.length} 个，最大者是`, JSON.stringify(outer));
    add.slice(0, 8).forEach((r) => log('   +', JSON.stringify({ tag: r.tag, cls: r.cls, box: `${r.w}x${r.h}@${r.x},${r.y}`, testid: r.testid, aria: r.aria, t: r.t })));
    // 容器全量线索
    rec.containers = await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[data-testid],[role="menu"],[role="listbox"]'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          lines: (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean).slice(0, 20) }; })
      .filter((c) => { const m = /(\d+)x(\d+)@/.exec(c.box); return m && +m[1] > 60 && +m[2] > 40; }).slice(0, 12));
    log(`  ${P.key} 容器候选 ${rec.containers.length} 个：`);
    rec.containers.slice(0, 6).forEach((c) => { log(`   ${c.testid || c.role} ${c.box} aria=${JSON.stringify(c.aria)}`);
      c.lines.forEach((l) => log(`       · ${l.slice(0, 36)}`)); });
    out.panels[P.key] = rec;
    await esc(1100);
  }

  // ══════ ③ 精测「节点 N」每一行的高度 ══════
  await focusCanvas();
  await clickTop('节点');
  out.nodeSummary = await p.evaluate(() => {
    const pop = document.querySelector('[data-testid="canvas-node-summary-popover"]')
      || Array.from(document.querySelectorAll('[role="dialog"]')).find((e) => /查看项目信息/.test(e.innerText || ''));
    if (!pop) return { found: false };
    const pr = pop.getBoundingClientRect();
    // 找所有「文字非空且高度在 20~60 之间、宽度 > 100」的直接子层 = 行
    const rows = Array.from(pop.querySelectorAll('*')).filter((e) => {
      const r = e.getBoundingClientRect(); const t = (e.innerText || '').trim();
      return t && t.length <= 24 && r.width > 100 && r.height >= 20 && r.height <= 60 && e.children.length <= 3; })
      .map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').trim().replace(/\n/g, ' '), w: Math.round(r.width), h: Math.round(r.height),
          y: Math.round(r.y), tag: e.tagName, cls: String(e.className || '').split(' ')[0],
          aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid') }; })
      .sort((a, b2) => a.y - b2.y);
    // 去重（父子同文本）
    const seen = new Set(); const uniq = [];
    for (const r of rows) { if (!seen.has(r.t + r.y)) { seen.add(r.t + r.y); uniq.push(r); } }
    const top = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
    return { found: true, popBox: `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}`,
      rows: uniq, nRows: uniq.length,
      triggerAria: top ? top.getAttribute('aria-label') : null,
      formula: { '40*rows+12': 40 * uniq.length + 12, actual: Math.round(pr.height) } };
  });
  log('节点汇总面板', JSON.stringify(out.nodeSummary?.popBox), `行数 ${out.nodeSummary?.nRows}`);
  (out.nodeSummary?.rows || []).forEach((r) => log('   ', JSON.stringify(r)));
  log('高度公式验算 40×行数+12 =', out.nodeSummary?.formula?.['40*rows+12'], '实际 =', out.nodeSummary?.formula?.actual);
  await esc(1100);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b83b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
