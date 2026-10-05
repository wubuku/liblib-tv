// 批次 196 f 轮：给 assets-and-upload.md 补三张图。
//
// ① 19４ 资产库 dialog 全貌（`801×620@240,50`）—— 框出**两级页签**（一级 资产/主体，二级 图片/视频/音频/文档）
// ② 19５ 「视频」二级页签的空态（逐字「暂无视频素材」）—— 与「图片」页对照
// ③ 19６ 「时间」页的日期筛选器（一级二级之外的那组控件）
//
// 🛡 每张：先断言该页签确实处于目标态（读 dialog 的 innerText）→ 画框 → 读回框 → 最后才 shutter。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const OUTDIR = 'docs/user-manual/jimeng-canvas/screenshots';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));

const 点左栏 = async (名) => { const s = await p.evaluate((n) => { const e = Array.from(document.querySelectorAll('button'))
  .find((x) => (x.getAttribute('aria-label') || '') === n && x.getBoundingClientRect().width > 0);
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 名);
  if (!s) return null; await p.mouse.click(s[0], s[1]); await p.waitForTimeout(2100); return s; };

const 框 = (K) => p.evaluate((S) => {
  document.querySelectorAll('[id^="__b196-"]').forEach((e) => e.remove());
  for (const s of S) { const d = document.createElement('div'); d.id = s.id;
    Object.assign(d.style, { position: 'fixed', left: s.x + 'px', top: s.y + 'px', width: s.w + 'px', height: s.h + 'px',
      boxSizing: 'border-box', pointerEvents: 'none', zIndex: 2147483000, borderRadius: '3px',
      border: (s.线型 === 'dashed' ? '2px dashed' : '2px solid') + ' rgb(255, 140, 0)' });
    document.body.appendChild(d); }
  const 读回 = {}; for (const s of S) { const c = getComputedStyle(document.getElementById(s.id));
    读回[s.id] = { 宽: parseFloat(c.width), 高: parseFloat(c.height), borderStyle: c.borderStyle, borderColor: c.borderColor, pointerEvents: c.pointerEvents }; }
  return { 框数: S.length, 读回 };
}, K);
const 校 = (画, 期望) => { const ids = Object.keys(画.读回);
  const r = { 框数对: 画.框数 === 期望, 全非空: ids.every((k) => 画.读回[k].宽 > 0 && 画.读回[k].高 > 0),
    线型都被认: ids.every((k) => ['solid', 'dashed'].includes(画.读回[k].borderStyle)),
    颜色都对: ids.every((k) => 画.读回[k].borderColor === 'rgb(255, 140, 0)'),
    pointerEvents都为none: ids.every((k) => 画.读回[k].pointerEvents === 'none') };
  r.全过 = Object.values(r).every(Boolean); return r; };
const 清框 = () => p.evaluate(() => document.querySelectorAll('[id^="__b196-"]').forEach((e) => e.remove()));

const out = { 轮次: 'b196f', 图: {} };
const 拍 = async (名, 规格, 守卫, 裁切) => {
  const 画 = await 框(规格); const c = 校(画, 规格.length); const d = await 守卫();
  out.图[名] = { 断言: d, 守卫: c, 裁切 };
  const 全过 = c.全过 && d.通过;
  log(名, '：', d.判据, '→', d.通过 ? '✅' : '🔴', '| 画框', c.全过 ? '✅' : '🔴' + JSON.stringify(c));
  if (!全过) { await 清框(); out.图[名].跳过 = '守卫没过 ⇒ 不拍'; return; }
  await p.screenshot({ path: `${OUTDIR}/${名}.png`, clip: 裁切 });
  out.图[名].已拍 = true; await 清框();
};

await 点左栏('资产库');
const dlg = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return null; const r = d.getBoundingClientRect();
  return { 屏上: [r.x, r.y, r.width, r.height].map(Math.round), 文本: d.innerText.replace(/\s+/g, ' ').trim() }; });
out.dialog = dlg;
log('dialog：', JSON.stringify(dlg));

const 页签 = async (文字) => p.evaluate((t) => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return null;
  const e = Array.from(d.querySelectorAll('button,[role="tab"]')).find((x) => (x.getAttribute('aria-label') || x.innerText || '').trim() === t && x.getBoundingClientRect().width > 4);
  if (!e) return null; const r = e.getBoundingClientRect();
  return { 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
    框: { x: Math.round(r.x - 3), y: Math.round(r.y - 3), w: Math.round(r.width + 6), h: Math.round(r.height + 6) },
    选中态: e.getAttribute('aria-selected') || e.getAttribute('data-state') || e.className.toString().includes('active') ? '是' : '否' }; }, 文字);

