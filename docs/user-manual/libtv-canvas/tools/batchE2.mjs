// Batch E2 —— 修正 batchE 的两处脚本缺陷后重跑。
//
// batchE 查出来的两件事：
//   1. `nodeCount(page)` 要传 page，零参调用把 7 个步骤全打挂了（不是产品没反应，是脚本崩了）。
//   2. K-02 截图里冒出一个手册里从没记过的元素：「当前视窗没有节点 / 返回节点」。
//      它可能是**视口飘到所有节点之外**时自动出现的定位提示 —— 如果属实，
//      这是 organize-canvas / troubleshooting 里很值钱的一条，本轮必须坐实。
//
// 另外 batchE 的 E1 读数自相矛盾：空白处无修饰键拖动，视口 transform 变了，
// 但位移 (−112.3, −173.0) 跟鼠标位移 (+150, +80) 对不上，不能草率写成「平移」。
// 这一轮把「鼠标位移 vs 视口位移 vs 框选框 vs 节点选中」四路读数同时采，才敢下结论。
//
// 安全边界：绝不按 ⌘Enter（= 生成，会扣积分）；不点发布；不碰用户真实项目。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE2';
const { browser, page } = await launch();

const N = () => nodeCount(page);                                  // 零参包装，修掉 batchE 的崩点
const nodesOf = () =>
  page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return {
      title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
      selected: n.classList.contains('selected'),
      cls: (n.className || '').toString().replace(/react-flow__node\s*/, '').trim().slice(0, 40),
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
    };
  }));
const sel = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const edges = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const groups = () => page.evaluate(() =>
  [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => /\bgroup\b/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || '')).length);
const vp = () => page.evaluate(() => {
  const s = document.querySelector('.react-flow__viewport')?.style.transform || '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(s);
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : { raw: s || null };
});
const marquee = () => page.evaluate(() => {
  const els = [...document.querySelectorAll('.react-flow__selection,.react-flow__nodesselection-rect')]
    .filter((e) => e.getBoundingClientRect().width > 0);
  return els.map((e) => { const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; });
});
/** 「当前视窗没有节点」提示：出现与否 + 按钮文案。 */
const lostPrompt = () => page.evaluate(() => {
  const hit = [...document.querySelectorAll('button,div,span')]
    .find((el) => (el.innerText || '').trim() === '当前视窗没有节点');
  if (!hit || !hit.getBoundingClientRect().width) return null;
  const box = hit.closest('[class*="paper"],[class*="Paper"],[class*="toast"],[class*="Toast"],[class*="float"],[class*="Float"]') || hit.parentElement;
  return {
    text: (box.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    buttons: [...box.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 12)),
    box: (() => { const r = box.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
  };
});

async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y);
  await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}

