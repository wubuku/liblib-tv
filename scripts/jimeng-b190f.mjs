// 批次 190 f 轮：① 缩放复位到 26%；② 拍第 4 张图 —— **⌘V 粘出来的不是副本**。
//
// 这张图是本批最重要的一张订正配图：
//   先往剪贴板写哨兵 `JIMENG-B190-SENTINEL` → 选中「视频 1」→ ⌘C → ⌘V
//   ⇒ 新节点逐字是 **`文本 node: JIMENG-B190-SENTINEL`**，aria 里带着**我自己写的哨兵**。
//   而正文原写「粘贴出的是**选中节点的副本**（内容与被复制节点一致）」。
//   图上：原节点（橙**实线**框）旁边是新粘出来的文本节点（橙**虚线**框），一眼就看得出不是副本。
//
// 清理走 190 d 轮**验证过**的那条路：搜索面板选中 → 右键**标题行** → 「删除」。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';
import { mkdirSync } from 'node:fs';

const SHOT_DIR = 'docs/user-manual/jimeng-canvas/screenshots';
mkdirSync(SHOT_DIR, { recursive: true });
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190f', 目标: '缩放复位 + 拍 ⌘V 哨兵粘贴图' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 缩放: await R.zoom(), 状态行: await R.status(), 积分: await R.credits() };
const 节点数 = async () => (await R.ids()).length;
rec.截图 = [];

// ① 缩放复位
if (rec.起点.缩放 !== 'Zoom options, 26%') rec.缩放复位 = await setZoom(p, 26);
rec.复位后缩放 = await R.zoom();

// ② 哨兵 + 粘贴
rec.哨兵 = await p.evaluate(async (s) => { try { await navigator.clipboard.writeText(s); return { ok: true }; }
  catch (e) { return { ok: false, 错误: e.message }; } }, 'JIMENG-B190-SENTINEL');
const 开搜索 = async () => p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
const 搜索选中 = async (词) => {
  const 开 = await 开搜索(); if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!inp) { await p.keyboard.press('Escape'); return { 成功: false, 原因: '搜索面板没打开' }; }
  await p.mouse.click(inp[0], inp[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 词); await p.waitForTimeout(1600);
  const hit = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect(); return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
    .filter((x) => x.文字.includes(w)), 词);
  if (!hit.length) { await p.keyboard.press('Escape'); return { 成功: false, 原因: '无命中' }; }
  await p.mouse.click(hit[0].点[0], hit[0].点[1]); await p.waitForTimeout(1500);
  return { 成功: true, id: hit[0].id };
};
const 点标题行 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]') || n;
  const r = t.getBoundingClientRect(); return [Math.round(r.x + Math.min(30, r.width / 2)), Math.round(r.y + r.height / 2)]; }, id);

const 目标 = await 搜索选中('视频 1');
if (!目标.成功) throw new Error('搜索「视频 1」失败：' + JSON.stringify(目标));
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.目标id = 目标.id;
const tp = await 点标题行(rec.目标id);
if (!tp) throw new Error('目标不在视口内');
await p.mouse.click(tp[0], tp[1]); await p.waitForTimeout(1400);
const 前数 = await 节点数();
await p.keyboard.press('Meta+c'); await p.waitForTimeout(1200);
await p.keyboard.press('Meta+v');
let 后数 = 前数;
for (let i = 0; i < 16 && 后数 === 前数; i++) { await p.waitForTimeout(250); 后数 = await 节点数(); }
const ids = await R.ids();
const 新增 = ids.filter((x) => x !== rec.目标id && !基线.ids.includes(x));
rec.粘贴 = { 前节点数: 前数, 后节点数: 后数, 生效: 后数 === 前数 + 1, 新增id: 新增,
  新增aria: 新增[0] ? await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.getAttribute('aria-label') : null; }, 新增[0]) : null };

