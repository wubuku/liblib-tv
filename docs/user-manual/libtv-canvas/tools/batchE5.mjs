// Batch E5 —— 收尾取证：把组操作条拍全、读出它的真实 DOM 结构，并复现「当前视窗没有节点」。
//
// batchE4b 留下的三个洞：
//   1. K-03 是在 201% 缩放下拍的，组操作条整条顶出画面，配图不可用；
//   2. 组操作条的按钮**不是 <button>**（读 button 得到空数组），所以 ⌘⌥G / ⊞ 下拉都没点到；
//   3. G6 想靠 Space 拖把视口甩远，但 G2 把缩放放大到 201%，节点铺满全屏，
//      findEmptySpot 找不到空白点，14 轮全是 vpDelta [0,0] —— 那不是「拖不动」，是**没拖到空白上**。
//
// 顺序很关键：这一轮一开始就先 ⌘0 复位，再往下走。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE5';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
const sel = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const vp = () => page.evaluate(() => {
  const s = document.querySelector('.react-flow__viewport')?.style.transform || '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(s);
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : { raw: s || null };
});
const lostPrompt = () => page.evaluate(() => {
  const hit = [...document.querySelectorAll('button,div,span')].find((el) => (el.innerText || '').trim() === '当前视窗没有节点');
  if (!hit || !hit.getBoundingClientRect().width) return null;
  const box = hit.closest('[class*="toast"],[class*="Toast"],[class*="float"],[class*="Float"]') || hit.parentElement;
  return { text: (box.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    buttons: [...box.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 12)) };
});
const GAP = 30, VPW = 1440, VPH = 810, SAFE_TOP = 80, SAFE_BOTTOM = 740;
function findEmptySpot(list) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = 40; x <= VPW - 40; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return null;
}
async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}
async function safe(id, title, target, fn) {
  try { await fn(); } catch (e) {
    console.log(`  ✗ ${id}: ${String(e).split('\n')[0].slice(0, 160)}`);
    await logStep(B, { id, title, target, failed: true, visible_text: `执行抛错：${String(e).split('\n')[0].slice(0, 300)}` });
  }
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '组操作条拍全 + 真实 DOM 结构 + 复现「当前视窗没有节点」；一开始先 ⌘0 复位' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(360, 280, '文本');
  await addNodeAt(1000, 280, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);
  console.log('节点:', JSON.stringify(await nodesOf()), 'vp:', JSON.stringify(await vp()));

  // ── H1 框选配图重拍（这次两张卡都完整在画面里）
  await safe('H1-marquee', 'Shift 拖动框选', '空白起手点按住 Shift 拖出完整包住两个节点的矩形', async () => {
    const list = await nodesOf();
    const x0 = Math.min(...list.map((n) => n.x)) - 14, y0 = Math.min(...list.map((n) => n.y)) - 14;
    const x1 = Math.max(...list.map((n) => n.x + n.w)) + 14, y1 = Math.max(...list.map((n) => n.y + n.h)) + 14;
    const spot = findEmptySpot(list);
    await page.keyboard.down('Shift');
    await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move((spot.x + x0) / 2, spot.y, { steps: 10 });
    await page.mouse.move(x0, (spot.y + y1) / 2, { steps: 10 });
    await page.mouse.move(x1, y1, { steps: 12 });
    await page.waitForTimeout(450);
    await shot(page, 'K-01-Shift拖动框选.png');
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
    await shot(page, 'K-02-框选结果.png');
    await logStep(B, { id: 'H1-marquee', title: 'Shift + 拖动框选',
      target: `起手 (${spot.x},${spot.y})，Shift + 拖到 (${x1},${y1})`,
      evidence: { selectedAfterRelease: await sel(), totalNodes: await N(),
        selectedTitles: await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => (n.innerText || '').replace(/\s+/g, ' ').slice(0, 14))) },
      visible_text: `松开后选中 ${await sel()} 个 / 共 ${await N()} 个`, shot: 'K-01-Shift拖动框选.png' });
  });

  // ── H2 成组，缩到能整条装下操作条，拍一张可用的配图 + 读真实结构
  await safe('H2-group-toolbar', '成组 + 组操作条真实结构', '⌘G 成组后逐个元素读出操作条（不只读 button）', async () => {
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    // 再缩一档，确保组的边框和顶部操作条都完整入画
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(1000);
    const g = (await nodesOf()).find((n) => n.isGroup);
    if (!g) throw new Error('没有生成组节点');
    await shot(page, 'K-03-成组后.png');
    const dom = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const r = g.getBoundingClientRect();
      // 只看组节点顶部 60px 内的可交互元素
      const hdr = [...g.querySelectorAll('*')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.y < r.y + 60;
      }).map((e) => ({ tag: e.tagName.toLowerCase(), t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
        role: e.getAttribute('role'), haspopup: e.getAttribute('aria-haspopup'), disabled: e.disabled === true || e.getAttribute('aria-disabled') === 'true' }))
        .filter((e) => e.t);
      return { groupRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], headerEls: hdr.slice(0, 30) };
    });
    await logStep(B, { id: 'H2-group-toolbar', title: '成组 + 组操作条真实结构', target: '⌘G 成组后，遍历组节点顶部 60px 内的所有元素',
      evidence: { groupNodes: 1, totalNodes: await N(), ...dom },
      visible_text: `组外框 ${JSON.stringify(dom?.groupRect)}；顶部元素 ${JSON.stringify(dom?.headerEls)}`, shot: 'K-03-成组后.png' });
  });

  // ── H3 点 ⊞ 下拉（按读出来的结构点，不靠猜）
  await safe('H3-group-dropdown', '组操作条 ⊞ 下拉', '点组操作条上带下拉箭头的那一枚', async () => {
    const opened = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return { ok: false, why: '没有组节点' };
      const r = g.getBoundingClientRect();
      const cand = [...g.querySelectorAll('*')].find((e) => {
        const b = e.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.y < r.y + 60 && (e.getAttribute('aria-haspopup') || /▾|⌄|▼/.test(e.innerText || ''));
      });
      if (!cand) return { ok: false, why: '顶部 60px 内没有带 aria-haspopup 或下拉箭头的元素' };
      const b = cand.getBoundingClientRect();
      return { ok: true, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        tag: cand.tagName.toLowerCase(), label: (cand.getAttribute('aria-label') || cand.innerText || '').trim().slice(0, 16) };
    });
    if (!opened.ok) throw new Error(opened.why);
    await page.mouse.click(opened.x, opened.y);
    await page.waitForTimeout(1300);
    const menu = await page.evaluate(() => {
      const m = [...document.querySelectorAll('[role="menu"],[class*="Popover"],[class*="Dropdown"]')].filter((d) => d.getBoundingClientRect().width > 40);
      return m.length ? m[m.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
    });
    await shot(page, 'K-09-组操作条下拉.png');
    await logStep(B, { id: 'H3-group-dropdown', title: '组操作条 ⊞ 下拉', target: `点 (${opened.x},${opened.y}) 的「${opened.label}」（${opened.tag}）`,
      evidence: { clicked: opened, openedMenuText: menu }, visible_text: `下拉内容 ${JSON.stringify(menu)}`, shot: 'K-09-组操作条下拉.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(800);
  });

  // ── H4 「转分镜组」：先重新选中组（Escape 会让整条操作条消失），再点
  await safe('H4-to-storyboard-group', '组操作条「转分镜组」', '重新选中组之后点「转分镜组」', async () => {
    const g = (await nodesOf()).find((n) => n.isGroup);
    await page.mouse.click(Math.max(20, Math.min(VPW - 20, g.x + g.w / 2)), Math.max(90, g.y + 90));
    await page.waitForTimeout(1200);
    const vis = await page.evaluate(() => {
      const el = [...document.querySelectorAll('*')].find((b) => (b.innerText || '').trim() === '转分镜组' && b.getBoundingClientRect().width > 0);
      return el ? { found: true, tag: el.tagName.toLowerCase(), y: Math.round(el.getBoundingClientRect().y) } : { found: false };
    });
    const before = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length };
    let clicked = false;
    if (vis.found) {
      await page.evaluate(() => {
        const el = [...document.querySelectorAll('*')].find((b) => (b.innerText || '').trim() === '转分镜组' && b.getBoundingClientRect().width > 0);
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        el.click();
      });
      clicked = true; await page.waitForTimeout(3000);
    }
    const after = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length,
      titles: (await nodesOf()).map((n) => n.title),
      toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
        .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 100))) };
    await shot(page, 'K-10-转分镜组后.png');
    await logStep(B, { id: 'H4-to-storyboard-group', title: '组操作条「转分镜组」', target: '重新选中组之后点「转分镜组」',
      evidence: { visible, clicked, before, after },
      visible_text: `选中组时操作条可见 ${vis.found}；点击成功 ${clicked}；节点 ${before.nodes} → ${after.nodes}；分组 ${before.groups} → ${after.groups}；提示 ${JSON.stringify(after.toast)}`, shot: 'K-10-转分镜组后.png' });
  });

  // ── H5 复现「当前视窗没有节点」：先 ⌘0 复位，再用**确实能平移**的 Space 拖甩远
  await safe('H5-lost-prompt', '「当前视窗没有节点」提示与「返回节点」', '⌘0 复位后，按住 Space 每轮拖 +400px，直到节点全部离开视口', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
    await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1000);
    const trace = [];
    for (let i = 0; i < 16; i += 1) {
      const list = await nodesOf();
      const spot = findEmptySpot(list);
      const v0 = await vp();
      if (!spot) { trace.push({ round: i + 1, skipped: '画面里已无空白点（节点铺满）' }); await page.keyboard.press('Meta+-'); await page.waitForTimeout(800); continue; }
      await page.keyboard.down('Space'); await page.waitForTimeout(120);
      await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(120);
      await page.mouse.move(spot.x + 200, spot.y, { steps: 12 });
      await page.mouse.move(spot.x + 420, spot.y, { steps: 12 });
      await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(900);
      const v1 = await vp();
      const on = list.filter((n) => n.x + n.w > 0 && n.x < VPW && n.y + n.h > 0 && n.y < VPH).length;
      trace.push({ round: i + 1, spot, vpDelta: [+(v1.x - v0.x).toFixed(1), +(v1.y - v0.y).toFixed(1)],
        domNodes: await N(), nodesOnScreen: on, prompt: (await lostPrompt()) ? '当前视窗没有节点' : null });
      if (trace[trace.length - 1].prompt) break;
    }
    const got = await lostPrompt();
    await shot(page, 'K-06-当前视窗没有节点.png');
    let back = null;
    if (got) {
      await page.getByRole('button', { name: '返回节点', exact: true }).first().click({ timeout: 5000 })
        .catch((e) => console.log('  点「返回节点」失败:', String(e).split('\n')[0].slice(0, 100)));
      await page.waitForTimeout(2600);
      back = { zoom: (await vp()).z, domNodes: await N(), prompt: (await lostPrompt()) ? '还在' : null };
    }
    await logStep(B, { id: 'H5-lost-prompt', title: '「当前视窗没有节点」提示与「返回节点」', target: '⌘0 复位后按住 Space 每轮拖 +420px，最多 16 轮',
      evidence: { trace, promptShown: got, afterClickingBack: back },
      visible_text: `轨迹 ${JSON.stringify(trace)}；提示 ${JSON.stringify(got)}；点「返回节点」后 ${JSON.stringify(back)}`, shot: 'K-06-当前视窗没有节点.png' });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
