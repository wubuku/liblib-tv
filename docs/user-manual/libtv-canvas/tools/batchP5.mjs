// Batch P5 —— 参数面板的真实结构：它是挂在节点**下方**的一张独立卡片。
//
// batchP4 的截图把话说明白了：音频节点本体（615×615）只画到「尝试：音频生视频」，
// 底下**另有一张卡片**（「+参考」「描述你想要的音频效果，可用 @ 引用音频」），
// 它的右下角还有一个 `⤢` 图标。参数面板就在这张卡片里，
// 位置在视口 810px 之下 —— 所以：
//   · `innerText` 读得到「高级设置 语速 声调 音量」（它在 DOM 里）
//   · 但 `node.getBoundingClientRect()` **不包含它**（它不在节点框内）
//   · 前几轮我一直在节点框里找滑杆，**找错地方了**
//
// 这轮：把画布缩到能一眼看全，然后
//   ① 量出「节点本体」和「参数面板」两个框的相对位置
//   ② 用 role="slider" / [class*=Slider] 找滑杆（Mantine 的滑杆不是 input[type=range]）
//   ③ 点右下角那个 ⤢，看它是展开还是收起
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP5';
const { browser, page } = await launch();

/** 节点本体 + 它下面那张参数面板，一起量。 */
const layout = () => page.evaluate(() => {
  const n = [...document.querySelectorAll('.react-flow__node')][0];
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  // 参数面板 = 节点框之外、又紧贴在节点下面的那一大块（按「包含 描述你想要/参考 且在节点下方」认）
  const panels = [...document.querySelectorAll('div')].filter((d) => {
    const b = d.getBoundingClientRect();
    if (b.width < 200 || b.height < 100) return false;
    if (b.y < r.bottom - 20) return false;                       // 必须在节点下方
    if (b.x > r.right + 20 || b.x + b.width < r.left - 20) return false;
    return /参考|描述你想要|高级设置|Seed Audio|Lib Image|文生视频|语速|声调|音量/.test(txt(d));
  }).map((d) => { const b = d.getBoundingClientRect();
    return { cls: (d.className || '').toString().slice(0, 40), text: txt(d).slice(0, 200),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })
    .sort((a, b) => a.rect[3] - b.rect[3]);                       // 挑最小的那个 = 面板本体
  return {
    nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    nodeBottom: Math.round(r.bottom),
    nodeText: txt(n).slice(0, 300),
    panels: panels.slice(0, 3),
    // 全页范围内找滑杆：Mantine 的滑杆是 div + role="slider"，不是 input[type=range]
    sliders: [...document.querySelectorAll('[role="slider"],[class*="Slider"],[class*="slider"]')]
      .map((e) => { const b = e.getBoundingClientRect();
        return { role: e.getAttribute('role'), aria: e.getAttribute('aria-label') || e.getAttribute('aria-valuenow'),
          ariaNow: e.getAttribute('aria-valuenow'), ariaMin: e.getAttribute('aria-valuemin'), ariaMax: e.getAttribute('aria-valuemax'),
          cls: (e.className || '').toString().slice(0, 34),
          rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })
      .filter((s) => s.rect[2] > 40 && s.rect[3] > 2),
    numbers: [...document.querySelectorAll('input[type="number"]')].map((e) => ({ aria: e.getAttribute('aria-label'), value: e.value, min: e.min, max: e.max })),
    // 参数面板右下角那个展开/收起图标
    expander: (() => {
      const cands = [...document.querySelectorAll('div,button,svg')].filter((e) => {
        const b = e.getBoundingClientRect();
        return b.width >= 12 && b.width <= 44 && b.height >= 12 && b.height <= 44 && b.y > r.bottom - 10;
      });
      const c = cands[cands.length - 1];
      if (!c) return null;
      const b = c.getBoundingClientRect();
      return { tag: c.tagName, cls: (c.className || '').toString().slice(0, 40),
        x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        w: Math.round(b.width), h: Math.round(b.height),
        inViewport: b.y >= 0 && b.bottom <= window.innerHeight };
    })(),
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '量节点本体与参数面板两个框；用 role=slider 找滑杆；试右下角 ⤢' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(420, 300); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2600);

  // 缩到能一眼看全（参数面板挂在下面，默认缩放会把它顶出视口）
  await fitView(page, 1);
  for (let i = 0; i < 3; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(500); }
  await page.waitForTimeout(1800);

  const L = await layout();
  console.log('节点框:', JSON.stringify(L.nodeRect), '底边 y =', L.nodeBottom);
  console.log('参数面板候选:', JSON.stringify(L.panels, null, 1));
  console.log('滑杆:', JSON.stringify(L.sliders, null, 1));
  console.log('数字框:', JSON.stringify(L.numbers));
  console.log('展开图标:', JSON.stringify(L.expander));
  await shot(page, 'M-22-音频节点-完整面板.png');

  // 点右下角 ⤢，看它做什么
  let afterExpander = null;
  if (L.expander && L.expander.inViewport) {
    const before = await layout();
    await page.mouse.click(L.expander.x, L.expander.y);
    await page.waitForTimeout(2600);
    afterExpander = await layout();
    await shot(page, 'M-23-音频节点-点展开图标之后.png');
    console.log('\n点 ⤢ 后：节点框', JSON.stringify(afterExpander.nodeRect),
      '滑杆数', afterExpander.sliders.length, '面板候选数', afterExpander.panels.length);
  }

  await logStep(B, { id: 'P5-audio-panel', title: '音频节点：参数面板是挂在节点下方的独立卡片',
    target: '只放一个音频节点，缩到能看全，量「节点本体」与「参数面板」两个框，并找滑杆',
    evidence: { layout: L, afterExpander },
    visible_text: `节点本体 ${JSON.stringify(L.nodeRect)}（底边 y=${L.nodeBottom}）；` +
      `参数面板 ${JSON.stringify(L.panels[0] ? L.panels[0].rect : null)}，内容 ${JSON.stringify(L.panels[0]?.text)}；` +
      `**滑杆 ${L.sliders.length} 个** ${JSON.stringify(L.sliders.map((s) => [s.role, s.aria, s.rect]))}；` +
      `数字框 ${L.numbers.length} 个；右下角展开图标 ${JSON.stringify(L.expander)}` +
      (afterExpander ? `；点 ⤢ 后滑杆数 ${afterExpander.sliders.length}、面板候选 ${afterExpander.panels.length}` : ''),
    shot: 'M-22-音频节点-完整面板.png' });
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
