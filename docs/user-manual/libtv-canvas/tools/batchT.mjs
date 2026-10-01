// Batch T —— 收掉 Batch S 剩下的三件事。
//
// batchS 的收获比预想大：
//   · 故事板**有内容时**是三列：文本列「文本节点 1」；图片列「待确认后生成」占位 +
//     `Lib Image 2.5 Pro` 模型标签；视频列带「全部」筛选 + `2.0` 标签。
//     手册原话「三列空状态」只是**空画布**的情形，需要改写。
//   · 意外撞开一个从没打开过的面板：右侧「新对话」浮层 = **TV Director 面板**，
//     四个入口 + 底栏「全能创作 ▾」，底部还挂着「故事板 正在跟随 / 按 ESC 退出」。
//     也就是说**点「故事板」会连带把 TV Director 拉出来跟着你**。
//
// 这轮补三件事：
//   T1 关掉 Director 浮层，重拍一张干净的故事板三列图
//   T2 TV Director 面板单独拍一张（只读，绝不点那四个入口 —— 会派发任务）
//   T3 batchS 失败的两个：「更多操作」菜单、「从生成历史选择」
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchT';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
async function addNodeAt(x, y, item) {
  for (const [dx, dy] of [[0, 0], [0, 80], [0, -80], [80, 0], [-80, 0], [0, 160], [0, -160]]) {
    const nodes = await nodeList();
    // 别往节点上放
    if (nodes.some((n) => x + dx > n.x - 20 && x + dx < n.x + n.w + 20 && y + dy > n.y - 20 && y + dy < n.y + n.h + 20)) continue;
    await page.mouse.dblclick(x + dx, y + dy); await page.waitForTimeout(1000);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const before = await N();
      await it.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(2200);
      if (await N() > before) return true;
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(600);
  }
  return false;
}
/** TV Director 浮层的完整读数。 */
const director = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const hit = [...document.querySelectorAll('div,aside,section')].find((d) => {
    const b = d.getBoundingClientRect();
    return b.width > 280 && b.width < 760 && b.height > 400 && /TV Director/.test(txt(d));
  });
  if (!hit) return null;
  const b = hit.getBoundingClientRect();
  return {
    rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
    text: txt(hit).slice(0, 500),
    cls: (hit.className || '').toString().slice(0, 60),
    entries: [...hit.querySelectorAll('div,button,span')].map((e) => (e.innerText || '').trim())
      .filter((t) => t && t.length <= 24 && !t.includes('让 TV Director')).slice(0, 26),
  };
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
  await beginBatch(B, { note: '干净故事板图 + TV Director 面板 + 更多操作 + 从生成历史选择' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const kind of ['文本', '图片', '视频']) {
    const n = await nodeList();
    console.log(`建 ${kind}:`, await addNodeAt(300 + n.length * 60, 260, kind));
  }
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
  const wfNodes = await nodeList();
  console.log('工作流态:', JSON.stringify(wfNodes.map((n) => n.title)));

  // ── T1 故事板：先切过去，Director 浮层可能在，切回工作流再切一次看它跟不跟
  const sb = page.getByRole('button', { name: '故事板', exact: true });
  if (await sb.count()) { await sb.first().click(); await page.waitForTimeout(3200); }
  const d1 = await director();
  console.log('\n切故事板后 Director 在吗:', d1 ? '在' : '不在', d1 ? JSON.stringify(d1.rect) : '');
  // 关掉 Director 浮层（点它右上角的「—」最小化，或按它自己说的 ESC）
  if (d1) {
    const minus = await page.evaluate((r) => {
      const c = [...document.querySelectorAll('button,div,svg')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width >= 10 && b.width <= 30 && b.height >= 10 && b.height <= 30
          && b.x > r[0] + r[2] - 70 && b.x < r[0] + r[2] + 5 && b.y > r[1] - 5 && b.y < r[1] + 60;
      });
      const el = c[c.length - 1]; if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
    }, d1.rect);
    console.log('收起按钮:', JSON.stringify(minus));
    if (minus) { await page.mouse.click(minus.x, minus.y); await page.waitForTimeout(1800); }
  }
  const d2 = await director();
  console.log('收起后 Director:', d2 ? '还在' : '已收起');
  await shot(page, 'M-29-故事板模式-有内容.png');
  const cols = await page.evaluate(() => {
    const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    const heads = ['文本', '图片', '视频'].map((h) => {
      const e = [...document.querySelectorAll('div,span,h1,h2,h3')].find((x) => txt(x) === h && x.getBoundingClientRect().width < 80);
      if (!e) return null;
      let col = e.parentElement;
      for (let i = 0; i < 6 && col; i += 1) { if (col.getBoundingClientRect().width > 200) break; col = col.parentElement; }
      const b = col ? col.getBoundingClientRect() : null;
      return { head: h, colRect: b ? [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] : null,
        colText: col ? txt(col).slice(0, 200) : null };
    });
    return heads;
  });
  console.log('三列:', JSON.stringify(cols, null, 1));
  await logStep(B, { id: 'T1-storyboard-clean', title: '故事板三列（有内容，Director 已收起）',
    target: '建 文本/图片/视频 后切故事板，收起右侧 Director 浮层再拍',
    evidence: { workflowNodes: wfNodes.map((n) => n.title), directorOnEnter: d1, directorAfterClose: d2, columns: cols },
    visible_text: `切到故事板时 TV Director 浮层${d1 ? '会跟着弹出' : '没有弹出'}（框 ${JSON.stringify(d1?.rect)}）；` +
      `收起后再看：${d2 ? '仍在' : '已收起'}。三列 ${JSON.stringify(cols.map((c) => c && [c.head, c.colRect, c.colText?.slice(0, 60)]))}`,
    shot: 'M-29-故事板模式-有内容.png' });

  // 切回工作流
  const wf = page.getByRole('button', { name: '工作流', exact: true });
  if (await wf.count()) { await wf.first().click(); await page.waitForTimeout(2600); }
  console.log('切回工作流, 节点:', await N());

  // ── T2 TV Director 面板：单独读一遍 + 截图（只读，不点任何入口）
  try {
    const d = await director();
    if (d) {
      await shot(page, 'M-33-TV-Director-面板.png');
      await logStep(B, { id: 'T2-director', title: 'TV Director 面板完整界面（只读）',
        target: '故事板态下右侧浮层「新对话」',
        evidence: d,
        visible_text: `面板框 ${JSON.stringify(d.rect)}，class ${d.cls}；正文 ${JSON.stringify(d.text)}；` +
          `内部可读文案 ${JSON.stringify(d.entries)}`,
        shot: 'M-33-TV-Director-面板.png' });
    } else {
      await logStep(B, { id: 'T2-director', title: 'TV Director 面板', failed: true, visible_text: '页面上找不到含「TV Director」的浮层' });
    }
  } catch (e) { await logStep(B, { id: 'T2-director', title: 'TV Director 面板', failed: true, visible_text: String(e).slice(0, 200) }); }

  // ── T3a 资产管理「更多操作」
  try {
    const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
    if (!(await opener.count())) throw new Error('找不到资产管理入口');
    await opener.first().click({ timeout: 6000 });
    await page.waitForTimeout(2600);
    const drawer = await page.evaluate(() => {
      const txt = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim();
      const d = [...document.querySelectorAll('div,aside')].find((x) => /共 \d+ 节点/.test(txt(x)) || (x.getBoundingClientRect().width > 200 && x.getBoundingClientRect().width < 560 && /定位到节点/.test(txt(x))));
      if (!d) return null;
      const b = d.getBoundingClientRect();
      const more = [...d.querySelectorAll('div,span,button')].filter((e) => txt(e) === '更多操作');
      return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
        text: txt(d).slice(0, 300), moreCount: more.length,
        moreRects: more.slice(0, 3).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }) };
    });
    console.log('\n抽屉:', JSON.stringify(drawer));
    if (!drawer || !drawer.moreCount) throw new Error('抽屉里没有「更多操作」；读到 ' + JSON.stringify(drawer?.text));
    await shot(page, 'M-30-资产管理抽屉.png');
    const m = drawer.moreRects[0];
    const r = await clickAndRead(async () => { await page.mouse.click(Math.round(m[0] + m[2] / 2), Math.round(m[1] + m[3] / 2)); });
    await shot(page, 'M-31-更多操作菜单.png');
    await logStep(B, { id: 'T3a-more-actions', title: '资产管理：每行的「更多操作」菜单里有什么',
      target: `点第一行的「更多操作」(${m[0]},${m[1]})，抽屉里共 ${drawer.moreCount} 处`,
      evidence: { drawer, fresh: r.fresh, popups: r.pop },
      visible_text: `抽屉 ${JSON.stringify(drawer.text)}；点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-31-更多操作菜单.png' });
    await page.mouse.click(1200, 760); await page.waitForTimeout(1200);
  } catch (e) { await logStep(B, { id: 'T3a-more-actions', title: '资产管理「更多操作」菜单', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── T3b 「从生成历史选择」
  try {
    await page.mouse.click(1200, 760); await page.waitForTimeout(1000);
    // 找一个确实没被节点占住的空位
    let spot = null;
    outer: for (let y = 120; y <= 560; y += 20) for (let x = 120; x <= 1100; x += 20) {
      const ns = await nodeList();
      if (!ns.some((n) => x > n.x - 30 && x < n.x + n.w + 30 && y > n.y - 30 && y < n.y + n.h + 30)) { spot = { x, y }; break outer; }
    }
    if (!spot) throw new Error('画布上找不到空位');
    await page.mouse.dblclick(spot.x, spot.y); await page.waitForTimeout(1600);
    const panelText = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' '));
    const has = /从生成历史选择/.test(panelText);
    if (!has) throw new Error('「添加节点」面板里没有「从生成历史选择」；面板文本片段 ' + JSON.stringify(panelText.slice(0, 200)));
    const r = await clickAndRead(async () => {
      await page.getByText('从生成历史选择', { exact: false }).first().click({ timeout: 6000 });
    });
    await shot(page, 'M-32-从生成历史选择.png');
    await logStep(B, { id: 'T3b-history-picker', title: '「从生成历史选择」面板里有什么',
      target: `双击空白 (${spot.x},${spot.y}) → 点「从生成历史选择」`,
      evidence: { fresh: r.fresh, popups: r.pop },
      visible_text: `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-32-从生成历史选择.png' });
  } catch (e) { await logStep(B, { id: 'T3b-history-picker', title: '「从生成历史选择」面板', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
