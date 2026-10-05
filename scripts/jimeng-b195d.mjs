// 批次 195 d 轮：🔴 深挖「选中即播」——点卡片正文后 <video> 到底播不播？
//
// 触发：c 轮档 C 点正文后读到 <video> 已挂进 DOM（readyState 4 / duration 6），
//   **但 paused = true、currentTime = 0**，播放钮 aria 仍是 `Play <名>`。
//   而 media-playback.md 入口节逐字写「单击视频卡片。**选中即播** —— 视频自动从 0 开始播放」。
//   ⇒ 两条读数冲突，必须用**时间序列**分清「起播了又停」和「根本没起播」（立规 62）。
//
// 本轮：① 点正文后连采时间序列；② 若没播，再点大播放键连采；
//   ③ 对照：取消选中后再点正文。只读，不截图。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_anew4vmz06';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
await setZoom(p, 100);

const 采一帧 = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { 消失: true };
  const v = n.querySelector('video');
  const tog = n.querySelector('[data-testid="video-node-playback-toggle"]');
  const clk = n.querySelector('[data-testid="video-node-player-clock"]');
  return {
    选中: n.classList.contains('selected'),
    有video: !!v,
    paused: v ? v.paused : null,
    currentTime: v ? Math.round(v.currentTime * 1000) / 1000 : null,
    readyState: v ? v.readyState : null,
    muted: v ? v.muted : null,
    播放钮aria: tog ? tog.getAttribute('aria-label') : null,
    时钟文字: clk ? clk.innerText.trim() : null,
    innerText尾: n.innerText.replace(/\s+/g, ' ').trim().slice(-60),
  };
}, SELF);

const 序列 = async (标签, 次数 = 12, 间隔 = 400) => {
  const 序 = [];
  for (let k = 0; k < 次数; k++) { 序.push({ 第几次: k + 1, 距上次ms: k === 0 ? 0 : 间隔, ...(await 采一帧()) }); await p.waitForTimeout(间隔); }
  log(标签, '：currentTime 序列 =', JSON.stringify(序.map((x) => x.currentTime)), '| paused 集合 =', JSON.stringify([...new Set(序.map((x) => x.paused))]), '| 播放钮aria 集合 =', JSON.stringify([...new Set(序.map((x) => x.播放钮aria))]));
  return 序;
};

const 点空白 = async () => {
  const spot = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y];
    }
    return null;
  });
  if (spot) { await p.mouse.click(spot[0], spot[1]); await p.waitForTimeout(1000); }
  return spot;
};

const 点标题 = async () => {
  const pt = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]');
    if (!t) return null; const r = t.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, SELF);
  if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1100); }
  return pt;
};

const 点正文 = async () => {
  const pt = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)];
  }, SELF);
  if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(300); }
  return pt;
};

const 点大播放键 = async () => {
  const pt = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const b2 = n.querySelector('[data-testid="video-simple-player"]') || n.querySelector('button[aria-label^="Play"]');
    if (!b2) return null; const r = b2.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, SELF);
  if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(300); }
  return pt;
};

const out = { 轮次: 'b195d', SELF, 假设: '点卡片正文会「选中即播」' };

// —— 臂 1：取消选中 → 点正文 → 连采 ——
await 点空白();
out.臂1_起点 = await 采一帧();
out.臂1_点正文坐标 = await 点正文();
out.臂1_序列 = await 序列('臂1 点正文', 12, 400);

// —— 臂 2：若没播，点大播放键 → 连采 ——
const 臂1动了吗 = out.臂1_序列.some((x) => x.currentTime > 0);
out.臂1动了吗 = 臂1动了吗;
if (!臂1动了吗) {
  // 先退回「已选中未播」那一档（大播放键状态），再点它
  await 点空白();
  out.臂2_点标题 = await 点标题();
  out.臂2_大播放键前 = await 采一帧();
  out.臂2_点大播放键坐标 = await 点大播放键();
  out.臂2_序列 = await 序列('臂2 点大播放键', 12, 400);
} else {
  out.臂2_跳过 = '臂1 已经动起来了，不必再点大播放键';
}

// —— 臂 3：对照 —— 取消选中后再点正文（手册说「取消选中后再点卡片会从 0 重播」）——
await 点空白();
out.臂3_取消后 = await 采一帧();
out.臂3_再点正文 = await 点正文();
out.臂3_序列 = await 序列('臂3 取消后重播', 12, 400);

fs.writeFileSync('/tmp/b195d.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
