// Batch E —— Gate B 回走：框选入口 + 快捷键面板逐条实按。
//
// 手册里 shortcuts.md 有 13 个键一直标着「⚠️ 未实按」，原因是它们的前置是
// **框选多个节点**，而框选入口此前没能在源站上坐实。克隆仓 docs/CANVAS_NAVIGATION.md
// 记的是「空白无修饰键拖动 = no-op，Shift+拖动 = 框选」（React Flow v12
// selectionOnDrag=false 语义），这里是**在源站上验证这个说法**，不是照抄。
//
// 安全边界：绝不按 ⌘Enter（= 生成，会扣积分）；不按发布；不碰用户真实项目。
// 每一步都包在 safe() 里 —— 一步失败不拖垮整批，失败原因照实记进证据。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, shotHighlighted } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE';
const { browser, page } = await launch();

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

const selCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const groupCount = () => page.evaluate(() =>
  [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => /\bgroup\b/i.test(n.className || '') || (n.getAttribute('data-id') || '').includes('group')).length);
const viewportTransform = () => page.evaluate(() => document.querySelector('.react-flow__viewport')?.style.transform || null);
const marqueeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__selection,.react-flow__nodesselection-rect').length);

async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y);
  await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}

/** 拖动一段距离（React Flow 有拖拽启动阈值，一步跳过去不生效）。 */
async function dragTo(from, to, steps = 22) {
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.waitForTimeout(150);
  await page.mouse.move(to.x, to.y, { steps });
  await page.waitForTimeout(250);
  await page.mouse.up();
  await page.waitForTimeout(900);
}

