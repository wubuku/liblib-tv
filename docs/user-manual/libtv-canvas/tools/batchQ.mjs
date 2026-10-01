// Batch Q —— 补拍「参数面板挂在节点下方」的结构示意图。
//
// batchP 那张最好的图（视频节点 + 整块参数面板）被我误删了，重拍一张。
// 取景要求：同时看得见 ①节点本体 ②挂在它下面的参数面板 ③面板里的字段行。
// 视频节点面板最长（参考/标记/特效/角色库/运镜 + 描述框 + 规格条），最适合当示意图。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchQ';
const { browser, page } = await launch();

/** 节点本体框 + 参数面板卡片的框，用来确认两者是分离的、且都在画面里。 */
const geometry = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => /视频节点/.test(txt(x)));
  if (!n) return { none: true };
  const nr = n.getBoundingClientRect();
  // 参数面板 = class 带 node-floating-ui 的那层
  const panel = document.querySelector('[class*="node-floating-ui"]');
  const pr = panel ? panel.getBoundingClientRect() : null;
  return {
    nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    nodeBottom: Math.round(nr.bottom),
    panelRect: pr ? [Math.round(pr.x), Math.round(pr.y), Math.round(pr.width), Math.round(pr.height)] : null,
    panelTop: pr ? Math.round(pr.top) : null,
    panelInViewport: pr ? pr.top >= 0 && pr.bottom <= window.innerHeight : null,
    panelText: panel ? txt(panel).slice(0, 220) : null,
    nodeAllInViewport: nr.top >= 0 && nr.bottom <= window.innerHeight,
    viewportH: window.innerHeight,
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '重拍参数面板结构示意图' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(700, 150); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('视频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2800);

  // 缩到节点和面板都能完整进画面
  await fitView(page, 1);
  await page.waitForTimeout(1000);
  for (let i = 0; i < 4; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(700); }
  await page.waitForTimeout(1500);
  // 往上平移，让节点顶到画面上部、面板整块露出来
  await page.keyboard.down('Space');
  await page.mouse.move(300, 600); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 5; i += 1) { await page.mouse.move(300, 600 - i * 22, { steps: 2 }); await page.waitForTimeout(60); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1500);

  // 点开参数面板（视频节点折叠态要点一下才展开）
  const g0 = await geometry();
  console.log('点开前:', JSON.stringify(g0));
  if (g0.none) throw new Error('没建出视频节点');
  if (g0.panelRect && g0.panelRect[3] < 120) {
    await page.locator('.react-flow__node').first().click({ position: { x: 240, y: 120 }, timeout: 8000 });
    await page.waitForTimeout(2600);
  }
  // 面板展开后画面会变高，再微调一次平移
  for (let k = 0; k < 4; k += 1) {
    const g = await geometry();
    if (g.nodeAllInViewport && g.panelInViewport) { console.log(`微调 ${k} 次后两者都在画面里`); break; }
    await page.keyboard.down('Space');
    await page.mouse.move(300, 600); await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move(300, 600 - 20, { steps: 6 }); await page.mouse.up(); await page.keyboard.up('Space');
    await page.waitForTimeout(1200);
  }
  const g = await geometry();
  console.log('最终:', JSON.stringify(g));
  await shot(page, 'M-20-参数面板挂在节点下方.png');

  await logStep(B, { id: 'Q-panel-geometry', title: '参数面板是挂在节点下方的独立卡片（重拍结构图）',
    target: '建一个视频节点，展开参数面板，量两个框的相对位置',
    evidence: { before: g0, after: g },
    visible_text: `节点本体 ${JSON.stringify(g.nodeRect)}（底边 y=${g.nodeBottom}）；` +
      `参数面板 ${JSON.stringify(g.panelRect)}（顶边 y=${g.panelTop}）；` +
      `**面板顶边比节点底边低 ${g.panelTop - g.nodeBottom}px，说明是挂在下面而非长在节点里**；` +
      `两者是否都在 ${g.viewportH}px 画面内：节点 ${g.nodeAllInViewport}、面板 ${g.panelInViewport}`,
    shot: 'M-20-参数面板挂在节点下方.png' });
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
