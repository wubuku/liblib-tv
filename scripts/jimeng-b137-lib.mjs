// 批次 137 共用件：**建节点 → 取证 → 删掉** 的建-删护栏（批次 128 确立、134 验证、137 重写）。
//
// 🔑 为什么重写：批次 134 的护栏 ④ 算的是「**本轮开始前**的 id 集合里消失的 id」，
//   而 SELF **根本不在本轮开始前的集合里**（它就是这轮新建的）⇒ 结果恒为 `[]` ⇒ 门报 ⛔。
//   清理本身是成功的，**错的是判据**。
//   ✅ 正确写法：拿「**建后**的 id 集合」做差 —— 建后 77、删后 76 ⇒ 消失集合恰好 `{SELF}`。
//   📌 **立规：判「我删的东西消失了」要拿「操作前」的集合做差，不是「本轮开始前」的集合。**
//
// 📌 另外三条护栏沿用：
//   ① 建前存全画布 id 集合；
//   ② 建后差集**恰好 1 个**，且该节点**恰好 `.selected`**（点建节点按钮会顺手选中它）；
//   ③ 删除**不走键盘**：右键 → 上下文菜单 →「删除」（前缀匹配，菜单项逐字是 `删除 ⌫`）——
//      节点有子控件时，键盘删除的焦点可能落在子控件上。
//
// ⚠️ 左栏「文本/图片/视频/音频/时间线/主体/导演台」**七个按钮都会建节点**（批次 129 逐个确认）。
//   ⇒ 只读普查**不许**拿它们当面板入口；要建必须走本护栏。
import { readers, settle, keyGuard } from './jimeng-b135-lib.mjs';

const idsOf = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const selCount = (p) => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = (p) => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
  .filter((m) => m.getBoundingClientRect().width > 1).length);
const canvasPos = (p) => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return [n.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));
const isSelected = (p, id) => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  return !!(n && n.classList.contains('selected')); }, id);

/** 在一个元素的内部找一个真能点到它的点（逐格采样 + `elementFromPoint` 双重把关）。 */
async function 可点落点(p, sel, inset = 3, step = 3) {
  return p.evaluate(([q, ins, st]) => {
    const e = document.querySelector(q); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + ins; y <= r.y + r.height - ins; y += st)
      for (let x = Math.ceil(r.x) + ins; x <= r.x + r.width - ins; x += st) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) return { x, y, 命中: h.getAttribute('data-testid') || h.tagName };
      }
    return { __err: 'no-point' };
  }, [sel, inset, step]);
}

/**
 * 完整的「建一个 → 给你一个函数取证 → 删掉」循环。
 * 任一护栏不满足就**当场中止并尝试归位**，绝不带着不一致的画布继续。
 * @returns {{ok:boolean, SELF?:string, 建后ids?:string[], 护栏:Array, 取证?:any}}
 */
