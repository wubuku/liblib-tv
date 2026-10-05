// 批次 174 e 轮：**把保存失败态真的撞出来**。
//
// 前四轮把「保存指示器」钉到这一步：
//   a 轮 `canvas-title-save-status` = `<output aria-live="polite">`，逐字「已保存」，
//        祖先链里有 `canvas-title-metadata` / `canvas-title-details`；
//        同页还有一个**从没人提过**的 `canvas-save-failure-anchor`。
//   d 轮 改名 6 秒内 197 次采样（30ms 一次）**只撞到「已保存」一个态**，
//        而 d-4 量到那个 anchor 是 `0×0`、零子元素、零内文、`pointer-events:none`
//        ⇒ **它当时只是定位锚点，不是 UI**。我据此**推断「存在保存失败态」，这个推断还没被验过**。
//
// 本轮用**断网**把失败态逼出来：CDP `Network.emulateNetworkConditions offline:true`
// → 改画布名 → 高频采样三处：保存指示器本体 / anchor 的子元素与内文 /
// 全页任何含「失败 / 重试 / 离线 / 未保存 / 网络」字的可见元素。
// ⚠️ 同时**盯紧画布名**：断网期间改的名**可能没存上**，恢复网络后必须逐字核��、
//    改回「测试项目」再验。断网**必须在收尾解除**并用一次 reload 确认页面正常。
//
// ⛔ 不生成、不分享、不新建节点。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174e' };
const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');

const 网 = async (offline) => {
  await cdp.send('Network.emulateNetworkConditions',
    offline ? { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 }
            : { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
  await p.waitForTimeout(600);
};
const 标题 = () => p.evaluate(() => ({
  文字: (document.querySelector('[data-testid="canvas-project-title-trigger"]')?.innerText || '').trim(),
  aria: document.querySelector('[data-testid="canvas-project-title-trigger"]')?.getAttribute('aria-label'),
}));
/** 三处一起采。带**非空守卫**：没采到东西必须显式记成 null，不许悄悄跳过。 */
const 采 = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-title-save-status"]');
  const a = document.querySelector('[data-testid="canvas-save-failure-anchor"]');
  const 词 = ['失败', '重试', '离线', '未保存', '网络', '保存'];
  const 命中 = [];
  // 只扫**可见且非空**的元素，且只在 textContent 里找词（O(n) 一遍，不做子树重算）
  for (const el of document.querySelectorAll('div,span,p,button,[role=alert],[role=status]')) {
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (Array.from(el.children).some((c) => { const cr = c.getBoundingClientRect(); return cr.width > 0 && cr.height > 0; })) continue; // 只留叶子
    const t = (el.textContent || '').trim();
    if (!t || t.length > 24) continue;
    if (词.some((w) => t.includes(w))) 命中.push({ 文本: t, testid: el.getAttribute('data-testid'), role: el.getAttribute('role'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return {
    指示器: e ? { 文本: (e.textContent || '').trim(), html: e.innerHTML.slice(0, 200), 子元素: e.children.length,
      祖先链: (() => { const o = []; for (let n = e; n && n !== document.body; n = n.parentElement) o.push(n.tagName.toLowerCase() + (n.dataset?.testid ? `[${n.dataset.testid}]` : '')); return o.slice(0, 4); })() } : null,
    失败锚: a ? { 子元素: a.children.length, 内文: (a.textContent || '').trim().slice(0, 120), html: a.innerHTML.slice(0, 300),
      rect: [Math.round(a.getBoundingClientRect().x), Math.round(a.getBoundingClientRect().y), Math.round(a.getBoundingClientRect().width), Math.round(a.getBoundingClientRect().height)] } : null,
    关键词元素: 命中.slice(0, 8),
  };
});
const 点中心 = async (sel) => {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, sel);
  if (!pt) return false; await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800); return true;
};

await settle(p, R);
// ⛔ 保险：断网是**全局副作用**。任何一步抛错都必须把网络恢复，
//    否则这台 Chrome 会一直断着，别人（和后续批次）全跟着遭殃。
process.on('uncaughtException', async (e) => {
  console.error('!! 异常，先恢复网络再退出:', String(e).slice(0, 300));
  try { await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 }); } catch {}
  process.exit(9);
});
rec.起点 = { 标题: await 标题(), 采样: await 采() };

