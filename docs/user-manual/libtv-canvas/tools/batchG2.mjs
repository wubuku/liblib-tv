// Batch G2 —— 重做 batchG 的面板读数。
//
// batchG 的面板其实**全都成功打开了**，但我的读数判据是错的：
// 我拿「页面上面积最大的可见元素」当面板，而 React Flow 的 `.react-flow__viewport`
// 因为带 transform，getBoundingClientRect() 永远巨大 —— 于是每一次读到的都是画布本身。
// 结果就是「截图是对的，文字是错的」。这种错最危险：只看截图会以为没问题。
//
// 这一轮改用 **DOM 差集法**（scenario.mjs 里的 fingerprint + diffPanels）：
// 先拍打开前的指纹，再拍打开后的，只取**新出现**的面板。这才是 batchC 验证过的方法，
// 我不该在 batchG 又退回到「猜最大元素」。
//
// 顺带补两件 batchG 没做成的事：
//   H4 节点里的「高级设置」—— 它不是 <button>，要按文案找 div/span
//   H6 组操作条的「布局下拉」「添加到工具箱」—— 同理
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchG2';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}

/**
 * 建一个节点，但**起手点由程序求解**。
 * 上一版写死 (400,300)/(1000,300) 结果第二个节点没建出来：图片节点宽 622px，
 * 铺到 x=1022，(1000,300) 正好落在它身上，双击打开的是节点编辑区不是「添加节点」面板。
 * 这是同一个坑第三次栽在同一个地方，所以这次不写死坐标。
 */
const GAP = 40, SAFE_TOP = 90, SAFE_BOTTOM = 720;
function findEmptySpot(list, minX = 120) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = minX; x <= 1300; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return { x: minX, y: SAFE_TOP };
}
async function addNodeSafe(item) {
  const spot = findEmptySpot(await nodesOf());
  await addNodeAt(spot.x, spot.y, item);
  return spot;
}
async function safe(id, title, target, fn) {
  try { await fn(); } catch (e) {
    console.log(`  ✗ ${id}: ${String(e).split('\n')[0].slice(0, 160)}`);
    await logStep(B, { id, title, target, failed: true, visible_text: `执行抛错：${String(e).split('\n')[0].slice(0, 300)}` });
  }
}

/**
 * 开面板 → 差集出「新出现的那一块」→ 读它 → 关掉。
 * 返回的是**新面板本身**的读数，不再是「最大的那个元素」。
 */