/** 单步包一层：失败也留下证据，不静默跳过。 */
async function safe(id, title, target, fn) {
  try {
    await fn();
  } catch (e) {
    console.log(`  ✗ ${id} 失败: ${String(e).split('\n')[0].slice(0, 160)}`);
    await logStep(B, {
      id, title, target, failed: true,
      visible_text: `执行抛错：${String(e).split('\n')[0].slice(0, 300)}`,
    });
  }
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);
  await beginBatch(B, { note: '框选入口 + 快捷键面板逐条实按；绝不按 ⌘Enter（会扣积分）' });

  // ── 准备：新建一张干净画布，建 3 个分散的节点
  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1500);
  const fresh = page.url();
  console.log('新画布:', fresh, '初始节点数:', await nodeCount(page));

  await addNodeAt(250, 200, '文本');
  await addNodeAt(780, 200, '图片');
  await addNodeAt(250, 620, '视频');
  const built = await nodesOf();
  console.log('建好的节点:', JSON.stringify(built));

  // 框选矩形由「前两个节点的实际外框 + 边距」反算，避免硬编码坐标落到卡片外
  const [n1, n2] = built;
  const box = {
    x0: Math.max(4, Math.min(n1.x, n2.x) - 30),
    y0: Math.max(4, Math.min(n1.y, n2.y) - 30),
    x1: Math.min(1436, Math.max(n1.x + n1.w, n2.x + n2.w) + 30),
    y1: Math.min(806, Math.max(n1.y + n1.h, n2.y + n2.h) + 30),
  };
  console.log('框选矩形:', JSON.stringify(box));

  // ── E1 空白处**无修饰键**拖动：是平移、框选，还是 no-op？
  await safe('E1-plain-drag', '空白处无修饰键拖动', '在三个节点之外的空旷区域左键拖动', async () => {
    const before = await nodesOf();
    const vpBefore = await viewportTransform();
    const marquee = await marqueeCount();
    await dragTo({ x: 1250, y: 700 }, { x: 1400, y: 780 });
    const after = await nodesOf();
    const vpAfter = await viewportTransform();
    await logStep(B, {
      id: 'E1-plain-drag',
      title: '空白处无修饰键拖动',
      target: '三个节点之外、右下角空旷区域左键拖动 150×80',
      evidence: {
        marqueeBefore: marquee,
        viewportChanged: vpBefore !== vpAfter,
        viewportBefore: vpBefore,
        viewportAfter: vpAfter,
        nodeRectsUnchanged: JSON.stringify(before.map((b) => [b.x, b.y])) === JSON.stringify(after.map((b) => [b.x, b.y])),
      },
      visible_text: `视口是否被平移：${vpBefore !== vpAfter}；拖动前是否已有框选框：${marquee}`,
    });
  });
  await page.keyboard.press('Meta+0').catch(() => {});
  await page.waitForTimeout(1500);

  // ── E2 Shift + 拖动：框选（本批最关键的缺口）
  await safe('E2-shift-marquee', 'Shift + 拖动框选', '画布空白处按住 Shift 再左键拖出矩形', async () => {
    await page.keyboard.down('Shift');
    await page.mouse.move(box.x0, box.y0);
    await page.mouse.down();
    await page.waitForTimeout(150);
    await page.mouse.move((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2, { steps: 10 });
    await page.mouse.move(box.x1, box.y1, { steps: 10 });
    await page.waitForTimeout(400);
    const during = await marqueeCount();
    const selLoc = page.locator('.react-flow__selection, .react-flow__nodesselection-rect').first();
    if (await selLoc.count()) await shotHighlighted(page, selLoc, 'K-01-Shift拖动框选.png', { step: 1 }).catch(() => {});
    else await shot(page, 'K-01-Shift拖动框选.png');
    await page.mouse.up();
    await page.keyboard.up('Shift');
    await page.waitForTimeout(1200);
    const sel = await selCount();
    await shot(page, 'K-02-框选结果.png');
    await logStep(B, {
      id: 'E2-shift-marquee',
      title: 'Shift + 拖动框选',
      target: `画布空白处 Shift + 左键拖出 ${Math.round(box.x1 - box.x0)}×${Math.round(box.y1 - box.y0)} 矩形`,
      evidence: { marqueeDuringDrag: during, selectedAfterRelease: sel, nodes: await nodesOf() },
      visible_text: `拖动过程中的框选框元素数: ${during}；松开后选中节点数: ${sel} / 共 ${built.length}`,
      shot: 'K-02-框选结果.png',
    });
  });

  // ── E3 ⌘L 连线（面板宣称；前提是多选）
  await safe('E3-connect-shortcut', '⌘L 连线', '选中两个节点后按 ⌘L', async () => {
    const e0 = await edgeCount();
    await page.keyboard.press('Meta+l');
    await page.waitForTimeout(2200);
    const e1 = await edgeCount();
    await logStep(B, {
      id: 'E3-connect-shortcut',
      title: '⌘L 连线',
      target: '框选两个节点后按 ⌘L',
      evidence: { selected: await selCount(), edgesBefore: e0, edgesAfter: e1 },
      visible_text: `连线数 ${e0} → ${e1}`,
    });
  });

  // ── E4 ⌘G 成组
  await safe('E4-group', '⌘G 成组', '多选状态下按 ⌘G', async () => {
    const g0 = await groupCount(); const n0 = await nodeCount();
    await page.keyboard.press('Meta+g');
    await page.waitForTimeout(2500);
    const g1 = await groupCount(); const n1 = await nodeCount();
    await shot(page, 'K-03-成组后.png');
    await logStep(B, {
      id: 'E4-group',
      title: '⌘G 成组',
      target: `多选（${await selCount()} 个）状态下按 ⌘G`,
      evidence: { groupsBefore: g0, groupsAfter: g1, nodesBefore: n0, nodesAfter: n1 },
      visible_text: `成组元素数 ${g0} → ${g1}；节点总数 ${n0} → ${n1}`,
      shot: 'K-03-成组后.png',
    });
  });

  // ── E5 ⌘⌥G 合并分镜组
  await safe('E5-merge-storyboard-group', '⌘⌥G 合并分镜组', '按 ⌘⌥G', async () => {
    const before = await nodesOf();
    await page.keyboard.press('Meta+Alt+KeyG');
    await page.waitForTimeout(2500);
    const after = await nodesOf();
    await logStep(B, {
      id: 'E5-merge-storyboard-group',
      title: '⌘⌥G 合并分镜组',
      target: '按 ⌘⌥G',
      evidence: {
        nodeCountBefore: before.length, nodeCountAfter: after.length,
        groupsAfter: await groupCount(),
        toast: await page.evaluate(() => [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"]')]
          .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 80))),
      },
      visible_text: `节点数 ${before.length} → ${after.length}；分组元素 ${await groupCount()} 个`,
    });
  });

  // ── E6 ⌘⇧G 解组
  await safe('E6-ungroup', '⌘⇧G 解组', '按 ⌘⇧G', async () => {
    const g0 = await groupCount(); const n0 = await nodeCount();
    await page.keyboard.press('Meta+Shift+KeyG');
    await page.waitForTimeout(2500);
    const g1 = await groupCount(); const n1 = await nodeCount();
    await logStep(B, {
      id: 'E6-ungroup',
      title: '⌘⇧G 解组',
      target: '按 ⌘⇧G',
      evidence: { groupsBefore: g0, groupsAfter: g1, nodesBefore: n0, nodesAfter: n1 },
      visible_text: `分组元素数 ${g0} → ${g1}；节点总数 ${n0} → ${n1}`,
    });
  });

  // ── E7 ⌘D 复制节点和连线（单选即可）
  await safe('E7-duplicate', '⌘D 复制节点和连线', '单击选中一个节点后按 ⌘D', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const n0 = await nodeCount();
    await page.locator('.react-flow__node').first().click({ force: true });
    await page.waitForTimeout(800);
    const sel = await selCount();
    await page.keyboard.press('Meta+d');
    await page.waitForTimeout(2500);
    const n1 = await nodeCount();
    await logStep(B, {
      id: 'E7-duplicate',
      title: '⌘D 复制节点和连线',
      target: `单击选中 ${sel} 个节点后按 ⌘D`,
      evidence: { nodesBefore: n0, nodesAfter: n1, edges: await edgeCount() },
      visible_text: `节点数 ${n0} → ${n1}；当前连线数 ${await edgeCount()}`,
    });
  });

  // ── E8 ⌘Z 撤销 / E9 ⌘⇧Z 重做
  await safe('E8-undo', '⌘Z 撤销', '按 ⌘Z', async () => {
    const n0 = await nodeCount();
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(2200);
    await logStep(B, {
      id: 'E8-undo',
      title: '⌘Z 撤销',
      target: '在 ⌘D 复制之后按 ⌘Z',
      evidence: { nodesBefore: n0, nodesAfter: await nodeCount() },
      visible_text: `节点数 ${n0} → ${await nodeCount()}`,
    });
  });
  await safe('E9-redo', '⌘⇧Z 重做', '按 ⌘⇧Z', async () => {
    const n0 = await nodeCount();
    await page.keyboard.press('Meta+Shift+KeyZ');
    await page.waitForTimeout(2200);
    await logStep(B, {
      id: 'E9-redo',
      title: '⌘⇧Z 重做',
      target: '在 ⌘Z 撤销之后按 ⌘⇧Z',
      evidence: { nodesBefore: n0, nodesAfter: await nodeCount() },
      visible_text: `节点数 ${n0} → ${await nodeCount()}`,
    });
  });

  // ── E10 ⌘F 画布节点搜索
  await safe('E10-search', '⌘F 画布节点搜索', '按 ⌘F', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    await page.keyboard.press('Meta+f');
    await page.waitForTimeout(1800);
    const st = await page.evaluate(() => ({
      visibleInputs: [...document.querySelectorAll('input')]
        .filter((i) => i.getBoundingClientRect().width > 4)
        .map((i) => i.getAttribute('aria-label') || i.placeholder || '(无标签)').slice(0, 8),
      dialogs: [...document.querySelectorAll('[role="dialog"],[class*="Popover"],[class*="Search"]')]
        .filter((d) => d.getBoundingClientRect().width > 40)
        .map((d) => (d.innerText || '').replace(/\s+/g, ' ').slice(0, 120)).slice(0, 4),
    }));
    await shot(page, 'K-04-节点搜索.png');
    await logStep(B, {
      id: 'E10-search',
      title: '⌘F 画布节点搜索',
      target: '按 ⌘F',
      evidence: st,
      visible_text: `可见输入框 ${JSON.stringify(st.visibleInputs)}；弹出层 ${JSON.stringify(st.dialogs)}`,
      shot: 'K-04-节点搜索.png',
    });
  });

  // ── E11 Tab 新建节点
  await safe('E11-tab-new-node', 'Tab 新建节点', '焦点在画布时按 Tab', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(800);
    const n0 = await nodeCount();
    await page.keyboard.press('Tab');
    await page.waitForTimeout(1800);
    const panel = await page.evaluate(() => {
      const p = document.querySelector('[data-guide-lockable-portal="true"],[data-canvas-menu-portal="true"]');
      return p && p.getBoundingClientRect().width > 40 ? (p.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    });
    await shot(page, 'K-05-Tab新建节点.png');
    await logStep(B, {
      id: 'E11-tab-new-node',
      title: 'Tab 新建节点',
      target: '按 Tab',
      evidence: { nodesBefore: n0, nodesAfter: await nodeCount(), panelText: panel },
      visible_text: `节点数 ${n0} → ${await nodeCount()}；弹出面板 ${JSON.stringify(panel)}`,
      shot: 'K-05-Tab新建节点.png',
    });
  });
  await page.keyboard.press('Escape').catch(() => {});

  // ── E12 Option + 拖动节点 = 节点复制
  await safe('E12-opt-drag-copy', 'Option + 拖动节点（节点复制）', '按住 Option 拖动一个节点', async () => {
    await page.waitForTimeout(600);
    const n0 = await nodeCount();
    const first = (await nodesOf())[0];
    if (!first) throw new Error('画布上没有节点可拖');
    const cx = Math.round(first.x + Math.min(120, first.w / 2));
    const cy = Math.round(first.y + 18);
    await page.keyboard.down('Alt');
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    await page.waitForTimeout(200);
    await page.mouse.move(cx + 180, cy + 120, { steps: 24 });
    await page.waitForTimeout(300);
    await page.mouse.up();
    await page.keyboard.up('Alt');
    await page.waitForTimeout(2000);
    await logStep(B, {
      id: 'E12-opt-drag-copy',
      title: 'Option + 拖动节点（节点复制）',
      target: `按住 Option 从 (${cx},${cy}) 拖到 (+180,+120)`,
      evidence: { nodesBefore: n0, nodesAfter: await nodeCount() },
      visible_text: `节点数 ${n0} → ${await nodeCount()}`,
    });
  });

  // ── E13 Space 临时平移
  await safe('E13-space-pan', 'Space 临时平移', '按住 Space 拖动画布', async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const vp0 = await viewportTransform();
    await page.keyboard.down('Space');
    await page.waitForTimeout(200);
    await dragTo({ x: 1300, y: 750 }, { x: 1150, y: 680 });
    await page.keyboard.up('Space');
    await page.waitForTimeout(800);
    const vp1 = await viewportTransform();
    await logStep(B, {
      id: 'E13-space-pan',
      title: 'Space 临时平移',
      target: '按住 Space 在空白处拖动',
      evidence: { viewportBefore: vp0, viewportAfter: vp1, changed: vp0 !== vp1 },
      visible_text: `视口是否被平移：${vp0 !== vp1}`,
    });
  });

  // ── E14 V / H 工具切换
  await safe('E14-vh-tools', 'V 移动 / H 抓手工具切换', '依次按 V、H，再按 V 复位', async () => {
    const probe = () => page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
      .filter((b) => b.getBoundingClientRect().width > 0 && b.getBoundingClientRect().y > 640)
      .map((b) => ({
        t: (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 10),
        active: /active|selected|is-on|data-active=true/.test(b.className || '') || b.getAttribute('aria-pressed') === 'true',
      })).slice(0, 12));
    const base = await probe();
    await page.mouse.click(1200, 780).catch(() => {});
    await page.keyboard.press('KeyV');
    await page.waitForTimeout(700);
    const afterV = await probe();
    await page.keyboard.press('KeyH');
    await page.waitForTimeout(700);
    const afterH = await probe();
    await page.keyboard.press('KeyV');
    await page.waitForTimeout(700);
    await logStep(B, {
      id: 'E14-vh-tools',
      title: 'V 移动 / H 抓手工具切换',
      target: '依次按 V、H、V',
      evidence: {
        base: base.filter((b) => b.active).map((b) => b.t),
        afterV: afterV.filter((b) => b.active).map((b) => b.t),
        afterH: afterH.filter((b) => b.active).map((b) => b.t),
        allBottomButtons: base.map((b) => b.t),
      },
      visible_text: `底部工具条按钮: ${JSON.stringify(base.map((b) => b.t))}；按 V 后 active=${JSON.stringify(afterV.filter((b) => b.active).map((b) => b.t))}；按 H 后 active=${JSON.stringify(afterH.filter((b) => b.active).map((b) => b.t))}`,
    });
  });

  await page.keyboard.press('Meta+0').catch(() => {});
  await page.waitForTimeout(1000);
  await shot(page, 'K-06-本批最终画布状态.png');
  console.log('\n最终画布:', page.url());
  console.log('最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
