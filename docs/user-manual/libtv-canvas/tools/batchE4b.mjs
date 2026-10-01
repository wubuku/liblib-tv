// Batch E5 —— 把「平移/缩放到底怎么操作」和组操作条一次坐实。
//
// batchE4 的 F4 给出一个决定性读数：空白处左键拖 300px，视口只动 5.8px，
// 而且**第一步采样之后就冻结**。也就是说默认「移动」工具下，空白处左键拖**不是平移**，
// 实用上就是 no-op —— 克隆仓 CANVAS_NAVIGATION.md 那条记的是对的，
// 是前面几轮把「有一点点位移」误读成了「在平移」。
//
// 这一轮把四种平移方式逐一量出「鼠标位移 vs 视口位移」，外加：
//   · 组操作条的完整文案与 ⊞ 下拉（batchE4 因为 y<150 的过滤把整条操作条切掉了，
//     它其实是**画在组节点内部**的，组节点名叫「Group 1」）；
//   · 点一次「转分镜组」，看 `⌘⌥G 合并分镜组` 到底是什么；
//   · 用真正能平移的方式（Space+拖）把视口甩远，看「当前视窗没有节点」能不能复现。
//
// 安全边界：不点「整组执行」（会触发生成、扣积分）、不按 ⌘Enter。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE4b';
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
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 24) for (let x = 40; x <= VPW - 40; x += 24) {
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
/** 统一的「拖一段并量出视口位移」探针。 */
async function panProbe(label, before, act) {
  const v0 = await vp();
  const spot = findEmptySpot(await nodesOf());
  await act(spot, 220, 120);
  await page.waitForTimeout(1000);
  const v1 = await vp();
  return { label, startPoint: spot, mouseDelta: [220, 120], zoom: v0.z,
    viewportDelta: [+(v1.x - v0.x).toFixed(2), +(v1.y - v0.y).toFixed(2)],
    ratio: v0.z ? +((v1.x - v0.x) / 220 / v0.z).toFixed(3) : null };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '四种平移方式逐一量出「鼠标位移 vs 视口位移」+ 组操作条完整文案' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(360, 280, '文本');
  await addNodeAt(1000, 280, '音频');
  await fitView(page, 1); await page.waitForTimeout(1200);
  console.log('节点:', JSON.stringify(await nodesOf()), 'vp:', JSON.stringify(await vp()));

  // ── G1 四种平移方式对照
  await safe('G1-pan-modes', '四种平移方式对照实验', '同一段鼠标位移 (+220,+120)，只改「按什么/点哪里」', async () => {
    const results = [];
    // a) 空白处无修饰键左键拖
    results.push(await panProbe('空白处左键拖（无修饰键）', null, async (s, dx, dy) => {
      await page.mouse.move(s.x, s.y); await page.mouse.down(); await page.waitForTimeout(150);
      await page.mouse.move(s.x + dx / 2, s.y + dy / 2, { steps: 10 });
      await page.mouse.move(s.x + dx, s.y + dy, { steps: 10 });
      await page.waitForTimeout(250); await page.mouse.up();
    }));
    // b) Space + 左键拖
    results.push(await panProbe('Space + 左键拖', null, async (s, dx, dy) => {
      await page.keyboard.down('Space'); await page.waitForTimeout(150);
      await page.mouse.move(s.x, s.y); await page.mouse.down(); await page.waitForTimeout(150);
      await page.mouse.move(s.x + dx / 2, s.y + dy / 2, { steps: 10 });
      await page.mouse.move(s.x + dx, s.y + dy, { steps: 10 });
      await page.waitForTimeout(250); await page.mouse.up(); await page.keyboard.up('Space');
    }));
    // c) 抓手工具 H + 左键拖
    await page.keyboard.press('KeyH'); await page.waitForTimeout(700);
    results.push(await panProbe('抓手工具 H + 左键拖', null, async (s, dx, dy) => {
      await page.mouse.move(s.x, s.y); await page.mouse.down(); await page.waitForTimeout(150);
      await page.mouse.move(s.x + dx / 2, s.y + dy / 2, { steps: 10 });
      await page.mouse.move(s.x + dx, s.y + dy, { steps: 10 });
      await page.waitForTimeout(250); await page.mouse.up();
    }));
    const cursorInGrab = await page.evaluate(() => document.querySelector('.react-flow__pane') ? getComputedStyle(document.querySelector('.react-flow__pane')).cursor : null);
    await page.keyboard.press('KeyV'); await page.waitForTimeout(700);
    // d) 中键拖
    results.push(await panProbe('中键拖', null, async (s, dx, dy) => {
      await page.mouse.move(s.x, s.y); await page.mouse.down({ button: 'middle' }); await page.waitForTimeout(150);
      await page.mouse.move(s.x + dx / 2, s.y + dy / 2, { steps: 10 });
      await page.mouse.move(s.x + dx, s.y + dy, { steps: 10 });
      await page.waitForTimeout(250); await page.mouse.up({ button: 'middle' });
    }));
    await logStep(B, { id: 'G1-pan-modes', title: '四种平移方式对照实验',
      target: '同一段鼠标位移 (+220,+120)，分别用：无修饰键左键拖 / Space+左键拖 / 抓手工具H+左键拖 / 中键拖',
      evidence: { results, cursorOnPaneWhileGrabTool: cursorInGrab,
        reading: 'ratio = 视口位移 ÷ 鼠标位移 ÷ 缩放；≈1 表示严格 1:1 跟手' },
      visible_text: results.map((r) => `${r.label}：视口位移 ${JSON.stringify(r.viewportDelta)}（ratio ${r.ratio}）`).join('；'),
      shot: undefined });
  });

  // ── G2 ⌘ + 滚轮
  await safe('G2-cmd-wheel-zoom', '⌘ + 滚轮缩放', '按住 ⌘ 在画布上滚轮', async () => {
    await fitView(page, 1); await page.waitForTimeout(800);
    const v0 = await vp();
    const spot = findEmptySpot(await nodesOf());
    await page.keyboard.down('Meta');
    await page.mouse.move(spot.x, spot.y);
    await page.mouse.wheel(0, -300);
    await page.waitForTimeout(900);
    await page.mouse.wheel(0, -300);
    await page.waitForTimeout(900);
    await page.keyboard.up('Meta');
    const v1 = await vp();
    const zoomLabel = await page.evaluate(() => {
      const el = [...document.querySelectorAll('button,div,span')].find((e) => /^\d{1,3}%$/.test((e.innerText || '').trim()));
      return el ? el.innerText.trim() : null;
    });
    await logStep(B, { id: 'G2-cmd-wheel-zoom', title: '⌘ + 滚轮缩放', target: '按住 ⌘ 在空白处向上滚两格',
      evidence: { zoomBefore: v0.z, zoomAfter: v1.z, zoomPercentLabel: zoomLabel },
      visible_text: `缩放 ${v0.z} → ${v1.z}；左下角百分比显示 ${JSON.stringify(zoomLabel)}` });
  });

  // ── G3 组操作条：重新成组，读完整文案 + ⊞ 下拉
  await safe('G3-group-toolbar', '组操作条完整文案与 ⊞ 下拉', '⌘G 成组后读组节点内操作条', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    const list = await nodesOf();
    const x0 = Math.min(...list.map((n) => n.x)) - 12, y0 = Math.min(...list.map((n) => n.y)) - 12;
    const x1 = Math.max(...list.map((n) => n.x + n.w)) + 12, y1 = Math.max(...list.map((n) => n.y + n.h)) + 12;
    const spot = findEmptySpot(list);
    await page.keyboard.down('Shift');
    await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1300);
    const picked = await sel();
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    const groups = (await nodesOf()).filter((n) => n.isGroup);
    const bar = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const hdr = [...g.querySelectorAll('button,[role="button"],[role="menuitem"]')].filter((b) => b.getBoundingClientRect().width > 0);
      return {
        groupLabel: (g.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
        buttons: hdr.map((b) => ({ t: (b.getAttribute('aria-label') || b.title || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
          haspopup: b.getAttribute('aria-haspopup'), disabled: b.disabled === true })),
      };
    });
    await shot(page, 'K-03-成组后.png');
    await logStep(B, { id: 'G3-group-toolbar', title: '组操作条完整文案与 ⊞ 下拉', target: `框选 ${picked} 个节点后按 ⌘G，读组节点内的按钮`,
      evidence: { pickedNodes: picked, groupCount: groups.length, groupRect: groups[0] || null, bar },
      visible_text: `组元素 ${groups.length} 个；组名 ${JSON.stringify(bar?.groupLabel)}；操作条按钮 ${JSON.stringify(bar?.buttons)}`, shot: 'K-03-成组后.png' });
  });

  // ── G4 ⊞ 下拉
  await safe('G4-group-dropdown', '组操作条 ⊞ 下拉', '点组操作条上带 aria-haspopup 的按钮', async () => {
    const pop = page.locator('.react-flow__node button[aria-haspopup]').first();
    if (!(await pop.count())) throw new Error('组操作条里没有 aria-haspopup 按钮');
    await pop.click({ timeout: 4000 });
    await page.waitForTimeout(1200);
    const menu = await page.evaluate(() => {
      const m = [...document.querySelectorAll('[role="menu"],[class*="Popover"],[class*="Dropdown"]')]
        .filter((d) => d.getBoundingClientRect().width > 40);
      return m.length ? m[m.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
    });
    await shot(page, 'K-09-组操作条下拉.png');
    await logStep(B, { id: 'G4-group-dropdown', title: '组操作条 ⊞ 下拉', target: '点组操作条上带 aria-haspopup 的按钮',
      evidence: { openedMenuText: menu }, visible_text: `下拉内容 ${JSON.stringify(menu)}`, shot: 'K-09-组操作条下拉.png' });
    await page.keyboard.press('Escape').catch(() => {});
  });

  // ── G5 「转分镜组」：⌘⌥G 合并分镜组到底在说什么
  await safe('G5-to-storyboard-group', '组操作条「转分镜组」', '在组选中状态下点「转分镜组」', async () => {
    // 上一步的 Escape 会让组取消选中、整条操作条消失 —— 先重新选中这个组
    const g = (await nodesOf()).find((n) => n.isGroup);
    if (!g) throw new Error('画布上没有组');
    await page.mouse.click(g.x + 60, g.y + 60);
    await page.waitForTimeout(1000);
    const barVisible = await page.evaluate(() => {
      const el = [...document.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '转分镜组');
      return el ? { found: true, x: Math.round(el.getBoundingClientRect().x), y: Math.round(el.getBoundingClientRect().y) } : { found: false };
    });
    const before = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length };
    let clicked = false;
    if (barVisible.found) {
      await page.getByRole('button', { name: '转分镜组', exact: true }).first().click({ timeout: 4000 });
      clicked = true;
      await page.waitForTimeout(3000);
    }
    const after = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length,
      groupLabel: (await nodesOf()).find((n) => n.isGroup)?.title || null,
      toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
        .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 100))) };
    await shot(page, 'K-10-转分镜组后.png');
    await logStep(B, { id: 'G5-to-storyboard-group', title: '组操作条「转分镜组」', target: '点组操作条的「转分镜组」',
      evidence: { barVisible, clicked, before, after },
      visible_text: `操作条在选中组时可见: ${barVisible.found}；点击成功 ${clicked}；节点 ${before.nodes} → ${after.nodes}；分组 ${before.groups} → ${after.groups}；组名 ${JSON.stringify(after.groupLabel)}；提示 ${JSON.stringify(after.toast)}`,
      shot: 'K-10-转分镜组后.png' });
  });

  // ── G6 用真正能平移的方式把视口甩远，看「当前视窗没有节点」
  await safe('G6-lost-prompt', '「当前视窗没有节点」提示与「返回节点」', '按住 Space 连续把视口拖出所有节点之外', async () => {
    const trace = [];
    for (let i = 0; i < 14 && !(await lostPrompt()); i += 1) {
      const spot = findEmptySpot(await nodesOf()) || { x: 720, y: 400 };
      const v0 = await vp();
      await page.keyboard.down('Space'); await page.waitForTimeout(120);
      await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(120);
      await page.mouse.move(spot.x + 200, spot.y, { steps: 12 }); await page.mouse.move(spot.x + 400, spot.y, { steps: 12 });
      await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(800);
      const v1 = await vp();
      trace.push({ round: i + 1, vpDelta: [+(v1.x - v0.x).toFixed(1), +(v1.y - v0.y).toFixed(1)],
        zoom: v1.z, domNodes: await N(), prompt: (await lostPrompt()) ? '当前视窗没有节点' : null });
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
    await logStep(B, { id: 'G6-lost-prompt', title: '「当前视窗没有节点」提示与「返回节点」', target: '按住 Space 每轮向 +400px 拖，最多 14 轮，直到提示出现',
      evidence: { trace, promptShown: got, afterClickingBack: back },
      visible_text: `轨迹 ${JSON.stringify(trace)}；提示 ${JSON.stringify(got)}；点「返回节点」后 ${JSON.stringify(back)}`, shot: 'K-06-当前视窗没有节点.png' });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
