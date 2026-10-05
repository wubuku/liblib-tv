// 批次 191 a 轮：把批次 190 那条「按 ⌘V 之后画布缩放会自己变」从**现象**推成**机制**。
//
// 批次 190 的原始记录只有三个数：26%→50%、26%→42%、26%→43%，并注「机制未验证」。
// 三轮的目标节点与落点都不同 ⇒ 那三个数**不可比**，只能当「有这个现象」。
//
// 🔑 本轮的设计：
//   ① 阳性对照 —— 先证明**读数器**真能看见缩放变化（自己 setZoom 到 80% 再读回来）；
//      不然「读数不变」和「读数器坏了」分不开（立规：先证明扫描器抓得到）。
//   ② 时间序列 —— 动作后 0/0.4/1/2/4/7s 连读，判断是「动画中途」还是「稳定的新值」
//      （立规 62）。aria 与 viewport transform 两套都读（立规 59）。
//   ③ 受控分离 —— ⌘V 键 vs 右键菜单「粘贴」vs 什么都不按 vs 只按一个无关键。
//      只有「粘贴」这一侧变了，才说明变量是**粘贴动作**；若只有「⌘V 键」变了，
//      那说明变的是**按键**（甚至可能只是快捷键把焦点/视口带跑了）。
//   ④ 每次都把**视口平移**也读出来 —— 区分「重新居中（只改 translate）」与
//      「重新适配（translate + scale 都改）」。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';

const OUT = '/tmp/b191a.json';
const 记 = { 轮次: 'b191a', 阳性对照: null, 各臂: [], 收尾: null, 清理: [] };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

/** 两套读数 + 视口平移，一次读全。 */
const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  const ms = /scale\(([-\d.]+)\)/.exec(t);
  const mt = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return {
    aria: e ? e.getAttribute('aria-label') : null,
    实测scale: ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null,
    平移: mt ? [Math.round(parseFloat(mt[1]) * 10) / 10, Math.round(parseFloat(mt[2]) * 10) / 10] : null,
  };
});

/** 动作后的时间序列：aria 与实测 scale 都连读，判断收敛与否。 */
async function 序列(p, 标签) {
  const 点 = [];
  const t0 = Date.now();
  for (const 计划 of [0, 400, 1000, 2000, 4000, 7000]) {
    const 等 = 计划 - (Date.now() - t0);
    if (等 > 0) await p.waitForTimeout(等);
    const z = await 读缩放(p);
    点.push({ ms: Date.now() - t0, ...z });
  }
  const scales = 点.map((x) => x.实测scale);
  const arias = 点.map((x) => x.aria);
  return { 标签, 点, scale末值: scales[scales.length - 1],
    scale是否收敛: new Set(scales).size === 1, aria是否收敛: new Set(arias).size === 1,
    末态: 点[点.length - 1] };
}

/** 把视口归到 26% 并等它追平（setZoom 自带 scale 追平轮询）。 */
async function 归位(p, pct = 26) { const r = await setZoom(p, pct); await p.waitForTimeout(600); return r; }

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), 状态: await R.status(), credits: await R.credits() };
save();

// ── ① 阳性对照：读数器能不能看见缩放变化 ──────────────────────────────
{
  await 归位(p, 26);
  const 前 = await 读缩放(p);
  const 跳 = await setZoom(p, 80);
  const 后 = await 读缩放(p);
  记.阳性对照 = { 前, setZoom回读: 跳, 后,
    读数器能看见变化: 前.实测scale !== 后.实测scale && 后.实测scale !== null,
    前scale: 前.实测scale, 后scale: 后.实测scale, 目标: 80 };
  console.log('阳性对照 =', JSON.stringify(记.阳性对照.读数器能看见变化), 前.实测scale, '→', 后.实测scale);
  save();
}