// ═══════════ ① 断网
await 网(true);
rec.断网后在线状态 = await p.evaluate(() => navigator.onLine);
rec.断网后采样 = await 采();

// ═══════════ ② 断网状态下改名 + 高频采样
rec.t0 = Date.now();
rec.采样 = []; rec.不同指示器态 = new Set(); rec.不同锚态 = new Set();
const 采样器 = setInterval(async () => {
  try { const s = await 采();
    rec.采样.push([Date.now() - rec.t0, s.指示器?.文本 ?? null, s.失败锚?.子元素 ?? null, (s.失败锚?.内文 || '').slice(0, 40)]);
    if (s.指示器) rec.不同指示器态.add(s.指示器.文本);
    rec.不同锚态.add(`${s.失败锚?.子元素}|${(s.失败锚?.内文 || '').slice(0, 40)}`);
  } catch {}
}, 120);
const 原名 = rec.起点.标题.文字;
rec.原名 = 原名;
await 点中心('[data-testid="canvas-project-title-trigger"]');
rec.输入框 = await p.evaluate(() => { const e = document.querySelector('[data-testid="workspace-canvas-title"] input')
  || Array.from(document.querySelectorAll('input')).find((x) => x.getBoundingClientRect().y < 60 && x.getBoundingClientRect().width > 20);
  return e ? { 值: e.value, 宽: Math.round(e.getBoundingClientRect().width) } : null; });
if (rec.输入框) {
  await p.fill('[data-testid="workspace-canvas-title"] input, input', 原名 + 't').catch(async () => {
    await p.evaluate((n) => { const e = document.querySelector('[data-testid="workspace-canvas-title"] input')
      || Array.from(document.querySelectorAll('input')).find((x) => x.getBoundingClientRect().y < 60 && x.getBoundingClientRect().width > 20);
      if (e) { e.value = n; e.dispatchEvent(new Event('input', { bubbles: true })); } }, 原名 + 't');
  });
  await p.waitForTimeout(150);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(5000);
}
rec.断网改名后标题 = await 标题();
rec.断网期采样ms = Date.now() - rec.t0;
clearInterval(采样器);
rec.采样条数 = rec.采样.length;
rec.不同指示器态 = [...rec.不同指示器态];
rec.不同锚态 = [...rec.不同锚态];
// 采样里第一次出现非「已保存」或锚有子元素的位置
rec.异常采样点 = rec.采样.filter((s) => s[1] !== '已保存' || (s[2] ?? 0) > 0).slice(0, 20);
rec.断网期末次采样 = await 采();

// ═══════════ ③ 恢复网络，看会不会自愈
await 网(false);
await p.waitForTimeout(3000);
rec.恢复网络后 = { 标题: await 标题(), 采样: await 采(), navigatorOnLine: await p.evaluate(() => navigator.onLine) };
// 再改一次（联网态）看是否回到「已保存」
await 点中心('[data-testid="canvas-project-title-trigger"]');
await p.waitForTimeout(600);
await p.evaluate((n) => { const e = document.querySelector('[data-testid="workspace-canvas-title"] input')
  || Array.from(document.querySelectorAll('input')).find((x) => x.getBoundingClientRect().y < 60 && x.getBoundingClientRect().width > 20);
  if (e) { e.value = n; e.dispatchEvent(new Event('input', { bubbles: true })); } }, 原名);
await p.waitForTimeout(150);
await p.keyboard.press('Enter');
await p.waitForTimeout(3000);
rec.改名回原名后 = { 标题: await 标题(), 采样: await 采() };

// ═══════════ ④ 收尾：确认网络已恢复、页面正常、名字已还原
await p.mouse.move(1250, 10);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  标题: await 标题(), navigatorOnLine: await p.evaluate(() => navigator.onLine) };
rec.复原成功 = rec.收尾.标题.文字 === 原名;
rec.网络已恢复 = rec.收尾.navigatorOnLine === true;
delete rec.t0;
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
