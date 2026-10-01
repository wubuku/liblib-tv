// Batch V —— 资产管理抽屉的「更多操作」，精确到单行。
//
// 前两轮（batchS/T、batchU）都没找到它，失败原因各不相同：
//   batchS：抽屉根本没开就去找按钮
//   batchT：抽屉框量到 [0,810,1440,0]，高度 0 —— **是收着的**
//   batchU：抽屉这次真的开了（[0,0,319,810]），但我的悬停目标
//           选中了**整个列表容器**（读回来 text 是「图片节点 2 文本节点 1」两行拼一起），
//           不是单独一行
//
// 而 batchG2 那一轮是**单节点**画布，读到了「定位到节点 {名}」+「更多操作」。
// 于是有两种可能：
//   A. 这两个按钮**悬停单行才出现**（最可能）
//   B. 它们只在**只有一个节点**时才出现（多节点时列表太挤被折叠了）
//
// 这轮把两种可能分开验：先量出每一行的**精确盒子**，逐行悬停，
// 每次悬停后只读**那一行自己**的 innerText，最后再用「只留一个节点」对照。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchV';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
async function addNodeAt(x, y, item) {
  for (const [dx, dy] of [[0, 0], [0, 90], [0, -90], [90, 0], [-90, 0]]) {
    const ns = await nodeList();
    if (ns.some((n) => x + dx > n.x - 20 && x + dx < n.x + n.w + 20 && y + dy > n.y - 20 && y + dy < n.y + n.h + 20)) continue;
    await page.mouse.dblclick(x + dx, y + dy); await page.waitForTimeout(1000);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N(); await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2200);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
  }
  return false;
}

/**
 * 资产管理抽屉的完整结构：**逐行**给出盒子，而不是把整个列表当成一个元素。
 * 「行」的判据：同一个容器里，文本形如「XX节点 N」且**自己不含第二个节点名**。
 */
