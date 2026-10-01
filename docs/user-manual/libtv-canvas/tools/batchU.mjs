// Batch U —— 补 batchT 的三个缺口。
//
//  T1 ✅ 故事板三列（干净图已拍到）
//  T2 ❌ 我在**读之前**就把 Director 收起了 —— 顺序写反了，浮层已经不在，当然读不到
//  T3a ❌ 资产管理抽屉量到框是 [0,810,1440,**0**]，高度 0 = **抽屉是收着的**；
//        而且收着的时候行里只有节点名、**没有「更多操作」**
//        —— 印证了 batchG2 的读数：「更多操作」很可能是**悬停某一行才出现**的
//  T3b ❌ 双击后「添加节点」面板没弹出来（点位可能压在节点/面板上）
//
// 这轮：先开 Director 读+拍（再收起），抽屉先确认展开再悬停某行，
// 「从生成历史选择」用「先读页面文本确认面板已开，再点」的方式。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchU';
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
const director = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const hit = [...document.querySelectorAll('div,aside,section')]
    .find((d) => { const b = d.getBoundingClientRect();
      return b.width > 280 && b.width < 760 && b.height > 400 && /TV Director/.test(txt(d)); });
  if (!hit) return null;
  const b = hit.getBoundingClientRect();
  return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
    cls: (hit.className || '').toString().slice(0, 50), text: txt(hit).slice(0, 400),
    entries: [...new Set([...hit.querySelectorAll('div,button,span')].map((e) => (e.innerText || '').trim())
      .filter((t) => t && t.length <= 24 && !/TV Director/.test(t)))] };
});
async function clickAndRead(fn, wait = 2400) {
  const before = await fingerprint(page);
  await fn(); await page.waitForTimeout(wait);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"],[class*="Drawer"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 36), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 320) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 320) })), pop };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先读再收 Director；抽屉悬停出行；添加节点面板先验开没开' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const k of ['文本', '图片', '视频']) { const n = await nodeList(); console.log(`建 ${k}:`, await addNodeAt(300 + n.length * 60, 260, k)); }

  // ── U1 先切故事板 → 先读 Director → 拍图 → 再收起
  const sb = page.getByRole('button', { name: '故事板', exact: true });
  if (await sb.count()) { await sb.first().click(); await page.waitForTimeout(3400); }
  const d = await director();
  if (d) {
    await shot(page, 'M-33-TV-Director-面板.png');
    await logStep(B, { id: 'U1-director', title: 'TV Director 面板完整界面（只读，一个入口都没点）',
      target: '切到故事板后右侧滑出的「新对话」浮层',
      evidence: d,
      visible_text: `浮层框 ${JSON.stringify(d.rect)}，class ${d.cls}；正文 ${JSON.stringify(d.text)}；` +
        `内部文案去重后 ${JSON.stringify(d.entries)}`,
      shot: 'M-33-TV-Director-面板.png' });
    console.log('Director 读数:', JSON.stringify(d.rect), d.entries.join(' / '));
  } else {
    await logStep(B, { id: 'U1-director', title: 'TV Director 面板', failed: true, visible_text: '切故事板后没找到含「TV Director」的浮层' });
  }
  // 收起
  if (d) {
    const minus = await page.evaluate((r) => {
      const c = [...document.querySelectorAll('button,div,svg')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width >= 10 && b.width <= 30 && b.height >= 10 && b.height <= 30
          && b.x > r[0] + r[2] - 70 && b.x < r[0] + r[2] + 5 && b.y > r[1] - 5 && b.y < r[1] + 60; });
      const el = c[c.length - 1]; if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
    }, d.rect);
    if (minus) { await page.mouse.click(minus.x, minus.y); await page.waitForTimeout(1800); }
    console.log('收起后还在吗:', (await director()) ? '还在' : '已收起');
  }
  const wf = page.getByRole('button', { name: '工作流', exact: true });
  if (await wf.count()) { await wf.first().click(); await page.waitForTimeout(2600); }
  console.log('切回工作流, 节点:', await N());

  // ── U2 资产管理：确认抽屉**真的展开**了，再悬停某一行找「更多操作」
  try {
    const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
    if (!(await opener.count())) throw new Error('找不到资产管理入口');
    await opener.first().click({ timeout: 6000 });
    await page.waitForTimeout(2800);
    let drawer = await page.evaluate(() => {
      const txt = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim();
      const d = [...document.querySelectorAll('div,aside')].find((x) => {
        const b = x.getBoundingClientRect();
        return b.width > 200 && b.width < 620 && b.height > 200 && /共 \d+ 节点/.test(txt(x)); });
      if (!d) return null;
      const b = d.getBoundingClientRect();
      return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], text: txt(d).slice(0, 320) };
    });
    console.log('\n抽屉一次点击后:', JSON.stringify(drawer));
    if (!drawer || drawer.rect[3] < 100) {
      console.log('  抽屉没收开，再点一次');
      await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
      drawer = await page.evaluate(() => {
        const txt = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim();
        const d = [...document.querySelectorAll('div,aside')].find((x) => {
          const b = x.getBoundingClientRect();
          return b.width > 200 && b.width < 620 && b.height > 200 && /共 \d+ 节点/.test(txt(x)); });
        if (!d) return null;
        const b = d.getBoundingClientRect();
        return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], text: txt(d).slice(0, 320) };
      });
      console.log('  两次点击后:', JSON.stringify(drawer));
    }
    if (!drawer) throw new Error('资产管理抽屉始终没出现');
    await shot(page, 'M-30-资产管理抽屉.png');

    // 悬停第一行节点名，看「更多操作」是否冒出来
    const row = await page.evaluate(() => {
      const txt = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim();
      const c = [...document.querySelectorAll('div')].find((x) => {
        const b = x.getBoundingClientRect();
        return b.width > 200 && b.width < 620 && b.height > 200 && /共 \d+ 节点/.test(txt(x)); });
      if (!c) return null;
      const hit = [...c.querySelectorAll('div,span')].find((e) => /^(文本|图片|视频|音频)节点/.test(txt(e)) && txt(e).length < 14);
      if (!hit) return null;
      const b = hit.getBoundingClientRect();
      return { text: txt(hit), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
    });
    console.log('  目标行:', JSON.stringify(row));
    if (!row) throw new Error('找不到节点行');
    await page.mouse.move(row.x, row.y); await page.waitForTimeout(1600);
    const afterHover = await page.evaluate(() => {
      const more = [...document.querySelectorAll('div,span,button')].filter((e) => (e.innerText || '').trim() === '更多操作' && e.getBoundingClientRect().width > 0);
      return { count: more.length, rects: more.slice(0, 3).map((e) => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; }) };
    });
    console.log('  悬停后「更多操作」:', JSON.stringify(afterHover));
    await shot(page, 'M-30b-资产管理-悬停行.png');
    if (!afterHover.count) throw new Error('悬停后仍没有「更多操作」；读到 ' + JSON.stringify(afterHover));
    const m = afterHover.rects[0];
    const r = await clickAndRead(async () => { await page.mouse.click(Math.round(m[0] + m[2] / 2), Math.round(m[1] + m[3] / 2)); });
    await shot(page, 'M-31-更多操作菜单.png');
    await logStep(B, { id: 'U2-more-actions', title: '资产管理：每行的「更多操作」菜单里有什么',
      target: `悬停节点行「${row.text}」→ 点冒出来的「更多操作」(${m[0]},${m[1]})`,
      evidence: { drawer, row, afterHover, fresh: r.fresh, popups: r.pop },
      visible_text: `抽屉 ${JSON.stringify(drawer.text)}；悬停前「更多操作」0 处 → 悬停后 ${afterHover.count} 处（**它只在悬停时出现**）；` +
        `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-31-更多操作菜单.png' });
    await page.mouse.click(1250, 780); await page.waitForTimeout(1200);
  } catch (e) { await logStep(B, { id: 'U2-more-actions', title: '资产管理「更多操作」菜单', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── U3 「从生成历史选择」：**先确认面板开了**，再点
  try {
    await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
    let spot = null;
    for (let y = 110; y <= 540 && !spot; y += 20) for (let x = 130; x <= 1150; x += 20) {
      const ns = await nodeList();
      if (!ns.some((n) => x > n.x - 40 && x < n.x + n.w + 40 && y > n.y - 40 && y < n.y + n.h + 40)) { spot = { x, y }; break; }
    }
    if (!spot) throw new Error('画布上找不到空位');
    // 连点两次双击，直到页面出现「添加资源」或节点数变化
    let opened = false;
    for (let k = 0; k < 4; k += 1) {
      await page.mouse.dblclick(spot.x, spot.y + k * 30);
      await page.waitForTimeout(1500);
      if (await page.evaluate(() => /添加资源|从生成历史选择|自由生成节点/.test(document.body.innerText || ''))) { opened = true; break; }
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
    }
    const bodyNow = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' '));
    console.log('\n双击后页面片段:', JSON.stringify(bodyNow.slice(0, 260)));
    if (!/从生成历史选择/.test(bodyNow)) throw new Error('「添加节点」面板始终没出现（opened=' + opened + '）');
    const r = await clickAndRead(async () => { await page.getByText('从生成历史选择', { exact: false }).first().click({ timeout: 6000 }); });
    await shot(page, 'M-32-从生成历史选择.png');
    await logStep(B, { id: 'U3-history-picker', title: '「从生成历史选择」面板里有什么',
      target: `双击空白 (${spot.x},${spot.y}) → 点「从生成历史选择」`,
      evidence: { pageBefore: bodyNow.slice(0, 300), fresh: r.fresh, popups: r.pop },
      visible_text: `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-32-从生成历史选择.png' });
  } catch (e) { await logStep(B, { id: 'U3-history-picker', title: '「从生成历史选择」面板', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
