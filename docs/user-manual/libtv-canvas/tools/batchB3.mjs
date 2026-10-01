// Batch B（三）—— 九类节点最终配图：每类建一次 → ⌘0 适应画布 → 全节点入镜截图 → 清场。
//
// 与 B2 的差别只有一个关键点：**截图前先 fitView()**。
// 节点按点击落点放置且卡片很大，100% 缩放下大半张在视口外（见 B2 的 B-n2-图片），
// 这种图不能当正文插图。
//
// 另修 B2 的两处：脚本 是带子菜单的入口（点击只展开子菜单），清场有时漏删残留节点。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { SHOTS } from './lib.mjs';
import { resolve } from 'node:path';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted } from './scenario.mjs';
import { nodeCount, listNodes, clearCanvas, addNode, readNodeControls, fitView } from './canvas-ops.mjs';

const B = 'batchB3';
await beginBatch(B, { note: '九类节点终版配图（fitView 后）+ 脚本子菜单' });

const { browser, page } = await launch();

/** 建节点；带子菜单的入口（脚本 / 素材库）需要再点一次子项。 */
async function createNode(page, name, sub = null) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);
  const addBtn = page.getByRole('button', { name: '添加节点', exact: true }).first();
  await addBtn.scrollIntoViewIfNeeded().catch(() => {});
  await addBtn.click({ timeout: 10000 });
  await page.waitForTimeout(900);
  const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  const item = panel.getByText(name, { exact: false }).first();
  await item.click({ timeout: 6000 });
  await page.waitForTimeout(1000);
  if (sub) {
    const subItem = page.getByText(sub, { exact: false }).first();
    if (await subItem.count()) {
      await subItem.click({ timeout: 6000 });
      await page.waitForTimeout(1500);
    }
  }
  await page.waitForTimeout(1400);
}

const PLAN = [
  ['文本', null, 'C-01-文本节点.png'],
  ['图片', null, 'C-02-图片节点.png'],
  ['视频', null, 'C-03-视频节点.png'],
  ['智能剪辑', null, 'C-04-智能剪辑节点.png'],
  ['导演台', null, 'C-05-导演台节点.png'],
  ['逐帧拉片', null, 'C-06-逐帧拉片节点.png'],
  ['音频', null, 'C-07-音频节点.png'],
];

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);

  await clearCanvas(page);
  await fitView(page);
  await logStep(B, {
    id: 'C0-empty', title: '空画布基线（⌘0 适应画布后）',
    target: '⌘0',
    evidence: { nodes: await listNodes(page) },
    shot: await shot(page, 'C-00-空画布.png'),
  });

  for (const [name, sub, file] of PLAN) {
    await clearCanvas(page);
    await fitView(page);
    await createNode(page, name, sub);
    await fitView(page);
    const ctl = await readNodeControls(page, 0);
    await shot(page, file);
    // 元素特写：只框住节点本身。节点卡片比视口还大，概览图必然拍不全；
    // 正文插图用这张，比整页截图干净得多。
    const nodeEl = page.locator('.react-flow__node').first();
    if (await nodeEl.count()) {
      await nodeEl.screenshot({ path: resolve(SHOTS, file.replace('.png', '-特写.png')) })
        .catch((e) => console.log('  元素截图失败:', e.message.slice(0, 80)));
    }
    await logStep(B, {
      id: `C-${name}`,
      title: `${name}节点（⌘0 适配后整卡入镜）`,
      target: `添加节点 → ${name}`,
      evidence: { nodeCount: await nodeCount(page), buttons: ctl.buttons, roles: ctl.roles, inputs: ctl.inputs },
      visible_text: ctl.text,
      shot: file,
    });
  }

  // 脚本：带子菜单
  await clearCanvas(page);
  await fitView(page);
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click();
  await page.waitForTimeout(900);
  const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  await panel.getByText('脚本', { exact: false }).first().click();
  await page.waitForTimeout(1200);
  const subItems = await page.evaluate(() => {
    const portals = [...document.querySelectorAll('[data-guide-lockable-portal="true"],[data-canvas-menu-portal="true"]')];
    return portals.map((p) => (p.innerText || '').replace(/\s+/g, ' ').slice(0, 300));
  });
  await shot(page, 'C-08-脚本子菜单.png');
  await logStep(B, {
    id: 'C-脚本-submenu', title: '脚本：入口带子菜单，先展开再选',
    target: '添加节点 → 脚本（右侧有 ›）',
    evidence: { portalTexts: subItems },
    visible_text: subItems.join(' || '),
    shot: 'C-08-脚本子菜单.png',
  });

  // 素材库子菜单
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click();
  await page.waitForTimeout(900);
  const panel2 = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  await panel2.getByText('素材库', { exact: false }).first().click();
  await page.waitForTimeout(1200);
  const libItems = await page.evaluate(() => {
    const portals = [...document.querySelectorAll('[data-guide-lockable-portal="true"],[data-canvas-menu-portal="true"]')];
    return portals.map((p) => (p.innerText || '').replace(/\s+/g, ' ').slice(0, 300));
  });
  await shot(page, 'C-09-素材库子菜单.png');
  await logStep(B, {
    id: 'C-素材库-submenu', title: '素材库：入口带子菜单',
    target: '添加节点 → 素材库（右侧有 ›）',
    evidence: { portalTexts: libItems },
    visible_text: libItems.join(' || '),
    shot: 'C-09-素材库子菜单.png',
  });
} finally {
  await browser.close();
}
