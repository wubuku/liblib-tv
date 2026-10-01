// Batch S —— 三个「面板开着但内容从没打开过」的缺口，一次补齐。
//
//  1. **故事板模式带内容**。`storyboard-mode.md` 整页是在**空画布**上写的，
//     所以「三列空状态」是坐实的，可「有节点时三列各显示什么」从来没验过。
//     这是故事板唯一的实际用法，必须补。
//
//  2. **资产管理抽屉每行的「更多操作」**。正文写着「📖 内容未打开」，
//     就是一个 `…` 菜单，点开读一下即可，不碰任何写操作。
//
//  3. **「从生成历史选择」**。正文只说「复用以前生成过的东西」，
//     面板本身长什么样、有没有内容、能不能点，全是推断。
//
// 三个都只读：打开面板 → 读文案 → 关掉，不触发任何生成、删除、上传。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchS';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

/** 双击空白 → 点类型。换位重试，以「节点数真的变了」为准（batchP3 的教训）。 */
async function addNodeAt(x, y, item) {
  for (const [dx, dy] of [[0, 0], [0, 80], [0, -80], [80, 0], [-80, 0], [0, 160]]) {
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

/** 点「更多操作 / 从生成历史选择 / 模式切换」之后，抓点开后才出现的面板（DOM 差集）。 */
async function clickAndRead(targetFn, wait = 2400) {
  const before = await fingerprint(page);
  await targetFn();
  await page.waitForTimeout(wait);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"],[class*="Drawer"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 36), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 320) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 320) })), pop };
}
/** 点空白把浮层收掉（不按 Esc —— 会触发画布行为）。 */
const dismiss = async () => { await page.mouse.click(1385, 770); await page.waitForTimeout(1200); };

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '故事板带内容 + 更多操作菜单 + 从生成历史选择' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);

  // ── S1 故事板模式：有内容时长什么样
  try {
    for (const kind of ['文本', '图片', '视频']) {
      const s = await nodeList();
      const spot = { x: 300 + s.length * 40, y: 200 };
      const ok = await addNodeAt(spot.x, spot.y, kind);
      console.log(`建 ${kind} 节点: ${ok}`);
    }
    await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
    const list = await nodeList();
    console.log('工作流态节点:', JSON.stringify(list));

    const storyboard = page.getByRole('button', { name: '故事板', exact: true });
    const has = await storyboard.count();
    if (!has) throw new Error('顶栏找不到「故事板」按钮');
    await storyboard.first().click();
    await page.waitForTimeout(3000);
    await shot(page, 'M-29-故事板模式-有内容.png');
    const sb = await page.evaluate(() => {
      const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
      // 故事板三列：找含「文本」「图片」「视频」表头的容器
      const cols = [...document.querySelectorAll('div')].filter((d) => {
        const b = d.getBoundingClientRect();
        if (b.width < 120 || b.height < 200) return false;
        const t = txt(d);
        return /文本/.test(t) && /图片/.test(t) && /视频/.test(t) && t.length < 900;
      }).map((d) => { const b = d.getBoundingClientRect();
        return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], text: txt(d).slice(0, 400) }; })
        .sort((a, b) => a.text.length - b.text.length);
      return {
        nodeCount: document.querySelectorAll('.react-flow__node').length,
        columns: cols.slice(0, 2),
        bodyHasPlaceholder: /暂无/.test(document.body.innerText || ''),
        bodySnippet: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 400),
      };
    });
    console.log('\n故事板态:', JSON.stringify(sb, null, 1));
    await logStep(B, { id: 'S1-storyboard', title: '故事板模式：有内容时三列各显示什么',
      target: '建 文本/图片/视频 三个节点后，点顶栏「故事板」',
      evidence: { workflowNodes: list, storyboard: sb },
      visible_text: `工作流态节点 ${list.length} 个 ${JSON.stringify(list.map((n) => n.title))}；` +
        `切到故事板后：react-flow 节点数 ${sb.nodeCount}（故事板不是节点画布）；` +
        `三列容器 ${JSON.stringify(sb.columns.map((c) => c.rect))}；是否出现「暂无」空态 ${sb.bodyHasPlaceholder}；` +
        `页面文本 ${JSON.stringify(sb.bodySnippet)}`,
      shot: 'M-29-故事板模式-有内容.png' });
  } catch (e) { await logStep(B, { id: 'S1-storyboard', title: '故事板模式（有内容）', failed: true, visible_text: String(e).slice(0, 300) }); }

  // 切回工作流，后面的取证要在节点画布上做
  try {
    const wf = page.getByRole('button', { name: '工作流', exact: true });
    if (await wf.count()) { await wf.first().click(); await page.waitForTimeout(2600); }
    console.log('切回工作流后节点数:', await N());
  } catch (e) { console.log('切回工作流失败:', String(e).slice(0, 120)); }

  // ── S2 资产管理抽屉：每行的「更多操作」菜单
  try {
    const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
    if (!(await opener.count())) throw new Error('找不到资产管理入口');
    await opener.first().click({ timeout: 6000 });
    await page.waitForTimeout(2400);
    await shot(page, 'M-30-资产管理抽屉.png');
    const more = page.getByText('更多操作', { exact: true });
    const n = await more.count();
    if (!n) throw new Error('抽屉里没有「更多操作」');
    const r = await clickAndRead(async () => { await more.first().click({ timeout: 6000 }); });
    await shot(page, 'M-31-更多操作菜单.png');
    await logStep(B, { id: 'S2-more-actions', title: '资产管理：每行的「更多操作」菜单里有什么',
      target: `点「更多操作」（共 ${n} 行，取第一行）`,
      evidence: { rowsWithMore: n, fresh: r.fresh, popups: r.pop },
      visible_text: `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-31-更多操作菜单.png' });
    await dismiss();
  } catch (e) { await logStep(B, { id: 'S2-more-actions', title: '资产管理「更多操作」菜单', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── S3 「从生成历史选择」面板
  try {
    await dismiss();
    await addNodeAt(600, 400, '文本');
    await page.mouse.dblclick(700, 300); await page.waitForTimeout(1400);
    const addRes = page.getByText('从生成历史选择', { exact: false }).first();
    if (!(await addRes.count())) throw new Error('「添加节点」面板里没有「从生成历史选择」');
    const r = await clickAndRead(async () => { await addRes.click({ timeout: 6000 }); });
    await shot(page, 'M-32-从生成历史选择.png');
    await logStep(B, { id: 'S3-history-picker', title: '「从生成历史选择」面板里有什么',
      target: '双击画布 → 点添加资源分区的「从生成历史选择」',
      evidence: { fresh: r.fresh, popups: r.pop },
      visible_text: `点开弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}`,
      shot: 'M-32-从生成历史选择.png' });
  } catch (e) { await logStep(B, { id: 'S3-history-picker', title: '「从生成历史选择」面板', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