const drawerRows = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const drawer = [...document.querySelectorAll('div,aside')].find((x) => {
    const b = x.getBoundingClientRect();
    return b.width > 200 && b.width < 620 && b.height > 200 && /共 \d+ 节点/.test(txt(x)); });
  if (!drawer) return { open: false };
  const db = drawer.getBoundingClientRect();
  // 逐行：叶子级、含节点名、宽接近整行
  const rows = [...drawer.querySelectorAll('div')].filter((e) => {
    const b = e.getBoundingClientRect();
    const t = txt(e);
    return b.width > db.width * 0.5 && b.height >= 18 && b.height <= 70
      && /^(文本|图片|视频|音频|剧本)节点/.test(t) && t.length < 20;
  }).map((e) => { const b = e.getBoundingClientRect();
    return { text: txt(e), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      innerHTML: e.innerHTML.slice(0, 300), childCount: e.children.length }; })
    .sort((a, b) => a.rect[1] - b.rect[1]);
  return { open: true, drawerRect: [Math.round(db.x), Math.round(db.y), Math.round(db.width), Math.round(db.height)],
    drawerText: txt(drawer).slice(0, 300), rows };
});
/** 读某一行自己当前的文案与内部结构（悬停前后对比）。 */
const readRow = (rect) => page.evaluate((r) => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const e = [...document.querySelectorAll('div')].find((d) => {
    const b = d.getBoundingClientRect();
    const t = txt(d);
    return Math.abs(b.x - r[0]) < 3 && Math.abs(b.y - r[1]) < 3 && Math.abs(b.width - r[2]) < 6
      && /^(文本|图片|视频|音频|剧本)节点/.test(t) && t.length < 20; });
  if (!e) return null;
  const b = e.getBoundingClientRect();
  const hit = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
  return { text: txt(e), html: e.innerHTML.slice(0, 400),
    hitTag: hit ? hit.tagName : null, hitCls: hit ? (hit.className || '').toString().slice(0, 34) : null,
    hitText: hit ? txt(hit).slice(0, 20) : null };
}, rect);
async function clickAndRead(fn, wait = 2200) {
  const before = await fingerprint(page);
  await fn(); await page.waitForTimeout(wait);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 36), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 300) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 300) })), pop };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '逐行悬停资产管理抽屉，找「更多操作」；再用单节点对照' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const k of ['文本', '图片']) { const n = await nodeList(); console.log(`建 ${k}:`, await addNodeAt(320 + n.length * 60, 260, k)); }
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
  console.log('节点:', await N());

  const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
  if (!(await opener.count())) throw new Error('找不到资产管理入口');
  await opener.first().click({ timeout: 6000 });
  await page.waitForTimeout(2800);

  // ── V1 两个节点时：逐行悬停
  try {
    let d = await drawerRows();
    if (!d.open || d.drawerRect[3] < 100) {
      await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
      d = await drawerRows();
    }
    console.log('\n抽屉:', JSON.stringify(d.drawerRect), '行数:', d.rows.length);
    for (const r of d.rows) console.log(`  行「${r.text}」 rect=${JSON.stringify(r.rect)}`);

    const tried = [];
    for (const row of d.rows) {
      const before = await readRow(row.rect);
      // 悬停到**这一行**的中心
      const cx = Math.round(row.rect[0] + row.rect[2] / 2);
      const cy = Math.round(row.rect[1] + row.rect[3] / 2);
      await page.mouse.move(cx - 40, cy); await page.waitForTimeout(400);
      await page.mouse.move(cx, cy); await page.waitForTimeout(1800);
      const after = await readRow(row.rect);
      const gotMore = await page.evaluate((r) => {
        const c = [...document.querySelectorAll('div,span,button')].filter((e) => {
          const b = e.getBoundingClientRect();
          return /更多操作|定位到节点/.test((e.innerText || '').trim()) && b.width > 0
            && b.y > r[1] - 12 && b.y < r[1] + r[3] + 12; });
        return c.map((e) => { const b = e.getBoundingClientRect();
          return { t: (e.innerText || '').trim(), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; });
      }, row.rect);
      console.log(`  悬停「${row.text}」(${cx},${cy}) → 行文案「${after?.text}」；命中的按钮 ${JSON.stringify(gotMore)}`);
      console.log(`     命中检测：该点最顶层 = ${after?.hitTag}.${after?.hitCls} 「${after?.hitText}」`);
      tried.push({ row: row.text, rect: row.rect, before, after, gotMore });
      if (gotMore.length) {
        await shot(page, 'M-34-资产管理-悬停单行.png');
        const target = gotMore.find((g) => g.t === '更多操作') || gotMore[0];
        const r = await clickAndRead(async () => { await page.mouse.click(target.x, target.y); });
        await shot(page, 'M-35-更多操作菜单.png');
        await logStep(B, { id: 'V1-more-actions', title: '资产管理：「更多操作」是悬停才出现的',
          target: `悬停第 ${d.rows.indexOf(row) + 1} 行「${row.text}」(${[cx, cy]}) → 点冒出来的「${target.t}」(${target.x},${target.y})`,
          evidence: { drawer: d, tries: tried, fresh: r.fresh, popups: r.pop },
          visible_text: `悬停前该行文案「${before?.text}」→ 悬停后「${after?.text}」；` +
            `同区域出现的按钮 ${JSON.stringify(gotMore)}（**未悬停时 0 个**）；` +
            `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
          shot: 'M-35-更多操作菜单.png' });
        await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
        break;
      }
    }
    if (!tried.some((t) => t.gotMore.length)) {
      await logStep(B, { id: 'V1-more-actions', title: '资产管理「更多操作」', failed: true,
        visible_text: `逐行悬停 ${tried.length} 行都没冒出「更多操作」；每行悬停前文案 ${JSON.stringify(tried.map((t) => t.before?.text))}；` +
          `悬停后 ${JSON.stringify(tried.map((t) => t.after?.text))}；命中检测 ${JSON.stringify(tried.map((t) => [t.after?.hitTag, t.after?.hitText]))}；` +
          `行 HTML 片段 ${JSON.stringify(d.rows.map((r) => r.innerHTML.slice(0, 200)))}` });
    }
  } catch (e) { await logStep(B, { id: 'V1-more-actions', title: '资产管理「更多操作」', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── V2 对照：删到只剩 1 个节点，看按钮会不会出现（区分「悬停」还是「单节点」）
  try {
    await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
    const before = await N();
    // 全选 + 删（焦点先交回画布）
    await page.mouse.click(1380, 300); await page.waitForTimeout(800);
    await page.keyboard.press('Meta+a'); await page.waitForTimeout(900);
    await page.keyboard.press('Backspace'); await page.waitForTimeout(2000);
    const afterN = await N();
    console.log(`\n删除: ${before} → ${afterN} 节点`);
    if (afterN !== 1) {
      // 还剩多个：只留第一个（逐个删）
      for (let k = 0; k < 4 && await N() > 1; k += 1) {
        const ns = await nodeList();
        if (!ns.length) break;
        await page.mouse.click(ns[ns.length - 1].x + 40, ns[ns.length - 1].y + 40);
        await page.waitForTimeout(900);
        await page.keyboard.press('Backspace'); await page.waitForTimeout(1600);
      }
    }
    console.log('删到剩:', await N(), '节点');
    if (await N() === 1) {
      const opener2 = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
      if (await opener2.count()) { await opener2.first().click({ timeout: 6000 }); await page.waitForTimeout(2600); }
      const d1 = await drawerRows();
      console.log('单节点抽屉:', JSON.stringify(d1.drawerText), '行:', JSON.stringify(d1.rows.map((r) => r.text)));
      const hasBtn = await page.evaluate(() => [...document.querySelectorAll('div,span,button')]
        .filter((e) => /更多操作|定位到节点/.test((e.innerText || '').trim()) && e.getBoundingClientRect().width > 0)
        .map((e) => ({ t: (e.innerText || '').trim(), rect: (() => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; })() })));
      console.log('单节点时「更多操作/定位到节点」:', JSON.stringify(hasBtn));
      await shot(page, 'M-36-资产管理-单节点.png');
      await logStep(B, { id: 'V2-single-node', title: '对照：只剩一个节点时，「更多操作」会不会出现',
        target: '把画布删到只剩 1 个节点，再开资产管理抽屉',
        evidence: { nodeCount: await N(), drawerText: d1.drawerText, rows: d1.rows, buttonsFound: hasBtn },
        visible_text: `节点数 ${await N()}；抽屉文本 ${JSON.stringify(d1.drawerText)}；` +
          `找到的「更多操作/定位到节点」${hasBtn.length} 个 ${JSON.stringify(hasBtn)}`,
        shot: 'M-36-资产管理-单节点.png' });
    }
  } catch (e) { await logStep(B, { id: 'V2-single-node', title: '单节点对照', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('最终节点:', await N());
} finally {
  await browser.close();
}
