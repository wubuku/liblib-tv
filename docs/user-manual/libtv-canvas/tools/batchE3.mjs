// Batch E3 —— 只做一件事：把「框选入口」和它下游的 ⌘L/⌘G/⌘⌥G/⌘⇧G 坐实。
//
// E1/E2 连着两轮都没成，原因是同一个低级错误：**我以为的「空白处」其实在节点上**。
// E1 想在右上角拖，图片节点却宽 615px、一直铺到 x=1312，手一按下去就把它拖走了；
// 节点一动，E2 事先算好的框选矩形就全错位。两轮读数因此互相打架。
//
// 这一轮改成几何自证：
//   1. 不猜「哪里是空白」。把每个节点的实测外框拿出来，**程序化搜**一个离所有节点都
//      ≥30px、且避开顶栏/底栏的点，从那儿起手。
//   2. 框选矩形每一步都从**当下**的节点外框重算，绝不复用上一轮的旧坐标。
//   3. 起手前后各读一次视口/框选框/选中数，四个信号同时落盘再下结论。
//
// 另外两件顺带要坐实的事：
//   · ⌘0 适应画布之后，视口有时会被甩到离所有节点一万八千像素外 —— E13 要弄清
//     「当前视窗没有节点 / 返回节点」是不是就是这么来的，以及那个按钮到底管不管用。
//   · 底部两条工具栏的完整按钮清单（E14 上一轮被展开节点的内层按钮污染了）。
//
// 安全边界：绝不按 ⌘Enter（= 生成，会扣积分）；不点发布；不碰用户真实项目。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE3';
const { browser, page } = await launch();

const VPW = 1440; const VPH = 810;
const SAFE_TOP = 80;      // 顶栏高度以下
const SAFE_BOTTOM = 740;  // 底栏高度以上
const GAP = 30;           // 起手点离任意节点外框的最小间距

const N = () => nodeCount(page);
const nodesOf = () =>
  page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return {
      title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
      selected: n.classList.contains('selected'),
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
    };
  }));
const sel = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const selTitles = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')]
  .map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14)));
const edges = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const groups = () => page.evaluate(() =>
  [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => /\bgroup\b/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || '')).length);
const vp = () => page.evaluate(() => {
  const s = document.querySelector('.react-flow__viewport')?.style.transform || '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(s);
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : { raw: s || null };
});
const marquee = () => page.evaluate(() =>
  [...document.querySelectorAll('.react-flow__selection,.react-flow__nodesselection-rect')]
    .filter((e) => e.getBoundingClientRect().width > 0)
    .map((e) => { const r = e.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }));
const lostPrompt = () => page.evaluate(() => {
  const hit = [...document.querySelectorAll('button,div,span')].find((el) => (el.innerText || '').trim() === '当前视窗没有节点');
  if (!hit || !hit.getBoundingClientRect().width) return null;
  const box = hit.closest('[class*="toast"],[class*="Toast"],[class*="float"],[class*="Float"],[class*="tip"],[class*="Tip"]') || hit.parentElement;
  return { text: (box.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    buttons: [...box.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 12)) };
});
const onScreen = (list) => list.filter((n) => n.x + n.w > 0 && n.x < VPW && n.y + n.h > 0 && n.y < VPH);

/** 程序化搜一个「确定不在任何节点上、也离得够远」的起手点。不猜。 */
function findEmptySpot(list) {
  const step = 24;
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += step) {
    for (let x = 40; x <= VPW - 40; x += step) {
      const inside = list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP);
      if (!inside) return { x, y };
    }
  }
  return null;
}
/** 完整包住 target 里所有节点的矩形；装不下返回 null。 */
function unionBox(list) {
  if (!list.length) return null;
  const x0 = Math.min(...list.map((n) => n.x)) - 12;
  const y0 = Math.min(...list.map((n) => n.y)) - 12;
  const x1 = Math.max(...list.map((n) => n.x + n.w)) + 12;
  const y1 = Math.max(...list.map((n) => n.y + n.h)) + 12;
  if (x0 < 0 || y0 < SAFE_TOP || x1 > VPW || y1 > SAFE_BOTTOM) return null;
  return { x0: Math.round(x0), y0: Math.round(y0), x1: Math.round(x1), y1: Math.round(y1) };
}
/** 装不下就 ⌘- 缩一档重试；返回可用的框选矩形。 */
async function fitBoxFor(list, maxTries = 5) {
  let cur = list;
  for (let i = 0; i <= maxTries; i += 1) {
    const b = unionBox(cur);
    if (b) return { box: b, zoom: (await vp()).z, tries: i };
    await page.keyboard.press('Meta+-');
    await page.waitForTimeout(800);
    cur = await nodesOf();
  }
  return null;
}