async function openAndRead(shotFile) {
  const before = await fingerprint(page);
  await page.waitForTimeout(2600);
  const after = await fingerprint(page);
  const fresh = diffPanels(before, after);
  if (shotFile) await shot(page, shotFile);
  return { fresh, top: fresh[0] || null };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: 'DOM 差集法重读 batchG 的面板；补「高级设置」与组操作条菜单' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await safe('H0-setup', '建三个节点', '程序化空位依次建 图片 / 视频 / 音频', async () => {
    const spots = [];
    spots.push(await addNodeSafe('图片'));
    spots.push(await addNodeSafe('视频'));
    spots.push(await addNodeSafe('音频'));
    await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);
    await logStep(B, { id: 'H0-setup', title: '建三个节点', target: '程序化空位依次建 图片 / 视频 / 音频',
      evidence: { spots, nodes: await nodesOf() },
      visible_text: `起手点 ${JSON.stringify(spots)}；节点 ${JSON.stringify((await nodesOf()).map((n) => n.title))}` });
  });
  console.log('节点:', JSON.stringify(await nodesOf()));

  // ── H1 生成历史
  await safe('H1-history', '生成历史面板', '点底部工具条「生成历史」→ DOM 差集', async () => {
    await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 6000 });
    const r = await openAndRead('M-01-生成历史.png');
    await logStep(B, { id: 'H1-history', title: '生成历史面板', target: '点底部工具条「生成历史」',
      evidence: { freshPanels: r.fresh.slice(0, 3).map((p) => ({ sig: p.sig, all: p.all.slice(0, 500), buttons: p.buttons })) },
      visible_text: r.top ? `新面板 ${r.top.sig}；文案 ${JSON.stringify(r.top.all.slice(0, 500))}；按钮 ${JSON.stringify(r.top.buttons)}` : '没有新面板',
      shot: 'M-01-生成历史.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1200);
    await clearToasts(page);
  });

  // ── H2 资产管理（左抽屉）
  await safe('H2-asset-management', '资产管理面板', '点左下角「资产管理」→ DOM 差集', async () => {
    await page.getByRole('button', { name: '资产管理', exact: true }).first().click({ timeout: 6000 });
    const r = await openAndRead('M-02-资产管理.png');
    await logStep(B, { id: 'H2-asset-management', title: '资产管理面板', target: '点左下角「资产管理」→ DOM 差集',
      evidence: { freshPanels: r.fresh.slice(0, 3).map((p) => ({ sig: p.sig, all: p.all.slice(0, 600), buttons: p.buttons })) },
      visible_text: r.top ? `新面板 ${r.top.sig}；文案 ${JSON.stringify(r.top.all.slice(0, 600))}；按钮 ${JSON.stringify(r.top.buttons)}` : '没有新面板',
      shot: 'M-02-资产管理.png' });
    // 「资产」标签也点一下
    const tab = page.getByText('资产', { exact: true }).first();
    if (await tab.count()) {
      await tab.click({ timeout: 4000 }); await page.waitForTimeout(2200);
      const assetTab = await page.evaluate(() => {
        const el = [...document.querySelectorAll('div')].filter((d) => {
          const r = d.getBoundingClientRect();
          return r.width > 200 && r.height > 200 && r.x < 500 && (d.innerText || '').trim().length > 4;
        }).sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
        return el ? { text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 400) } : null;
      });
      await shot(page, 'M-07-资产管理-资产标签.png');
      await logStep(B, { id: 'H2b-asset-tab', title: '资产管理抽屉的「资产」标签', target: '点左抽屉里的「资产」标签',
        evidence: assetTab, visible_text: `「资产」标签内容 ${JSON.stringify(assetTab)}`, shot: 'M-07-资产管理-资产标签.png' });
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
    const back = page.getByRole('button', { name: '收起', exact: false }).first();
    if (await back.count()) { await back.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(1200); }
  });

  // ── H3 小地图（batchG 已坐实，这轮补一张干净的定妆照）
  await safe('H3-minimap', '小地图', '点左下角「切换小地图」', async () => {
    const before = await page.evaluate(() => !!document.querySelector('.react-flow__minimap'));
    await page.getByRole('button', { name: '切换小地图', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2200);
    const after = await page.evaluate(() => {
      const m = document.querySelector('.react-flow__minimap');
      if (!m) return { exists: false };
      const r = m.getBoundingClientRect();
      return { exists: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        minimapNodes: m.querySelectorAll('.react-flow__minimap-node').length,
        viewportBox: m.querySelectorAll('.react-flow__minimap-mask').length,
        cls: (m.className || '').toString().slice(0, 60) };
    });
    await shot(page, 'M-03-小地图.png');
    await logStep(B, { id: 'H3-minimap', title: '小地图', target: '点左下角「切换小地图」',
      evidence: { minimapBefore: before, after },
      visible_text: `点之前有 ${before}；点之后 ${JSON.stringify(after)}`, shot: 'M-03-小地图.png' });
    await page.getByRole('button', { name: '切换小地图', exact: true }).first().click({ timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(1000);
  });

  // ── H4 节点里的「高级设置」（不是 button，按文案找叶子元素）
  for (const nodeLabel of ['图片', '视频', '音频']) {
    await safe(`H4-advanced-${nodeLabel}`, `${nodeLabel}节点的「高级设置」`, `选中${nodeLabel}节点 → 点它的「高级设置」（按文案定位 div/span）`, async () => {
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
      const list = await nodesOf();
      const target = list.find((n) => n.title.includes(nodeLabel));
      if (!target) throw new Error(`画布上没有${nodeLabel}节点`);
      await page.mouse.click(target.x + Math.min(80, target.w / 2), target.y + 12);
      await page.waitForTimeout(1400);
      const before = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        return n ? { text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 400), h: Math.round(n.getBoundingClientRect().height) } : null;
      });
      const adv = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        if (!n) return { found: false, why: '没有选中的节点' };
        const el = [...n.querySelectorAll('div,span')].find((e) => (e.innerText || '').trim() === '高级设置' && e.getBoundingClientRect().width > 0);
        if (!el) return { found: false, why: '节点内没有文案为「高级设置」的元素' };
        const b = el.getBoundingClientRect();
        return { found: true, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
      });
      if (!adv.found) throw new Error(adv.why);
      await page.mouse.click(adv.x, adv.y);
      await page.waitForTimeout(2000);
      const after = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 900), h: Math.round(r.height),
          controls: [...n.querySelectorAll('input,select,textarea,[role="slider"],[role="switch"],[data-switch]')]
            .filter((e) => e.getBoundingClientRect().width > 0)
            .map((e) => ({ tag: e.tagName.toLowerCase(), type: e.getAttribute('type') || e.getAttribute('role') || '',
              t: (e.getAttribute('aria-label') || e.placeholder || e.closest('label')?.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 18) })).slice(0, 20) };
      });
      await shot(page, `M-04-${nodeLabel}节点-高级设置.png`);
      await logStep(B, { id: `H4-advanced-${nodeLabel}`, title: `${nodeLabel}节点的「高级设置」`, target: `选中${nodeLabel}节点 → 点「高级设置」`,
        evidence: { nodeHeightBefore: before?.h, nodeHeightAfter: after?.h, textAfter: after?.text, controls: after?.controls },
        visible_text: `展开后节点高度 ${before?.h} → ${after?.h}；新增控件 ${JSON.stringify(after?.controls)}；节点文本 ${JSON.stringify(after?.text?.slice(0, 400))}`,
        shot: `M-04-${nodeLabel}节点-高级设置.png` });
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(900);
    });
  }

  // ── H5 工具箱
  await safe('H5-toolbox', '我的工具箱', '点「素材库」→「打开工具箱」→ DOM 差集', async () => {
    await page.getByRole('button', { name: '素材库', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2000);
    const opener = page.getByText('打开工具箱', { exact: true }).first();
    if (!(await opener.count())) throw new Error('素材库面板里找不到「打开工具箱」');
    await opener.click({ timeout: 5000 });
    const r = await openAndRead('M-05-工具箱.png');
    // 预设条目名单
    const presets = await page.evaluate(() => {
      const t = (document.body.innerText || '').match(/【预设】[^\n]*/g) || [];
      return [...new Set(t.map((s) => s.trim()))].slice(0, 20);
    });
    await logStep(B, { id: 'H5-toolbox', title: '我的工具箱', target: '点「素材库」→「打开工具箱」',
      evidence: { freshPanels: r.fresh.slice(0, 2).map((p) => ({ sig: p.sig, all: p.all.slice(0, 500), buttons: p.buttons })), presets },
      visible_text: r.top ? `新面板 ${r.top.sig}；文案 ${JSON.stringify(r.top.all.slice(0, 400))}；预设条目 ${JSON.stringify(presets)}` : '没有新面板',
      shot: 'M-05-工具箱.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1200);
  });

  // ── H6 组操作条的「布局下拉」与「添加到工具箱」
  await safe('H6-group-actions', '组操作条「布局下拉」与「添加到工具箱」', '成组后把操作条拆成每一枚叶子元素，逐个点开只读', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
    const plain = (await nodesOf()).filter((n) => !n.isGroup);
    const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
    const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
    await page.keyboard.down('Shift');
    await page.mouse.move(40, 80); await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1300);
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);

    const leaves = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const r = g.getBoundingClientRect();
      return [...g.querySelectorAll('div,span')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 70 && !e.querySelector('div,span');
      }).map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
          x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
          w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity }; })
        .sort((a, b) => a.x - b.x);
    });
    console.log('  操作条叶子元素:', JSON.stringify(leaves));

    const results = [];
    let shotTaken = false;
    for (const c of leaves || []) {
      if (c.w > 200) continue;
      if (c.t === '整组执行') { results.push({ ...c, opened: 'SKIPPED（会跑生成、扣积分）' }); continue; }
      await page.mouse.click(c.x, c.y);
      await page.waitForTimeout(2000);
      const pop = await page.evaluate(() => {
        const els = [...document.querySelectorAll('[role="menu"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"]')]
          .filter((d) => d.getBoundingClientRect().width > 40);
        return els.length ? els[els.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
      });
      results.push({ ...c, opened: pop || '（无弹出内容）' });
      if (pop && !shotTaken) { await shot(page, 'M-06-组操作条-布局下拉.png'); shotTaken = true; }
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(1000);
    }
    await logStep(B, { id: 'H6-group-actions', title: '组操作条「布局下拉」与「添加到工具箱」',
      target: '成组后把操作条拆成每一枚叶子元素，逐个点开只读（跳过「整组执行」）',
      evidence: { leaves, results },
      visible_text: results.map((r) => `${r.t || `(无文案,w${r.w})`}[x=${r.x},op=${r.op}] → ${r.opened}`).join('；'),
      shot: shotTaken ? 'M-06-组操作条-布局下拉.png' : undefined });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
