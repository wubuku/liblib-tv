// 批次 83 · C：修 b 轮的匹配缺陷，并把三个洞补完。
//
// 🔴 **b 轮点「项目」点错了按钮**：`clickTop` 用 `includes('项目')` 匹配 aria，
//    而画布标题的 aria 是 `Canvas title: 测试项目` —— **也含「项目」**，
//    `els[0]` 取到的是标题触发器，不是项目切换器。
//    证据：project 轮「新增元素」里最大的是 `<HTML>`，**面板压根没打开**。
//    ⇒ 判据缺陷：**按名字点按钮必须精确匹配 aria，不能用子串包含。**
//    （「分享」那次侥幸命中，因为「测试项目」不含「分享」。）
//
// 🔴 **「标记色」很可能已经从顶栏消失了**，但 b 轮的正则给不出证据：
//    `/标记|mark\b|color|tag|label/i` 去匹配 **class 字符串**，
//    结果 `text-workspace-share-entry-label` 这类全被误命中，18 条全是噪音。
//    正解不是加词表，是**穷举**：把顶栏 `x ∈ [190, 911]` 区间内
//    **所有有面积的元素**（不筛类型）列出来，看那一段到底有没有东西。
//
// ✅ **「分享画布」面板结构抓到了**（b 轮）：
//    `canvas-share-panel-surface` **400×251@868,56**（`DIV.fixed`）
//      └ `canvas-share-panel` **400×251@868,56**（`SECTION`，`aria="分享画布"`）
//          ├ 标题区 `400×52@868,56`，`H2`「分享画布」`56×22@884,75`
//          └ 内容区 `400×199@868,108`，其中链接块 `400×122@868,108`
//    ⚠️ **面板里有画布链接明文**（实测首段 `https://jimeng.jiany…`）
//       ⇒ **这一页不能给分享面板配图**，否则会把画布链接截进图里。
//
// 本轮：① 精确 aria 打开项目面板；② 穷举「标记色」区间；
//      ③ 分享面板逐字内容（只读，不点复制链接/权限下拉/创建团队）。
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
/** 🔑 精确 aria 匹配（不再用 includes）。 */
const clickExact = async (aria) => { const pt = await p.evaluate((n) => {
    const bar = document.querySelector('[data-testid="canvas-top-bar"]') || document.body;
    const e = Array.from(bar.querySelectorAll('button,[role="button"],a[href]'))
      .find((x) => x.getAttribute('aria-label') === n);
    if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, aria);
  if (!pt) return { ok: false, why: `顶栏没有 aria 逐字等于「${aria}」的按钮` };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700);
  return { ok: true, at: `${pt.x},${pt.y}` }; };
const snap = () => p.evaluate(() => { const o = [];
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    o.push({ k: `${e.tagName}|${String(e.className||'').split(' ')[0]}|${Math.round(r.width)}x${Math.round(r.height)}|${e.getAttribute('data-testid')||''}|${e.getAttribute('aria-label')||''}|${(e.innerText||'').trim().split('\n')[0].slice(0,16)}`,
      tag: e.tagName, w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
      testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
      t: (e.innerText || '').trim().split('\n')[0].slice(0, 24) }); }
  return o; });
const diffAdd = (A, B) => { const m = new Set(A.map((r) => r.k)); return B.filter((r) => !m.has(r.k)); };