export async function 建删一轮(p, 断言, 左栏aria, 取证函数, 出处, 预期节点数) {
  const R = readers(p);
  const 护栏 = [];
  const rec = { 护栏, 左栏aria, 出处 };
  const 记 = async (名, 条件, 详情) => { const ok = !!!!条件; 护栏.push({ 名, 通过: ok, 详情 });
    (await import('node:fs')).writeFileSync(new URL('./_tmp-b137-current.json', import.meta.url), JSON.stringify(rec, null, 1));
    if (断言) 断言(名, ok, 详情); return ok; };

  await keyGuard(p);
  await settle(p, R);
  const 基线ids = await idsOf(p);
  const 建前canvas = await canvasPos(p);
  rec.建前 = { 节点数: 基线ids.length, 状态行: await R.status() };
  await 记('①建前已存全画布 id 集合', 基线ids.length > 0, { 节点数: 基线ids.length });
  // 🔴 护栏 ① 原写成「节点数 > 0」——**太弱，挡不住残留**。
  //   本批就吃过这个亏：a 轮第一次崩在 `selCount()`，而**建节点那一步已经点下去了**，
  //   留下了一枚孤儿「视频 2」；重跑时「建后比建前多 1」当然不成立（建前就已经有它了），
  //   门报 ⛔ 才把残留暴露出来 —— 晚了一步。
  //   ⇒ 加严：给了 `预期节点数` 就必须**逐个相等**，不等当场停手。
  if (预期节点数 !== undefined) {
    await 记('①b 建前节点数 == 预期基线（挡残留）', 基线ids.length === 预期节点数, { 实际: 基线ids.length, 预期: 预期节点数 });
  }
  await 记('①c 建前 0 选中（不能有上一次留下的选中态）', (await selCount(p)) === 0, { 选中数: await selCount(p) });

  // ---- 建
  const pt = await 可点落点(p, `[aria-label="${左栏aria}"]`, 3, 3);
  rec.建落点 = pt;
  if (pt.__err) { await 记(`建节点失败（${pt.__err}）`, false, pt); rec.ok = false; return rec; }
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(2500);
  await settle(p, R);

  const 建后ids = await idsOf(p);
  const 新增 = 建后ids.filter((x) => !基线ids.includes(x));
  const 消失 = 基线ids.filter((x) => !建后ids.includes(x));
  rec.建后 = { 节点数: 建后ids.length, 新增, 消失, 选中数: await selCount(p) };
  if (!await 记('②建后差集恰好 1 个且无消失', 新增.length === 1 && 消失.length === 0, rec.建后)) {
    rec.ok = false; return rec;   // ⚠️ 差集不合法 ⇒ 不知道删谁，绝不猜
  }
  const SELF = 新增[0];
  rec.SELF = SELF;
  await 记('②b 新节点恰好是 .selected', await isSelected(p, SELF), { SELF, 选中数: await selCount(p) });

  // ---- 取证（只读）
  try { rec.取证 = await 取证函数(p, R, SELF); }
  catch (e) { rec.取证 = { __异常: String(e && e.message).slice(0, 200) }; }

  // ---- 删
  await 记('③a 删除前 SELF 仍选中', await isSelected(p, SELF), { 仍选中: await isSelected(p, SELF) });
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${SELF}"]`, 4, 4);
  rec.删除落点 = 落;
  if (落.__err) { await 记(`③b 找不到节点内部的可点落点（${落.__err}）`, false, 落); rec.ok = false; return rec; }
  await p.mouse.click(落.x, 落.y, { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
      }
    return { __err: 'no-point' };
  });
  rec.删除项 = del;
  if (del.__err) { await 记(`③c 右键菜单里没有可点的「删除」（${del.__err}）`, false, del); rec.ok = false; return rec; }
  await p.mouse.click(del.x, del.y);
  await p.waitForTimeout(2500);
  await settle(p, R);

  // ---- ④ 用**建后**的集合做差（批次 134 的判据 bug 就出在这里）
  const 删后ids = await idsOf(p);
  rec.删后 = { 节点数: 删后ids.length,
    消失: 建后ids.filter((x) => !删后ids.includes(x)),
    新增: 删后ids.filter((x) => !建后ids.includes(x)) };
  await 记('④ 删除后「建后ids」里消失的恰好只有 SELF',
    rec.删后.消失.length === 1 && rec.删后.消失[0] === SELF && rec.删后.新增.length === 0, rec.删后);

  // ⚠️ 不能写成 `filter((id) => ... await ...)` —— 那个回调不是 async，`await` 是保留字。
  //   先把「删后 canvas 坐标」取出来，再做纯比较。
  const 删后canvas = await canvasPos(p);
  const 移动 = Object.keys(建前canvas).filter((id) => JSON.stringify(建前canvas[id]) !== JSON.stringify(删后canvas[id]));
  rec.收尾 = { 状态行: await R.status(), 选中: await selCount(p), 浮层: await overlays(p), zoom: await R.zoom(),
    minimap: await R.minimap(), 节点数: 删后ids.length, 节点被移动: 移动,
    与基线差集: { 多: 删后ids.filter((x) => !基线ids.includes(x)), 少: 基线ids.filter((x) => !删后ids.includes(x)) } };
  await 记('⑤ 其余节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
  await 记('⑥ 节点 id 与建前基线逐个一致',
    rec.收尾.与基线差集.多.length === 0 && rec.收尾.与基线差集.少.length === 0, rec.收尾.与基线差集);
  rec.ok = 护栏.every((h) => h.通过);
  return rec;
}
