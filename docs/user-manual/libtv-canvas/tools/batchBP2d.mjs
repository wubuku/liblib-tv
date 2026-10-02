// Batch BP2d — 修好守卫、把「资产管理」弹窗读透、给「上传资产」的 accept 做归因。
//
// ⛔ 先认 BP2c 的两个错（都是我自己造的噪声，不是产品行为）：
//   ① `assertClosed` 里我把正则写成 /Modal|Dialog|Drawer/，结果把**我要它开着的那只抽屉**
//      （`mantine-Drawer-inner`）也算成「没关掉的弹窗」→ `closed` 永远是 false →
//      于是「Escape 关不掉这个弹窗」这个结论是**我的守卫造出来的**，作废。
//      ⇒ 修法：弹窗只认 `.mantine-Modal-content` / `[role="dialog"]` / `[class*=Modal-root]`，
//        **显式排除 Drawer**；再加 `titleCount` 和 `elementFromPoint` 两条独立证据。
//   ② 「读弹窗」时我取的是「面积最大的 >800×500 的 div」，那拿到的是**画布背景**，
//      所以弹窗正文读出来是「音频节点 6 尝试：音频生视频…」这种画布噪声。
//      ⇒ 修法：从标题「资产管理」**向上走到最近的浮层根**，只在那个根里面读。
//
// ⭐ BP2c 里唯一站得住的两条结论（保留）：
//   · 点抽屉头部「管理」后，`elementFromPoint(219,162)` 的命中链从抽屉里的
//     `SPAN.flex > BUTTON.flex` 变成了 `DIV.rounded-xl > DIV.z-201`
//     ⇒ **确实有东西盖上来了**，「管理」开的就是那个弹窗。
//   · 新增浮层里有一行 `待分类资产 2026-10-02`，**日期就是今天** ⇒ BP1 确实建了这个分类。
//
// 本轮全部只读：⛔ 不建文件夹、不传文件、不建主体、不删不改名。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2d';
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .find((x) => x.getAttribute('aria-label') === l && x.getBoundingClientRect().width >= 4
        && x.getBoundingClientRect().height >= 4);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2600, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** ⭐ 修好的守卫：弹窗只认 Modal/Dialog，**显式排除 Drawer**；加两条独立证据。 */
const assertClosed = async ({ probe = null } = {}) => page.evaluate((pv) => {
  const shown = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  // ① 弹窗容器：只认 Modal / Dialog，**Drawer 不算**（抽屉本来就该开着）
  const modals = [...document.querySelectorAll('.mantine-Modal-content,[role="dialog"],[class*="Modal-root"]')]
    .filter(shown).map((e) => ({ cls: (e.className || '').toString().slice(0, 50),
      t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) }));
  // ② 标题「资产管理」在可见 DOM 里的出现次数
  const titleCount = [...document.querySelectorAll('div,h1,h2,span')]
    .filter((e) => (e.innerText || '').trim() === '资产管理' && shown(e)).length;
  // ③ ⭐ 阳性对照：elementFromPoint 打不打得中抽屉里的按钮
  let hit = null;
  if (pv) {
    const el = document.elementFromPoint(pv[0], pv[1]);
    const chain = []; for (let e = el, i = 0; e && i < 5; e = e.parentElement, i++)
      chain.push(`${e.tagName}.${(e.className || '').toString().split(' ').slice(0, 2).join('.')}`);
    hit = { chain, aria: el?.getAttribute?.('aria-label') || null,
      inModal: !!el?.closest('.mantine-Modal-content,[role="dialog"],[class*="Modal-root"]') };
  }
  return { closed: modals.length === 0 && titleCount === 0 && (!hit || !hit.inModal),
    modals, titleCount, probeHit: hit };
}, probe);

const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1100); };

