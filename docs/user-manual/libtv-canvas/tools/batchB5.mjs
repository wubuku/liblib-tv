// Batch B（五）—— 在一张**干净画布**上重跑九类节点，产出可用于正文的总览图。
//
// batchB4 的元素特写全部成功，但那张画布已经堆到 19 个节点（历轮残留），
// 总览图没法用。这一版先确保画布是空的：逐张打开候选画布，挑节点数为 0 的那张；
// 都脏就现场新建一张（新建出来的一定是空的），并把新 projectId 记进台账。
import { launch, open } from './lib.mjs';
import { CANVAS_URL, TEST } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot } from './scenario.mjs';
import { nodeCount, listNodes } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const B = 'batchB5';
await beginBatch(B, { note: '干净画布上的九类节点总览' });

const { browser, page } = await launch();
const HERE = dirname(fileURLToPath(import.meta.url));

const PLAN = [
  ['文本', '文本节点', 'D-01-文本'],
  ['图片', '图片节点', 'D-02-图片'],
  ['视频', '视频节点', 'D-03-视频'],
  ['智能剪辑', '智能剪辑', 'D-04-智能剪辑'],
  ['导演台', '导演台', 'D-05-导演台'],
  ['逐帧拉片', '逐帧拉片', 'D-06-逐帧拉片'],
  ['音频', '音频节点', 'D-07-音频'],
];

const countIn = async (pid) => {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${TEST.spaceId}&projectId=${pid}`, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1000);
  return nodeCount(page);
};

try {
  // 1) 找一张干净画布
  const candidates = [TEST.projectId, '34226ef170f248248c74f85290228f6b'];
  let clean = null;
  for (const pid of candidates) {
    const n = await countIn(pid);
    console.log(`候选 ${pid} → ${n} 个节点`);
    if (n === 0) { clean = pid; break; }
  }

  if (!clean) {
    // 都不干净：在当前画布上新建一张
    await openDropdown(page, 1000);
    await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
    await page.waitForTimeout(3500);
    clean = page.url().match(/projectId=([a-f0-9]+)/)?.[1] || null;
    console.log('新建画布 projectId =', clean);
    await writeFile(resolve(HERE, '.auth/clean-canvas-id.txt'), String(clean), 'utf8');
  }

  console.log('选定干净画布:', clean);
  await open(page, `https://www.liblib.tv/canvas?spaceId=${TEST.spaceId}&projectId=${clean}`, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);

  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(400); }

  await shot(page, 'D-00-空画布-干净.png');
  await logStep(B, {
    id: 'D0-clean', title: '干净画布基线',
    target: `projectId=${clean}`,
    evidence: { nodes: await listNodes(page), url: page.url() },
    shot: 'D-00-空画布-干净.png',
  });

  for (const [item, prefix, base] of PLAN) {
    await page.keyboard.press('Escape').catch(() => {});
    await page.getByRole('button', { name: '添加节点', exact: true }).first().click({ timeout: 10000 });
    await page.waitForTimeout(1000);
    const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
    await panel.getByText(item, { exact: false }).first().click({ timeout: 6000 });
    await page.waitForTimeout(2400);
    const el = page.locator('.react-flow__node').filter({ hasText: prefix }).first();
    if (await el.count()) {
      await el.screenshot({ path: resolve(HERE, '../screenshots', `${base}-节点特写.png`) }).catch(() => {});
    }
  }

  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1400);
  await shot(page, 'D-99-九类节点总览.png');
  await logStep(B, {
    id: 'D99-overview', title: '九类节点同框总览（干净画布）',
    target: '⌘0 适应画布',
    evidence: { nodes: await listNodes(page), count: await nodeCount(page) },
    shot: 'D-99-九类节点总览.png',
  });
} finally {
  await browser.close();
}