const 裁切 = { x: Math.max(2, dlg.屏上[0] - 14), y: Math.max(2, dlg.屏上[1] - 14),
  width: Math.min(dlg.屏上[2] + 28, 1280 - dlg.屏上[0] - 2), height: Math.min(dlg.屏上[3] + 28, 720 - dlg.屏上[1] - 2) };
out.裁切 = 裁切;

const 一级资产 = await 页签('资产');
const 二级视频 = await 页签('视频');
const 二级图片 = await 页签('图片');
log('一级「资产」：', JSON.stringify(一级资产), '| 二级「视频」：', JSON.stringify(二级视频), '| 二级「图片」：', JSON.stringify(二级图片));

// ===== 19４ dialog 全貌：框 dialog + 两级页签 =====
await 拍('194-asset-library-dialog', [
    { id: '__b196-dlg', x: 裁切.x + 12, y: 裁切.y + 12, w: dlg.屏上[2], h: dlg.屏上[3], 线型: 'solid' },
    ...(一级资产 ? [{ id: '__b196-t1', ...一级资产.框, 线型: 'dashed' }] : []),
    ...(二级视频 ? [{ id: '__b196-t2', ...二级视频.框, 线型: 'dashed' }] : []) ],
  async () => ({ 判据: 'dialog 在 且 文本逐字含「暂无图片素材」', 读数: dlg.文本.slice(0, 80), 通过: !!dlg && dlg.文本.includes('暂无图片素材') }), 裁切);

// ===== 19５ 切到「视频」页签后的空态 =====
if (二级视频) { await p.mouse.click(二级视频.屏上[0] + 二级视频.屏上[2] / 2, 二级视频.屏上[1] + 二级视频.屏上[3] / 2); await p.waitForTimeout(1500); }
const 视频页文本 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return d ? d.innerText.replace(/\s+/g, ' ').trim() : null; });
out.视频页文本 = 视频页文本;
log('视频页：', 视频页文本);
const 裁切视频 = { x: 裁切.x, y: Math.max(2, dlg.屏上[1] + 40), width: 裁切.width, height: Math.min(dlg.屏上[1] + dlg.屏上[3] + 14 - Math.max(2, dlg.屏上[1] + 40), 720 - Math.max(2, dlg.屏上[1] + 40) - 2) };
await 拍('195-asset-library-video-empty', [
    { id: '__b196-video-tab', ...(二级视频 ? 二级视频.框 : { x: 0, y: 0, w: 0, h: 0 }), 线型: 'solid' } ],
  async () => ({ 判据: 'dialog 文本逐字含「暂无视频素材」', 读数: 视频页文本 ? 视频页文本.slice(0, 80) : null, 通过: !!视频页文本 && 视频页文本.includes('暂无视频素材') }), 裁切视频);

// ===== 19６ 「时间」页的日期筛选器 =====
const 时间页签 = await 页签('时间');
if (时间页签) { await p.mouse.click(时间页签.屏上[0] + 时间页签.屏上[2] / 2, 时间页签.屏上[1] + 时间页签.屏上[3] / 2); await p.waitForTimeout(1500); }
const 时间页文本 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return d ? d.innerText.replace(/\s+/g, ' ').trim() : null; });
const 时间控件 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return [];
  return Array.from(d.querySelectorAll('button,[role="button"],[role="radio"]')).map((e) => { const r = e.getBoundingClientRect();
    return { 文字: (e.getAttribute('aria-label') || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40),
      屏上: [r.x, r.y, r.width, r.height].map(Math.round) }; })
    .filter((x) => /全部|最近一周|最近一个月|最近三个月|开始日期|结束日期/.test(x.文字)); });
out.时间页文本 = 时间页文本; out.时间控件 = 时间控件;
log('时间页：', 时间页文本); log('时间页控件：', JSON.stringify(时间控件));
const 规格时间 = 时间控件.slice(0, 3).map((c, i) => ({ id: '__b196-tc' + i, x: Math.round(c.屏上[0] - 3), y: Math.round(c.屏上[1] - 3), w: Math.round(c.屏上[2] + 6), h: Math.round(c.屏上[3] + 6), 线型: i % 2 === 0 ? 'solid' : 'dashed' }));
await 拍('196-asset-library-time-filter', 规格时间,
  async () => ({ 判据: 'dialog 文本逐字含「最近一周」且 读到 ≥1 个日期控件', 读数: 时间页文本 ? 时间页文本.slice(0, 120) : null,
    通过: !!时间页文本 && 时间页文本.includes('最近一周') && 时间控件.length >= 1 }), 裁切);

await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
fs.writeFileSync('/tmp/b196f.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
