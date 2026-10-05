// 批次 182：**把 `⌘⇧C 复制为图片` 这个从批次 175 就留着的白钉掉。**
//
// 为什么 178 测不到（不是「测不了」，是路径选错了）：
//   178 的做法是「先在图片节点上按 ⌘C，再 ⌘V 粘出来，然后在**粘出来的那个节点**上找
//   『复制为图片』」。而 178 同批刚测出 **⌘C 复制的是文本** ⇒ 粘出来的是**文本节点**
//   ⇒ 文本节点的菜单里根本没有这一项 ⇒ 「测不了」。
//   🔴 **靶子一开始就摆在画布上**：`b22-upload` 就是图片节点，批次 175 还在它上面
//   读到过「复制为图片 ⌘⇧C」这一项。**根本不需要先粘一个出来。**
//
// 🔴 本批的关键实验设计（照搬批次 175 查 ⌘D 的教训）：
//   批次 175 发现「菜单上明明白白印着 ⌘D，按了没反应」——**只测按键不足以断言功能坏**。
//   所以这里**两条路都测**：① 菜单里点「复制为图片」；② 键盘按 `Meta+Shift+c`。
//   两者读数不同 ⇒ 结论完全不同：
//     两条都成功 ⇒ 功能与按键都在；
//     菜单成功、按键无反应 ⇒ **功能可用、快捷键是摆设**（与 ⌘D 同族）；
//     两条都无反应 ⇒ 才是功能本身的问题。
//
// 🔴 读剪贴板不能只读文本：批次 178 用 `readText()` 判「是不是图片 dataURL」——
//   如果它放进去的是一个 **PNG blob**，`readText()` 会**抛错**而不是返回空串，
//   于是「读失败」会被我误当成「没复制」。这里改用 `navigator.clipboard.read()`
//   枚举 **items → types**，文本与二进制两路都读。
//   仍保留批次 178 的两道保险：CDP 先授权 + `Promise.race` 2.5 秒上限。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '182' };

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

/**
 * 枚举剪贴板里的**所有**条目与类型（不只读文本）。
 * 关键：`navigator.clipboard.read()` 能看见 `image/png` 这类二进制项，
 * 而 `readText()` 遇到二进制项会抛错 —— 只用 readText 会把「复制成功」读成「读取失败」。
 */
const 读剪贴板 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒内没返回' }), 2500));
  const 真读 = (async () => {
    try {
      const items = await navigator.clipboard.read();
      const out = [];
      for (const it of items) for (const t of it.types) {
        const rec0 = { type: t, 字节: null, 文本: null, 错误: null };
        try {
          if (t.startsWith('text/')) { const b0 = await it.getType(t); rec0.文本 = (await b0.text()).slice(0, 140); rec0.字节 = b0.size; }
          else { const b0 = await it.getType(t); rec0.字节 = b0.size; }
        } catch (e) { rec0.错误 = String(e).slice(0, 90); }
        out.push(rec0);
      }
      return { 读成功: true, 条目数: items.length, 明细: out,
        有图片项: out.some((x) => x.type.startsWith('image/')),
        有文本项: out.some((x) => x.type.startsWith('text/')) };
    } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 140) }; }
  })();
  return Promise.race([真读, 超时]);
});
/** 往剪贴板写一个哨兵文本 —— 用来证明「剪贴板真的被这个动作改过」。 */
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; }
  catch (e) { return '写失败: ' + String(e).slice(0, 90); } }, s);

const 标题文案 = (id) => p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id);

/** 用搜索面板选中一个节点（批次 127 记的可靠路径，177/178 各验 100%）。 */
const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词);
  await p.waitForTimeout(1200);
  const 命中 = await p.evaluate((词) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''),
        文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 50),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
    .filter((x) => !词 || x.文字.includes(词)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没有命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1300);
  const s = await 选中集();
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 3) };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 守卫: await keyGuard(p) };

// 靶子：画布上现成的图片节点
const 图节点 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image') ||
  Array.from(document.querySelectorAll('.react-flow__node')).find((x) => /node-image/.test(x.className));
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  const img = n.querySelector('img');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
    有IMG: !!img, alt: img ? (img.getAttribute('alt') || '').slice(0, 90) : null }; });
rec.靶子 = 图节点;

// ═════════ A 菜单读数：确认「复制为图片 ⌘⇧C」在，且没被禁用
rec.A菜单 = {};
if (图节点) {
  const S = await 搜索选中(图节点.标题);
  rec.A菜单.选中 = S;
  if (S.成功) {
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, 图节点.id);
    rec.A菜单.标题坐标 = pt;
    if (pt) {
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
      const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
        return { 项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => ({ aria: i.getAttribute('aria-label'),
          快捷键: i.getAttribute('aria-keyshortcuts'), 禁用: i.getAttribute('aria-disabled') === 'true' })) }; });
      rec.A菜单.读数 = m;
      await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    }
  }
}

// ═════════ B 路径①：**菜单里点**「复制为图片」 —— 判「功能本身」在不在
rec.B菜单点击 = {};
if (图节点) {
  const S = await 搜索选中(图节点.标题);
  rec.B菜单点击.选中 = S;
  // 非空守卫：没选中就不往下走，宁可留白也不在错的节点上测
  if (S.成功 && S.选中集.includes(图节点.id)) {
    rec.B菜单点击.哨兵写入 = await 写哨兵('B182-SENTINEL-菜单点击');
    rec.B菜单点击.剪贴板前 = await 读剪贴板();
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, 图节点.id);
    if (pt) {
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
      const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('复制为图片'));
        if (!e) return null; const r = e.getBoundingClientRect();
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          禁用: e.getAttribute('aria-disabled') === 'true', 快捷键: e.getAttribute('aria-keyshortcuts'),
          原文: (e.innerText || '').trim().replace(/\n/g, ' ') }; });
      rec.B菜单点击.菜单项 = 项;
      if (项 && !项.禁用) {
        await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(2200);
        rec.B菜单点击.剪贴板后 = await 读剪贴板();
      } else rec.B菜单点击.说明 = 项 ? '菜单项被禁用，没点' : '菜单里没有这一项';
    } else rec.B菜单点击.说明 = '取不到标题坐标';
  } else rec.B菜单点击.说明 = '没能选中图片节点，留白';
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

// ═════════ C 路径②：**键盘按** `Meta+Shift+c` —— 判「快捷键」在不在
rec.C按键 = {};
if (图节点) {
  const S = await 搜索选中(图节点.标题);
  rec.C按键.选中 = S;
  if (S.成功 && S.选中集.includes(图节点.id)) {
    rec.C按键.焦点守卫 = await keyGuard(p);          // 🔴 焦点在输入面里的话，按键会变成打字
    rec.C按键.哨兵写入 = await 写哨兵('B182-SENTINEL-按键');
    rec.C按键.剪贴板前 = await 读剪贴板();
    const 前数 = await 节点数();
    await p.keyboard.press('Meta+Shift+c'); await p.waitForTimeout(2200);
    rec.C按键.剪贴板后 = await 读剪贴板();
    rec.C按键.节点数 = { 前: 前数, 后: await 节点数() };
    rec.C按键.选中集 = await 选中集();
  } else rec.C按键.说明 = '没能选中图片节点，留白';
}

await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ═════════ 收尾：刷新复位 + 核验（纯读，不造节点）
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 现存 = await id集();
rec.收尾核验 = { 现在节点数: 现存.length, 起点节点数: 前id.length,
  新增id: 现存.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !现存.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
