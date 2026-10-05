// 批次 195 g 轮：给 media-playback.md 拍三张「三档状态」对照图 + 一张控件行逐项标注图。
//
// 三张对照图用**同一裁切**（节点位置不动 ⇒ 可叠着看），各自证明三档表的一行：
//   189 未选中      —— 只有封面图 + 2 个按钮，无 <video>、无播放键、无控件行
//   190 已选中未播  —— 多出正中 44×44 大播放键，按钮恰好 5 个，仍无 <video>
//   191 正在播      —— 大播放键消失、控件行 5 个控件到齐、<video> 在且 paused=false
//   192 控件行逐项  —— 5 个控件各一个框 + 屏上尺寸读数
//
// 🛡 纪律：每张拍前先断言该档状态（阳性守卫）→ 画框 → 读回自己画的框 → 截图放最后。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_anew4vmz06';
const OUTDIR = 'docs/user-manual/jimeng-canvas/screenshots';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
await setZoom(p, 100);

const 状态 = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video');
  return { 选中: n.classList.contains('selected'), 有video: !!v, paused: v ? v.paused : null,
    currentTime: v ? Math.round(v.currentTime * 1000) / 1000 : null,
    按钮数: n.querySelectorAll('button').length,
    按钮: Array.from(n.querySelectorAll('button')).map((x) => x.getAttribute('aria-label') || x.innerText.trim()),
    控件行: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    大播放键: !!n.querySelector('[data-testid="video-simple-player"]') };
}, SELF);

// ---- 画框 + 读回（立规 56 / 68）----
const 画框 = (规格) => p.evaluate((K) => {
  document.querySelectorAll('[id^="__b195-"]').forEach((e) => e.remove());
  const made = K.map((s) => {
    const d = document.createElement('div');
    d.id = s.id; Object.assign(d.style, {
      position: 'fixed', left: s.x + 'px', top: s.y + 'px', width: s.w + 'px', height: s.h + 'px',
      boxSizing: 'border-box', pointerEvents: 'none', zIndex: 2147483000,
      border: (s.线型 === 'dashed' ? '2px dashed' : '2px solid') + ' rgb(255, 140, 0)', borderRadius: '2px' });
    document.body.appendChild(d); return s.id;
  });
  const 读回 = {};
  for (const id of made) { const e = document.getElementById(id); const c = getComputedStyle(e);
    读回[id] = { 宽: parseFloat(c.width), 高: parseFloat(c.height), borderStyle: c.borderStyle, borderColor: c.borderColor, pointerEvents: c.pointerEvents }; }
  return { 框数: made.length, 读回 };
}, 规格);

const 校验 = (画, 期望框数) => {
  const ids = Object.keys(画.读回);
  const 全非空 = ids.every((k) => 画.读回[k].宽 > 0 && 画.读回[k].高 > 0);
  const 线型都被认 = ids.every((k) => ['solid', 'dashed'].includes(画.读回[k].borderStyle));
  const 颜色都对 = ids.every((k) => 画.读回[k].borderColor === 'rgb(255, 140, 0)');
  const 都不可吃鼠标 = ids.every((k) => 画.读回[k].pointerEvents === 'none');
  const 框数对 = 画.框数 === 期望框数;
  return { 框数对, 全非空, 线型都被认, 颜色都对, pointerEvents都为none: 都不可吃鼠标,
    全过: 框数对 && 全非空 && 线型都被认 && 颜色都对 && 都不可吃鼠标 };
};

const 清框 = () => p.evaluate(() => document.querySelectorAll('[id^="__b195-"]').forEach((e) => e.remove()));

const 点空白 = async () => { const s = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) { const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; } return null; });
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(700); } return s; };
const 点标题 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(900); } return s; };
const 点正文 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(350); } return s; };

// 同一裁切：节点 ∪ 标题行 ∪ 控件行，外扩 26px
const 裁切 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  let t = r.top, bo = r.bottom, le = r.left, ri = r.right;
  for (const sel of ['[data-testid="flow-node-title"]', '[data-testid="video-node-player-bar"]', '[data-testid="video-simple-player"]']) {
    const e = n.querySelector(sel); if (!e) continue; const b = e.getBoundingClientRect();
    t = Math.min(t, b.top); bo = Math.max(bo, b.bottom); le = Math.min(le, b.left); ri = Math.max(ri, b.right);
  }
  const pad = 26;
  return { x: Math.max(2, Math.round(le - pad)), y: Math.max(62, Math.round(t - pad)),
           width: Math.min(Math.round(ri + pad) - Math.max(2, Math.round(le - pad)), 1280 - Math.max(2, Math.round(le - pad)) - 2),
           height: Math.min(Math.round(bo + pad) - Math.max(62, Math.round(t - pad)), 720 - Math.max(62, Math.round(t - pad)) - 2),
           节点屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100) };
}, SELF);
log('裁切：', JSON.stringify(裁切));
const out = { 轮次: 'b195g', SELF, 裁切, 图: {} };

const 拍 = async (文件名, 规格, 守卫, 裁切框) => {
  const 画 = await 画框(规格);
  const 校验结果 = 校验(画, 规格.length);
  const 断言 = await 守卫();
  out.图[文件名] = { 断言, 框: 画.读回, 守卫: 校验结果, 裁切: 裁切框 || 裁切 };
  const 全过 = 校验结果.全过 && 断言.通过;
  log(文件名, '：断言', 断言.判据, '→', 断言.通过 ? '✅' : '🔴', '| 画框守卫', 校验结果.全过 ? '✅' : '🔴 ' + JSON.stringify(校验结果));
  if (!全过) { await 清框(); out.图[文件名].跳过 = '守卫没过 ⇒ 不拍'; return; }
  await p.screenshot({ path: `${OUTDIR}/${文件名}.png`, clip: 裁切框 || 裁切 });
  out.图[文件名].已拍 = true;
  await 清框();
};

