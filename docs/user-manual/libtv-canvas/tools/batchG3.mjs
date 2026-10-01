// Batch G3 —— 收掉 batchG2 留下的三个不确定点。
//
//   I1 高级设置：G2 读到的节点**串位了**（按 图片 进去，读出来是音频节点的内容），
//      因为 `querySelector('.react-flow__node.selected')` 取的是第一个 selected，
//      而上一轮 Escape 之后画布上可能还留着别的选中态。这次改成**按标题精确定位目标节点**。
//   I2 「添加到工具箱」：G2 点它没有任何弹出内容。怀疑是**静默写入** ——
//      点之前后各数一次工具箱里的条目数，差值就是它到底加没加。
//   I3 「⊞ 布局下拉」：它是无文案元素（w20），G2 的判据没抓到弹层。
//      这次改用 DOM 差集法抓「点开后才出现的东西」，不再猜 class。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchG3';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

const GAP = 40, SAFE_TOP = 90, SAFE_BOTTOM = 720;
function findEmptySpot(list, minX = 120) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = minX; x <= 1300; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return { x: minX, y: SAFE_TOP };
}
async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
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
/** 工具箱里【预设】条目的个数 —— 用它当「有没有被加进去」的探针。 */
const toolboxCount = () => page.evaluate(() =>
  [...new Set((document.body.innerText || '').match(/【预设】[^\n【]*/g) || [])].length);