async function dragTo(from, to, steps = 22) {
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.waitForTimeout(150);
  await page.mouse.move(to.x, to.y, { steps });
  await page.waitForTimeout(300);
  await page.mouse.up();
  await page.waitForTimeout(900);
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
  await beginBatch(B, { note: '修正 batchE 的 nodeCount 零参崩溃；四路同步读数判定框选入口；坐实「当前视窗没有节点」' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1500);
  console.log('新画布:', page.url());

  // 两个节点足够框选；第三个留着验证「框选不误伤框外节点」
  await addNodeAt(320, 260, '文本');
  await addNodeAt(900, 260, '图片');
  await addNodeAt(320, 660, '音频');
  await fitView(page, 1);
  await page.waitForTimeout(1200);
  console.log('fit 后节点:', JSON.stringify(await nodesOf()), 'vp:', JSON.stringify(await vp()));
  console.log('fit 后「当前视窗没有节点」:', JSON.stringify(await lostPrompt()));

  // 框选矩形由前两节点外框 + 边距反算；装不下就 ⌘- 缩一档重来
  let box = null; const list0 = await nodesOf();
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const [a, b] = list0;
    const cand = {
      x0: Math.max(4, Math.min(a.x, b.x) - 24), y0: Math.max(4, Math.min(a.y, b.y) - 24),
      x1: Math.min(1436, Math.max(a.x + a.w, b.x + b.w) + 24), y1: Math.min(806, Math.max(a.y + a.h, b.y + b.h) + 24),
    };
    const clipped = cand.x1 !== Math.max(a.x + a.w, b.x + b.w) + 24 || cand.y1 !== Math.max(a.y + a.h, b.y + b.h) + 24;
    if (!clipped) { box = cand; break; }
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(700);
    Object.assign(list0, await nodesOf());
  }
  if (!box) throw new Error('多轮缩放后仍算不出能完整框住两个节点的矩形');
  console.log('框选矩形:', JSON.stringify(box));

  // ── E1 空白处无修饰键拖动：四路同步读数
  await safe('E1-plain-drag', '空白处无修饰键拖动', '所有节点之外的右上角空旷区域左键拖 +150/+80', async () => {
    const vp0 = await vp(); const nodes0 = await nodesOf(); const mq0 = await marquee();
    await page.mouse.move(1240, 120);
    await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(1330, 165, { steps: 10 });
    await page.mouse.move(1390, 200, { steps: 10 });
    const mqDuring = await marquee();
    const vpDuring = await vp();
    await page.mouse.up();
    await page.waitForTimeout(1000);
    const vp1 = await vp(); const sel1 = await sel();
    await logStep(B, {
      id: 'E1-plain-drag',
      title: '空白处无修饰键拖动',
      target: '画布右上角空旷处（全部节点之外）左键拖动 +150,+80',
      evidence: {
        mouseDelta: [150, 80],
        viewportBefore: vp0, viewportDuringDrag: vpDuring, viewportAfter: vp1,
        viewportDelta: vp1.x != null && vp0.x != null ? [+(vp1.x - vp0.x).toFixed(2), +(vp1.y - vp0.y).toFixed(2)] : null,
        zoomChanged: vp0.z !== vp1.z,
        marqueeBefore: mq0.length, marqueeDuringDrag: mqDuring.length,
        selectedAfter: sel1,
        nodeRectsBefore: nodes0.map((n) => [n.x, n.y]), nodeRectsAfter: (await nodesOf()).map((n) => [n.x, n.y]),
      },
      visible_text: `鼠标位移 (+150,+80)；视口位移 ${JSON.stringify(vp1.x != null && vp0.x != null ? [+(vp1.x - vp0.x).toFixed(2), +(vp1.y - vp0.y).toFixed(2)] : null)}；拖动中框选框 ${mqDuring.length} 个；松开后选中 ${sel1} 个；缩放 ${vp0.z}→${vp1.z}`,
    });
  });
  await fitView(page, 1);

  // ── E2 Shift + 拖动：框选
  await safe('E2-shift-marquee', 'Shift + 拖动框选', `画布空白处 Shift + 左键拖出 ${Math.round(box.x1 - box.x0)}×${Math.round(box.y1 - box.y0)} 矩形`, async () => {
    await page.keyboard.down('Shift');
    await page.mouse.move(box.x0, box.y0);
    await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2, { steps: 10 });
    await page.mouse.move(box.x1, box.y1, { steps: 10 });
    await page.waitForTimeout(400);
    const mq = await marquee();
    await shot(page, 'K-01-Shift拖动框选.png');   // 拖动中不注入高亮：框选框会随鼠标移动，高亮脚本会失败
    await page.mouse.up();
    await page.keyboard.up('Shift');
    await page.waitForTimeout(1400);
    const s = await sel();
    await shot(page, 'K-02-框选结果.png');
    await logStep(B, {
      id: 'E2-shift-marquee',
      title: 'Shift + 拖动框选',
      target: `Shift + 左键拖出 ${Math.round(box.x1 - box.x0)}×${Math.round(box.y1 - box.y0)} 矩形（覆盖前两个节点）`,
      evidence: { marqueeDuringDrag: mq, selectedAfterRelease: s, totalNodes: await N(), nodes: await nodesOf() },
      visible_text: `拖动中框选框 ${JSON.stringify(mq)}；松开后选中 ${s} 个 / 共 ${await N()} 个`,
      shot: 'K-02-框选结果.png',
    });
  });

  // ── E3 ⌘L 连线
  await safe('E3-connect-shortcut', '⌘L 连线', '多选状态下按 ⌘L', async () => {
    const e0 = await edges();
    await page.keyboard.press('Meta+l');
    await page.waitForTimeout(2500);
    await logStep(B, {
      id: 'E3-connect-shortcut', title: '⌘L 连线', target: `选中 ${await sel()} 个节点后按 ⌘L`,
      evidence: { edgesBefore: e0, edgesAfter: await edges() },
      visible_text: `连线数 ${e0} → ${await edges()}`,
    });
  });

  // ── E4 ⌘G 成组
  await safe('E4-group', '⌘G 成组', '多选状态下按 ⌘G', async () => {
    const g0 = await groups(); const n0 = await N(); const s = await sel();
    await page.keyboard.press('Meta+g');
    await page.waitForTimeout(2500);
    const g1 = await groups(); const n1 = await N();
    await shot(page, 'K-03-成组后.png');
    await logStep(B, {
      id: 'E4-group', title: '⌘G 成组', target: `多选（${s} 个）状态按 ⌘G`,
      evidence: { groupsBefore: g0, groupsAfter: g1, nodesBefore: n0, nodesAfter: n1 },
      visible_text: `分组元素 ${g0} → ${g1}；节点总数 ${n0} → ${n1}`,
      shot: 'K-03-成组后.png',
    });
  });

  // ── E5 ⌘⌥G 合并分镜组
  await safe('E5-merge-storyboard-group', '⌘⌥G 合并分镜组', '按 ⌘⌥G', async () => {
    const b = await N();
    await page.keyboard.press('Meta+Alt+KeyG');
    await page.waitForTimeout(2500);
    await logStep(B, {
      id: 'E5-merge-storyboard-group', title: '⌘⌥G 合并分镜组', target: '按 ⌘⌥G',
      evidence: {
        nodesBefore: b, nodesAfter: await N(), groups: await groups(),
        toast: await page.evaluate(() => [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"]')]
          .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 80))),
      },
      visible_text: `节点数 ${b} → ${await N()}；分组元素 ${await groups()} 个；有无提示：${JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('[role="alert"]')].map((t) => (t.innerText || '').slice(0, 60))))}`,
    });
  });

  // ── E6 ⌘⇧G 解组
  await safe('E6-ungroup', '⌘⇧G 解组', '按 ⌘⇧G', async () => {
    const g0 = await groups(); const n0 = await N();
    await page.keyboard.press('Meta+Shift+KeyG');
    await page.waitForTimeout(2500);
    const g1 = await groups(); const n1 = await N();
    await logStep(B, {
      id: 'E6-ungroup', title: '⌘⇧G 解组', target: '按 ⌘⇧G',
      evidence: { groupsBefore: g0, groupsAfter: g1, nodesBefore: n0, nodesAfter: n1 },
      visible_text: `分组元素 ${g0} → ${g1}；节点总数 ${n0} → ${n1}`,
    });
  });

  // ── E7 ⌘D 复制节点和连线
  await safe('E7-duplicate', '⌘D 复制节点和连线', '点节点标题栏选中后按 ⌘D', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const n0 = await N();
    const f = (await nodesOf())[0];
    await page.mouse.click(f.x + Math.min(80, f.w / 2), f.y + 12);
    await page.waitForTimeout(800);
    const s = await sel();
    await page.keyboard.press('Meta+d');
    await page.waitForTimeout(2500);
    const n1 = await N();
    await shot(page, 'K-07-复制节点后.png');
    await logStep(B, {
      id: 'E7-duplicate', title: '⌘D 复制节点和连线', target: `选中 ${s} 个节点后按 ⌘D`,
      evidence: { nodesBefore: n0, nodesAfter: n1, edges: await edges() },
      visible_text: `节点数 ${n0} → ${n1}`,
      shot: 'K-07-复制节点后.png',
    });
  });

  // ── E8 ⌘Z 撤销 / E9 ⌘⇧Z 重做
  await safe('E8-undo', '⌘Z 撤销', '⌘D 之后按 ⌘Z', async () => {
    const n0 = await N();
    await page.keyboard.press('Meta+z'); await page.waitForTimeout(2200);
    await logStep(B, { id: 'E8-undo', title: '⌘Z 撤销', target: '按 ⌘Z', evidence: { nodesBefore: n0, nodesAfter: await N() }, visible_text: `节点数 ${n0} → ${await N()}` });
  });
  await safe('E9-redo', '⌘⇧Z 重做', '⌘Z 之后按 ⌘⇧Z', async () => {
    const n0 = await N();
    await page.keyboard.press('Meta+Shift+KeyZ'); await page.waitForTimeout(2200);
    await logStep(B, { id: 'E9-redo', title: '⌘⇧Z 重做', target: '按 ⌘⇧Z', evidence: { nodesBefore: n0, nodesAfter: await N() }, visible_text: `节点数 ${n0} → ${await N()}` });
  });

  // ── E10 ⌘F 画布节点搜索（batchE 已坐实，这轮补搜索框实操）
  await safe('E10-search', '⌘F 画布节点搜索', '按 ⌘F 后在搜索框里输入「图片」', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(400);
    await page.keyboard.press('Meta+f'); await page.waitForTimeout(1800);
    const box = page.locator('input[placeholder*="搜索画布元素"], input[aria-label*="搜索画布元素"]').first();
    const found = await box.count();
    const panel0 = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div')].find((d) => /搜索画布元素/.test(d.placeholder || '') || (d.innerText || '').includes('共 ') && /节点/.test(d.innerText || ''));
      return el ? (el.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    });
    if (found) { await box.click(); await page.keyboard.type('图片', { delay: 60 }); await page.waitForTimeout(1200); }
    const panel1 = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div')].find((d) => (d.innerText || '').includes('共 ') && /节点/.test(d.innerText || ''));
      return el ? (el.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    });
    await shot(page, 'K-04-节点搜索.png');
    await logStep(B, {
      id: 'E10-search', title: '⌘F 画布节点搜索', target: '按 ⌘F，再在搜索框输入「图片」',
      evidence: { searchInputFound: found, panelBefore: panel0, panelAfterTyping: panel1 },
      visible_text: `搜索框定位到: ${found > 0}；输入前 ${JSON.stringify(panel0)}；输入「图片」后 ${JSON.stringify(panel1)}`,
      shot: 'K-04-节点搜索.png',
    });
    await page.keyboard.press('Escape').catch(() => {});
  });

  // ── E11 Tab 新建节点
  await safe('E11-tab-new-node', 'Tab 新建节点', '焦点在画布时按 Tab', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
    const n0 = await N();
    await page.keyboard.press('Tab'); await page.waitForTimeout(1800);
    const panel = await page.evaluate(() => {
      const p = document.querySelector('[data-guide-lockable-portal="true"],[data-canvas-menu-portal="true"]');
      return p && p.getBoundingClientRect().width > 40 ? (p.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    });
    await shot(page, 'K-05-Tab新建节点.png');
    await logStep(B, {
      id: 'E11-tab-new-node', title: 'Tab 新建节点', target: '按 Tab',
      evidence: { nodesBefore: n0, nodesAfter: await N(), panelText: panel },
      visible_text: `节点数 ${n0} → ${await N()}；弹出面板 ${JSON.stringify(panel)}`,
      shot: 'K-05-Tab新建节点.png',
    });
    await page.keyboard.press('Escape').catch(() => {});
  });

  // ── E12 Option + 拖动节点 = 节点复制
  await safe('E12-opt-drag-copy', 'Option + 拖动节点（节点复制）', '按住 Option 拖动一个节点', async () => {
    await page.waitForTimeout(600);
    const n0 = await N();
    const f = (await nodesOf())[0];
    if (!f) throw new Error('画布上没有节点可拖');
    const cx = f.x + Math.min(80, f.w / 2); const cy = f.y + 12;
    await page.keyboard.down('Alt');
    await page.mouse.move(cx, cy); await page.mouse.down(); await page.waitForTimeout(200);
    await page.mouse.move(cx + 90, cy + 60, { steps: 12 });
    await page.mouse.move(cx + 180, cy + 120, { steps: 12 });
    await page.waitForTimeout(300);
    await page.mouse.up(); await page.keyboard.up('Alt'); await page.waitForTimeout(2200);
    await logStep(B, {
      id: 'E12-opt-drag-copy', title: 'Option + 拖动节点（节点复制）', target: `按住 Option 从 (${Math.round(cx)},${Math.round(cy)}) 拖到 (+180,+120)`,
      evidence: { nodesBefore: n0, nodesAfter: await N() },
      visible_text: `节点数 ${n0} → ${await N()}`,
    });
  });

  // ── E13 「当前视窗没有节点」提示：怎么触发、怎么消
  await safe('E13-viewport-lost-prompt', '「当前视窗没有节点」提示与「返回节点」', '把视口平移到所有节点之外', async () => {
    await fitView(page, 1); await page.waitForTimeout(800);
    const p0 = await lostPrompt();
    const list = await nodesOf();
    const cx = list[0] ? list[0].x + list[0].w / 2 : 700;
    const cy = list[0] ? list[0].y + list[0].h / 2 : 400;
    // 朝远离节点的方向平移 1200px
    await dragTo({ x: 700, y: 400 }, { x: 700 + (cx > 700 ? -1200 : 1200), y: 400 + (cy > 400 ? -400 : 400) });
    await page.waitForTimeout(1200);
    const p1 = await lostPrompt();
    const visibleNodes = (await nodesOf()).filter((n) => n.x > -n.w && n.x < 1440 && n.y > -n.h && n.y < 810).length;
    await shot(page, 'K-06-当前视窗没有节点.png');
    let after = null;
    if (p1) {
      await page.getByRole('button', { name: '返回节点', exact: true }).first().click({ timeout: 4000 }).catch((e) => { console.log('  返回节点点击失败', String(e).slice(0, 80)); });
      await page.waitForTimeout(2500);
      after = { prompt: await lostPrompt(), visibleNodes: (await nodesOf()).filter((n) => n.x > -n.w && n.x < 1440 && n.y > -n.h && n.y < 810).length, vp: await vp() };
    }
    await logStep(B, {
      id: 'E13-viewport-lost-prompt', title: '「当前视窗没有节点」提示与「返回节点」', target: '从适应画布状态把视口平移到所有节点之外',
      evidence: { promptWhenFitted: p0, promptAfterPanAway: p1, visibleNodesAfterPan: visibleNodes, afterClickingBack: after },
      visible_text: `适应画布时提示: ${JSON.stringify(p0)}；平移出界后提示: ${JSON.stringify(p1)}；平移后视口内可见节点数 ${visibleNodes}；点「返回节点」后 ${JSON.stringify(after)}`,
      shot: 'K-06-当前视窗没有节点.png',
    });
  });

  // ── E14 V / H 工具切换：把底部工具条每个按钮的完整属性都读一遍
  await safe('E14-vh-tools', 'V 移动 / H 抓手工具切换', '依次按 V、H、V', async () => {
    const probe = () => page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
      .filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 620; })
      .map((b) => ({
        t: (b.getAttribute('aria-label') || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
        pressed: b.getAttribute('aria-pressed'),
        data: [...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).join(' '),
        cls: (b.className || '').toString().replace(/\s+/g, ' ').slice(0, 90),
      })));
    const base = await probe();
    await page.mouse.click(700, 120).catch(() => {});
    await page.keyboard.press('KeyV'); await page.waitForTimeout(800);
    const afterV = await probe();
    await page.keyboard.press('KeyH'); await page.waitForTimeout(800);
    const afterH = await probe();
    const diff = (a, b) => a.filter((x, i) => JSON.stringify(x) !== JSON.stringify(b[i])).map((x) => x.t);
    await page.keyboard.press('KeyV'); await page.waitForTimeout(500);
    await logStep(B, {
      id: 'E14-vh-tools', title: 'V 移动 / H 抓手工具切换', target: '依次按 V、H、V，读底部工具条按钮属性',
      evidence: {
        bottomButtons: base.map((b) => b.t),
        changedByV: diff(afterV, base), changedByH: diff(afterH, afterV),
        moveBtnBase: base.find((b) => b.t.startsWith('移动')) || null,
        moveBtnAfterV: afterV.find((b) => b.t.startsWith('移动')) || null,
        moveBtnAfterH: afterH.find((b) => b.t.startsWith('移动')) || null,
      },
      visible_text: `底部按钮 ${JSON.stringify(base.map((b) => b.t))}；按 V 变化的按钮 ${JSON.stringify(diff(afterV, base))}；按 H 变化的按钮 ${JSON.stringify(diff(afterH, afterV))}`,
    });
  });

  await fitView(page, 1); await page.waitForTimeout(1000);
  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
