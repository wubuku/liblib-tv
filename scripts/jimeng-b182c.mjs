// 批次 182 c 轮：**隔离「批次 178 的 ⌘C 读数复现不了」到底是我的仪表弄的，还是 178 记错了。**
//
// 182 b 轮的四格读数里有一格与批次 178 **直接冲突**：
//   178：选中图片节点按 `⌘C` ⇒ 剪贴板读到 **17 字纯文本**「接力 亚运 一百米 男子 2026」；
//   182b：同一节点、同一路径，`Meta+c` ⇒ 页面**收到了 keydown**、**`copy` 事件也触发了**，
//         但剪贴板**一字未动**。
// ⇒ 两个读数不可能同时对。**在写任何结论前必须先定位是哪一个错了。**
//
// 182b 比 178 多了三样东西，每一样都可能是元凶，逐个拆开做受控对照：
//   甲 **哨兵写入** —— b 轮在按键前调了 `navigator.clipboard.writeText()`；
//   乙 **事件监听器** —— b 轮在 `document` 上装了捕获阶段的 `keydown` / `copy` 监听；
//   丙 **读取方式** —— b 轮用 `clipboard.read()`，178 用 `clipboard.readText()`。
//
// 五格：
//   V1 **完全复刻 178**（无哨兵、无监听、readText）—— 若这里出 17 字 ⇒ 是我的仪表问题；
//   V2 只加监听器；
//   V3 只加哨兵；
//   V4 复刻 178 但用 `read()` 读 —— 单独验「读取方式」这个变量；
//   V5 复刻 178 + 按键后**立刻读一次、4 秒后再读一次** —— 验「是不是异步写入、我读早了」。
//
// 🔴 非空守卫：每一格都必须先确认**剪贴板此刻确实是我写进去/读到的东西**，
//   否则「没变」与「读不到」分不开。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '182c' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
/** 178 原样：readText，带 2.5 秒上限。 */
const 读文本 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒没返回' }), 2500));
  const 真读 = (async () => { try { const t = await navigator.clipboard.readText();
    return { 读成功: true, 长度: t.length, 逐字: t.slice(0, 120) }; } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 100) }; } })();
  return Promise.race([真读, 超时]);
});
/** b 轮原样：read() 枚举类型。 */
const 读全部 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒没返回' }), 2500));
  const 真读 = (async () => { try { const items = await navigator.clipboard.read(); const out = [];
      for (const it of items) for (const t of it.types) { const o = { type: t, 字节: null, 文本: null };
        try { const b0 = await it.getType(t); o.字节 = b0.size; if (t.startsWith('text/')) o.文本 = (await b0.text()).slice(0, 120); } catch (e) { o.错误 = String(e).slice(0, 60); }
        out.push(o); }
      return { 读成功: true, 明细: out }; } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 100) }; } })();
  return Promise.race([真读, 超时]);
});
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);
const 装监听 = () => p.evaluate(() => { window.__c = { keydown: [], copy: [] };
  document.addEventListener('keydown', (e) => { if (e.metaKey) window.__c.keydown.push({ key: e.key, code: e.code, shiftKey: e.shiftKey }); }, true);
  document.addEventListener('copy', (e) => { window.__c.copy.push({ 项数: e.clipboardData ? e.clipboardData.items.length : null,
    类型: e.clipboardData ? Array.from(e.clipboardData.types) : null }); }, true); return '已装'; });
const 取监听 = () => p.evaluate(() => JSON.parse(JSON.stringify(window.__c || {})));

const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1200);
  const 命中 = await p.evaluate((词) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 50),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !词 || x.文字.includes(词)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没有命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1300);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};

const 图 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]'); const img = n.querySelector('img');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
    alt: img ? (img.getAttribute('alt') || '') : null, 节点aria: n.getAttribute('aria-label'),
    节点内全部文字: (n.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 160) }; });
rec.靶子 = 图;
rec.起点 = { 节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length), 积分: await R.credits() };

rec.格 = [];
const 一格 = async (名, 配置) => {
  const 行 = { 名, ...配置 };
  const S = await 搜索选中(图.标题);
  行.选中 = S.选中集; 行.选中成功 = S.成功;
  if (!(S.成功 && S.选中集.includes(图.id))) { 行.说明 = '没选中图片节点，跳过'; rec.格.push(行); return; }
  if (配置.监听) 行.监听 = await 装监听();
  if (配置.哨兵) 行.哨兵 = await 写哨兵(`${名}-哨兵`);
  行.按前 = 配置.读全部 ? await 读全部() : await 读文本();
  if (!行.按前.读成功) { 行.说明 = '按前就读不出来，本格作废'; rec.格.push(行); return; }
  await p.keyboard.press(配置.键); await p.waitForTimeout(2400);
  行.按后 = 配置.读全部 ? await 读全部() : await 读文本();
  if (配置.再等) { await p.waitForTimeout(4000); 行.再等4秒后 = 配置.读全部 ? await 读全部() : await 读文本(); }
  if (配置.监听) 行.事件 = await 取监听();
  行.与按前相同 = JSON.stringify(行.按后) === JSON.stringify(行.按前);
  rec.格.push(行);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
};

// V1 完全复刻 178：监听✗ 哨兵✗ readText 键=Meta+c
await 一格('V1_完全复刻178', { 监听: false, 哨兵: false, 读全部: false, 键: 'Meta+c' });
// V2 只加监听器
await 一格('V2_只加监听器', { 监听: true, 哨兵: false, 读全部: false, 键: 'Meta+c' });
// V3 只加哨兵
await 一格('V3_只加哨兵', { 监听: false, 哨兵: true, 读全部: false, 键: 'Meta+c' });
// V4 复刻 178 但改用 read() 读
await 一格('V4_改用read读', { 监听: false, 哨兵: false, 读全部: true, 键: 'Meta+c' });
// V5 复刻 178 + 立刻读与 4 秒后再读各一次
await 一格('V5_加二次读', { 监听: false, 哨兵: false, 读全部: false, 键: 'Meta+c', 再等: true });

await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
