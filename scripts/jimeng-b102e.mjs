// 批次 102 · e 轮：① `.txt` 上传到底有没有完成态状态串（现在离上传已过去几分钟）
//                     ② 给「文本文件 → 文本节点」拍一张干净的截图
//                     ③ 按护栏删掉自建节点、归位
//
// d 轮的结论已经很硬：
//   · 「空白右键 → 新建节点 → **本地上传**」**这条入口成立**（手册列了但从没验过）
//     且它用的 input **就挂在子菜单里**（`DIV#context-menu-submenu-add-node` 之下），
//     `accept` **同样是 111 条**、`multiple` 同样为 `true`
//   · **`.txt` 上传后建出来的是「文本」节点**（`react-flow__node-text`，aria `文本 node: jimeng-b102-doc`），
//     **文件内容被灌进了节点正文**（innerText 逐字含 `JIMENG B102 DOC TEST / line two / line three`）
//     ⇒ 「上传文本文件」是产品声明支持、而**全册手册一个字都没提过**的能力
//   · 积分 **805 → 805**（文本上传也免费）
//   · ⚠️ d 轮抓状态串时**只看到** `b22-upload.png: Upload complete` 与
//     `jimeng-b101-test-avc1.mp4: Upload complete`，**没有** txt 那条 —— 需确认是「文本不产生」
//     还是「文本的状态串出现得更晚」
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_0gg1c9b3tq' };
const SELF = out.selfId;
const SHOT = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// ---- ① 状态串：按**叶子元素**逐个读，别读父容器的 textContent（会重复 20 遍） ----
log('=== ① 状态串（按叶子元素）===');
out.status = await p.evaluate(() => {
  const leaves = Array.from(document.querySelectorAll('.sr-only,[role=status],[aria-live]'))
    .filter((e) => !Array.from(e.children).some((c) => /upload|上传/i.test(c.textContent || '')))
    .map((e) => ({ t: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 80),
      w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))
    .filter((x) => x.t && /upload|上传|\.txt|\.png|\.mp4/i.test(x.t));
  return { n: leaves.length, uniq: Array.from(new Set(leaves.map((x) => x.t))), sample: leaves.slice(0, 8) };
});
log('叶子状态串去重后：', JSON.stringify(out.status.uniq, null, 1));
out.txtHasStatus = out.status.uniq.some((t) => /b102-doc|\.txt/.test(t));
log('  ⇒ 有没有 `jimeng-b102-doc.txt: Upload complete` 这条？', out.txtHasStatus ? '✅ 有' : '❌ 没有');

// ---- ② 截图：把文本节点挪到无遮挡位置 ----
log('\n=== ② 文本节点截图 ===');
out.plan = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const se = n.querySelector('[data-testid="text-flow-node-full"]') || n;
  const surf = se.getBoundingClientRect();
  const te = n.querySelector('[data-testid="flow-node-title"]');
  const TITLE = te ? Math.round(surf.y - te.getBoundingClientRect().y) : 0;
  const W = Math.round(surf.width), H = Math.round(surf.height);
  const L = 12, T = 0, R = 12, Bt = 12;
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e !== n && !e.contains(n) && !n.contains(e))
    .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height }; });
  const clearAt = (x, y) => { const bx0 = x - L, by0 = y - TITLE - T, bx1 = x + W + R, by1 = y + H + Bt;
    if (bx0 < 195 || by0 < 62 || bx1 > 1276 || by1 > 636) return false;
    return !others.some((o) => o.x0 < bx1 && o.x1 > bx0 && o.y0 < by1 && o.y1 > by0); };
  const cur = { x: Math.round(surf.x), y: Math.round(surf.y) };
  let best = null;
  for (let dy = -200; dy <= 200; dy += 4) for (let dx = -280; dx <= 280; dx += 4) {
    if (!clearAt(cur.x + dx, cur.y + dy)) continue;
    const d = Math.abs(dx) + Math.abs(dy); if (!best || d < best.d) best = { dx, dy, d }; }
  return { W, H, TITLE, cur, best, othersCount: others.length, hereClear: clearAt(cur.x, cur.y) };
}, SELF);
log('尺寸/空位：', JSON.stringify(out.plan));

if (out.plan && !out.plan.__err && out.plan.best) {
  const grab = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return { __err: 'no-title' };
    const r = t.getBoundingClientRect();
    for (let f = 0.03; f <= 0.97; f += 0.02) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
      const el = document.elementFromPoint(x, y);
      if (!el || el.closest('button') || !el.closest('[data-testid="flow-node-title"]')) continue;
      return { point: [x, y] }; }
    return { __err: 'no-free-point' }; }, SELF);
  if (!grab.__err) {
    await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(400);
    await p.mouse.down(); await p.waitForTimeout(280);
    await p.mouse.move(grab.point[0] + Math.round(out.plan.best.dx / 2), grab.point[1] + Math.round(out.plan.best.dy / 2), { steps: 10 });
    await p.waitForTimeout(300);
    await p.mouse.move(grab.point[0] + out.plan.best.dx, grab.point[1] + out.plan.best.dy, { steps: 10 });
    await p.waitForTimeout(450); await p.mouse.up(); await p.waitForTimeout(1300);
    log('已拖动：', JSON.stringify(out.plan.best));
  }
  // 重新选中（文本节点选中不自动播，等价地重新点一次）
  const pt = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = (n.querySelector('[data-testid="text-flow-node-full"]') || n).getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + 24);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(300); await p.mouse.click(pt.point[0], pt.point[1]); await p.waitForTimeout(1100); }
}

out.crop = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const pick = ['flow-node-title', 'text-flow-node-full', 'text-node-selection-outline', 'text-node-resize-controls'];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const t of pick) { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) continue;
    const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); }
  if (!isFinite(x0)) { const r = n.getBoundingClientRect(); x0 = r.x; y0 = r.y; x1 = r.x + r.width; y1 = r.y + r.height; }
  const L = 12, T = 0, R = 12, Bt = 12;
  const clip = { x: Math.max(0, Math.floor(x0 - L)), y: Math.max(0, Math.floor(y0 - T)), width: 0, height: 0 };
  clip.width = Math.ceil(Math.min(x1 - x0 + L + R, 1280 - clip.x));
  clip.height = Math.ceil(Math.min(y1 - y0 + T + Bt, 720 - clip.y));
  const hits = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label') }));
  const chrome = Array.from(document.querySelectorAll('.react-flow__node-toolbar,[role=menu],[role=dialog]'))
    .map((e) => { const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) return null;
      if (!(r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y)) return null;
      return { cls: (e.className || '').toString().slice(0, 40), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }).filter(Boolean);
  return { clip, hits, chrome, innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = !out.crop.__err && out.crop.hits.length === 0 && out.crop.chrome.length === 0;
log('守卫：', out.guardPass ? '✅' : '🔴');
if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('103-upload-txt-becomes-text-node.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 ', JSON.stringify(out.shot));
}

writeFileSync(new URL('./_tmp-b102e.json', import.meta.url), JSON.stringify(out, null, 1));
log('\n当前：', JSON.stringify({ nodes: await nodeN(), sel: await selN() }));
await b.close();
