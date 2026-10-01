// Batch B（定稿）—— 九类节点逐个建一次，每次先清空画布，保证每张截图都从同一状态出发。
//
// 修正 batchB 第一版的四处问题：
//   1. 残留节点不清场 → 每轮开始先 clearCanvas()；
//   2. `button:has-text("音频")` 撞上画布上的「音频生成」快捷芯片 → 改成在面板容器内取文本；
//   3. 抓「最大面板」抓到整页 → 改成直接读 .react-flow__node；
//   4. 双击坐标落在面板上（面板会挡住双击点）→ 先关面板再双击，且双击点选空白处。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted } from './scenario.mjs';
import { nodeCount, listNodes, clearCanvas, addNode, readNodeControls } from './canvas-ops.mjs';

const B = 'batchB2';
await beginBatch(B, { note: '九类节点逐个创建 + 控件字段清单；不提交任何生成' });

const { browser, page } = await launch();

const NODES = [
  ['文本', 'B-n1-文本.png'],
  ['图片', 'B-n2-图片.png'],
  ['视频', 'B-n3-视频.png'],
  ['智能剪辑', 'B-n4-智能剪辑.png'],
  ['导演台', 'B-n5-导演台.png'],
  ['逐帧拉片', 'B-n6-逐帧拉片.png'],
  ['音频', 'B-n7-音频.png'],
  ['脚本', 'B-n8-脚本.png'],
];

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(800);

  const cleared = await clearCanvas(page);
  console.log('清场:', JSON.stringify(cleared));
  await logStep(B, {
    id: 'B0-clear', title: '取证前清场：画布回到空画布状态',
    target: '⌘A 全选 → ⌫ 删除',
    evidence: cleared,
    visible_text: `剩余节点: ${JSON.stringify(await listNodes(page))}`,
    shot: await shot(page, 'B0-empty-canvas.png'),
  });

  for (const [name, file] of NODES) {
    let delta;
    try {
      delta = await addNode(page, name);
    } catch (e) {
      await logStep(B, { id: `B-${name}`, title: `${name}：创建失败`, visible_text: String(e.message).slice(0, 300) });
      continue;
    }
    await page.waitForTimeout(900);
    const ctl = await readNodeControls(page, 0);
    await shot(page, file);
    await logStep(B, {
      id: `B-${name}`,
      title: `${name}节点：创建后画布上多了一个什么`,
      target: `添加节点面板 → ${name}`,
      evidence: { nodeDelta: delta, buttons: ctl.buttons, inputs: ctl.inputs, roles: ctl.roles, ports: ctl.ports?.length, rect: ctl.rect },
      visible_text: ctl.text,
      shot: file,
    });
    await clearCanvas(page);
    await page.waitForTimeout(500);
  }

  // 空画布双击 → 同一个面板（面板锚在双击点）
  await clearCanvas(page);
  await page.waitForTimeout(600);
  await shotHighlighted(page, page.locator('.react-flow__pane').first(), 'B-n0-dblclick-hint.png', { step: 1 });
  await page.mouse.dblclick(520, 300);
  await page.waitForTimeout(1400);
  const panelItems = await page.evaluate(() => {
    const p = document.querySelector('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]');
    return p ? { text: (p.innerText || '').replace(/\s+/g, ' ').slice(0, 400), rect: (() => { const r = p.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null;
  });
  await logStep(B, {
    id: 'B-dblclick', title: '双击空白画布：在落点弹出同一个「添加节点」面板',
    target: '.react-flow__pane 双击 (520,300)',
    evidence: panelItems,
    visible_text: panelItems?.text,
    shot: await shot(page, 'B-n0-dblclick-panel.png'),
  });
} finally {
  await browser.close();
}
