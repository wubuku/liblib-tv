// Batch B（终版）—— 一张画布放齐九类节点，既产出「全类型总览图」，
// 又给每类产出一张**只框住该节点**的元素特写。
//
// 为什么放弃「建一个删一个」：clearCanvas 依赖 ⌘A+⌫，而 ⌘A 的行为随焦点位置变化，
// 连续四轮都没稳定清干净，截图里一直挂着上一轮的残留节点。与其和焦点较劲，
// 不如**一次建齐**：残留问题直接消失，而且「九类节点同框」本身就是手册里最有用的那张图。
//
// 每个节点用「标题前缀」定位自己的元素（.first() 会抓到上一轮残留的那一个）。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot } from './scenario.mjs';
import { SHOTS } from './lib.mjs';
import { nodeCount, listNodes } from './canvas-ops.mjs';
import { resolve } from 'node:path';

// 每一类：面板项文案 → 建出来的节点标题前缀 → 截图文件名
const PLAN = [
  ['文本', '文本节点', 'D-01-文本'],
  ['图片', '图片节点', 'D-02-图片'],
  ['视频', '视频节点', 'D-03-视频'],
  ['智能剪辑', '智能剪辑', 'D-04-智能剪辑'],
  ['导演台', '导演台', 'D-05-导演台'],
  ['逐帧拉片', '逐帧拉片', 'D-06-逐帧拉片'],
  ['音频', '音频节点', 'D-07-音频'],
];

const BATCH = 'batchB4';
await beginBatch(BATCH, { note: '九类节点一次建齐：每类元素特写 + 全类型总览图' });

const { browser, page } = await launch();

async function createNode(page, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click({ timeout: 10000 });
  await page.waitForTimeout(1000);
  const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  await panel.getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2400);
}

/** 按标题前缀找节点元素，避免抓到残留节点。 */
function nodeByTitle(page, prefix) {
  return page.locator('.react-flow__node').filter({ hasText: prefix }).first();
}

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);

  await logStep(BATCH, {
    id: 'D0-baseline', title: '起始状态（专用测试画布）',
    evidence: { nodes: await listNodes(page), url: page.url() },
  });

  for (const [item, prefix, base] of PLAN) {
    await createNode(page, item);
    const el = nodeByTitle(page, prefix);
    const exists = await el.count();
    let shotFile = null;
    if (exists) {
      // 元素特写：只框住这个节点
      shotFile = `${base}-节点特写.png`;
      await el.screenshot({ path: resolve(SHOTS, shotFile) }).catch((e) => console.log('元素截图失败', e.message.slice(0, 70)));
    }
    const ctl = await page.evaluate((p) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
      if (!n) return { none: true };
      const pick = (el) => (el.getAttribute('aria-label') || el.getAttribute('placeholder') || (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ')).slice(0, 40);
      return {
        text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 1500),
        buttons: [...n.querySelectorAll('button')].map(pick).filter(Boolean),
        inputs: [...n.querySelectorAll('input,textarea')].map((e) => ({ type: e.type, aria: e.getAttribute('aria-label'), ph: e.getAttribute('placeholder'), checked: e.checked })),
        roles: [...n.querySelectorAll('[role="combobox"],[role="listbox"],[role="radio"],[role="switch"],[role="slider"]')].map((e) => `${e.getAttribute('role')}:${pick(e)}`),
        handles: n.querySelectorAll('.react-flow__handle').length,
      };
    }, prefix);
    await logStep(BATCH, {
      id: `D-${item}`,
      title: `${item}节点：面板上的全部控件`,
      target: `添加节点 → ${item}`,
      evidence: { found: !!exists, totalNodes: await nodeCount(page), buttons: ctl.buttons, inputs: ctl.inputs, roles: ctl.roles, handles: ctl.handles },
      visible_text: ctl.text,
      shot: shotFile,
    });
  }

  // 九类同框总览
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1200);
  await shot(page, 'D-99-九类节点总览.png');
  await logStep(BATCH, {
    id: 'D99-overview', title: '九类节点同框（⌘0 适应画布后的总览图）',
    target: '⌘0',
    evidence: { nodes: await listNodes(page) },
    shot: 'D-99-九类节点总览.png',
  });
} finally {
  await browser.close();
}
