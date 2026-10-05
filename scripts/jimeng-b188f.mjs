// 批次 188 f 轮：**⊕ 到底是不是 canvas 恒定 72×72？188 自己那条订正要先被自己验。**
//
// 188 前三轮的读数拼起来长这样（同一个 `b22-upload` 图片节点，只改缩放）：
//   22% → 15.8   26% → 18.7(≈19)   50% → 36   100% → 36
// 而 **100% 档读到的是 36，不是 72** ⇒ 「canvas 恒定 72×72」在 100% 档**不成立**。
// 唯一能同时解释四个读数的公式是 **屏上 = min(72×缩放, 36)** —— 一个**下限钳位**：
//   22%: min(15.84,36)=15.84 ✔   26%: min(18.72,36)=18.72 ✔
//   50%: min(36,36)=36      ✔   100%: min(72,36)=36      ✔
// ⇒ **批次 78「屏上恒为 36×36」的读数可能一条都没错，错的是它测的区间**：
//    50/60/100 三档**全部落在钳位的平台上**（阈值是 50%），平台上看不出任何变量。
//
// 但 offsetWidth 五档都是 36（不随缩放变），而屏上 = offsetWidth × 2 × 缩放（22/26/50 档）
// ⇒ **祖先里还有一个 scale(2)**，且 100% 档它不见了。本轮要把这条链读出来。
//
// 预测（先写下来）：祖先链上有某个元素的 computed transform 带 scale，其值随缩放反向变化，
// 使屏上尺寸 = min(72×缩放, 36)。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188f', 预测公式: '屏上 = min(72×缩放, 36)', 拐点: '缩放 ≥ 50% 后恒为 36' };
await settle(p, R);
rec.起点 = { 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
const 基线 = { ids: await R.ids(), testids: await R.testids() };

// 选中**靠搜索面板点结果行**（批次 184c 起逐类验证可靠；188b 也用它读到过 ⊕）——
// 比「点节点中心」稳：26% 下节点很小，elementFromPoint 经常落在节点外的空隙上。
// ⊕ 只在选中时出现，而选中本身不需要点节点本体。
const 候选 = await p.evaluate(() => {
  const t = (n) => { const e = n.querySelector('[data-testid="flow-node-title"]'); return (e ? e.textContent : '') || ''; };
  const pick = (sel, 要资源) => Array.from(document.querySelectorAll(sel))
    .filter((n) => (要资源 ? !!n.querySelector('img,video,audio') : true))
    .map((n) => ({ id: n.getAttribute('data-id'), 标题: t(n), aria: n.getAttribute('aria-label') }))
    .filter((x) => x.标题.trim().length > 0);
  return { 图片: pick('.react-flow__node-image', true)[0] || null, 视频: pick('.react-flow__node-video', true)[0] || null };
});
rec.候选 = 候选;

const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没打开' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1500);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '无命中' }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1500);
  const s = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};

if (!候选.图片) throw new Error('画布上没有带资源的图片节点');
const 选图 = await 搜索选中(候选.图片.标题);
rec.选图 = 选图;
if (!选图.成功) throw new Error('搜索选中图片节点失败：' + JSON.stringify(选图) + ' 关键词=' + 候选.图片.标题);
rec.图片id = 候选.图片.id;
if (候选.视频) { rec.选视频 = await 搜索选中(候选.视频.标题); if (rec.选视频.成功) rec.视频id = 候选.视频.id; }

/** 读某个节点：⊕ 的屏上盒 / offsetWidth / 祖先链每一层的 computed transform 与 offsetWidth / 节点自身。 */
const 读节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = ms ? parseFloat(ms[1]) : null;
  const 层 = (e) => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 名: e.tagName + '.' + String(e.className || '').split(' ').slice(0, 2).join('.'),
      testid: e.getAttribute('data-testid'), transform: cs.transform, offsetW: e.offsetWidth, offsetH: e.offsetHeight,
      屏上: { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 } }; };
  const 链 = (e) => { const c = []; for (let n2 = e; n2 && n2 !== document.body; n2 = n2.parentElement) c.push(层(n2)); return c; };
  const es = Array.from(n.querySelectorAll('[aria-label^="Create connected node"]'));
  return {
    scale, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中: n.classList.contains('selected'),
    节点: { 层: 层(n), inline: n.style.transform || null },
    加号: es.map((e) => ({ testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 层: 层(e), 链: 链(e) })),
    手柄: Array.from(n.querySelectorAll('[data-testid$="-handle"]')).map((e) => ({ testid: e.getAttribute('data-testid'), 层: 层(e) })),
  };
}, id);

