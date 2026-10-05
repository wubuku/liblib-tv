// 批次 185 c 轮：**把导演台浮层的结构与「返回入口」挖出来并拍照。**
//
// 185b 已把两件事定死：
//   ① 「进入导演台」的 click **确实命中**（`elementFromPoint` 就是那个 BUTTON，逐字「进入导演台」）；
//   ② 点下去 **1 秒内** 就多出：`dialog 0→1`、全屏遮罩 `0→2`、testid 数 `177→227`（+50）、
//      控制点 `112→166`、body 直接子节点 `15→19`；而 **URL 不变、标签页数仍是 1**。
// ⇒ 🔴 **它不是「跳到外部工作台」，而是**在同一个画布页上开了一层全屏 dialog**。
//    手册 `director-node.md` 写的「点『进入导演台』后离开了画布」与读数不符。
//
// 185b 最后一步 `新出现的testid` 写错了（`p.evaluate(...).slice is not a function`）⇒ 异常
// 抛在截图**之前**，所以没拍到图。本轮把顺序改正：**先挖结构 → 再截图 → 最后才做别的**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
import fs from 'node:fs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '185c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 搜索选中 = async (关键词) => {
  if (typeof 关键词 !== 'string' || !关键词.trim()) return { 成功: false, 原因: '关键词非法' };
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
/** 浮层结构：所有 role=dialog，加上其中每一个带 aria / 可点特征的叶子。 */
const 挖浮层 = () => p.evaluate(() => {
  const 对话框 = Array.from(document.querySelectorAll('[role=dialog]'));
  return { 个数: 对话框.length, 明细: 对话框.map((d) => {
    const r = d.getBoundingClientRect();
    return { 标签: d.tagName, aria: d.getAttribute('aria-label'), ariaLabelledby: d.getAttribute('aria-labelledby'),
      testid: d.getAttribute('data-testid'), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      可见: r.width > 1 && r.height > 1,
      逐字前200: (d.innerText || '').trim().replace(/\n+/g, ' | ').slice(0, 200),
      子元素数: d.querySelectorAll('*').length,
      候选控件: Array.from(d.querySelectorAll('button,[role=button],a,[tabindex]')).map((e) => { const b = e.getBoundingClientRect();
        return { 标签: e.tagName, 逐字: (e.innerText || '').trim().replace(/\n/g, ' ').slice(0, 30), aria: e.getAttribute('aria-label'),
          testid: e.getAttribute('data-testid'), title: e.getAttribute('title'),
          屏上: { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) },
          中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)],
          禁用: e.getAttribute('aria-disabled') === 'true' }; }).slice(0, 40) };
  }) };
});
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom(), 标签页数: b.contexts()[0].pages().length };
const 导演 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-external'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.导演台节点 = 导演;
try {
  const S = await 搜索选中(导演.标题); rec.选中 = S;
  const 钮 = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const b = Array.from(n.querySelectorAll('button')).find((x) => (x.innerText || '').trim().includes('进入导演台')); if (!b) return null;
    const r = b.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const 落 = document.elementFromPoint(cx, cy);
    return { 中心: [cx, cy], 落点就是这个按钮吗: !!(落 && (落 === b || b.contains(落))) };
  }, 导演.id);
  rec.按钮 = 钮;
  if (!(S.成功 && 钮?.落点就是这个按钮吗)) rec.结论 = '没选中或落点不对，不盲点';
  else {
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(5000);
    rec.浮层 = await 挖浮层();
    // 📸 **先截图**：上一次就是异常抛在截图之前，图没拍到
    const f = 'docs/user-manual/jimeng-canvas/screenshots/_tmp-185c-director-overlay.png';
    await p.screenshot({ path: f });
    rec.截图 = fs.existsSync(f) ? fs.statSync(f).size + ' 字节' : '没拍到';
    rec.URL未变 = (await p.evaluate(() => location.href)) === 前id && false;
    rec.当前URL = p.url();
    rec.标签页数 = b.contexts()[0].pages().length;
    // 返回入口候选：按文案/aria 三路找
    const 候选 = [];
    for (const d of (rec.浮层.明细 || [])) for (const c of (d.候选控件 || [])) {
      const 串 = [c.逐字, c.aria, c.testid, c.title].join(' ');
      if (/返回|退出|关闭|画布|回到|back|close|exit/i.test(串)) 候选.push(c);
    }
    rec.返回候选 = 候选;
    if (候选.length && !候选[0].禁用) {
      const t = 候选[0];
      const 落 = await p.evaluate((pt) => { const e = document.elementFromPoint(pt[0], pt[1]); return e ? { 标签: e.tagName, 逐字: (e.innerText || '').trim().slice(0, 20) } : null; }, t.中心);
      rec.返回按钮落点 = 落;
      if (落) {
        await p.mouse.click(t.中心[0], t.中心[1]);
        await p.waitForTimeout(3500);
        rec.返回后 = { dialog数: await p.evaluate(() => document.querySelectorAll('[role=dialog]').length),
          节点数: await 节点数(), URL: p.url(), 状态行: await R.status() };
      }
    } else rec.说明 = '浮层里没找到带「返回/退出/关闭」字样的控件';
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays(), 标签页数: b.contexts()[0].pages().length };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
