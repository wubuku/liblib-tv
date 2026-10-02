// 批次 95 · 收尾第 7 轮：**先把缩放从 23% 归位**，并把「节点屏上尺寸随不随缩放」测干净。
//
// 🔴 b95h 结尾留了个坑：`setZoom(60)` **没成功**（终态 zoom=23，标 🔴）。
//     原因线索：`Zoom options` 弹层里的 `input[data-testid="canvas-zoom-percent-input"]`
//     在 23% 档（适配画布出来的值）**可能压根不出现**，于是 3 次重试全落空。
//     ⇒ 收尾门要求的「缩放归位」在本轮**没通过**，先修这个，别带着 23% 留给别人。
//
// 🔴 b95g / b95h 的三档缩放读数**两次全废**，但这一轮想到了更根本的简化：
//     **量尺寸根本不需要节点在视口内。** `getBoundingClientRect()` 对离屏元素照样返回，
//     跑出视口只是 x/y 变负，width/height 照常。
//     ⇒ 缩放三档的判据应该只要求「节点在 DOM 里 + scale 连读两次相同」，
//        **不该**附加「inView / 点得到 / 选中」这些前置 —— 前置越多，越容易在共享画布上假 VOID。
//     resize 控件必须选中才能量，那部分单独一档、单独标注。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), zooms: [], attempts: [] };

const zoomPct = () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const scaleStable = async () => { const a = await scaleNow(); await p.waitForTimeout(400); const c = await scaleNow();
  return { a, c, stable: a !== null && a === c, usable: a }; };
const TID = 'node_3bfb9r79qe';

// ---- 诊断：缩放弹层里到底有什么 ----
out.diag = await p.evaluate(() => {
  const btn = document.querySelector('button[aria-label^="Zoom options"]');
  return { zoomBtnAria: btn ? btn.getAttribute('aria-label') : null,
    zoomPctInputs: Array.from(document.querySelectorAll('input')).map((i) => ({
      tid: i.getAttribute('data-testid'), type: i.type, value: i.value,
      aria: i.getAttribute('aria-label'), min: i.min, max: i.max, step: i.step })).slice(0, 8) };
});
log('缩放控件诊断：', JSON.stringify(out.diag));

// ---- 归位：多路兜底，直到 zoomPct() 真的等于 60 ----
const setZoom = async (target) => {
  for (let k = 1; k <= 4; k++) {
    const now = await zoomPct();
    if (now === target) return { ok: true, tries: k - 1 };
    const rec = { try: k, from: now };
    await p.click('button[aria-label^="Zoom options"]');
    await p.waitForTimeout(900);
    // 兜底 A：百分比输入框
    const hasInput = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
    rec.hasInput = hasInput;
    if (hasInput) {
      await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
        i.dispatchEvent(new Event('input', { bubbles: true }));
        i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
        i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, target);
      await p.waitForTimeout(1700);
    } else {
      // 兜底 B：直接找弹层里显示百分比的按钮/菜单项（Zoom options 弹层通常是步进列表）
      rec.listFound = await p.evaluate((v) => {
        const want = v + '%';
        const els = Array.from(document.querySelectorAll('button,[role="menuitem"],[role="option"]'));
        const hit = els.find((e) => (e.innerText || '').trim() === want || (e.getAttribute('aria-label') || '').includes(want));
        if (hit) { hit.click(); return true; }
        return false;
      }, target);
      await p.waitForTimeout(1700);
      if (!rec.listFound) {
        // 兜底 C：弹层里任何滑块/加减
        rec.slider = await p.evaluate(() => {
          const s = document.querySelector('input[type="range"]');
          if (!s) return null; return { min: s.min, max: s.max, value: s.value };
        });
        if (rec.slider) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
      }
    }
    await p.keyboard.press('Escape');
    await p.waitForTimeout(900);
    rec.to = await zoomPct();
    out.attempts.push(rec);
    log(`  归位第 ${k} 次：${rec.from} → ${rec.to}（hasInput=${rec.hasInput} listFound=${rec.listFound ?? '-'} slider=${rec.slider ? 'yes' : '-'}）`);
  }
  return { ok: await zoomPct() === target, tries: 4 };
};

out.restore = await setZoom(60);
out.zoomAfter = await zoomPct();
log('归位结果：', JSON.stringify(out.restore), '｜现在 zoom =', out.zoomAfter);

// ---- 三档只量尺寸（不点、不要求可见）----
for (const z of [40, 60, 100]) {
  if (z !== 60) { const r = await setZoom(z); if (!r.ok) log(`⚠️ 切到 ${z}% 失败（现在 ${await zoomPct()}%）`); }
  const sc = await scaleStable();
  const m = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { aria: n.getAttribute('aria-label'), w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
      x: Math.round(r.x), y: Math.round(r.y), inView: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720,
      transform: n.style.transform };
  }, TID);
  const zoomNow = await zoomPct();
  // 前置：节点在 DOM + scale 稳定 + zoom 与 scale 自洽（**这一条能抓出「档位标签与真实缩放不一致」**）
  const consistent = m && sc.stable && Math.abs(zoomNow / 100 - sc.usable) < 0.005;
  const rec = { z: z, zoomLabel: zoomNow, scale: sc.usable, scaleStable: sc.stable, consistent,
    measured: m, canvasW: m && sc.usable ? Math.round(m.w / sc.usable * 100) / 100 : null,
    canvasH: m && sc.usable ? Math.round(m.h / sc.usable * 100) / 100 : null };
  out.zooms.push(rec);
  log(`z标签=${zoomNow}% scale=${sc.usable} 一致=${consistent} 节点屏上=${m?.w}×${m?.h} canvas=${rec.canvasW}×${rec.canvasH} inView=${m?.inView} @${m?.x},${m?.y}`);
}

// ---- 归位回 60% 并收尾 ----
const fin = await setZoom(60);
if (await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]) !== '0') {
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
out.end = { zoom: await zoomPct(), scale: (await scaleStable()).usable,
  sel: await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]),
  nodes: await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]) };
log('终态：', JSON.stringify(out.end), '｜缩放归位', out.end.zoom === 60 ? '✅' : '🔴', '｜fin=', JSON.stringify(fin));
writeFileSync(new URL('./_tmp-b95i.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