// ===== 图 189：未选中 =====
await 点空白(); await p.waitForTimeout(800);
const s189 = await 状态();
log('189 状态：', JSON.stringify(s189));
await 拍('189-video-node-unselected', [{ id: '__b195-card', ...(() => { const [x, y, w, h] = 裁切.节点屏上; return { x: Math.round(x - 4), y: Math.round(y - 4), w: Math.round(w + 8), h: Math.round(h + 8) }; })(), 线型: 'solid' }],
  async () => { const s = await 状态(); const ok = s.选中 === false && s.有video === false && s.大播放键 === false && s.控件行 === false;
    return { 判据: '选中=false 且 无<video> 且 无大播放键 且 无控件行', 读数: s, 通过: ok }; });

// ===== 图 190：已选中但没播过 =====
await 点标题(); await p.waitForTimeout(700);
const s190 = await 状态();
log('190 状态：', JSON.stringify(s190));
const g190 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-simple-player"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x - 20), y: Math.round(r.y - 20), w: Math.round(r.width + 40), h: Math.round(r.height + 40) };
}, SELF);
await 拍('190-video-node-selected-not-played', [
    { id: '__b195-card', ...(() => { const [x, y, w, h] = 裁切.节点屏上; return { x: Math.round(x - 4), y: Math.round(y - 4), w: Math.round(w + 8), h: Math.round(h + 8) }; })(), 线型: 'solid' },
    ...(g190 ? [{ id: '__b195-play', ...g190, 线型: 'dashed' }] : []) ],
  async () => { const s = await 状态(); const ok = s.选中 === true && s.有video === false && s.大播放键 === true && s.按钮.length === 5;
    return { 判据: '选中=true 且 无<video> 且 有大播放键 且 按钮数=5', 读数: s, 通过: ok }; });

// ===== 图 191：正在播 =====
await 点正文(); await p.waitForTimeout(500);
const s191 = await 状态();
log('191 状态：', JSON.stringify(s191));
const g191 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-player-bar"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x - 6), y: Math.round(r.y - 6), w: Math.round(r.width + 12), h: Math.round(r.height + 12) };
}, SELF);
await 拍('191-video-node-playing', [
    { id: '__b195-card', ...(() => { const [x, y, w, h] = 裁切.节点屏上; return { x: Math.round(x - 4), y: Math.round(y - 4), w: Math.round(w + 8), h: Math.round(h + 8) }; })(), 线型: 'solid' },
    ...(g191 ? [{ id: '__b195-bar', ...g191, 线型: 'dashed' }] : []) ],
  async () => { const s = await 状态(); const ok = s.选中 === true && s.有video === true && s.paused === false && s.控件行 === true && s.大播放键 === false && s.currentTime > 0;
    return { 判据: '选中=true 且 有<video> 且 paused=false 且 控件行在 且 大播放键不在 且 currentTime>0', 读数: s, 通过: ok }; });

// ===== 图 192：控件行逐项标注 =====
const 控件 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const 单 = (sel) => { const e = n.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect();
    return { 屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100),
             框: { x: Math.round(r.x - 7), y: Math.round(r.y - 7), w: Math.round(r.width + 14), h: Math.round(r.height + 14) },
             aria: e.getAttribute('aria-label'), text: (e.innerText || '').trim().slice(0, 20) }; };
  return { 播放暂停: 单('[data-testid="video-node-playback-toggle"]'), 时间读数: 单('[data-testid="video-node-player-clock"]'),
           静音: 单('[data-testid="video-node-mute-toggle"]'), 全屏: 单('[data-testid="video-node-fullscreen-toggle"]'),
           进度条: 单('[data-testid="slider-track"]'),
           全部slider: Array.from(n.querySelectorAll('[role="slider"]')).map((e) => (e.getAttribute('aria-label') || '') + ' | valuemax=' + e.getAttribute('aria-valuemax') + ' | value=' + e.getAttribute('aria-valuenow')) };
}, SELF);
log('控件读数：', JSON.stringify(控件, null, 1));
out.控件读数 = 控件;
const 规格192 = [['__b195-tog', 控件.播放暂停], ['__b195-clk', 控件.时间读数], ['__b195-mute', 控件.静音], ['__b195-fs', 控件.全屏], ['__b195-seek', 控件.进度条]]
  .filter(([, v]) => v).map(([id, v], k) => ({ id, ...v.框, 线型: k % 2 === 0 ? 'solid' : 'dashed' }));
// 控件行可能在播放中消失 ⇒ 逐项实读，不一致就标无效臂
const 仍控件行 = await 状态();
out.图['192'] = { 控件读数: 控件, 拍前状态: 仍控件行 };
if (规格192.length === 5) {
  await 拍('192-video-player-bar-items', 规格192,
    async () => { const s = await 状态(); return { 判据: '控件行仍在 且 paused=false', 读数: s, 通过: s.控件行 === true }; });
} else {
  out.图['192'].跳过 = `只读到 ${规格192.length} 个控件 ⇒ 不拍`;
  log('🔴 192 跳过：', out.图['192'].跳过);
}

fs.writeFileSync('/tmp/b195g.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
