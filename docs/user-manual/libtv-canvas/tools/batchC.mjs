// Batch C —— 连线 + 选中态节点编辑器。
//
// 一趟干两件事，因为建节点本身就要好几分钟：
//  1. 文本 / 图片 / 视频 三个节点**选中态**的完整编辑器特写（折叠态只露出「尝试：」，
//     选中后才会展开提示词框、参考/标记/特效、底部参数条 —— 那才是手册要讲的面）；
//  2. 从图片节点的输出端口拖到视频节点的输入端口，验证连线语义与视觉。
//
// 全程只读不提交：不点任何生成按钮。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, shotHighlighted, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const SHOTS = resolve(HERE, '../screenshots');
const SPACE = '10354929';
const B = 'batchC';

const PLAN = [
  ['文本', '文本节点', 'F-01-文本节点-展开'],
  ['图片', '图片节点', 'F-02-图片节点-展开'],
  ['视频', '视频节点', 'F-03-视频节点-展开'],
];

async function createNode(page, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click({ timeout: 10000 });
  await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2400);
}

/** 严格按节点 data-id 取元素，避免 hasText 子串误匹配
 *  （'视频节点' 会命中「请连接视频节点后操作」的智能剪辑节点，实测踩过）。 */
const nodeEl = (page, titlePrefix) =>
  page.evaluateHandle((p) => [...document.querySelectorAll('.react-flow__node')]
    .find((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p)) || null, titlePrefix);

const { browser, page } = await launch();

try {
  // 现场新建一张干净画布，保证起点确定
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1000);
  await beginBatch(B, { note: '选中态节点编辑器 + 连线；不提交生成' });

  for (const [item, prefix, base] of PLAN) {
    await createNode(page, item);
    const h = await nodeEl(page, prefix);
    const el = h.asElement();
    if (!el) { console.log('未找到节点', prefix); continue; }
    await el.click();
    await page.waitForTimeout(2000);
    // 选中后卡片会展开，重新取一次元素再截
    const h2 = await nodeEl(page, prefix);
    const el2 = h2.asElement();
    if (el2) await el2.screenshot({ path: resolve(SHOTS, `${base}.png`) }).catch((e) => console.log('截图失败', e.message.slice(0, 60)));
    await logStep(B, {
      id: `F-${item}`,
      title: `${item}节点（选中后展开）`,
      target: `添加节点 → ${item} → 点击节点`,
      visible_text: await page.evaluate((p) => {
        const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
        return n ? (n.innerText || '').replace(/\s+/g, ' ').slice(0, 1200) : null;
      }, prefix),
      shot: `${base}.png`,
    });
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(400);
  }

  console.log('节点数:', await nodeCount(page));

  // ── 连线：图片节点输出端口 → 视频节点输入端口
  const handles = await page.evaluate(() =>
    [...document.querySelectorAll('.react-flow__node')].map((n) => ({
      title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      handles: [...n.querySelectorAll('.react-flow__handle')].map((h) => {
        const r = h.getBoundingClientRect();
        return { cls: (h.className || '').toString().replace(/[\w-]*css-\w+/g, '').slice(0, 60), id: h.getAttribute('data-handleid'), pos: h.getAttribute('data-handlepos'), xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }),
    })),
  );
  console.log('端口:', JSON.stringify(handles, null, 1));

  const img = handles.find((h) => h.title.startsWith('图片节点'));
  const vid = handles.find((h) => h.title.startsWith('视频节点'));
  if (img && vid) {
    const out = img.handles.find((h) => h.pos === 'right') || img.handles[img.handles.length - 1];
    const inp = vid.handles.find((h) => h.pos === 'left') || vid.handles[0];
    await page.mouse.move(out.xy[0], out.xy[1]);
    await page.waitForTimeout(300);
    await page.mouse.down();
    await page.mouse.move(inp.xy[0], inp.xy[1], { steps: 24 });
    await page.waitForTimeout(500);
    await page.mouse.up();
    await page.waitForTimeout(2200);
    const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    await shot(page, 'F-04-节点连线.png');
    await logStep(B, {
      id: 'F-connect',
      title: '连线：图片节点输出 → 视频节点输入',
      target: `${out.cls} (${out.pos}) → ${inp.cls} (${inp.pos})`,
      evidence: { edgeCount: edges, from: out, to: inp },
      visible_text: `画布上的连线数: ${edges}`,
      shot: 'F-04-节点连线.png',
    });
  }
} finally {
  await browser.close();
}
