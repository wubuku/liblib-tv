// 批次 184 b 轮：**补上 before ⊕ / after ⊕ 两格**，与 184 主探针的「拖手柄」格做指纹对照。
//
// 🔴 184 主探针的格 1/格 2 崩了：`p.evaluate((i, tid) => …, 靶.id, testid)` ——
//    **Playwright 的 `evaluate` 只接受一个参数**，多传会抛
//    `Too many arguments. If you need to pass more than 1 argument …`。
//    ⇒ 这是本会话第二次「JS 调用签名写错导致整格作废」（上一次是 `page.fill(undefined)`）。
//    修法：**多参数一律包成对象** `{ id, tid }`。
//
// 184 主探针已测到「拖手柄」格：菜单标题「添加节点」，七项里可点 **图片/视频/音频/时间线/主体**，
// 禁用 **文本/导演台**。本轮取同一节点实例的 before ⊕ 与 after ⊕ 指纹来对。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '184b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 读菜单 = async () => {
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      标题: (Array.from(e.querySelectorAll('*')).map((x) => (x.innerText || '').trim()).find((t) => t === '添加上下文' || t === '添加节点') || null),
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => { const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null }; }) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  return m;
};
const 可点集 = (m) => (m?.项 || []).filter((x) => !x.禁用).map((x) => x.名);
const 指纹 = (m) => JSON.stringify({ 标题: m?.标题, 可点: 可点集(m) });
const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 靶 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.靶子 = 靶;
rec.格 = [];
if (靶) {
  await p.mouse.move(640, 400); await p.waitForTimeout(250);
  await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400);
  for (const [名, tid] of [['1_before⊕', 'flow-node-target-connection-menu-button'], ['2_after⊕', 'flow-node-source-connection-menu-button']]) {
    const 行 = { 名, testid: tid };
    try {
      const S = await 搜索选中(靶.标题); 行.选中 = S.选中集;
      if (!(S.成功 && S.选中集.includes(靶.id))) { 行.说明 = '没选中靶节点'; rec.格.push(行); continue; }
      // 🔴 多参数包成对象（Playwright 的 evaluate 只收一个）
      const pt = await p.evaluate(({ id, tid }) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"] [data-testid="${tid}"]`);
        if (!e) return null; const r = e.getBoundingClientRect();
        if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 几何: { w: Math.round(r.width), h: Math.round(r.height) }, aria: e.getAttribute('aria-label') }; }, { id: 靶.id, tid });
      行.按钮 = pt;
      if (!pt) { 行.说明 = '取不到 ⊕ 按钮坐标'; rec.格.push(行); continue; }
      await p.mouse.click(pt.点[0], pt.点[1]); await p.waitForTimeout(1500);
      行.菜单 = await 读菜单(); 行.指纹 = 指纹(行.菜单);
    } catch (e) { 行.异常 = String(e).slice(0, 160); }
    rec.格.push(行);
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  const G = Object.fromEntries(rec.格.map((g) => [g.名, g.指纹]));
  const 拖 = '{"标题":"添加节点","可点":["图片","视频","音频","时间线","主体"]}';   // 184 主探针实测值
  rec.判定 = { 格1_before: G['1_before⊕'] || null, 格2_after: G['2_after⊕'] || null, 格3_拖手柄: 拖 };
  rec.判定.拖手柄等于after = 拖 === (G['2_after⊕'] || null);
  rec.判定.拖手柄等于before = 拖 === (G['1_before⊕'] || null);
  rec.判定.before与after是否不同 = !!(G['1_before⊕'] && G['2_after⊕'] && G['1_before⊕'] !== G['2_after⊕']);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