/** 按标题精确定位某个节点里的叶子元素（组操作条/高级设置都不是 <button>）。 */
function leafInNode(pred, label) {
  return page.evaluate(([src, lb]) => {
    const fn = new Function('t', `return (${src})`);
    const n = [...document.querySelectorAll('.react-flow__node')].find((e) => fn((e.innerText || '').replace(/\s+/g, ' ')));
    if (!n) return { found: false, why: '没找到匹配的节点' };
    const el = [...n.querySelectorAll('div,span')].find((e) => (e.innerText || '').trim() === lb && e.getBoundingClientRect().width > 0);
    if (!el) return { found: false, why: `节点内没有文案为「${lb}」的元素` };
    const b = el.getBoundingClientRect();
    return { found: true, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2), op: +getComputedStyle(el).opacity };
  }, [pred, label]);
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '收尾：按标题精确定位节点读高级设置 / 工具箱条目数探针 / 差集法抓布局下拉' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeSafe('图片');
  await addNodeSafe('视频');
  await addNodeSafe('音频');
  await addNodeSafe('文本');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);
  console.log('节点:', JSON.stringify((await nodesOf()).map((n) => n.title)));

  // ── I1 每一类节点的「高级设置」，按标题精确定位
  for (const [tag, title] of [['图片', '图片节点'], ['视频', '视频节点'], ['音频', '音频节点'], ['文本', '文本节点']]) {
    await safe(`I1-advanced-${tag}`, `${tag}节点的「高级设置」`, `按标题「${title}」精确定位节点 → 点它的「高级设置」`, async () => {
      // 先点画布空白把上一轮的选中态清掉，再只点这一个节点
      const spot = findEmptySpot(await nodesOf());
      await page.mouse.click(spot.x, spot.y);
      await page.waitForTimeout(800);
      const beforeSel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
      const list = await nodesOf();
      const t = list.find((n) => n.title.startsWith(title));
      if (!t) throw new Error(`画布上没有「${title}」`);
      await page.mouse.click(t.x + Math.min(80, t.w / 2), t.y + 12);
      await page.waitForTimeout(1500);
      const selTitle = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        return n ? (n.innerText || '').replace(/\s+/g, ' ').slice(0, 20) : null;
      });
      const h0 = await page.evaluate((ti) => {
        const n = [...document.querySelectorAll('.react-flow__node')].find((e) => (e.innerText || '').startsWith(ti));
        return n ? Math.round(n.getBoundingClientRect().height) : null;
      }, title);
      const adv = await leafInNode(`t.startsWith(${JSON.stringify(title)})`, '高级设置');
      if (!adv.found) {
        await logStep(B, { id: `I1-advanced-${tag}`, title: `${tag}节点的「高级设置」`, target: `按标题「${title}」定位`,
          evidence: { selectedNode: selTitle, beforeSelectedCount: beforeSel, hasAdvancedButton: false, why: adv.why, nodeText: await page.evaluate((ti) => {
            const n = [...document.querySelectorAll('.react-flow__node')].find((e) => (e.innerText || '').startsWith(ti));
            return n ? (n.innerText || '').replace(/\s+/g, ' ').slice(0, 400) : null;
          }, title) },
          visible_text: `该节点上没有「高级设置」：${adv.why}` });
        return;
      }
      await page.mouse.click(adv.x, adv.y);
      await page.waitForTimeout(2200);
      const after = await page.evaluate((ti) => {
        const n = [...document.querySelectorAll('.react-flow__node')].find((e) => (e.innerText || '').startsWith(ti));
        if (!n) return null;
        return { text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 900), h: Math.round(n.getBoundingClientRect().height),
          sliders: n.querySelectorAll('[role="slider"]').length,
          numbers: n.querySelectorAll('input[type="text"]').length,
          labels: [...n.querySelectorAll('[role="slider"]')].map((s) => {
            const lab = s.closest('div')?.parentElement?.innerText || '';
            return (lab || '').replace(/\s+/g, ' ').slice(0, 20);
          }).slice(0, 6) };
      }, title);
      await shot(page, `M-04-${tag}节点-高级设置.png`);
      await logStep(B, { id: `I1-advanced-${tag}`, title: `${tag}节点的「高级设置」`, target: `按标题「${title}」定位节点 → 点「高级设置」`,
        evidence: { selectedNode: selTitle, beforeSelectedCount: beforeSel, buttonOpacity: adv.op,
          heightBefore: h0, heightAfter: after?.h, sliders: after?.sliders, numberInputs: after?.numbers,
          sliderContexts: after?.labels, textAfter: after?.text },
        visible_text: `选中的是 ${JSON.stringify(selTitle)}；高度 ${h0} → ${after?.h}；滑杆 ${after?.sliders} 个 + 数字输入框 ${after?.numbers} 个；节点文本 ${JSON.stringify(after?.text?.slice(0, 400))}`,
        shot: `M-04-${tag}节点-高级设置.png` });
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(900);
    });
  }

  // ── I2 「添加到工具箱」：用工具箱条目数当探针
  await safe('I2-add-to-toolbox', '组操作条「添加到工具箱」', '点之前后各数一次工具箱里的【预设】条目数', async () => {
    const plain = (await nodesOf()).filter((n) => !n.isGroup);
    const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
    const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
    await page.keyboard.down('Shift');
    await page.mouse.move(40, 80); await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1400);
    const picked = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);

    // 先开一次工具箱记基线
    await page.getByRole('button', { name: '素材库', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(1800);
    await page.getByText('打开工具箱', { exact: true }).first().click({ timeout: 5000 });
    await page.waitForTimeout(2600);
    const base = await toolboxCount();
    const baseNames = await page.evaluate(() => [...new Set((document.body.innerText || '').match(/【预设】[^\n【]*/g) || [])].slice(0, 30));
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);

    // 回到画布，成组仍应选中，点「添加到工具箱」
    const btn = await leafInNode(`/^整组执行/.test(t)`, '添加到工具箱');
    let clicked = false; let pop = null;
    if (btn.found) {
      const fpBefore = await fingerprint(page);
      await page.mouse.click(btn.x, btn.y);
      await page.waitForTimeout(2600);
      clicked = true;
      const after = await fingerprint(page);
      const fresh = diffPanels(fpBefore, after);
      pop = fresh.length ? fresh.map((f) => f.all.slice(0, 200)) : null;
    }
    // 再开工具箱看条目数有没有变
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(800);
    await page.getByRole('button', { name: '素材库', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(1800);
    await page.getByText('打开工具箱', { exact: true }).first().click({ timeout: 5000 });
    await page.waitForTimeout(2600);
    const after2 = await toolboxCount();
    const afterNames = await page.evaluate(() => [...new Set((document.body.innerText || '').match(/【预设】[^\n【]*/g) || [])].slice(0, 30));
    await shot(page, 'M-06-添加到工具箱后.png');
    const added = afterNames.filter((n) => !baseNames.includes(n));
    await logStep(B, { id: 'I2-add-to-toolbox', title: '组操作条「添加到工具箱」', target: '点之前后各数一次工具箱里的【预设】条目数',
      evidence: { selectedBeforeGroup: picked, button: btn, clicked, popover: pop,
        presetsBefore: base, presetsAfter: after2, newlyAdded: added },
      visible_text: `按钮 ${JSON.stringify(btn)}；点击成功 ${clicked}；弹出内容 ${JSON.stringify(pop)}；工具箱条目 ${base} → ${after2}；新增 ${JSON.stringify(added)}`,
      shot: 'M-06-添加到工具箱后.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
  });

  // ── I3 ⊞ 布局下拉（无文案元素，用差集法抓）
  await safe('I3-layout-dropdown', '组操作条 ⊞ 布局下拉', '点组操作条上「整组执行」左边那枚无文案小按钮，用差集法抓弹层', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(800);
    const g = (await nodesOf()).find((n) => n.isGroup);
    if (!g) throw new Error('画布上没有组');
    await page.mouse.click(Math.max(30, Math.min(1400, g.x + 60)), Math.max(100, g.y + 40));
    await page.waitForTimeout(1400);
    const target = await page.evaluate(() => {
      const gEl = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!gEl) return { found: false, why: '没有组节点' };
      const r = gEl.getBoundingClientRect();
      // 「整组执行」的坐标已知，取它左边最近的、小于 40px 的无文案元素 = 布局下拉
      const run = [...gEl.querySelectorAll('div,span')].find((e) => (e.innerText || '').trim() === '整组执行');
      if (!run) return { found: false, why: '找不到「整组执行」' };
      const rb = run.getBoundingClientRect();
      const cands = [...gEl.querySelectorAll('div,span')].map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.innerText || '').trim(), x: b.x + b.width / 2, y: b.y + b.height / 2, w: b.width, h: b.height,
          left: b.x + b.width < rb.x + 1 }; })
        .filter((c) => c.left && c.w > 4 && c.w < 40 && c.h > 4 && c.h < 40 && c.y < r.y + 60)
        .sort((a, b) => b.x - a.x);
      const c = cands[0];
      if (!c) return { found: false, why: '「整组执行」左边没有小尺寸候选' };
      return { found: true, x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.w), candidates: cands.length };
    });
    if (!target.found) throw new Error(target.why);
    const fpBefore = await fingerprint(page);
    await page.mouse.click(target.x, target.y);
    await page.waitForTimeout(2200);
    const fresh = diffPanels(fpBefore, await fingerprint(page));
    const body = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 500));
    await shot(page, 'M-08-组操作条-布局下拉.png');
    await logStep(B, { id: 'I3-layout-dropdown', title: '组操作条 ⊞ 布局下拉', target: '点「整组执行」左边那枚无文案小按钮',
      evidence: { target, newPanels: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 200), buttons: f.buttons })), bodyText: body },
      visible_text: `目标 ${JSON.stringify(target)}；新出现的面板 ${JSON.stringify(fresh.map((f) => f.all.slice(0, 200)))}`,
      shot: 'M-08-组操作条-布局下拉.png' });
  });

  console.log('\n最终节点:', JSON.stringify((await nodesOf()).map((n) => n.title)));
} finally {
  await browser.close();
}
