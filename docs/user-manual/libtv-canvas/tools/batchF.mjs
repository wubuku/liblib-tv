// Batch F —— 补三块还没进过的工作区，以及组操作条剩下的菜单。
//
//   F1 **导演台三维工作区**：create-nodes.md 里一直写着「本手册本轮没有进入」，
//      task-inventory 里的 director-3d 标的是 excluded —— 原因是「还没做」不是「测不了」。
//      这一轮进去，把壳、面板、退出方式全部读出来。
//   F2 **组操作条剩下的两个菜单**：「布局下拉」和「添加到工具箱」的内容。
//      「整组执行」会跑生成扣积分，永远不点。
//   F3 **素材库面板**（风格库 / 特效库）与 **角色造型室** 面板的完整控件。
//
// 安全边界：不点「整组执行」/「开始拉片」/ 任何生成按钮；不提交任何表单；
// 导演台里只看不建场景。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchF';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
/** 全屏浮层的存在性 + 里面看得见的一切。 */
const overlay = () => page.evaluate(() => {
  const cands = [...document.querySelectorAll('div,section,aside')]
    .filter((e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return r.width >= window.innerWidth * 0.85 && r.height >= window.innerHeight * 0.7 && s.visibility !== 'hidden' && +s.opacity > 0.1; })
    .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
                  - (a.getBoundingClientRect().width * a.getBoundingClientRect().height));
  if (!cands.length) return null;
  const host = cands[0];
  const r = host.getBoundingClientRect();
  return {
    cls: (host.className || '').toString().slice(0, 80),
    text: (host.innerText || '').replace(/\s+/g, ' ').slice(0, 700),
    buttons: [...host.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"]')]
      .filter((b) => b.getBoundingClientRect().width > 0)
      .map((b) => ({ t: (b.getAttribute('aria-label') || b.title || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
        data: [...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).join(' ') }))
      .filter((b) => b.t).slice(0, 40),
    inputs: [...host.querySelectorAll('input,textarea')]
      .filter((i) => i.getBoundingClientRect().width > 0)
      .map((i) => i.getAttribute('aria-label') || i.placeholder || '(无标签)').slice(0, 10),
    canvases: host.querySelectorAll('canvas').length,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
  };
});
/** 整页可见文字（用于抓全屏工作区的文案）。 */
const pageText = () => page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 1200));
const canvasInfo = () => page.evaluate(() => [...document.querySelectorAll('canvas')].map((c) => {
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  return { w: c.width, h: c.height, cssW: Math.round(c.getBoundingClientRect().width), cssH: Math.round(c.getBoundingClientRect().height),
    renderer: gl ? (gl.getExtension('WEBGL_debug_renderer_info') ? gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL) : 'n/a') : 'NO_WEBGL' };
}));

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
  await beginBatch(B, { note: '导演台 3D 工作区 + 组操作条剩余菜单 + 素材库/角色造型室；全程只读，不触发任何生成' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(700, 320, '导演台');
  await fitView(page, 1); await page.waitForTimeout(1200);
  console.log('节点:', JSON.stringify(await nodesOf()));

  // ── F1 打开导演台三维工作区
  await safe('F1-director-3d', '导演台三维工作区', '点导演台节点里的「打开导演台」', async () => {
    const before = { nodes: await N(), url: page.url(), overlay: await overlay() };
    const btn = page.getByRole('button', { name: /打开导演台/ }).first();
    const found = await btn.count();
    if (!found) throw new Error('节点上找不到「打开导演台」按钮');
    await btn.click({ timeout: 6000 });
    await page.waitForTimeout(6000);
    const ov = await overlay();
    const txt = await pageText();
    const gl = await canvasInfo();
    await shot(page, 'L-01-导演台三维工作区.png');
    await logStep(B, {
      id: 'F1-director-3d', title: '导演台三维工作区', target: '点导演台节点里的「打开导演台」',
      evidence: { buttonFound: found, urlBefore: before.url, urlAfter: page.url(),
        nodesBefore: before.nodes, nodesAfter: await N(),
        overlay: ov, webgl: gl, fullPageText: txt },
      visible_text: `进入后 URL ${page.url() === before.url ? '未变' : '已变'}；全屏浮层 ${ov ? '有' : '无'}；canvas ${JSON.stringify(gl)}；页面文案 ${JSON.stringify(txt.slice(0, 300))}`,
      shot: 'L-01-导演台三维工作区.png',
    });
  });

  // ── F1b 在工作区里把看得见的控件都列一遍（多等一会儿让 3D 场景加载完）
  await safe('F1b-director-3d-controls', '导演台工作区的控件清单', '进入后逐层读可见按钮/输入框/标签页', async () => {
    await page.waitForTimeout(5000);
    const ov = await overlay();
    await shot(page, 'L-02-导演台-控件.png');
    await logStep(B, {
      id: 'F1b-director-3d-controls', title: '导演台工作区的控件清单', target: '进入后读浮层内所有可见控件',
      evidence: { overlay: ov, pageText: await pageText(), webgl: await canvasInfo() },
      visible_text: ov ? `按钮 ${JSON.stringify(ov.buttons.map((b) => b.t))}；输入框 ${JSON.stringify(ov.inputs)}；文案 ${JSON.stringify(ov.text.slice(0, 300))}` : '没有全屏浮层',
      shot: 'L-02-导演台-控件.png',
    });
  });

  // ── F1c 怎么退出？（角色造型室已知 Esc 关不掉，导演台要单独测）
  await safe('F1c-exit-director', '怎么退出导演台工作区', '先按 Esc；还在就找可见的关闭/返回按钮', async () => {
    await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
    const afterEsc = await overlay();
    let clicked = null;
    if (afterEsc) {
      const cand = await page.evaluate(() => {
        const c = [...document.querySelectorAll('button,[role="button"]')]
          .filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0; })
          .map((b) => ({ t: (b.getAttribute('aria-label') || b.title || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12), x: Math.round(b.getBoundingClientRect().x), y: Math.round(b.getBoundingClientRect().y) }))
          .filter((b) => /关闭|退出|返回|取消|close|back/i.test(b.t));
        return c[0] || null;
      });
      if (cand) { await page.mouse.click(cand.x + 6, cand.y + 6); await page.waitForTimeout(2500); clicked = cand.t; }
    }
    const finalOv = await overlay();
    await logStep(B, {
      id: 'F1c-exit-director', title: '怎么退出导演台工作区', target: '先按 Esc；再找「关闭/退出/返回」类按钮',
      evidence: { overlayAfterEsc: afterEsc, closeButtonFound: clicked, overlayNow: finalOv,
        nodesBack: await N(), url: page.url() },
      visible_text: `Esc 后浮层 ${afterEsc ? '还在' : '已关闭'}；找到关闭按钮 ${JSON.stringify(clicked)}；现在浮层 ${finalOv ? '还在' : '已关闭'}；画布节点数 ${await N()}`,
    });
    if (finalOv) {
      await page.keyboard.press('Escape').catch(() => {});
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(4000);
      await closePromos(page);
      console.log('  已刷新回画布, 节点数:', await N());
    }
  });

  // ── F2 组操作条：「布局下拉」与「添加到工具箱」
  await safe('F2-group-menus', '组操作条的「布局下拉」与「添加到工具箱」', '成组后逐个打开这两个菜单，只读不确认', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    await addNodeAt(300, 300, '文本');
    await addNodeAt(1000, 300, '音频');
    await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);
    const list = await nodesOf();
    const x0 = Math.min(...list.filter((n) => !n.isGroup).map((n) => n.x)) - 14;
    const y0 = Math.min(...list.filter((n) => !n.isGroup).map((n) => n.y)) - 14;
    const x1 = Math.max(...list.filter((n) => !n.isGroup).map((n) => n.x + n.w)) + 14;
    const y1 = Math.max(...list.filter((n) => !n.isGroup).map((n) => n.y + n.h)) + 14;
    const spot = { x: 40, y: 80 };
    await page.keyboard.down('Shift');
    await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(150);
    await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
    await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1300);
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
    await page.keyboard.press('Meta+-'); await page.waitForTimeout(1000);
    const picked = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

    // 「布局下拉」：组节点顶部、位于「整组执行」左边的那枚
    const lay = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const r = g.getBoundingClientRect();
      const all = [...g.querySelectorAll('div,span')].filter((e) => { const b = e.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.x < r.x + 260; });
      return all.map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12),
          x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2), w: Math.round(b.width) }; });
    });
    let layoutMenu = null;
    // 从右往左点（布局下拉在「整组执行」左边，即位置靠左）
    const cand = (lay || []).filter((e) => e.w < 60).sort((a, b) => b.x - a.x);
    for (const c of cand.slice(0, 4)) {
      await page.mouse.click(c.x, c.y);
      await page.waitForTimeout(1200);
      const m = await page.evaluate(() => {
        const el = [...document.querySelectorAll('[role="menu"],[class*="Popover"],[class*="Dropdown"]')].filter((d) => d.getBoundingClientRect().width > 40);
        return el.length ? el[el.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 200) : null;
      });
      if (m) { layoutMenu = { clicked: c, text: m }; break; }
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    }
    if (layoutMenu) await shot(page, 'L-03-组布局下拉.png');
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);

    // 「添加到工具箱」
    const box = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
      if (!g) return null;
      const r = g.getBoundingClientRect();
      const el = [...g.querySelectorAll('div,span')].find((e) => (e.innerText || '').trim() === '添加到工具箱' && e.getBoundingClientRect().y < r.y + 60);
      if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2), disabled: +getComputedStyle(el).opacity < 0.9 };
    });
    let toolbox = null;
    if (box && !box.disabled) {
      await page.mouse.click(box.x, box.y);
      await page.waitForTimeout(2200);
      toolbox = await page.evaluate(() => {
        const el = [...document.querySelectorAll('[role="menu"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"]')]
          .filter((d) => d.getBoundingClientRect().width > 60);
        return el.length ? el[el.length - 1].innerText.replace(/\s+/g, ' ').slice(0, 300) : null;
      });
      await shot(page, 'L-04-添加到工具箱.png');
    }
    await logStep(B, {
      id: 'F2-group-menus', title: '组操作条的「布局下拉」与「添加到工具箱」', target: '成组后逐个打开这两个菜单，只读不确认',
      evidence: { selectedBeforeGroup: picked, groupToolbarElements: lay, layoutMenu, toolboxButton: box, toolboxPanel: toolbox },
      visible_text: `布局下拉 ${JSON.stringify(layoutMenu)}；添加到工具箱按钮 ${JSON.stringify(box)}；面板 ${JSON.stringify(toolbox)}`,
    });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
  });

  // ── F3 素材库面板（风格库 / 特效库）
  await safe('F3-asset-library', '素材库面板', '点底部工具条「素材库」', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    await page.getByRole('button', { name: '素材库', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2500);
    const ov = await overlay();
    const panel = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div,section')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 200 && r.height > 150 && (e.innerText || '').trim().length > 10; })
        .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height) - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
      if (!el) return null;
      return { text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 600),
        tabs: [...el.querySelectorAll('[role="tab"],button')].filter((b) => b.getBoundingClientRect().width > 0)
          .map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14)).filter(Boolean).slice(0, 20) };
    });
    await shot(page, 'L-05-素材库面板.png');
    await logStep(B, {
      id: 'F3-asset-library', title: '素材库面板', target: '点底部工具条「素材库」',
      evidence: { overlay: ov, panel },
      visible_text: `面板 ${JSON.stringify(panel)}`, shot: 'L-05-素材库面板.png',
    });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(800);
  });

  // ── F4 角色造型室（全屏浮层，Esc 关不掉，得显式找关闭按钮）
  await safe('F4-character-studio', '角色造型室', '点底部工具条「角色造型室」', async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(500);
    await page.getByRole('button', { name: '角色造型室', exact: true }).first().click({ timeout: 6000 });
    await page.waitForTimeout(3500);
    const ov = await overlay();
    const panel = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div,section')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 300 && r.height > 200 && (e.innerText || '').trim().length > 20; })
        .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height) - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
      if (!el) return null;
      return { text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 800),
        buttons: [...el.querySelectorAll('button,[role="button"],[role="tab"]')].filter((b) => b.getBoundingClientRect().width > 0)
          .map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14)).filter(Boolean).slice(0, 30),
        inputs: [...el.querySelectorAll('input,textarea')].filter((i) => i.getBoundingClientRect().width > 0)
          .map((i) => i.getAttribute('aria-label') || i.placeholder || '(无标签)').slice(0, 10) };
    });
    await shot(page, 'L-06-角色造型室.png');
    await logStep(B, {
      id: 'F4-character-studio', title: '角色造型室', target: '点底部工具条「角色造型室」',
      evidence: { overlay: ov, panel },
      visible_text: `浮层 ${ov ? '有' : '无'}；面板 ${JSON.stringify(panel)}`, shot: 'L-06-角色造型室.png',
    });
    // 显式找关闭按钮并点掉，别让全屏浮层挡住后续
    const closer = await page.evaluate(() => {
      const c = [...document.querySelectorAll('button,[role="button"]')]
        .filter((b) => b.getBoundingClientRect().width > 0)
        .map((b) => ({ t: (b.getAttribute('aria-label') || b.title || '').trim(), x: Math.round(b.getBoundingClientRect().x), y: Math.round(b.getBoundingClientRect().y) }))
        .filter((b) => /关闭|close/i.test(b.t));
      return c[0] || null;
    });
    if (closer) { await page.mouse.click(closer.x + 6, closer.y + 6); await page.waitForTimeout(1500); }
    await logStep(B, { id: 'F4b-close-character-studio', title: '关掉角色造型室', target: '点它的关闭按钮',
      evidence: { closer, overlayAfter: await overlay() },
      visible_text: `关闭按钮 ${JSON.stringify(closer)}；关闭后浮层 ${(await overlay()) ? '还在' : '已关闭'}` });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
