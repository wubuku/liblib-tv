// 批次 83 · A：审计 `canvas-context.md` —— 全册最陈旧的读者页（停在批次 55）。
//
// 这一页的六个面板，尺寸全部是 **2026-09-23** 前后测的。问题在于：
// **测量当时的画布只有 1 个节点**。现在画布上有 **20 个**（视频/文本×3/时间线/导演台/
// 音频×12/图片），凡是「按节点类型逐行展开」的面板，尺寸**必然**变了。
// 页面第 46 行「弹出小结面板（role="dialog"，实测 200×92），自上而下两行」——
// 「两行」是**单节点时代**的读数。
//
// 本轮做两件可证伪的事：
//   ① **顶栏全量可点元素普查**（按文档序，不只 button——返回首页是 `<a>`），
//      与页面第 18-20 行那 12 项**逐项对账**。
//      批次 81 数到「10 个可点元素」，而页面列 12 项、其中「已保存」不是可点项
//      ⇒ **对不上，少一个**。先确认到底几个、谁没被列进去。
//   ② 把 5 个**只读**面板逐个打开重测尺寸与逐字内容：项目切换器 / 节点 N /
//      生成历史 / 分享 / 更多。
//      ⚠️ 只**打开**看，不点里面任何执行项（项目名、复制链接、权限下拉、
//      创建团队、复制项目、生成历史的任何一条记录都不点）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
const esc = async (ms = 900) => { await p.keyboard.press('Escape'); await p.waitForTimeout(ms); };

/** 只在画布空白上点一下（焦点守卫），不碰任何节点。 */
const focusCanvas = async () => { await esc(600);
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 24) for (let x = 210; x < 1240; x += 32) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  return e ? (await keyGuard(p)) : null; };

/** 打开一个顶栏按钮（按 aria / testid 匹配），返回能否点到。 */
const clickTop = async (name) => {
  const pt = await p.evaluate((n) => {
    const bar = document.querySelector('[data-testid="canvas-top-bar"]') || document.body;
    const els = Array.from(bar.querySelectorAll('button,[role="button"],a[href],input')).filter((e) => {
      const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return false;
      const t = ((e.getAttribute('aria-label') || '') + '|' + (e.innerText || '')).trim();
      return t.includes(n); });
    if (!els.length) return null;
    const e = els[0]; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  }, name);
  if (!pt) return { ok: false, why: `顶栏找不到「${name}」` };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
  return { ok: true, at: `${pt.x},${pt.y}` };
};

try {
  await focusCanvas();
  out.canvas = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
  log('画布', out.canvas);

  // ══════ ① 顶栏全量可点元素（按文档序） ══════
  out.topBar = await p.evaluate(() => {
    const bar = document.querySelector('[data-testid="canvas-top-bar"]');
    if (!bar) return { found: false };
    const r = bar.getBoundingClientRect();
    const CLICKABLE = 'button,[role="button"],a[href],input,select,textarea,[tabindex]:not([tabindex="-1"])';
    const all = Array.from(bar.querySelectorAll(CLICKABLE)).map((e) => {
      const rr = e.getBoundingClientRect();
      return { tag: e.tagName, x: Math.round(rr.x), w: Math.round(rr.width), h: Math.round(rr.height),
        aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
        text: (e.innerText || e.value || '').trim().split('\n')[0].slice(0, 18),
        title: e.getAttribute('title'), role: e.getAttribute('role') };
    }).filter((e) => e.w > 0 && e.h > 0).sort((a, b) => a.x - b.x);
    // 顶栏里所有可见的短文本片段（用来抓「已保存」这类非可点状态标签）
    const texts = Array.from(bar.querySelectorAll('*')).map((e) => {
      const rr = e.getBoundingClientRect();
      const t = (e.innerText || '').trim();
      return { t: t.split('\n')[0].slice(0, 18), x: Math.round(rr.x), w: Math.round(rr.width), h: Math.round(rr.height),
        tag: e.tagName, inClickable: !!e.closest(CLICKABLE) };
    }).filter((e) => e.t && e.w > 0 && e.h > 0 && e.h < 40);
    const seen = new Set(); const uniq = [];
    for (const t of texts) { const k = `${t.t}@${t.x}`; if (!seen.has(k)) { seen.add(k); uniq.push(t); } }
    return { found: true, barBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      clickableCount: all.length, clickable: all, texts: uniq.sort((a, b) => a.x - b.x) };
  });
  log(`顶栏 ${out.topBar.barBox}｜可点元素 ${out.topBar.clickableCount} 个（左→右）：`);
  out.topBar.clickable.forEach((e, i) => log(`  ${String(i).padStart(2)} ${e.tag.padEnd(6)} ${String(e.w).padStart(4)}x${String(e.h).padEnd(3)} @${String(e.x).padStart(4)}  aria=${JSON.stringify(e.aria)}  testid=${JSON.stringify(e.testid)}  text=${JSON.stringify(e.text)}`));
  log('顶栏非可点的可见文本（找漏记的状态标签）：');
  out.topBar.texts.filter((t) => !t.inClickable).slice(0, 14).forEach((t) => log(`     ${JSON.stringify(t.t)} ${t.w}x${t.h}@${t.x} <${t.tag}>`));

  // ══════ ② 五个只读面板逐个重测 ══════
  const panels = [
    { key: 'project', name: '项目', page: '240×200' },
    { key: 'nodeSummary', name: '节点', page: '200×92' },
    { key: 'history', name: '生成历史', page: '320×211' },
    { key: 'share', name: '分享', page: '（未记尺寸）' },
    { key: 'more', name: '更多', page: '200×84' },
  ];
  out.panels = {};
  for (const P of panels) {
    const rec = { page: P.page };
    try {
      const c = await clickTop(P.name);
      rec.click = c;
      if (!c.ok) { out.panels[P.key] = rec; log(`${P.key} ✗`, JSON.stringify(rec)); continue; }
      const info = await p.evaluate(() => {
        // 新出现的浮层：role=dialog / popover / menu，或顶栏按钮的后代
        const cands = [];
        for (const e of document.querySelectorAll('[role="dialog"],[role="menu"],[data-testid$="popover"],[data-testid$="popover-content"],[data-testid$="-popover"],[data-radix-popper-content-wrapper]')) {
          const r = e.getBoundingClientRect();
          if (r.width > 1 && r.height > 1) cands.push({ sel: e.getAttribute('data-testid') || e.getAttribute('role'), tag: e.tagName,
            box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
            aria: e.getAttribute('aria-label'), lines: (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean).slice(0, 30) });
        }
        return cands;
      });
      rec.candidates = info;
      log(`${P.key} 页面写 ${P.page} → 抓到 ${info.length} 个浮层候选`);
      info.slice(0, 3).forEach((c) => { log(`   ${c.sel || c.tag} ${c.box} aria=${JSON.stringify(c.aria)}`);
        (c.lines || []).forEach((l) => log(`        · ${l.slice(0, 40)}`)); });
      out.panels[P.key] = rec;
    } catch (e) { rec.error = e.message; out.panels[P.key] = rec; log(`${P.key} !! ${e.message}`); }
    await esc(1000);
  }
  out.afterAll = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
  log('终态', out.afterAll);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b83a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
