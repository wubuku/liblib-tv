// 批次 178：**把批次 175–177 留下的四个「未取证」项一次钉完**。
//
// 这四个都不是「测不了」，而是**上一批各自因为具体原因没测到**，且都留了白：
//   ① ⌘C 复制 —— 批次 175 只按了、没读剪贴板 ⇒ 「无可见变化、无报错」不能断言可用
//   ② ⌘⇧C 复制为图片 —— 批次 175 没按（只有图片节点有这一项）
//   ③ 重做什么时候会亮 —— 批次 177：刚做完可撤销操作仍禁用；按完 ⌘Z 后因选中集
//      被清空读不到菜单 ⇒ 两头都没测到
//   ④ 节点描述会不会随选中态变 —— 批次 176：4 种类型里 3 种点不中，唯一选中的
//      图片节点描述本来就是空的
//
// ④ 的解法用批次 127 记过的**「搜索面板点结果」**这条可靠选中路径（批次 177 c 轮
//    验证过它 100% 可靠）。③ 的解法：**读完菜单立刻把菜单重新打开**，
//    不要依赖选中态还在。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
// 收尾：本轮造出来的节点全部按 id 删除并逐个验明。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
// ⚠️ v1 卡死 280 秒被 timeout 杀的真正原因：`navigator.clipboard.readText()` 在
//    **没有用户手势**时会弹权限询问，Promise **永不 resolve** —— 整轮挂在那儿。
//    两道保险：① CDP 先授予 clipboard-read；② 读的时候用 Promise.race 加 2.5 秒上限。
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '178' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

/** 读剪贴板，带 2.5 秒上限（v1 就是死在这里）。 */
const 读剪贴板 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒内没返回（多半是被权限询问挂住了）' }), 2500));
  const 真读 = (async () => { try { const t = await navigator.clipboard.readText();
      return { 读成功: true, 长度: t.length, 开头120字: t.slice(0, 120),
        看起来像JSON: /^[\s]*[[{]/.test(t), 是图片dataURL: /^data:image\//.test(t) }; }
    catch (e) { return { 读成功: false, 错误: String(e).slice(0, 120) }; } })();
  return Promise.race([真读, 超时]);
});
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
const 标题文案 = (id) => p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id);

/** 用搜索面板选中一个节点（批次 127 记的可靠路径）。 */
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
  await p.keyboard.press('Escape'); await p.waitForTimeout(450);
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 3) };
};
/** 读右键菜单里「重做」「撤销」两态。**不依赖选中态**（自己保证菜单能开）。 */
const 读撤销重做 = async (id) => {
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, id);
  if (!pt) return { 读不到: '取不到标题坐标' };
  await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(250);
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1300);
  const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    return { 项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => ({ aria: i.getAttribute('aria-label'),
      快捷键: i.getAttribute('aria-keyshortcuts'), 禁用: i.getAttribute('aria-disabled') === 'true',
      span: Array.from(i.children).map((c) => (c.innerText || '').trim()) })) }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (!m) return { 读不到: '菜单没开' };
  const 挑 = (k) => { const x = m.项.find((i) => i.aria === k); return x ? { 禁用: x.禁用, 快捷键: x.快捷键, 原文: x.span.join(' ｜ ') } : '(菜单里没有这一项)'; };
  return { 重做: 挑('重做'), 撤销: 挑('撤销') };
};
const 描述 = (id) => p.evaluate((i) => {
  const h = document.getElementById(`canvas-node-description-${i}`); const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return { 选中: n?.classList.contains('selected') ?? null, 节点aria: n?.getAttribute('aria-label') ?? null, 描述: h ? (h.innerText || '').trim() : null }; }, id);

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 守卫: await keyGuard(p) };

// ═════════ ④ 节点描述会不会随选中态变（用搜索面板可靠选中）
rec['④描述随选中态'] = [];
for (const 类型 of ['text', 'audio']) {   // v1 测 4 类超时被杀 ⇒ 抽 2 类，已足够判「会不会变」
  const 节点 = await p.evaluate((t) => { for (const n of document.querySelectorAll(`.react-flow__node-${t}`)) {
    const q = n.querySelector('[data-testid="flow-node-title"]'); if (!q) continue;
    return { id: n.getAttribute('data-id'), 标题: (q.innerText || '').trim().split('\n')[0] }; } return null; }, 类型);
  if (!节点) { rec['④描述随选中态'].push({ 类型, 说明: '画布上没有这种节点' }); continue; }
  const 前 = await 描述(节点.id);
  const S = await 搜索选中(节点.标题);
  const 中 = await 描述(节点.id);
  await p.mouse.click(640, 690); await p.waitForTimeout(1000);
  const 后 = await 描述(节点.id);
  rec['④描述随选中态'].push({ 类型, id: 节点.id, 标题: 节点.标题, 选中成功: S.成功, 选中集: S.选中集,
    未选中时: 前, 选中时: 中, 取消后: 后,
    描述在选中时变了: 前.描述 !== 中.描述, 节点aria变了: 前.节点aria !== 中.节点aria,
    取消后复原: 后.描述 === 前.描述 && 后.节点aria === 前.节点aria });
}

