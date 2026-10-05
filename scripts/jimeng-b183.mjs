// 批次 183：**把 `⌘D 复制副本` 也用 182 那套事件级方法重测一遍。**
//
// 为什么非做不可（这是我自己的内部不一致，不是新题目）：
//   批次 182 在手册里写下「🔴 判某个复制快捷键有没有用，**不能靠节点数变没变**」，
//   并把 `⌘C` / `⌘⇧C` 两行换成了事件级证据。
//   但同一张表里 **`⌘D` 那一行的证据仍然是批次 175 的「节点数仍�� 76、无新 id」**
//   —— 也就是我刚刚判定为**不成立**的那种测法。
//   ⇒ 手册在同一页里同时说「别这么判」和「我就是这么判的」。
//
// 本批要回答三件事：
//   ① 按 `Meta+D` 时页面**收没收到** keydown？有没有 `copy` / `cut` 事件？有没有任何后续？
//   ② 菜单里点「复制副本」**到底能不能用**（182 只测了「复制为图片」，没测这一项）
//      —— 这是对照：功能在不在。
//   ③ 顺手把 `Meta+D` 的**大写写法**也试掉（182 发现 `⌘C` 大写小写都能送达，
//      但 `⌘⇧C` 两种写法都无后续 ⇒ 不能想当然）。
//
// ⚠️ ② 会**真的造出一个节点**（76 → 77）⇒ 收尾必须按批次 178 记的**删节点三道守卫**清掉：
//   用搜索面板可靠选中 → 读 `.selected` 的 id 确认 → 按 `⌫` → 按同 id 验它消失
//   → 顺带验原有 76 个 id 逐个仍在。**点不中就不删，宁可留白也不删错。**
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 读全部 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒没返回' }), 2500));
  const 真读 = (async () => { try { const items = await navigator.clipboard.read(); const out = [];
      for (const it of items) for (const t of it.types) { const o = { type: t, 字节: null, 文本: null };
        try { const b0 = await it.getType(t); o.字节 = b0.size; if (t.startsWith('text/')) o.文本 = (await b0.text()).slice(0, 80); } catch (e) { o.错误 = String(e).slice(0, 60); }
        out.push(o); }
      return { 读成功: true, 明细: out }; } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 100) }; } })();
  return Promise.race([真读, 超时]);
});
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);
/** 立规 52 的正向守卫：把页面**实际收到**的事件逐条记下来。 */
const 装监听 = () => p.evaluate(() => { window.__b183 = { keydown: [], copy: [], cut: [] };
  document.addEventListener('keydown', (e) => { if (e.metaKey) window.__b183.keydown.push({ key: e.key, code: e.code, shiftKey: e.shiftKey }); }, true);
  document.addEventListener('copy', (e) => { window.__b183.copy.push({ 项数: e.clipboardData ? e.clipboardData.items.length : null, 类型: e.clipboardData ? Array.from(e.clipboardData.types) : null }); }, true);
  document.addEventListener('cut', (e) => { window.__b183.cut.push({}); }, true);
  return '已装'; });
const 清监听 = () => p.evaluate(() => { if (window.__b183) { window.__b183.keydown.length = 0; window.__b183.copy.length = 0; window.__b183.cut.length = 0; } });
const 取监听 = () => p.evaluate(() => JSON.parse(JSON.stringify(window.__b183 || {})));

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
const 标题文案 = (id) => p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id);

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
const 图 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.靶子 = 图;
rec.监听器 = 图 ? await 装监听() : '没有靶子';

// ═════════ A 按 Meta+D（小写）+ Meta+D（大写）：事件级读数
rec.A按键 = [];
if (图) {
  for (const 组合 of ['Meta+d', 'Meta+D']) {
    const 行 = { 组合 };
    const S = await 搜索选中(图.标题);
    行.选中 = S.选中集; 行.选中成功 = S.成功;
    if (!(S.成功 && S.选中集.includes(图.id))) { 行.说明 = '没选中图片节点，跳过'; rec.A按键.push(行); continue; }
    行.焦点守卫 = (await keyGuard(p)).safe;
    行.哨兵 = await 写哨兵(`B183-${组合}-哨兵`);
    行.剪贴板前 = await 读全部();
    行.节点数前 = await 节点数();
    await 清监听();
    await p.keyboard.press(组合); await p.waitForTimeout(2400);
    行.节点数后 = await 节点数();
    行.剪贴板后 = await 读全部();
    行.页面收到的事件 = await 取监听();
    行.剪贴板是否改变 = JSON.stringify(行.剪贴板后) !== JSON.stringify(行.剪贴板前);
    行.节点数是否改变 = 行.节点数后 !== 行.节点数前;
    rec.A按键.push(行);
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }
}

// ═════════ B 菜单里点「复制副本」：功能本身在不在（会真的造节点）
rec.B菜单点击 = {};
if (图) {
  const S = await 搜索选中(图.标题);
  rec.B菜单点击.选中 = S.选中集; rec.B菜单点击.选中成功 = S.成功;
  if (S.成功 && S.选中集.includes(图.id)) {
    rec.B菜单点击.节点数前 = await 节点数();
    rec.B菜单点击.剪贴板前 = await 写哨兵('B183-MENU-哨兵').then(() => 读全部());
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, 图.id);
    if (pt) {
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
      const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('复制副本'));
        if (!e) return null; const r = e.getBoundingClientRect();
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true',
          快捷键: e.getAttribute('aria-keyshortcuts'), 原文: (e.innerText || '').trim().replace(/\n/g, ' ') }; });
      rec.B菜单点击.菜单项 = 项;
      if (项 && !项.禁用) {
        await 清监听();
        await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(2600);
        rec.B菜单点击.节点数后 = await 节点数();
        rec.B菜单点击.剪贴板后 = await 读全部();
        rec.B菜单点击.页面收到的事件 = await 取监听();
        rec.B菜单点击.选中集 = await 选中集();
      }
    } else rec.B菜单点击.说明 = '取不到标题坐标';
  } else rec.B菜单点击.说明 = '没选中图片节点，留白';
}
await p.keyboard.press('Escape'); await p.waitForTimeout(800);

// ═════════ 收尾：删节点三道守卫
rec.清理 = {};
const 现存 = await id集();
const 新增 = 现存.filter((i) => !前id.includes(i));
rec.清理.本轮新增 = 新增;
for (const id of 新增) {
  const 行 = { id, 标题: await 标题文案(id) };
  const S = await 搜索选中(行.标题);
  行.选中成功 = S.成功; 行.选中集 = S.选中集;
  if (S.成功 && S.选中集.includes(id)) {          // 第二道守卫：确认选中的就是它
    await p.keyboard.press('Backspace'); await p.waitForTimeout(2200);
    行.删后还在吗 = !!(await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`), id));
  } else { 行.说明 = '没能可靠选中，不删（宁可留白也不删错）'; rec.清理.逐个.push?.(行); }
  rec.清理.逐个 = rec.清理.逐个 || []; rec.清理.逐个.push(行);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 新增id: 末.filter((i) => !前id.includes(i)),
  丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
