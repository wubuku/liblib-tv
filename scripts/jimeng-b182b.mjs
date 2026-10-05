// 批次 182 b 轮：**给「⌘⇧C 按了没反应」这个否定读数配三道对照。**
//
// 182 a 轮的读数：菜单里点「复制为图片」⇒ 剪贴板变成 image/png 1,141,819 字节；
// 键盘按 `Meta+Shift+c` ⇒ 剪贴板一字未动。⇒ 看着像 ⌘D 的同族（功能可用、快捷键是摆设）。
//
// 🔴 但**否定读数最容易骗人**。不排除下面三种解释就不能写进手册：
//   甲 **按键根本没送到页面** —— Playwright 的 `press` 组合键没生效，页面压根没收到事件；
//   乙 **大小写/修饰键记法不匹配** —— handler 比对的是 `KeyC` + `shiftKey`，
//      而我发的是小写 `c`，于是「没反应」只是**我按错了键**；
//   丙 **`Meta+C` 本身也坏** —— 那「⌘⇧C 无效」就不是独立结论，只是同一个故障。
//
// 手法：① 在 `document` 上装**捕获阶段**监听器，把页面**实际收到**的
//   `keydown`（key / code / metaKey / shiftKey）与 `copy` 事件逐条记下来 ——
//   这一条直接把甲杀掉；② 每种组合都跑 `Meta+c` / `Meta+C` / `Meta+Shift+c` / `Meta+Shift+C`
//   四格，逐格**先写哨兵再读回**，逐格对照 —— 杀掉乙与丙；
//   ③ 每格都带**非空守卫**：哨兵读不回来就不判「没变」。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '182b' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));

/** 枚举剪贴板条目与类型（同 a 轮：readText() 遇二进制会抛错，不能用）。 */
const 读剪贴板 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒内没返回' }), 2500));
  const 真读 = (async () => { try {
      const items = await navigator.clipboard.read(); const out = [];
      for (const it of items) for (const t of it.types) { const o = { type: t, 字节: null, 文本: null };
        try { const b0 = await it.getType(t); o.字节 = b0.size; if (t.startsWith('text/')) o.文本 = (await b0.text()).slice(0, 80); } catch (e) { o.错误 = String(e).slice(0, 60); }
        out.push(o); }
      return { 读成功: true, 明细: out, 有图片项: out.some((x) => x.type.startsWith('image/')), 有文本项: out.some((x) => x.type.startsWith('text/')) };
    } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 120) }; } })();
  return Promise.race([真读, 超时]);
});
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);

/** 装捕获阶段监听器：记录页面**实际收到**了什么。 */
const 装监听 = () => p.evaluate(() => {
  window.__b182 = { keydown: [], copy: [], 装于: performance.now() };
  const kd = (e) => { if (e.metaKey || e.ctrlKey || e.key === 'c' || e.key === 'C' || e.key === 'v' || e.key === 'V' || e.key === 'z' || e.key === 'Z')
    window.__b182.keydown.push({ key: e.key, code: e.code, metaKey: e.metaKey, shiftKey: e.shiftKey, ctrlKey: e.ctrlKey, 目标: e.target?.tagName || null }); };
  const cp = (e) => { window.__b182.copy.push({ 类型: e.type, 剪贴板可用: !!(e.clipboardData), 项数: e.clipboardData ? e.clipboardData.items.length : null }); };
  document.addEventListener('keydown', kd, true);
  document.addEventListener('copy', cp, true);
  return '已装';
});
const 取监听 = () => p.evaluate(() => JSON.parse(JSON.stringify(window.__b182 || { keydown: [], copy: [] })));
const 清监听 = () => p.evaluate(() => { if (window.__b182) { window.__b182.keydown.length = 0; window.__b182.copy.length = 0; } });

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
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 2) };
};

const 图 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.靶子 = 图;
rec.起点 = { 节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length), 积分: await R.credits(), 缩放: await R.zoom() };

// ═════════ 四格按键对照 + 一格菜单对照（同一节点、同一焦点状态、每格独立哨兵）
rec.格 = [];
if (图) {
  rec.监听器 = await 装监听();
  for (const 组合 of ['Meta+c', 'Meta+C', 'Meta+Shift+c', 'Meta+Shift+C', 'Meta+Shift+c']) {
    const S = await 搜索选中(图.标题);
    const 行 = { 组合, 第几次按: rec.格.filter((x) => x.组合 === 组合).length + 1, 选中成功: S.成功, 选中集: S.选中集 };
    if (!(S.成功 && S.选中集.includes(图.id))) { 行.说明 = '没选中图片节点，跳过本格'; rec.格.push(行); continue; }
    行.焦点守卫 = (await keyGuard(p)).safe;
    行.哨兵 = await 写哨兵(`B182B-${组合}-${行.第几次按}`);
    const 前 = await 读剪贴板();
    行.按前 = 前;                                     // 🔴 非空守卫：读不回来就不能判「没变」
    if (!前.读成功 || !前.有文本项) { 行.说明 = '哨兵读不回来，本格作废'; rec.格.push(行); continue; }
    await 清监听();
    await p.keyboard.press(组合); await p.waitForTimeout(2200);
    const 后 = await 读剪贴板();
    行.按后 = 后;
    行.页面收到的事件 = await 取监听();
    // 判据：哨兵逐字还在 ⇒ 剪贴板没被这个组合改过
    行.剪贴板是否改变 = !(后.读成功 && 后.有文本项 && 后.明细.some((x) => x.文本 === 前.明细.find((y) => y.文本)?.文本));
    行.结果 = 后.有图片项 ? '✅ 放进图片' : (行.剪贴板是否改变 ? '⚠️ 变了但不是图片' : '❌ 剪贴板没变');
    rec.格.push(行);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  }
  // 菜单对照：同一个节点上点一次，证明这一格的功能是活的
  const S = await 搜索选中(图.标题);
  rec.菜单对照 = { 选中成功: S.成功, 选中集: S.选中集 };
  if (S.成功 && S.选中集.includes(图.id)) {
    rec.菜单对照.哨兵 = await 写哨兵('B182B-MENU');
    rec.菜单对照.按前 = await 读剪贴板();
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, 图.id);
    if (pt) {
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
      const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('复制为图片'));
        if (!e) return null; const r = e.getBoundingClientRect(); return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
      rec.菜单对照.菜单项 = 项;
      if (项 && !项.禁用) { await 清监听(); await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(2200);
        rec.菜单对照.按后 = await 读剪贴板(); rec.菜单对照.页面收到的事件 = await 取监听(); }
    }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