// ═════════ ①  ⌘C 到底复制了什么
rec['①Meta+C'] = {};
rec['②Meta+Shift+C'] = {};
rec['③重做'] = {};
const 图节点 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image') ||
  Array.from(document.querySelectorAll('.react-flow__node')).find((x) => /node-image/.test(x.className));
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec['①Meta+C'].目标 = 图节点;
if (图节点) {
  const S = await 搜索选中(图节点.标题);
  rec['①Meta+C'].选中 = S;
  if (S.成功) {
    await p.keyboard.press('Meta+c'); await p.waitForTimeout(1600);
    rec['①Meta+C'].剪贴板 = await 读剪贴板();
    // ⌘V 粘贴，看能不能贴出东西
    const 前数 = await 节点数();
    await p.keyboard.press('Meta+v'); await p.waitForTimeout(2200);
    const 现 = await id集();
    const 新增 = 现.filter((i) => !前id.includes(i));
    rec['①Meta+C']['Meta+V后'] = { 前节点数: 前数, 后节点数: 现.length, 新增id: 新增 };
    // ② ⌘⇧C：只有图片节点有「复制为图片」
    const 选中了图 = 新增.length ? await 搜索选中(await 标题文案(新增[0])) : null;
    if (选中了图?.成功) {
      const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
        const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新增[0]);
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1300);
      const 定位 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('复制为图片'));
        if (!e) return null; const r = e.getBoundingClientRect();
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true', 快捷键: e.getAttribute('aria-keyshortcuts') }; });
      rec['②Meta+Shift+C'] = { 菜单项: 定位 };
      if (定位 && !定位.禁用) {
        const 前剪 = (await 读剪贴板()).长度 ?? null;
        await p.keyboard.press('Meta+Shift+c'); await p.waitForTimeout(1600);
        const 后剪 = await 读剪贴板();
        rec['②Meta+Shift+C'].剪贴板前长度 = 前剪;
        rec['②Meta+Shift+C'].剪贴板后 = 后剪;
        rec['②Meta+Shift+C'].结论 = 后剪 && 后剪.是图片dataURL ? '✅ 剪贴板变成了图片 dataURL'
          : (后剪 && 后剪.长度 > 0 && 后剪.长度 !== 前剪 ? '⚠️ 剪贴板内容变了但不是图片 dataURL' : '❌ 剪贴板没变');
      }
      await p.keyboard.press('Escape'); await p.waitForTimeout(700);
    } else rec['②Meta+Shift+C'] = { 说明: '没选中刚粘贴出来的图片节点，测不了' };

    // ③ 重做：做完一次操作 → 撤销 → 读（重新选中，不依赖旧选中态）
    const 靶 = 新增[0] || 图节点.id;
    const S2 = await 搜索选中(await 标题文案(靶));
    rec['③重做'].选中 = S2;
    if (S2.成功) {
      rec['③重做'].S_做完操作后 = await 读撤销重做(靶);
      await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000);
      const 撤后数 = await 节点数();
      // 关键：**重新选中**再读菜单，不靠 ⌘Z 之后那个已经被清掉的选中态
      const S3 = await 搜索选中(await 标题文案(图节点.id));
      rec['③重做'].S_按MetaZ后_重新选中 = { 重新选中: S3, 节点数: 撤后数, 读数: S3.成功 ? await 读撤销重做(图节点.id) : null };
      // 再按一次 ⌘⇧Z 试重做
      if (S3.成功) {
        const 前2 = await 节点数();
        await p.keyboard.press('Meta+Shift+z'); await p.waitForTimeout(2000);
        const 后2 = await 节点数();
        rec['③重做'].S_按MetaShiftZ后 = { 前节点数: 前2, 后节点数: 后2,
          读数: (await 搜索选中(await 标题文案(图节点.id))).成功 ? await 读撤销重做(图节点.id) : null };
      }
    }
  }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ═════════ 收尾：按 id 清掉本轮新增 + 刷新复位
const 现存 = await id集(); const 新增全部 = 现存.filter((i) => !前id.includes(i));
for (const id of 新增全部) {
  const S = await 搜索选中(await 标题文案(id));
  if (S.成功 && S.选中集.includes(id)) { await p.keyboard.press('Backspace'); await p.waitForTimeout(2000); }
}
rec.新增全部 = 新增全部;
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
rec.收尾核验 = { 现在节点数: await 节点数(),
  残留: await p.evaluate((ids) => ids.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)), 新增全部),
  原有总数: 前id.length, 原有仍在: await p.evaluate((old) => old.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)).length, 前id) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