/** ⭐ 从标题「资产管理」向上找到最近的浮层根，只在它里面读内容。 */
const readModal = () => page.evaluate(() => {
  const title = [...document.querySelectorAll('div,h1,h2,span')]
    .find((e) => (e.innerText || '').trim() === '资产管理' && e.getBoundingClientRect().width > 0);
  if (!title) return { found: false };
  let root = title;
  for (let i = 0; i < 8 && root.parentElement; i++) {
    root = root.parentElement;
    const r = root.getBoundingClientRect();
    if (r.width > 500 && r.height > 350) break;
  }
  const shown = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const at = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; };
  const dedup = (a) => a.filter((v, i, x) => x.findIndex((y) => y.t === v.t && y.at[1] === v.at[1] && y.at[0] === v.at[0]) === i);
  const rr = root.getBoundingClientRect();
  return { found: true, rootRect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    rootCls: (root.className || '').toString().slice(0, 60),
    text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    // 侧栏（根内靠左的一条）
    side: dedup([...root.querySelectorAll('div,button,a,li')].filter(shown).map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ r, e }) => r.x < rr.x + 40 && r.width > 70 && r.height >= 24 && r.height <= 56 && e.children.length <= 3)
      .map(({ e }) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), at: at(e),
        bg: getComputedStyle(e).backgroundColor })).filter((x) => x.t)),
    // 标签行（根内靠上、横向一排的小按钮）
    tabs: dedup([...root.querySelectorAll('div,button,li,span')].filter(shown).map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ r, e }) => r.y > rr.y + 40 && r.y < rr.y + 200 && r.height >= 24 && r.height <= 44
        && r.width >= 28 && r.width <= 120 && e.children.length === 0)
      .map(({ e }) => ({ t: (e.innerText || '').trim(), at: at(e),
        bg: getComputedStyle(e).backgroundColor })).filter((x) => x.t)),
    buttons: [...root.querySelectorAll('button,[role="button"]')].filter(shown)
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        aria: e.getAttribute('aria-label'), at: at(e) })),
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '修好守卫（排除 Drawer）+ 从标题锚点读弹窗 + 捕获 click 事件归因 file input' });
  const out = {};
  const probe = [219, 162];

  await clickAria('资产管理', 2800);
  await clickText('资产', 2600, 20);
  const g0 = await assertClosed({ probe }); out.guard0 = g0;
  console.log(`═══ 守卫自检 ═══ closed=${g0.closed}｜弹窗容器=${g0.modals.length} 标题数=${g0.titleCount}`);
  console.log(`  ⭐ 阳性对照 elementFromPoint(${probe}) → ${JSON.stringify(g0.probeHit)}`);
  console.log(`  ${g0.closed ? '✅ 守卫工作正常（这次 closed=true 才算可信）' : '⛔ 守卫仍不可信'}`);

  // ── ① 点「管理」，用守卫 + 截图双证弹窗开没开
  const mg = await clickAria('资产管理', 2600);
  const g1 = await assertClosed({ probe }); out.afterManage = { ...mg, guard: g1 };
  console.log(`\n═══ ① 点抽屉头部「管理」（executed=${mg.executed}）═══\n  closed=${g1.closed}｜弹窗容器=${g1.modals.length} 标题数=${g1.titleCount}`);
  console.log(`  elementFromPoint → ${JSON.stringify(g1.probeHit)}`);
  await shot(page, 'M-255-资产管理弹窗-从管理进入.png');

  const M0 = await readModal(); out.modal0 = M0;
  console.log(`\n═══ ② 弹窗读数（根=${M0.rootCls} rect=${JSON.stringify(M0.rootRect)}）═══`);
  if (M0.found) {
    console.log(`  全文：${M0.text}`);
    console.log(`  侧栏：${JSON.stringify(M0.side)}`);
    console.log(`  标签：${JSON.stringify(M0.tabs)}`);
    console.log(`  按钮：${JSON.stringify(M0.buttons)}`);
  } else console.log('  ⛔ 没找到标题锚点');

  // ── ③ ⭐ Escape 到底关不关得上（视觉 + 守卫双证）
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  const g2 = await assertClosed({ probe }); out.afterEscape = g2;
  console.log(`\n═══ ③ 单按 Escape 之后 ═══ closed=${g2.closed}｜弹窗容器=${g2.modals.length} 标题数=${g2.titleCount}`);
  console.log(`  elementFromPoint → ${JSON.stringify(g2.probeHit)}`);
  await shot(page, 'M-257-按Escape之后.png');
  out.escapeCloses = g2.closed;
  console.log(`  ⭐⭐ Escape 能关掉「资产管理」弹窗吗？ ${g2.closed ? '✅ 能' : '❌ 不能'}`);
  if (!g2.closed) {
    const x = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].filter((e) => { const r = e.getBoundingClientRect();
          return r.width > 10 && r.height > 10 && r.x > 1000 && r.y < 260; })
        .find((e) => /^[✕×xX]$/.test((e.innerText || '').trim()) || /关闭|Close/.test(e.getAttribute('aria-label') || ''));
      if (!b) return null; const r = b.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    console.log(`  ✕ 坐标：${JSON.stringify(x)}`);
    if (x) { await page.mouse.click(x[0], x[1]); await page.waitForTimeout(1400); }
    const g2b = await assertClosed({ probe }); out.afterCloseBtn = g2b;
    console.log(`  点 ✕ 之后 closed=${g2b.closed}｜弹窗容器=${g2b.modals.length} 标题数=${g2b.titleCount}`);
    out.closeBtnWorks = g2b.closed;
  }

  // ── ④ 弹窗内标签页是否真的筛内容（判别式 = 正文首个卡片名）
  if (M0.found && M0.tabs.length) {
    console.log(`\n═══ ④ 逐个标签页 ═══`);
    const tabsOut = [];
    const bodyText = () => page.evaluate(() => {
      const title = [...document.querySelectorAll('div,h1,h2,span')]
        .find((e) => (e.innerText || '').trim() === '资产管理' && e.getBoundingClientRect().width > 0);
      if (!title) return null;
      let root = title;
      for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
        const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
      return (root.innerText || '').replace(/\s+/g, ' ').trim(); });
    for (const t of M0.tabs) {
      const r = await clickText(t.t, 1800, 20);
      const body = await bodyText();
      tabsOut.push({ tab: t.t, executed: r.executed, body: body?.slice(0, 160) });
      console.log(`  【${t.t}】executed=${r.executed} → 正文：${JSON.stringify(body?.slice(0, 140))}`);
    }
    out.tabsProbe = tabsOut;
    const sigs = [...new Set(tabsOut.map((t) => t.body))];
    console.log(`  ⭐ ${tabsOut.length} 个标签给出 ${sigs.length} 个不同正文 ${sigs.length > 1 ? '✅ 各不相同 → 筛选生效' : '❌ 全一样 → 点了没反应'}`);
    out.tabsDistinguish = sigs.length;
    await esc();
    const g4 = await assertClosed({ probe });
    console.log(`  守卫：closed=${g4.closed}`);
    if (!g4.closed) { await page.mouse.click(30, 700); await page.waitForTimeout(1200); }
  }

  // ── ⑤ ⭐ 上传归因：在 document 上装**捕获阶段** click 监听，
  //      记录到底是哪个 <input type=file> 收到了那次点击 —— 比等 filechooser 事件更硬。
  console.log(`\n═══ ⑤ 上传归因（捕获 click 事件） ═══`);
  await page.evaluate(() => {
    window.__fcHits = [];
    document.addEventListener('click', (e) => {
      const t = e.target;
      if (t && t.tagName === 'INPUT' && t.type === 'file') {
        window.__fcHits.push({ accept: t.getAttribute('accept'), multiple: t.getAttribute('multiple'),
          cls: (t.className || '').toString().slice(0, 40),
          outer: t.outerHTML.slice(0, 200) });
      }
    }, true);
  });
  const cr = await clickAria('创建', 2200);
  const dd = await page.evaluate(() => {
    const seen = new Set(); const out = [];
    for (const e of document.querySelectorAll('div,button,li,span')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^(新建文件夹|上传资产)$/.test(t)) continue;
      const r = e.getBoundingClientRect(); if (r.width < 30 || r.height < 12) continue;
      const k = `${t}@${Math.round(r.x)},${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      out.push({ t, at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    } return out; });
  console.log(`  「创建」下拉项：${JSON.stringify(dd)}（executed=${cr.executed}）`);
  const upItem = dd.find((d) => d.t === '上传资产');
  if (!upItem) { console.log('  ⛔ 下拉里没有「上传资产」'); out.uploadAccept = null; }
  else {
    const fcP = page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null);
    await page.mouse.click(upItem.at[0], upItem.at[1]);
    const fc = await fcP; await page.waitForTimeout(1200);
    const hits = await page.evaluate(() => window.__fcHits);
    console.log(`  filechooser 事件：${fc ? '✅ 弹了' : '❌ 没弹'}`);
    console.log(`  ⭐ 收到 click 的 file input：${JSON.stringify(hits)}`);
    out.upload = { dropdownItems: dd, chooserFired: !!fc, clickHits: hits };
    if (fc) {
      const el = fc.element();
      out.upload.accept = await el.getAttribute('accept');
      out.upload.multiple = await el.getAttribute('multiple');
      console.log(`  ⭐⭐ 归因到了：accept=${JSON.stringify(out.upload.accept)} multiple=${JSON.stringify(out.upload.multiple)}`);
    }
    if (hits.length) console.log(`  ⭐⭐ 归因到了：accept=${JSON.stringify(hits[0].accept)} multiple=${JSON.stringify(hits[0].multiple)}`);
    out.upload.accept = out.upload.accept ?? hits[0]?.accept ?? null;
    out.upload.multiple = out.upload.multiple ?? hits[0]?.multiple ?? null;
  }
  await esc();

  const gEnd = await assertClosed({ probe });
  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN, guard: gEnd };
  console.log(`\n═══ 收尾：节点 ${finalN}，守卫 closed=${gEnd.closed}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BP2d-asset-modal-and-upload-accept',
    title: '⭐ Escape 关不关得上「资产管理」弹窗（守卫已修）+ 上传资产 accept 归因',
    target: 'BP2c 的守卫把「Drawer」也算成没关掉的弹窗，导致 `closed` 恒为 false，'
      + '「Escape 关不掉」是守卫造出来的结论，作废；BP2c 读弹窗时取「面积最大的 div」拿到的是画布背景，'
      + '读出来全是画布噪声。本轮守卫改为**只认 Modal/Dialog、显式排除 Drawer**，'
      + '弹窗内容改为**从标题「资产管理」向上锚定浮层根**来读；'
      + '同时用**捕获阶段的 click 监听**归因「上传资产」背后到底是哪个 file input，'
      + '而不是只等 filechooser 事件。⛔ 不建文件夹、不传文件、不建主体、不删不改名。',
    evidence: out,
    visible_text: JSON.stringify({
      守卫自检: out.guard0, 点管理后: out.afterManage,
      弹窗根: out.modal0 && { cls: out.modal0.rootCls, rect: out.modal0.rootRect },
      弹窗全文: out.modal0?.text, 侧栏: out.modal0?.side, 标签: out.modal0?.tabs,
      Escape后: out.afterEscape, Escape能关: out.escapeCloses, '点关闭钮能关': out.closeBtnWorks,
      标签页探测: out.tabsProbe, 标签正文不同值数: out.tabsDistinguish,
      上传: out.upload, 收尾: out.final }).slice(0, 3400),
    shot: 'M-255-资产管理弹窗-从管理进入.png',
  });
  console.log('\nBP2d 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}