async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y);
  await page.waitForTimeout(1000);
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
  await closePromos(page); await clearToasts(page);
  await page.waitForTimeout(1200);
  await beginBatch(B, { note: '几何自证版框选取证：程序化找空白起手点，框选矩形每步重算' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1500);

  // 只建两个小方块节点（文本/音频都是 ~346×346），给框选留出余地
  await addNodeAt(340, 280, '文本');
  await addNodeAt(1000, 280, '音频');
  await fitView(page, 1); await page.waitForTimeout(1200);
  const built = await nodesOf();
  console.log('节点:', JSON.stringify(built), 'vp:', JSON.stringify(await vp()));

  // ── E1 空白处无修饰键拖动：起手点程序化求解，四个信号同时读
  await safe('E1-plain-drag', '空白处无修饰键拖动', '从「离所有节点≥30px 的程序化求解点」左键拖 +150,+80', async () => {
    const list = await nodesOf();
    const spot = findEmptySpot(list);
    if (!spot) throw new Error('画面里找不到离所有节点都 ≥30px 的空白点');
    const inside = list.some((n) => spot.x > n.x && spot.x < n.x + n.w && spot.y > n.y && spot.y < n.y + n.h);
    const vp0 = await vp();
    await page.mouse.move(spot.x, spot.y);
    await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(spot.x + 75, spot.y + 40, { steps: 10 });
    await page.mouse.move(spot.x + 150, spot.y + 80, { steps: 10 });
    const mqDuring = await marquee();
    const vpDuring = await vp();
    await page.mouse.up(); await page.waitForTimeout(1200);
    const vp1 = await vp();
    const after = await nodesOf();
    const d = vp1.x != null && vp0.x != null ? [+(vp1.x - vp0.x).toFixed(2), +(vp1.y - vp0.y).toFixed(2)] : null;
    await logStep(B, {
      id: 'E1-plain-drag', title: '空白处无修饰键拖动',
      target: `从 (${spot.x},${spot.y}) 左键拖到 (${spot.x + 150},${spot.y + 80})`,
      evidence: {
        startPoint: spot, startPointOnNode: inside, mouseDelta: [150, 80],
        viewportBefore: vp0, viewportDuringDrag: vpDuring, viewportAfter: vp1, viewportDelta: d,
        zoomChanged: vp0.z !== vp1.z,
        marqueeDuringDrag: mqDuring, selectedAfter: await sel(),
        nodeRectsBefore: list.map((n) => [n.x, n.y]), nodeRectsAfter: after.map((n) => [n.x, n.y]),
      },
      visible_text: `起手点 (${spot.x},${spot.y}) 是否压在节点上: ${inside}；鼠标位移 (+150,+80)；视口位移 ${JSON.stringify(d)}；拖动中框选框 ${mqDuring.length} 个；松开后选中 ${await sel()} 个；缩放 ${vp0.z}→${vp1.z}`,
    });
  });

  // ── E2 Shift + 拖动框选：矩形从「当下」节点外框重算
  await safe('E2-shift-marquee', 'Shift + 拖动框选', '空白起手点按住 Shift 拖出完整包住两个节点的矩形', async () => {
    const fitted = await fitBoxFor(await nodesOf());
    if (!fitted) throw new Error('缩到最小仍算不出能完整包住两个节点的矩形');
    const { box, zoom, tries } = fitted;
    const spot = findEmptySpot(await nodesOf());
    if (!spot) throw new Error('找不到空白起手点');
    if (spot.x > box.x0 || spot.x < box.x0) {
      // 起手点必须在框外，否则就不是「从空白处起手框选」
      if (spot.y > box.y1 - 5 || spot.y < box.y0 + 5) {
        console.log(`  ! 起手点 (${spot.x},${spot.y}) 落在框选矩形内部，改用框外左边缘`);
      }
    }
    console.log(`  框选矩形 ${JSON.stringify(box)} @zoom ${zoom}（缩放 ${tries} 次），起手点 (${spot.x},${spot.y})`);
    await page.keyboard.down('Shift');
    await page.mouse.move(spot.x, spot.y);
    await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move((spot.x + box.x0) / 2, spot.y, { steps: 10 });
    await page.mouse.move((box.x0 + box.x1) / 2, (spot.y + box.y1) / 2, { steps: 10 });
    await page.mouse.move(box.x1, box.y1, { steps: 10 });
    await page.waitForTimeout(450);
    const mq = await marquee();
    await shot(page, 'K-01-Shift拖动框选.png');
    await page.mouse.up();
    await page.keyboard.up('Shift');
    await page.waitForTimeout(1500);
    const s = await sel();
    await shot(page, 'K-02-框选结果.png');
    await logStep(B, {
      id: 'E2-shift-marquee', title: 'Shift + 拖动框选',
      target: `起手 (${spot.x},${spot.y})，Shift + 拖到 (${box.x1},${box.y1})，矩形 ${box.x1 - box.x0}×${box.y1 - box.y0}（zoom ${zoom}）`,
      evidence: { marqueeRectDuringDrag: mq, selectedAfterRelease: s, totalNodes: await N(), selectedTitles: await selTitles(), zoomTries: tries },
      visible_text: `拖动中的框选框 ${JSON.stringify(mq)}；松开后选中 ${s} 个 / 共 ${await N()} 个：${JSON.stringify(await selTitles())}`,
      shot: 'K-02-框选结果.png',
    });
  });

  // ── E3 ⌘L 连线（多选前提）
  await safe('E3-connect-shortcut', '⌘L 连线', `选中 ${await sel()} 个节点后按 ⌘L`, async () => {
    const e0 = await edges();
    await page.keyboard.press('Meta+l'); await page.waitForTimeout(2500);
    await logStep(B, { id: 'E3-connect-shortcut', title: '⌘L 连线', target: '多选状态按 ⌘L',
      evidence: { selected: await sel(), selectedTitles: await selTitles(), edgesBefore: e0, edgesAfter: await edges() },
      visible_text: `连线数 ${e0} → ${await edges()}` });
  });

  // ── E4 ⌘G 成组
  await safe('E4-group', '⌘G 成组', `多选（${await sel()}）状态按 ⌘G`, async () => {
    const g0 = await groups(); const n0 = await N();
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    const g1 = await groups(); const n1 = await N();
    await shot(page, 'K-03-成组后.png');
    await logStep(B, { id: 'E4-group', title: '⌘G 成组', target: `多选（${await sel()}）按 ⌘G`,
      evidence: { groupsBefore: g0, groupsAfter: g1, nodesBefore: n0, nodesAfter: n1 },
      visible_text: `分组元素 ${g0} → ${g1}；节点总数 ${n0} → ${n1}`, shot: 'K-03-成组后.png' });
  });

  // ── E5 ⌘⌥G 合并分镜组
  await safe('E5-merge-storyboard-group', '⌘⌥G 合并分镜组', '按 ⌘⌥G', async () => {
    const n0 = await N(); const g0 = await groups();
    await page.keyboard.press('Meta+Alt+KeyG'); await page.waitForTimeout(2500);
    await logStep(B, { id: 'E5-merge-storyboard-group', title: '⌘⌥G 合并分镜组', target: '按 ⌘⌥G',
      evidence: { nodesBefore: n0, nodesAfter: await N(), groupsBefore: g0, groupsAfter: await groups(),
        toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
          .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 80))) },
      visible_text: `节点数 ${n0} → ${await N()}；分组元素 ${g0} → ${await groups()}` });
  });

  // ── E6 ⌘⇧G 解组
  await safe('E6-ungroup', '⌘⇧G 解组', '按 ⌘⇧G', async () => {
    const g0 = await groups(); const n0 = await N();
    await page.keyboard.press('Meta+Shift+KeyG'); await page.waitForTimeout(2500);
    await logStep(B, { id: 'E6-ungroup', title: '⌘⇧G 解组', target: '按 ⌘⇧G',
      evidence: { groupsBefore: g0, groupsAfter: await groups(), nodesBefore: n0, nodesAfter: await N() },
      visible_text: `分组元素 ${g0} → ${await groups()}；节点总数 ${n0} → ${await N()}` });
  });

  // ── E7 Tab 新建节点：先把焦点明确交回画布空白
  await safe('E7-tab-new-node', 'Tab 新建节点', '点一下程序化空白点后按 Tab', async () => {
    const spot = findEmptySpot(await nodesOf());
    await page.mouse.click(spot.x, spot.y);
    await page.waitForTimeout(700);
    const focus = await page.evaluate(() => {
      const a = document.activeElement;
      return a ? `${a.tagName.toLowerCase()}${a.className ? '.' + a.className.toString().split(' ')[0] : ''}` : 'null';
    });
    const n0 = await N();
    await page.keyboard.press('Tab'); await page.waitForTimeout(1800);
    const panel = await page.evaluate(() => {
      const ps = [...document.querySelectorAll('[data-guide-lockable-portal="true"],[data-canvas-menu-portal="true"],[role="menu"],[class*="Popover"]')]
        .filter((p) => p.getBoundingClientRect().width > 40);
      return ps.length ? ps[ps.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 200) : null;
    });
    await shot(page, 'K-05-Tab新建节点.png');
    await logStep(B, { id: 'E7-tab-new-node', title: 'Tab 新建节点', target: `点空白 (${spot.x},${spot.y}) 后按 Tab`,
      evidence: { focusAfterClickEmpty: focus, nodesBefore: n0, nodesAfter: await N(), panelText: panel },
      visible_text: `点空白后焦点在 ${focus}；节点数 ${n0} → ${await N()}；弹出面板 ${JSON.stringify(panel)}`, shot: 'K-05-Tab新建节点.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
  });

  // ── E8 ⌘0 适应画布：把视口甩到离节点极远，观察「当前视窗没有节点」
  await safe('E8-viewport-lost-prompt', '「当前视窗没有节点」提示与「返回节点」', '连续在空白处拖动，直到视口内一个节点都看不到', async () => {
    const before = { prompt: await lostPrompt(), visible: onScreen(await nodesOf()).length, vp: await vp() };
    let spot = findEmptySpot(await nodesOf());
    let rounds = 0;
    while (onScreen(await nodesOf()).length > 0 && rounds < 12) {
      spot = findEmptySpot(await nodesOf()) || { x: 720, y: 400 };
      const dir = (await vp()).x > 0 ? -260 : 260;   // 往远离节点的方向推
      await page.mouse.move(spot.x, spot.y);
      await page.mouse.down(); await page.waitForTimeout(120);
      await page.mouse.move(spot.x + dir / 2, spot.y, { steps: 12 });
      await page.mouse.move(spot.x + dir, spot.y, { steps: 12 });
      await page.mouse.up(); await page.waitForTimeout(700);
      rounds += 1;
    }
    const away = { prompt: await lostPrompt(), visible: onScreen(await nodesOf()).length, vp: await vp(), rounds };
    await shot(page, 'K-06-当前视窗没有节点.png');
    let back = null;
    if (away.prompt) {
      await page.getByRole('button', { name: '返回节点', exact: true }).first().click({ timeout: 5000 })
        .catch((e) => console.log('  点「返回节点」失败:', String(e).split('\n')[0].slice(0, 100)));
      await page.waitForTimeout(2500);
      back = { prompt: await lostPrompt(), visible: onScreen(await nodesOf()).length, vp: await vp() };
    }
    await logStep(B, {
      id: 'E8-viewport-lost-prompt', title: '「当前视窗没有节点」提示与「返回节点」', target: '反复在空白处拖动，直到视口内可见节点数归零',
      evidence: { before, afterPanningAway: away, afterClickingBack: back },
      visible_text: `拖动前 ${JSON.stringify(before)}；拖出界后（${rounds} 轮）${JSON.stringify(away)}；点「返回节点」后 ${JSON.stringify(back)}`,
      shot: 'K-06-当前视窗没有节点.png',
    });
  });

  // ── E9 底部两条工具栏的完整清单：先取消选中、关掉所有面板，再读
  await safe('E9-toolbar-inventory', '底部两条工具栏按钮清单', '取消选中并关闭所有浮层后，读两条工具栏每个按钮的 aria-label 与 data-* ', async () => {
    await fitView(page, 1); await page.waitForTimeout(800);
    await page.keyboard.press('Escape').catch(() => {});
    const spot = findEmptySpot(await nodesOf());
    await page.mouse.click(spot.x, spot.y);
    await page.waitForTimeout(900);
    const read = () => page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
      .filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 560; })
      .map((b) => ({ t: (b.getAttribute('aria-label') || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
        data: [...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).join(' '),
        x: Math.round(b.getBoundingClientRect().x), y: Math.round(b.getBoundingClientRect().y) })));
    const base = await read();
    await page.keyboard.press('KeyH'); await page.waitForTimeout(800);
    const afterH = await read();
    await page.keyboard.press('KeyV'); await page.waitForTimeout(800);
    const afterV = await read();
    await shot(page, 'K-08-底部两条工具栏.png');
    await logStep(B, {
      id: 'E9-toolbar-inventory', title: '底部两条工具栏按钮清单', target: '取消选中、关闭浮层后读 y>560 的所有按钮；再按 H / V 各读一次',
      evidence: { base, afterH, afterV },
      visible_text: `默认: ${JSON.stringify(base.map((b) => b.t))}；按 H 后: ${JSON.stringify(afterH.map((b) => b.t))}；按 V 后: ${JSON.stringify(afterV.map((b) => b.t))}`,
      shot: 'K-08-底部两条工具栏.png',
    });
  });

  await fitView(page, 1); await page.waitForTimeout(800);
  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