// ── 准备工作：剪贴板哨兵 + 找一个当复制品的节点 ────────────────────────
const 哨兵 = 'JIMENG-B191-SENTINEL';
await p.evaluate((s) => navigator.clipboard.writeText(s), 哨兵);
const 选 = await p.evaluate((want) => {
  // 找一个「在视口内、类型是视频/图片」的非空节点当复制品
  const a = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    return { el: n, id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') || (n.innerText || '').slice(0, 30),
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  });
  const ok = a.filter((n) => n.w > 40 && n.h > 30 && n.x > 80 && n.x + n.w < innerWidth - 340 && n.y > 90 && n.y + n.h < innerHeight - 90);
  const pick = ok.find((n) => /视频|图片/.test(n.aria)) || ok[0] || null;
  if (!pick) return null;
  const t = pick.el.querySelector('[data-testid="flow-node-title"]') || pick.el;
  const r = t.getBoundingClientRect();
  return { id: pick.id, aria: pick.aria, 节点屏上: [pick.x, pick.y, pick.w, pick.h],
    标题行中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
}, null);
记.选中的复制品 = 选;
console.log('复制品 =', JSON.stringify(选));
save();

/** 选中一个节点：点标题行（批次 190 已证：正文区点不动，标题行才行）。 */
async function 选中标题行(pt) {
  await p.mouse.click(pt[0], pt[1]);
  await p.waitForTimeout(900);
  return { 选中数: await R.selCount(), 焦点: await p.evaluate(() => {
    const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; }) };
}

// ── 臂 1：⌘V 键（复现批次 190 的现象） ────────────────────────────────
{
  await 归位(p, 26);
  const 前 = await 读缩放(p);
  const 选前 = 选 ? await 选中标题行(选.标题行中心) : null;
  const 焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; });
  const guard = await keyGuard(p, 'Meta+v');
  const ids前 = await R.ids();
  await p.keyboard.press('Meta+v');
  const ids后立即 = await R.ids();
  const 序列读数 = await 序列(p, '臂1 ⌘V');
  const ids后 = await R.ids();
  记.各臂.push({ 臂: 1, 动作: '⌘V 键（已选中复制品）', 前, 选前, 焦点, guard,
    节点数: [ids前.length, ids后立即.length, ids后.length],
    新增id: ids后.filter((x) => !ids前.includes(x)),
    序列: 序列读数,
    判定: { scale变化: 前.实测scale !== 序列读数.末态.实测scale,
             aria变化: 前.aria !== 序列读数.末态.aria,
             平移变化: JSON.stringify(前.平移) !== JSON.stringify(序列读数.末态.平移) } });
  console.log('臂1 =', JSON.stringify(记.各臂[0].判定), 前.实测scale, '→', 序列读数.末态.实测scale);
  save();
}

// ── 臂 2：对照 · 右键菜单「粘贴」（同一个粘贴动作，但不是 ⌘V 键） ──────────
{
  await 归位(p, 26);
  const 前 = await 读缩放(p);
  let 菜单项 = null, 右键落点 = null;
  if (选) {
    右键落点 = 选.标题行中心;
    await p.mouse.click(右键落点[0], 右键落点[1]);
    await p.waitForTimeout(600);
    await p.mouse.click(右键落点[0], 右键落点[1], { button: 'right' });
    await p.waitForTimeout(900);
    const 菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]')).map((m) => ({
      文字: (m.innerText || '').replace(/\s+/g, ' ').trim(), 禁用: m.getAttribute('aria-disabled'),
      testid: m.getAttribute('data-testid') })));
    菜单项 = 菜单;
    const 粘贴项 = 菜单.find((m) => m.文字.startsWith('粘贴'));
    if (粘贴项) {
      const el = await p.evaluateHandle(() => Array.from(document.querySelectorAll('[role=menuitem]')).find((m) => (m.innerText || '').trim().startsWith('粘贴')));
      const bb = await el.asElement().boundingBox();
      if (bb) { await p.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(300); }
    }
  }
  const 序列读数 = await 序列(p, '臂2 菜单粘贴');
  记.各臂.push({ 臂: 2, 动作: '右键菜单「粘贴」（不是 ⌘V 键）', 前, 菜单项, 右键落点, 序列: 序列读数,
    判定: { scale变化: 前.实测scale !== 序列读数.末态.实测scale,
             aria变化: 前.aria !== 序列读数.末态.aria,
             平移变化: JSON.stringify(前.平移) !== JSON.stringify(序列读数.末态.平移) } });
  console.log('臂2 =', JSON.stringify(记.各臂[1].判定), 前.实测scale, '→', 序列读数.末态.实测scale);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  save();
}

