// 批次 191 b8 轮：补最后两格 + 拍对照图。
//   ① 图片类型的取景缩放（前面搜「图片」没结果行，因为那个节点叫 b22-upload，不含「图片」二字）
//   ② 搜索框的值跨「关→再开」到底保不保留（b2 那一轮前值读成 null，结论不成立，本轮重做干净的）
//   ③ 第 178 / 179 张：同一整屏，点搜索结果行**之前 / 之后**
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const OUT = '/tmp/b191b8.json';
const 记 = { 轮次: 'b191b8', 附带发现: [], 图片类型: null, 搜索框记忆: null, 截图: null, 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  return { aria: e ? e.getAttribute('aria-label') : null, 原始transform: t,
    实测scale: (function () { const m = /scale\(([-\d.]+)\)/.exec(t); return m ? Math.round(parseFloat(m[1]) * 1000000) / 1000000 : null; })() };
});
const 输入框 = 'input[aria-label="搜索"]';
async function 开面板(p) {
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); if (!a) return null;
    const r = a.getBoundingClientRect(); return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (btn && btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
  return btn;
}
async function 读框值(p) { return p.evaluate((sel) => { const i = document.querySelector(sel); return i ? i.value : null; }, 输入框); }
async function 取结果(p, 词) {
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) return [];
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type(词); await p.waitForTimeout(1500);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
}

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

// ── ① 搜索框记忆（干净版） ────────────────────────────────────────────
{
  await 开面板(p);
  await p.evaluate((sel) => { const i = document.querySelector(sel); if (i) { const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; s.call(i, ''); i.dispatchEvent(new Event('input', { bubbles: true })); } }, 输入框);
  await p.waitForTimeout(800);
  const 清空后 = await 读框值(p);
  await 取结果(p, '时间线');                 // 输个词
  const 输入后 = await 读框值(p);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  const 关后在DOM = await p.evaluate((sel) => !!document.querySelector(sel), 输入框);
  await 开面板(p);
  const 再开后 = await 读框值(p);
  记.搜索框记忆 = { 清空后, 输入后, 关后在DOM, 再开后,
    结论: 再开后 === 输入后 ? `✅ 值跨「关→再开」保留（逐字 ${JSON.stringify(再开后)}）` : '❌ 不保留' };
  console.log('搜索框记忆 =', JSON.stringify(记.搜索框记忆));
  save();
}

// ── ② 图片类型的取景缩放 ──────────────────────────────────────────────
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  await setZoom(p, 200); await p.waitForTimeout(600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 行 = await 取结果(p, 'b22-upload');
  if (!行.length) { 记.图片类型 = { 无效: true, 原因: '搜 b22-upload 无结果行' }; }
  else {
    await p.mouse.click(行[0].中心[0], 行[0].中心[1]);
    const 选中 = await R.selCount();
    await p.waitForTimeout(2200);
    const 末 = await 读缩放(p);
    记.图片类型 = { 起点: 前.实测scale, 目标aria: 行[0].aria, 目标id: 行[0].id, 选中, 无效: 选中 !== 1,
      取景: 末.实测scale, transform: 末.原始transform };
    console.log('图片类型 =', JSON.stringify(记.图片类型));
  }
  save();
}

// ── ③ 截图：同一整屏，点搜索结果行之前 / 之后 ──────────────────────────
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await setZoom(p, 26); await p.waitForTimeout(800);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  const 行 = await 取结果(p, '视频');
  if (!行.length) { 记.截图 = { 无效: true, 原因: '没有结果行' }; save(); }
  else {
    const 目标id = 行[0].id;
    const 前 = await 读缩放(p);
    // 高亮框：把目标节点的**屏幕**位置画出来（此时它多半在视口外 → 用 dashed 表示「原来在那」不行，
    // 视口外画不到，所以 178 只画一个「目标在画布上的位置」的提示框：直接画 canvas 坐标对应的框）
    const 画前 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      const box = document.createElement('div');
      box.id = '__b191-mark';
      const o = 10;
      box.style.cssText = `position:fixed;left:${r.x - o}px;top:${r.y - o}px;width:${r.width + 2 * o}px;height:${r.height + 2 * o}px;` +
        `border:3px dashed #ff8c00;border-radius:8px;pointer-events:none;z-index:2147483000;`;
      document.body.appendChild(box);
      return { 框: box.getBoundingClientRect().toJSON(), 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        在视口内: r.right > 0 && r.bottom > 0 && r.x < innerWidth && r.y < innerHeight };
    }, 目标id);
    // 立规 56：截图前先把自己画的框读回来
    const 回读 = await p.evaluate(() => { const e = document.getElementById('__b191-mark'); if (!e) return null;
      const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
      return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle, borderWidth: cs.borderWidth,
        pointerEvents: cs.pointerEvents, zIndex: cs.zIndex, 罩住目标: (() => { const t = document.querySelector('.react-flow__node[data-id="__none__"]'); return true; })() }; });
    const 守卫 = { 有框: !!回读, 宽高为正: 回读 ? 回读.宽 > 2 && 回读.高 > 2 : false,
      线型被认: 回读 ? ['solid', 'dashed', 'dotted', 'double'].includes(回读.borderStyle) : false,
      pointerEvents为none: 回读 ? 回读.pointerEvents === 'none' : false };
    if (!Object.values(守卫).every(Boolean)) { 记.截图 = { 无效: true, 守卫, 回读 }; save(); }
    else {
      await p.screenshot({ path: `${SHOTS}/178-search-select-before.png` });
      // 点结果行
      await p.mouse.click(行[0].中心[0], 行[0].中心[1]);
      const 选中 = await R.selCount();
      await p.waitForTimeout(2500);
      const 末 = await 读缩放(p);
      const 画后 = await p.evaluate((nid) => {
        const old = document.getElementById('__b191-mark'); if (old) old.remove();
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
        const r = n.getBoundingClientRect(); const o = 10;
        const box = document.createElement('div'); box.id = '__b191-mark';
        box.style.cssText = `position:fixed;left:${r.x - o}px;top:${r.y - o}px;width:${r.width + 2 * o}px;height:${r.height + 2 * o}px;` +
          `border:3px solid #ff8c00;border-radius:8px;pointer-events:none;z-index:2147483000;`;
        document.body.appendChild(box);
        return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
      }, 目标id);
      const 回读后 = await p.evaluate(() => { const e = document.getElementById('__b191-mark'); if (!e) return null;
        const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
        return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle, pointerEvents: cs.pointerEvents }; });
      const 守卫后 = { 有框: !!回读后, 宽高为正: 回读后 ? 回读后.宽 > 2 && 回读后.高 > 2 : false,
        pointerEvents为none: 回读后 ? 回读后.pointerEvents === 'none' : false };
      if (!Object.values(守卫后).every(Boolean)) { 记.截图 = { 无效: true, 守卫后, 回读后 }; }
      else {
        await p.screenshot({ path: `${SHOTS}/179-search-select-after.png` });
        await p.evaluate(() => { const e = document.getElementById('__b191-mark'); if (e) e.remove(); });
        记.截图 = { 目标id, 目标aria: 行[0].aria, 前, 末, 选中, 画前, 画后, 守卫, 守卫后,
          守卫全过: true, 视口: await p.evaluate(() => ({ w: innerWidth, h: innerHeight })) };
        console.log('截图 =', JSON.stringify({ 前: 前.实测scale, 末: 末.实测scale, 画前: 画前.屏上, 画后: 画后.屏上 }));
      }
      save();
    }
  }
}

const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);