try {
  await focusCanvas();

  // ══════ ① 顶栏 x∈[190,911] 穷举：「标记色」还在不在 ══════
  out.gapScan = await p.evaluate(() => {
    const bar = document.querySelector('[data-testid="canvas-top-bar"]'); if (!bar) return { err: '无顶栏' };
    const all = Array.from(bar.querySelectorAll('*')).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), cls: String(e.className || '').split(' ')[0],
        t: (e.innerText || '').trim().split('\n')[0].slice(0, 16) }; })
      .filter((e) => e.w > 0 && e.h > 0 && e.x >= 190 && e.x < 911);
    const seen = new Set(); const uniq = [];
    for (const e of all) { const k = `${e.tag}|${e.x},${e.y}|${e.w}x${e.h}`; if (!seen.has(k)) { seen.add(k); uniq.push(e); } }
    const left = bar.querySelector('[data-testid="canvas-top-bar-left"]'); const lr = left ? left.getBoundingClientRect() : null;
    return { inGap: uniq.sort((a, b) => a.x - b.x), n: uniq.length,
      topBarLeft: lr ? `${Math.round(lr.width)}x${Math.round(lr.height)}@${Math.round(lr.x)},${Math.round(lr.y)}` : null,
      barAria: bar.getAttribute('aria-label'), barTag: bar.tagName };
  });
  log(`顶栏 [190,911) 区间内共 ${out.gapScan.n} 个有面积元素（顶栏 aria=${JSON.stringify(out.gapScan.barAria)} <${out.gapScan.barTag}>，左段 ${out.gapScan.topBarLeft}）：`);
  out.gapScan.inGap.forEach((e) => log('   ', JSON.stringify(e)));

  // ══════ ② 精确 aria 打开「项目」面板 ══════
  await focusCanvas();
  const A1 = await snap();
  const c1 = await clickExact('项目');
  const B1 = await snap();
  const add1 = diffAdd(A1, B1);
  out.project = { click: c1, added: add1.length };
  const outer1 = add1.slice().sort((a, b) => (b.w * b.h) - (a.w * a.h))[0];
  out.project.outer = outer1;
  log(`「项目」精确点击 → ${JSON.stringify(c1)}，新增 ${add1.length} 个；最大新增：`);
  log('   ', JSON.stringify(outer1));
  add1.slice(0, 6).forEach((r) => log('    +', JSON.stringify({ tag: r.tag, cls: r.cls, box: `${r.w}x${r.h}@${r.x},${r.y}`, testid: r.testid, aria: r.aria, t: r.t })));
  out.project.detail = await p.evaluate(() => {
    const pop = document.querySelector('[data-testid="canvas-project-panel-popover"]');
    const lists = Array.from(document.querySelectorAll('nav,ul,[role="listbox"],[role="menu"]'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          items: Array.from(e.querySelectorAll('button,[role="menuitem"],li,a')).map((x) => { const rr = x.getBoundingClientRect();
            return `${(x.innerText || '').trim().split('\n')[0].slice(0, 18)} ${Math.round(rr.width)}x${Math.round(rr.height)}`; }) }; })
      .filter((e) => e.items.length);
    if (!pop) return { found: false, lists };
    const pr = pop.getBoundingClientRect();
    return { found: true, popBox: `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}`,
      popAria: pop.getAttribute('aria-label'),
      lines: (pop.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean),
      buttons: Array.from(pop.querySelectorAll('button,[role="menuitem"],a')).map((x) => { const rr = x.getBoundingClientRect();
        return { t: (x.innerText || '').trim().split('\n')[0].slice(0, 20), box: `${Math.round(rr.width)}x${Math.round(rr.height)}`, testid: x.getAttribute('data-testid') }; }),
      lists };
  });
  log('项目面板', JSON.stringify(out.project.detail?.popBox || out.project.detail?.found));
  (out.project.detail?.lines || []).forEach((l) => log('   ·', l.slice(0, 44)));
  log('  按钮：'); (out.project.detail?.buttons || []).forEach((x) => log('   ', JSON.stringify(x)));
  log('  列表：'); (out.project.detail?.lists || []).forEach((x) => log('   ', x.tag, x.role, x.box, 'aria=' + JSON.stringify(x.aria), '|', x.items.join(' ; ').slice(0, 90)));
  await esc(1200);

  // ══════ ③ 分享面板逐字（只读） ══════
  await focusCanvas();
  const A2 = await snap();
  const c2 = await clickExact('分享');
  const B2 = await snap();
  const add2 = diffAdd(A2, B2);
  log(`「分享」→ ${JSON.stringify(c2)}，新增 ${add2.length} 个`);
  out.share = await p.evaluate(() => {
    const panel = document.querySelector('[data-testid="canvas-share-panel"]');
    const surface = document.querySelector('[data-testid="canvas-share-panel-surface"]');
    const pr = panel ? panel.getBoundingClientRect() : null; const sr = surface ? surface.getBoundingClientRect() : null;
    const items = (panel || surface) ? Array.from((panel || surface).querySelectorAll('button,input,[role="combobox"],[role="button"],a'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, t: (e.innerText || e.value || '').trim().slice(0, 18), aria: e.getAttribute('aria-label'),
          role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }) : [];
    const inputs = (panel || surface) ? Array.from((panel || surface).querySelectorAll('input'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { type: e.getAttribute('type'), testid: e.getAttribute('data-testid'), readOnly: e.readOnly,
          valueHead: (e.value || '').slice(0, 12) + '…', len: (e.value || '').length,
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }) : [];
    return { surface: sr ? `${Math.round(sr.width)}x${Math.round(sr.height)}@${Math.round(sr.x)},${Math.round(sr.y)}` : null,
      panel: pr ? `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}` : null,
      panelTag: panel ? panel.tagName : null, panelAria: panel ? panel.getAttribute('aria-label') : null,
      lines: (panel || surface) ? ((panel || surface).innerText || '').split('\n').map((s) => s.trim()).filter(Boolean) : [],
      buttons: items, inputs,
      hasUrlText: /jimeng\.jianying\.com/.test((panel || surface) ? (panel || surface).innerText || '' : '') };
  });
  log('分享面板', JSON.stringify({ surface: out.share.surface, panel: out.share.panel, tag: out.share.panelTag, aria: out.share.panelAria }));
  (out.share.lines || []).forEach((l) => log('   ·', /https?:/.test(l) ? l.slice(0, 14) + '…（链接明文已遮）' : l.slice(0, 44)));
  log('  按钮：'); (out.share.buttons || []).forEach((x) => log('   ', JSON.stringify(x)));
  log('  输入框：'); (out.share.inputs || []).forEach((x) => log('   ', JSON.stringify(x)));
  log('  ⚠️ 面板内含画布链接明文：', out.share.hasUrlText);
  await esc(1200);
  out.after = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
  log('终态', out.after);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b83c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