// ── 臂 3：对照 · 什么都不按（排除「缩放自己在漂」） ────────────────────
{
  await 归位(p, 26);
  const 前 = await 读缩放(p);
  const 序列读数 = await 序列(p, '臂3 无动作');
  记.各臂.push({ 臂: 3, 动作: '什么都不按（7 秒静置）', 前, 序列: 序列读数,
    判定: { scale变化: 前.实测scale !== 序列读数.末态.实测scale, aria变化: 前.aria !== 序列读数.末态.aria } });
  console.log('臂3 =', JSON.stringify(记.各臂[2].判定), 前.实测scale, '→', 序列读数.末态.实测scale);
  save();
}

// ── 臂 4：对照 · 只按一个无关键（⌘C 本身） ─────────────────────────────
{
  await 归位(p, 26);
  const 前 = await 读缩放(p);
  if (选) { await p.mouse.click(选.标题行中心[0], 选.标题行中心[1]); await p.waitForTimeout(700); }
  const guard = await keyGuard(p, 'Meta+c');
  await p.keyboard.press('Meta+c');
  const 序列读数 = await 序列(p, '臂4 ⌘C');
  记.各臂.push({ 臂: 4, 动作: '⌘C 键（复制，不粘贴）', 前, guard, 序列: 序列读数,
    判定: { scale变化: 前.实测scale !== 序列读数.末态.实测scale, aria变化: 前.aria !== 序列读数.末态.aria } });
  console.log('臂4 =', JSON.stringify(记.各臂[3].判定), 前.实测scale, '→', 序列读数.末态.实测scale);
  save();
}

// ── 收尾：删掉本轮所有新增节点 + 归位 ─────────────────────────────────
{
  const ids = await R.ids();
  const 新 = ids.filter((x) => !基线.ids.includes(x));
  for (const id of 新) {
    const ok = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 删: false, 原因: '找不到节点' };
      const aria = n.getAttribute('aria-label') || (n.innerText || '').slice(0, 40);
      const t = n.querySelector('[data-testid="flow-node-title"]') || n;
      const r = t.getBoundingClientRect();
      if (r.width < 2) return { 删: false, 原因: '标题行不在视口内', aria };
      return { 删: true, aria, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, id);
    if (!ok.删) { 记.清理.push({ id, 失败: ok }); continue; }
    await p.mouse.click(ok.点[0], ok.点[1]); await p.waitForTimeout(600);
    await p.mouse.click(ok.点[0], ok.点[1], { button: 'right' }); await p.waitForTimeout(800);
    const bb = await p.evaluateHandle(() => {
      const m = Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除'));
      return m || null; });
    const el = bb.asElement();
    if (!el) { 记.清理.push({ id, 失败: '菜单里没有删除项' }); await p.keyboard.press('Escape'); continue; }
    const box = await el.boundingBox();
    if (!box) { 记.清理.push({ id, 失败: '删除项没有包围盒' }); await p.keyboard.press('Escape'); continue; }
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await p.waitForTimeout(1200);
    记.清理.push({ id, 删了: true, aria: ok.aria });
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  await 归位(p, 26);
  const ids2 = await R.ids();
  记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(),
    节点数: ids2.length, 基线节点数: 基线.ids.length,
    残留: ids2.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids2.includes(x)),
    credits基线: 基线.credits };
  save();
  console.log('收尾 =', JSON.stringify(记.收尾));
}
await b.close();
console.log('写出', OUT);
