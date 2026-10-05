// 批次 195 c 轮：三档状态的**逐元素读数**（未选中 / 已选中未播 / 正在播）
//
// 假设：media-playback.md 的三档表仍然成立，且
//   ① 「已选中还没播过」档只有 5 个按钮，mute/fullscreen 不在 DOM 里；
//   ② 点**标题行**能造出「已选中但没播过」这一档（点卡片正文会「选中即播」）；
//   ③ 「正在播」档控件行 5 个控件尺寸与手册逐字一致。
// 只读，不截图。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_anew4vmz06';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));

await setZoom(p, 100);

const 读 = (档) => p.evaluate((args) => {
  const [i, 名] = args;
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { 档: 名, 消失: true };
  const r = n.getBoundingClientRect();
  const g = (sel) => { const e = n.querySelector(sel); if (!e) return null;
    const b2 = e.getBoundingClientRect();
    return { 屏上: [b2.x, b2.y, b2.width, b2.height].map((x) => Math.round(x * 100) / 100) }; };
  return {
    档: 名,
    屏上: [r.x, r.y, r.width, r.height].map((x) => Math.round(x * 100) / 100),
    选中: n.classList.contains('selected'),
    innerText: n.innerText.replace(/\s+/g, ' ').trim(),
    video: Array.from(n.querySelectorAll('video')).map((v) => ({
      src: (v.currentSrc || v.getAttribute('src') || '').slice(0, 60), paused: v.paused,
      currentTime: Math.round((v.currentTime || 0) * 1000) / 1000, dur: v.duration, muted: v.muted, vol: v.volume, readyState: v.readyState })),
    img: n.querySelectorAll('img').length,
    按钮: Array.from(n.querySelectorAll('button')).map((b2) => b2.getAttribute('aria-label') || b2.innerText.trim()),
    关键几何: {
      封面: g('[data-testid="video-passive-preview"]'),
      大播放键: g('[data-testid="video-simple-player"]'),
      控件行: g('[data-testid="video-node-player-bar"]'),
      播放暂停: g('[data-testid="video-node-playback-toggle"]'),
      时间读数: g('[data-testid="video-node-player-clock"]'),
      静音: g('[data-testid="video-node-mute-toggle"]'),
      全屏: g('[data-testid="video-node-fullscreen-toggle"]'),
      进度条: g('[role="slider"]'),
    },
    进度条aria: Array.from(n.querySelectorAll('[role="slider"]')).map((e) => e.getAttribute('aria-label') + ' | valuemax=' + e.getAttribute('aria-valuemax') + ' | value=' + e.getAttribute('aria-valuenow')),
  };
}, [SELF, 'x']);

const 点空白 = async () => {
  const spot = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y];
    }
    return null;
  });
  if (!spot) { log('🔴 找不到空白点'); return null; }
  await p.mouse.click(spot[0], spot[1]); await p.waitForTimeout(900);
  return spot;
};

const out = { 轮次: 'b195c', SELF };

// 档 A：未选中
const sp = await 点空白();
out.空白点 = sp;
out.档A_未选中 = await 读('A 未选中');
log('档A 选中=', out.档A_未选中.选中, '| 按钮', JSON.stringify(out.档A_未选中.按钮), '| video', out.档A_未选中.video.length, '| img', out.档A_未选中.img);

// 档 B：点**标题行**（不点卡片正文，避免「选中即播」）
const 标题点 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const t = n.querySelector('[data-testid="flow-node-title"]') || n.querySelector('.flow-node-title');
  if (!t) return null;
  const r = t.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, SELF);
out.标题点 = 标题点;
log('标题点 =', JSON.stringify(标题点));
if (标题点) { await p.mouse.click(标题点[0], 标题点[1]); await p.waitForTimeout(1200); }
out.档B_点标题行 = await 读('B 点标题行');
log('档B 选中=', out.档B_点标题行.选中, '| 按钮', JSON.stringify(out.档B_点标题行.按钮), '| video', out.档B_点标题行.video.length, '| 控件行', JSON.stringify(out.档B_点标题行.关键几何.控件行));

// 档 C：点**卡片正文**（应「选中即播」）
const 正文点 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)];
}, SELF);
out.正文点 = 正文点;
log('正文点 =', JSON.stringify(正文点));
if (正文点) { await p.mouse.click(正文点[0], 正文点[1]); await p.waitForTimeout(1500); }
out.档C_点正文 = await 读('C 点正文');
log('档C 选中=', out.档C_点正文.选中, '| 按钮', JSON.stringify(out.档C_点正文.按钮), '| video', JSON.stringify(out.档C_点正文.video), '| 控件行', JSON.stringify(out.档C_点正文.关键几何.控件行));

fs.writeFileSync('/tmp/b195c.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
