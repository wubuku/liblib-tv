// 批次 102 · d 轮：走**「空白右键 → 新建节点 → 本地上传」**这条入口上传一个 `.txt`。
//
// 为什么挑 `.txt`：
//   · a 轮挖到的 `accept` 白名单里有 **`text/markdown,.md` 与 `text/plain,.txt`**
//     ⇒ 「上传文本文件」是**产品声明支持**的，但**全册手册一个字都没提过**
//   · 而「新建节点」子菜单里**没有「文档」这一类**（只有 文本/图片/视频/音频/时间线/主体/导演台）
//     ⇒ 预判成三种可能之一：① 生成「文本」节点 ② 生成一种手册没记过的新节点 ③ 被拒
//   哪个都对读者有用，**所以必须实测**。
//
// 同时这一轮**顺带验证手册列了却从没验过的第二个入口**：
// 手册「入口」一节写着「空白右键 → 新建节点 → 从资产库添加 / **本地上传**」，
// 但全页没有任何一句说这条入口验过。
//
// 🔴 三重护栏（批次 97 事故后立的）：删前 id 集合 → 差集**恰好一个**且**同时是 .selected**
//                              → 事后核对消失的 id **恰好只有 SELF**。
//    **点子菜单项前必须验落点**：子菜单里有「文本」「图片」等**会建节点的项**，
//    万一点偏一格就会在共享画布上多出一个节点。本轮用
//    `innerText 逐字 === '本地上传'` + `命中元素落在该项内部` 双重把关。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const DOC = '/tmp/jimeng-b102-doc.txt';

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

// ---- 护栏 ① ----
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
log('上传前 id 数：', idsBefore.length, '｜积分', out.creditsBefore = await credits());

// ---- 空白右键 → 悬停「新建节点」→ 点「本地上传」 ----
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 280; y < 620; y += 16) for (let x = 260; x < 1100; x += 16) if (!bad(x, y)) return [x, y];
  return null; });
await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1000);
const trig = await p.evaluate(() => { const it = document.getElementById('context-menu-submenu-trigger-add-node');
  if (!it) return null; const r = it.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
log('「新建节点」触发项：', JSON.stringify(trig));
await p.mouse.move(trig[0], trig[1]); await p.waitForTimeout(400);
await p.mouse.move(trig[0] + 4, trig[1]); await p.waitForTimeout(1200);
out.subOpen = await p.evaluate(() => { const s = document.getElementById('context-menu-submenu-add-node');
  const f = s ? s.querySelector('[role=menuitem]') : null;
  return { expanded: document.getElementById('context-menu-submenu-trigger-add-node').getAttribute('aria-expanded'),
    firstVisible: f ? getComputedStyle(f).visibility : null }; });
log('子菜单：', JSON.stringify(out.subOpen));

// 落点：只认 innerText 逐字等于「本地上传」的那一项，且命中元素必须落在它内部
const up = await p.evaluate(() => {
  const s = document.getElementById('context-menu-submenu-add-node');
  if (!s) return null;
  for (const it of s.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim() !== '本地上传') continue;
    const r = it.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      hitTag: el ? el.tagName : null, hitText: el ? (el.textContent || '').trim() : null,
      hitRole: el ? el.getAttribute('role') : null,
      insideItem: !!(el && (el === it || it.contains(el))) };
  }
  return null; });
log('「本地上传」落点：', JSON.stringify(up));
out.land = up;
if (!up || !up.insideItem || up.hitText !== '本地上传') { log('🔴 落点判失败 ⇒ 不点（子菜单里别的项会建节点）'); }
else {
  // filechooser：必须用全局 on（waitForEvent 在 connectOverCDP 下会超时）
  let seen = null;
  p.on('filechooser', async (fc) => {
    const info = await fc.element().evaluate((n) => ({
      acceptTokens: (n.getAttribute('accept') || '').split(',').length,
      multiple: n.hasAttribute('multiple'),
      chain: (() => { const c = []; for (let a = n.parentElement; a && c.length < 4; a = a.parentElement)
        c.push(`${a.tagName}${a.getAttribute('data-testid') ? '#' + a.getAttribute('data-testid') : ''}${a.id ? '#' + a.id : ''}`); return c; })(),
    })).catch((e) => ({ err: e.message }));
    seen = { isMultiple: fc.isMultiple(), ...info };
    log('  filechooser 触发：', JSON.stringify(seen));
    try { await fc.setFiles(DOC); log('  setFiles：', DOC); }
    catch (e) { log('  setFiles 失败：', e.message); }
  });
  await p.mouse.move(up.point[0], up.point[1]); await p.waitForTimeout(400);
  await p.mouse.click(up.point[0], up.point[1]);
  await p.waitForTimeout(1500);
  out.chooser = seen;

  // 轮询等节点出现（最多 30 秒）
  let created = [];
  for (let k = 1; k <= 20; k++) {
    await p.waitForTimeout(1500);
    const now = await allIds();
    created = now.filter((id) => !idsBefore.includes(id));
    if (created.length) { out.gotAtMs = k * 1500; break; }
  }
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const newSel = selIds.filter((id) => !idsBefore.includes(id));
  out.guard = { before: idsBefore.length, after: (await allIds()).length, created, selIds, newSel };
  log('护栏：', JSON.stringify(out.guard));
  out.creditsAfter = await credits();
  log('上传后积分：', out.creditsAfter, '（上传前', out.creditsBefore, '）');

  const SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');

  if (SELF) {
    out.selfInfo = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), cls: n.className, transform: n.style.transform,
        screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 160),
        testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
        arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))) }; }, SELF);
    log('SELF 结构：', JSON.stringify(out.selfInfo, null, 1));
    // 全局状态串里有没有 Upload complete
    out.statusStrings = await p.evaluate(() => Array.from(document.querySelectorAll('.sr-only,[role=status],[aria-live]'))
      .map((e) => (e.textContent || '').replace(/\s+/g, ' ').trim())
      .filter((t) => /upload|上传|b102/i.test(t)).slice(0, 10));
    log('含 upload/b102 的状态串：', JSON.stringify(out.statusStrings));
  }
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('本轮终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b102d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