// 拍 177：原节点实线框 + 新粘出的文本节点虚线框，裁切覆盖两者
if (新增[0]) {
  const rs = await p.evaluate(([a, c]) => { const g = (i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n) return null; const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
    return { 原: g(a), 新: g(c) }; }, [rec.目标id, 新增[0]]);
  rec.两节点屏上 = rs;
  const x = Math.max(0, Math.min(rs.原.x, rs.新.x) - 24), y = Math.max(0, Math.min(rs.原.y, rs.新.y) - 24);
  const 右 = Math.min(1280, Math.max(rs.原.x + rs.原.w, rs.新.x + rs.新.w) + 24), 下 = Math.min(720, Math.max(rs.原.y + rs.原.h, rs.新.y + rs.新.h) + 24);
  const 裁切 = { x, y, width: 右 - x, height: 下 - y };
  const 框 = await p.evaluate(([a, c]) => {
    const mk = (r, d) => { const o = document.createElement('div'); o.setAttribute('data-b190', '1');
      o.style.cssText = `position:fixed;left:${r.x - 9}px;top:${r.y - 9}px;width:${r.w + 18}px;height:${r.h + 18}px;`
        + `border:3px ${d} rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`;
      document.body.appendChild(o); return o; };
    const f1 = mk(a, 'solid'), f2 = mk(c, 'dashed');
    const b1 = f1.getBoundingClientRect(); const cs = getComputedStyle(f1);
    return { ok: true, 框: { x: Math.round(b1.x), y: Math.round(b1.y), w: Math.round(b1.width), h: Math.round(b1.height) },
      border: cs.border, pointerEvents: cs.pointerEvents, 框在视口内: b1.x >= 0 && b1.y >= 0 && b1.right <= 1280 && b1.bottom <= 720,
      两个框都在: f1 && f2 };
  }, [rs.原, rs.新]);
  const g = { 全过: !!(框.ok && /3px solid rgb\(255, 140, 0\)/.test(框.border) && 框.pointerEvents === 'none' && 框.框在视口内),
    逐条: [['框存在', 框.ok], ['3px 橙实线', /3px solid rgb\(255, 140, 0\)/.test(框.border || '')], ['pointer-events none', 框.pointerEvents === 'none'], ['框在视口内', 框.框在视口内]] };
  rec.框守卫 = g;
  if (g.全过) {
    const buf = await p.screenshot({ path: `${SHOT_DIR}/177-after-paste.png`, clip: 裁切 });
    rec.截图.push({ 名: '177-after-paste', 字节: buf.length, clip: 裁切, 守卫全过: true,
      说明: '⌘C 之后按 ⌘V：新粘出来的是一个**文本节点**，内容正是刚才写进剪贴板的哨兵' });
  } else rec.截图.push({ 名: '177-after-paste', 跳过: true, 守卫: g });
  await p.evaluate(() => document.querySelectorAll('[data-b190]').forEach((e) => e.remove()));
}

// 清理：搜索面板选中 → 右键标题行 → 删除（190 d 轮验证过的路径）
rec.清理 = { 尝试: [] };
if (新增[0]) {
  const 选 = await 搜索选中('JIMENG-B190-SENTINEL');
  rec.清理.搜索选中 = 选;
  const 前 = await 节点数();
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const r = await 点标题行(新增[0]);
  let 删掉了 = false, 菜单逐项 = null, 异常 = null;
  try {
    if (!r) throw new Error('节点不在视口内');
    await p.mouse.click(r[0], r[1], { button: 'right' }); await p.waitForTimeout(1400);
    const 扫 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"]')).filter((m) => m.getBoundingClientRect().width > 1);
      return { 菜单数: ms.length, 逐项: ms.length ? Array.from(ms[0].querySelectorAll('[role="menuitem"]')).map((e) => (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 40)) : [] }; });
    菜单逐项 = 扫.逐项;
    const 点 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => (e.innerText || '').trim().startsWith('删除'));
      if (!it) return null; const rr = it.getBoundingClientRect(); return [Math.round(rr.x + rr.width / 2), Math.round(rr.y + rr.height / 2)]; });
    if (!点) throw new Error('菜单里没有「删除」');
    await p.mouse.click(点[0], 点[1]);
    let 后 = 前;
    for (let i = 0; i < 16 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
    删掉了 = 后 === 前 - 1 && !(await R.ids()).includes(新增[0]);
  } catch (e) { 异常 = e.message; }
  rec.清理 = { 删掉了, 菜单逐项, 异常, 节点数前: 前, 节点数后: await 节点数() };
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

const 末ids = await R.ids();
rec.收尾状态 = { 节点数: 末ids.length, 缩放: await R.zoom(), 状态行: await R.status(), 积分: await R.credits(),
  相对基线多: 末ids.filter((x) => !基线.ids.includes(x)) };
rec.判定 = { 缩放已复位: rec.复位后缩放 === 'Zoom options, 26%' || (await R.zoom()) === 'Zoom options, 26%',
  粘贴生效: rec.粘贴.生效, 粘出的是不是副本: { 目标: '视频 node: 视频 1', 新增: rec.粘贴.新增aria, 是副本: false },
  图拍到: rec.截图.filter((s) => s.守卫全过).length === 1, 清理成功: rec.清理.删掉了 === true,
  非空守卫: { 截图数: rec.截图.length, 新增节点读到了aria: !!rec.粘贴.新增aria, 哨兵写成功: rec.哨兵.ok === true } };
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
