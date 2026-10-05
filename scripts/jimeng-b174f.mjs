// 批次 174 f 轮：断网 × 改名 —— **这次先把改名验成**，再谈失败态。
//
// 🔴 e 轮（jimeng-b174e.mjs）整轮作废，原因值得留档：
//   我把 `p.fill` 的选择器写成 `'[data-testid="workspace-canvas-title"] input, input'`，
//   **逗号选择器命中多个元素 ⇒ Playwright 严格模式抛错**；我挂了个 `.catch()` 兜底，
//   兜底里直接 `e.value = 新名` + `dispatchEvent('input')` —— 而标题是 **React 受控输入**，
//   直接写 `.value` **不会进 React state**，于是改名**静默失败**。
//   读数上却和「改名成功但没报错」**完全一样**（标题仍是原名、保存态仍是「已保存」）。
//   ⇒ 立规补充：**受控输入上的兜底写入是假的**；要么用能触发 React 的真实输入
//   （`p.fill` / `p.type` / `p.keyboard`），要么**断言改名真的生效了**再读别的。
//   本轮开头就断言 `标题 === 原名+t`，不成立直接记「没测成」，不再往下编结论。
//
// 本轮要回答的（用户真的会遇到）：
//   Q1 断网时改画布名，**改名本身**成不成立？（乐观保存 / 静默失败 / 报错）
//   Q2 保存指示器会不会变？会不会出现「保存失败 / 重试 / 离线」？
//   Q3 `canvas-save-failure-anchor` 会不会长出子元素？（它是 0×0 的定位锚）
//   Q4 恢复网络后会不会自愈？
//
// ⛔ 不生成、不分享、不新建节点。断网用 CDP，且**必��恢复**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174f' };
const cdp = await p.context().newCDPSession(p);
await cdp.send('Network.enable');
const 网 = async (offline) => {
  await cdp.send('Network.emulateNetworkConditions',
    offline ? { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 }
            : { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
  await p.waitForTimeout(600);
};
process.on('uncaughtException', async (e) => {
  console.error('!! 异常，先恢复网络:', String(e).slice(0, 300));
  try { await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 }); } catch {}
  process.exit(9);
});

const 标题 = () => p.evaluate(() => ({
  文字: (document.querySelector('[data-testid="canvas-project-title-trigger"]')?.innerText || '').trim(),
  aria: document.querySelector('[data-testid="canvas-project-title-trigger"]')?.getAttribute('aria-label'),
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
}));
const 采 = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-title-save-status"]');
  const a = document.querySelector('[data-testid="canvas-save-failure-anchor"]');
  const 词 = ['失败', '重试', '离线', '未保存', '网络异常', '稍后'];
  const 命中 = [];
  for (const el of document.querySelectorAll('div,span,p,button,[role=alert],[role=status]')) {
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (Array.from(el.children).some((c) => { const cr = c.getBoundingClientRect(); return cr.width > 0 && cr.height > 0; })) continue;
    const t = (el.textContent || '').trim();
    if (!t || t.length > 24 || !词.some((w) => t.includes(w))) continue;
    命中.push({ 文本: t, testid: el.getAttribute('data-testid'), role: el.getAttribute('role'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  const ar = a ? a.getBoundingClientRect() : null;
  return { 指示器: e ? (e.textContent || '').trim() : null, 指示器子元素: e ? e.children.length : null,
    锚子元素: a ? a.children.length : null, 锚内文: a ? (a.textContent || '').trim().slice(0, 80) : null,
    锚rect: ar ? [Math.round(ar.x), Math.round(ar.y), Math.round(ar.width), Math.round(ar.height)] : null,
    关键词元素: 命中.slice(0, 6) };
});
// ⚠️ 改名沿用 **d 轮那套已验成**的写法：`p.fill('input,textarea', …)`。不要换成逗号选择器。
const 改名 = async (新名) => {
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-title-trigger"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!pt) return { 失败: '找不到标题按钮' };
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(900);
  const 输入框数 = await p.evaluate(() => document.querySelectorAll('input,textarea').length);
  await p.fill('input,textarea', 新名);
  await p.waitForTimeout(150);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(2600);
  return { 输入框数, 回读: await 标题() };
};

await settle(p, R);
rec.起点 = { 标题: await 标题(), 采样: await 采() };
const 原名 = rec.起点.标题.文字;
rec.原名 = 原名;

// ═════════ ① 先在**联网**状态下确认改名机制本身是好的（阳性对照）
rec.阳性对照 = await 改名(原名 + 't');
rec.阳性对照成立 = rec.阳性对照.回读?.文字 === 原名 + 't';
if (!rec.阳性对照成立) {
  rec.结论 = '**改名机制都没验成，本轮到此为止** —— 不对「断网时保存指示器变不变」下任何结论。';
} else {
  await 改名(原名);                                   // 还原
  rec.还原后 = await 标题();

  // ═════════ ② 断网 + 改名
  await 网(true);
  rec.断网后 = { onLine: await p.evaluate(() => navigator.onLine), 采样: await 采() };
  rec.t0 = Date.now();
  rec.采样 = []; rec.不同指示器态 = new Set(); rec.不同锚态 = new Set(); rec.不同关键词 = [];
  const 采样器 = setInterval(async () => {
    try { const s = await 采();
      rec.采样.push([Date.now() - rec.t0, s.指示器, s.锚子元素, (s.锚内文 || '').slice(0, 30), s.关键词元素.length]);
      rec.不同指示器态.add(String(s.指示器)); rec.不同锚态.add(`${s.锚子元素}|${(s.锚内文 || '').slice(0, 30)}`);
      if (s.关键词元素.length) rec.不同关键词.push([Date.now() - rec.t0, s.关键词元素]);
    } catch {}
  }, 120);
  rec.断网改名 = await 改名(原名 + 't');
  await p.waitForTimeout(4000);
  rec.断网期ms = Date.now() - rec.t0;
  clearInterval(采样器);
  rec.断网改名后标题 = await 标题();
  rec.断网改名成立 = rec.断网改名后标题.文字 === 原名 + 't';
  rec.不同指示器态 = [...rec.不同指示器态];
  rec.不同锚态 = [...rec.不同锚态];
  rec.异常采样点 = rec.采样.filter((s) => s[1] !== '已保存' || (s[2] ?? 0) > 0 || s[4] > 0).slice(0, 20);
  rec.断网期采样条数 = rec.采样.length;

  // ═════════ ③ 恢复网络，看自愈
  await 网(false);
  await p.waitForTimeout(3500);
  rec.恢复后 = { 标题: await 标题(), 采样: await 采(), onLine: await p.evaluate(() => navigator.onLine) };
  await 改名(原名);
  await p.waitForTimeout(2000);
  rec.最终标题 = await 标题();
  rec.复原成功 = rec.最终标题.文字 === 原名;
}
delete rec.t0;
await p.mouse.move(1250, 10);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  onLine: await p.evaluate(() => navigator.onLine) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
