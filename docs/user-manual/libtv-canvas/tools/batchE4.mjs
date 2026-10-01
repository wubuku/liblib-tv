// Batch E4 —— 顺着 batchE3 的发现继续：新表面 + 两个还没解释清楚的读数。
//
// batchE3 坐实了框选与成组，顺带浮出一条**手册里从来没有的组操作条**：
//   ● | ⊞˅ | ▶ 整组执行 | 添加到工具箱 | 转分镜组 | 解组 | ⬇
// 这一轮要做的：
//   F1 把组操作条逐个按钮读出来（只读，不点「整组执行」——它会触发生成、扣积分）。
//   F2 读 ⊞˅ 下拉的选项。
//   F3 点一次「转分镜组」看它把画布变成什么（`⌘⌥G 合并分镜组` 大概就是同一个东西）。
//   F4 平移是不是真的线性跟随鼠标？batchE3 量到鼠标走 150px 视口只动 21px，不像。
//   F5 缩到多小才会出现「当前视窗没有节点 / 返回节点」，那个按钮到底管不管用。
//
// 安全边界：不点「整组执行」（触发生成、扣积分）、不点「下载」、不按 ⌘Enter。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, shotHighlighted } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE4';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    selected: n.classList.contains('selected'), isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
const sel = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const edges = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const vp = () => page.evaluate(() => {
  const s = document.querySelector('.react-flow__viewport')?.style.transform || '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(s);
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : { raw: s || null };
});
const lostPrompt = () => page.evaluate(() => {
  const hit = [...document.querySelectorAll('button,div,span')].find((el) => (el.innerText || '').trim() === '当前视窗没有节点');
  if (!hit || !hit.getBoundingClientRect().width) return null;
  const box = hit.closest('[class*="toast"],[class*="Toast"],[class*="float"],[class*="Float"]') || hit.parentElement;
  const r = box.getBoundingClientRect();
  return { text: (box.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    buttons: [...box.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 12)),
    box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
/** 顶部 y<150 一带的按钮 —— 组操作条就挂在这。 */
const topBar = () => page.evaluate(() => [...document.querySelectorAll('button,[role="button"],[role="menuitem"]')]
  .filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y < 150 && r.y > 40; })
  .map((b) => { const r = b.getBoundingClientRect();
    return { t: (b.getAttribute('aria-label') || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 18),
      title: b.getAttribute('title'), disabled: b.disabled === true || b.getAttribute('aria-disabled') === 'true',
      x: Math.round(r.x), y: Math.round(r.y) }; }));

const GAP = 30, VPW = 1440, VPH = 810, SAFE_TOP = 80, SAFE_BOTTOM = 740;
function findEmptySpot(list) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 24) for (let x = 40; x <= VPW - 40; x += 24) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return null;
}
async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
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
  await beginBatch(B, { note: '组操作条普查 + 平移线性度 + 「当前视窗没有节点」触发条件；不点「整组执行」' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);

  await addNodeAt(340, 280, '文本');
  await addNodeAt(1000, 280, '音频');
  await fitView(page, 1); await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+-'); await page.waitForTimeout(700);   // 缩一档，两张卡都完整进画面
  const built = await nodesOf();
  console.log('节点:', JSON.stringify(built), 'vp:', JSON.stringify(await vp()));

  // ── F0 重拍框选图：这次让两张卡都完整入画
  await safe('F0-marquee-shot', 'Shift 拖动框选（重拍配图）', '空白起手点按住 Shift 拖出完整包住两个节点的矩形', async () => {
    const list = await nodesOf();
    const x0 = Math.min(...list.map((n) => n.x)) - 12, y0 = Math.min(...list.map((n) => n.y)) - 12;
    const x1 = Math.max(...list.map((n) => n.x + n.w)) + 12, y1 = Math.max(...list.map((n) => n.y + n.h)) + 12;
    const spot = findEmptySpot(list);
    await page.keyboard.down('Shift');
    await page.mouse.move(spot.x, spot.y);
    await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move((spot.x + x0) / 2, spot.y, { steps: 10 });
    await page.mouse.move(x0, (spot.y + y1) / 2, { steps: 10 });
    await page.mouse.move(x1, y1, { steps: 12 });
    await page.waitForTimeout(450);
    const mq = await page.evaluate(() => [...document.querySelectorAll('.react-flow__selection,.react-flow__nodesselection-rect')]
      .filter((e) => e.getBoundingClientRect().width > 0).map((e) => { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }));
    await shot(page, 'K-01-Shift拖动框选.png');
    await page.mouse.up(); await page.keyboard.up('Shift');
    await page.waitForTimeout(1500);
    await shot(page, 'K-02-框选结果.png');
    await logStep(B, { id: 'F0-marquee-shot', title: 'Shift + 拖动框选（重拍配图）',
      target: `起手 (${spot.x},${spot.y})，Shift + 拖到 (${x1},${y1})`,
      evidence: { marqueeDuringDrag: mq, selectedAfterRelease: await sel(), selectedTitles: await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => (n.innerText || '').replace(/\s+/g, ' ').slice(0, 14))) },
      visible_text: `框选框 ${JSON.stringify(mq)}；松开后选中 ${await sel()} 个 / 共 ${await N()} 个`,
      shot: 'K-01-Shift拖动框选.png' });
  });

  // ── F1 ⌘G 成组后，顶部浮出的组操作条
  await safe('F1-group-toolbar', '成组后顶部浮出的组操作条', '多选两个节点后按 ⌘G，再读顶部 y<150 的所有按钮', async () => {
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    const bar = await topBar();
    const groups = (await nodesOf()).filter((n) => n.isGroup);
    await shot(page, 'K-03-成组后.png');
    await logStep(B, { id: 'F1-group-toolbar', title: '成组后顶部浮出的组操作条', target: '⌘G 之后读顶部区域按钮',
      evidence: { groupNodes: groups, groupNodeCount: groups.length, totalNodes: await N(), topBarButtons: bar },
      visible_text: `组元素 ${groups.length} 个 / 节点总数 ${await N()}；顶部操作条 ${JSON.stringify(bar.map((b) => b.t))}`, shot: 'K-03-成组后.png' });
  });

  // ── F2 组操作条第二枚按钮（⊞˅）的下拉
  await safe('F2-group-layout-menu', '组操作条 ⊞ 下拉', '点组操作条上带下拉箭头的网格按钮', async () => {
    const before = await fingerprintLite();
    const cand = page.locator('button[aria-label*="布局"], button[title*="布局"], button[aria-haspopup="menu"]')
      .or(page.getByRole('button', { name: /布局|排列|网格|样式/ })).first();
    if (await cand.count()) {
      await cand.click({ timeout: 4000 });
    } else {
      // 退而求其次：点操作条上第 3 个（⊞ 之后）按钮
      await page.locator('button[aria-haspopup]').first().click({ timeout: 4000 }).catch(() => {});
    }
    await page.waitForTimeout(1200);
    const menu = await page.evaluate(() => {
      const m = [...document.querySelectorAll('[role="menu"],[class*="Popover"],[class*="Dropdown"]')]
        .filter((d) => d.getBoundingClientRect().width > 40);
      return m.length ? m[m.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
    });
    await shot(page, 'K-09-组操作条下拉.png');
    await logStep(B, { id: 'F2-group-layout-menu', title: '组操作条 ⊞ 下拉', target: '点组操作条上的下拉按钮',
      evidence: { openedMenuText: menu },
      visible_text: `下拉内容 ${JSON.stringify(menu)}`, shot: 'K-09-组操作条下拉.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
  });

  // ── F3 点「转分镜组」，看它把画布变成什么（`⌘⌥G 合并分镜组` 很可能就是它）
  await safe('F3-to-storyboard-group', '组操作条「转分镜组」', '点组操作条的「转分镜组」', async () => {
    const n0 = await N();
    const btn = page.getByRole('button', { name: '转分镜组', exact: false }).first();
    const found = await btn.count();
    let after = null;
    if (found) { await btn.click({ timeout: 4000 }); await page.waitForTimeout(3000); }
    after = { nodes: (await nodesOf()).map((n) => n.title), count: await N(), edges: await edges(),
      groups: (await nodesOf()).filter((n) => n.isGroup).length,
      toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
        .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 100))) };
    await shot(page, 'K-10-转分镜组后.png');
    await logStep(B, { id: 'F3-to-storyboard-group', title: '组操作条「转分镜组」', target: '点组操作条的「转分镜组」',
      evidence: { buttonFound: found, nodesBefore: n0, ...after },
      visible_text: `按钮存在 ${found}；节点 ${n0} → ${after.count}；分组元素 ${after.groups}；提示 ${JSON.stringify(after.toast)}`, shot: 'K-10-转分镜组后.png' });
  });

  // ── F4 平移线性度：沿途多点采样，看视口是不是跟手
  await safe('F4-pan-linearity', '空白处拖动是否真的平移画布', '从程序化空白点起手，每 50px 采样一次视口 transform', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(600);
    const list = await nodesOf();
    const spot = findEmptySpot(list) || { x: 720, y: 400 };
    const samples = [];
    const v0 = await vp();
    await page.mouse.move(spot.x, spot.y);
    await page.mouse.down(); await page.waitForTimeout(150);
    for (let i = 1; i <= 6; i += 1) {
      await page.mouse.move(spot.x + i * 50, spot.y + i * 30, { steps: 6 });
      await page.waitForTimeout(180);
      samples.push({ mouse: [i * 50, i * 30], vp: await vp() });
    }
    await page.mouse.up(); await page.waitForTimeout(800);
    const v1 = await vp();
    await logStep(B, { id: 'F4-pan-linearity', title: '空白处拖动是否真的平移画布',
      target: `从 (${spot.x},${spot.y}) 向右下共 (+300,+180)，沿途每 50px 采样`,
      evidence: { startPoint: spot, zoom: v0.z, samples, final: v1,
        note: '若视口位移与鼠标位移成正比 → 真平移；明显偏小 → 画布在抵抗位移' },
      visible_text: `缩放 ${v0.z}；采样 ${JSON.stringify(samples.map((s) => [s.mouse[0], s.vp.x != null ? +(s.vp.x - v0.x).toFixed(1) : null]))}；终点视口位移 ${JSON.stringify([+(v1.x - v0.x).toFixed(2), +(v1.y - v0.y).toFixed(2)])}（鼠标 +300,+180）` });
  });

  // ── F5 一直 ⌘- 缩下去，看「当前视窗没有节点 / 返回节点」到底怎么来的
  await safe('F5-zoom-out-to-lost', '缩到多小才出现「当前视窗没有节点」', '连按 ⌘-，每次记录缩放、DOM 节点数、提示是否出现', async () => {
    const trace = [];
    for (let i = 0; i < 12; i += 1) {
      const v = await vp();
      trace.push({ press: i + 1, zoom: v.z, domNodes: await N(), prompt: (await lostPrompt()) ? '当前视窗没有节点' : null });
      if (trace[trace.length - 1].prompt) break;
      await page.keyboard.press('Meta+-'); await page.waitForTimeout(800);
    }
    const final = trace[trace.length - 1];
    // 关键交叉验证：DOM 里没有节点了，⌘F 还能不能搜到它们？
    let searchStillLists = null;
    if (final.domNodes === 0) {
      await page.keyboard.press('Meta+f'); await page.waitForTimeout(1800);
      searchStillLists = await page.evaluate(() => {
        const el = [...document.querySelectorAll('div')].find((d) => /共 \d+ 节点/.test(d.innerText || ''));
        return el ? el.innerText.replace(/\s+/g, ' ').slice(0, 200) : null;
      });
      await page.keyboard.press('Escape').catch(() => {});
    }
    await shot(page, 'K-06-当前视窗没有节点.png');
    let afterBack = null;
    if (final.prompt) {
      await page.getByRole('button', { name: '返回节点', exact: true }).first().click({ timeout: 5000 })
        .catch((e) => console.log('  点「返回节点」失败:', String(e).split('\n')[0].slice(0, 100)));
      await page.waitForTimeout(2500);
      afterBack = { zoom: (await vp()).z, domNodes: await N(), prompt: (await lostPrompt()) ? '还在' : null };
    }
    await logStep(B, { id: 'F5-zoom-out-to-lost', title: '缩到多小才出现「当前视窗没有节点」', target: '连按 ⌘- 最多 12 次，每次记录缩放 / DOM 节点数 / 提示',
      evidence: { trace, searchPanelWhileDomEmpty: searchStillLists, afterClickingBack: afterBack },
      visible_text: `轨迹 ${JSON.stringify(trace)}；DOM 空时 ⌘F 仍列出 ${JSON.stringify(searchStillLists)}；点「返回节点」后 ${JSON.stringify(afterBack)}`, shot: 'K-06-当前视窗没有节点.png' });
  });

  // ── F6 两条工具栏定妆照（成组已解组的干净状态）
  await safe('F6-toolbar-shot', '底部两条工具栏', '取消选中后拍底部两条工具栏', async () => {
    await fitView(page, 1); await page.waitForTimeout(800);
    await page.keyboard.press('Escape').catch(() => {});
    const spot = findEmptySpot(await nodesOf());
    if (spot) await page.mouse.click(spot.x, spot.y);
    await page.waitForTimeout(900);
    await shot(page, 'K-08-底部两条工具栏.png', { clip: { x: 0, y: 620, width: 1440, height: 190 } });
    await logStep(B, { id: 'F6-toolbar-shot', title: '底部两条工具栏', target: '裁剪 y 620–810 拍底部两条工具栏',
      evidence: { topBar: await topBar() }, visible_text: '底部左工具条 + 底部中央七键工具条' });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}

function fingerprintLite() { return null; }