const 档位 = [22, 26, 40, 50, 60, 75, 100, 150, 200, 26];
// 🔴 f 第一版的教训：**每档都重新用搜索面板选中**，结果点结果行会触发**缩放动画**
//    （aria 已经变成目标值、`.react-flow__viewport` 的 scale 还在补间途中）
//    ⇒ 22/26/40 三档读到的 scale 是 **0.5**（上一档的残留），150/200 读到 **1.31484**（补间中间值）。
//    整轮读数作废。正确做法（照批次 188 e 轮）：**选中一次、之后只改缩放**，
//    每档读**节点自身屏上尺寸**作为独立的 scale 见证（canvas 570×320 × scale）。
if (!rec.选图.成功) throw new Error('图片节点没选中');
rec.各档 = [];
for (const pct of 档位) {
  const z = await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(900);
  const rd = await 读节点(rec.图片id);
  rec.各档.push({ 档: pct, 回读: z.回读, setZoom实测scale: z.实测scale, setZoom已追平: z.scale已追平, ...rd });
}

// —— 判定：逐档对照 min(72×scale, 36)
const 图档 = rec.各档;
rec.公式对照 = 图档.map((r) => {
  const a = r.加号 && r.加号[0]; if (!a) return { 档: r.档, 缺: true, scale: r.scale, 选中: r.选中 };
  const 屏上 = a.层.屏上.w; const 预测 = Math.min(72 * r.scale, 36);
  // 独立见证：节点自身屏上宽 ÷ 已知 canvas 宽（b22-upload 卡片 canvas 570×320）
  const 节点屏上 = r.节点 && r.节点.层 ? r.节点.层.屏上.w : null;
  return { 档: r.档, scale: r.scale, 屏上, 预测: Math.round(预测 * 10) / 10, 差: Math.round((屏上 - 预测) * 100) / 100,
    符合: Math.abs(屏上 - 预测) <= 0.6, offsetW: a.层.offsetW, 纯缩放预测: Math.round(a.层.offsetW * r.scale * 10) / 10,
    节点屏上, 节点屏上反推scale: 节点屏上 ? Math.round((节点屏上 / 570) * 1000) / 1000 : null };
});
rec.判定 = {
  公式全档符合: rec.公式对照.every((x) => !x.缺 && x.符合),
  不符合的档: rec.公式对照.filter((x) => x.缺 || !x.符合).map((x) => x.档),
  纯offsetWidth乘缩放全档符合: rec.公式对照.every((x) => x.缺 || Math.abs(x.屏上 - x.纯缩放预测) <= 0.6),
  拐点实测: rec.公式对照.filter((x) => !x.缺).map((x) => ({ 档: x.档, 屏上: x.屏上 })),
  offsetWidth是否恒定: (() => { const v = rec.公式对照.map((x) => x.offsetW).filter((x) => x); return { 值: v, 恒定: new Set(v).size === 1 }; })(),
};
// 祖先链里带非 1 缩放的层（机制）
rec.机制 = (() => {
  const 样本 = 图档.find((r) => r.加号 && r.加号[0]);
  if (!样本) return null;
  const out = [];
  for (const x of 图档) { if (!x.加号 || !x.加号[0]) continue;
    const 层 = x.加号[0].链.map((l) => { const m = /matrix\(([-\d.e]+),\s*0,\s*0,\s*([-\d.e]+)/.exec(l.transform || '');
      return { 名: l.名, testid: l.testid, 缩放分量: m ? Math.round(parseFloat(m[2]) * 1000) / 1000 : null, offsetW: l.offsetW, 屏上w: l.屏上.w }; })
      .filter((l) => l.缩放分量 !== null && l.缩放分量 !== 1);
    out.push({ 档: x.档, scale: x.scale, 非1缩放的祖先层: 层 }); }
  return out;
})();
rec.判定.非空守卫 = { 档数: 图档.length, 读到加号的档数: 图档.filter((r) => r.加号 && r.加号[0]).length,
  全部档都选中: 图档.every((r) => r.选中 === true),
  scale见证与aria一致: 图档.every((r) => Math.abs(r.scale - r.档 / 100) <= 0.005),
  节点反推scale与scale一致: 图档.filter((x) => x.节点屏上反推scale !== null).every((x) => Math.abs(x.节点屏上反推scale - x.scale) <= 0.01) };

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
