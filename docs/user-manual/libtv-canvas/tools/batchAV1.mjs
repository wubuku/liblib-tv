// Batch AV1 —— **只 dump，不点**：把参数面板里那些「没有文字的按钮」一个不漏地清点出来。
//
// 为什么盯上它们：M-139 / M-140 两张实拍图里，
//   视频面板底部参数条右侧有**三枚无任何文字的图标按钮**（📄 / 文A / ⚙），
//   音频面板有**两枚**，两个面板右上角各有一枚 `⤢`。
//   **手册一个字都没记过它们** —— 既没说是什么，也没说点了会怎样。
//
// 而「这个产品几乎每枚按钮都有 aria」这条经验（§15）在这里**可能不成立**：
// 无文字的纯图标按钮很可能连 aria 都没有，那就只能靠 **SVG path 的 d 属性**当指纹。
// 所以这一轮把每个可点元素的「图标指纹」也读出来 —— 同样的 d 前缀 = 同一个图标。
//
// ⚠️ 两条硬前提，都是上一批踩出来的：
//   ① **先关掉右侧 TV Director 对话抽屉**（`Esc`），否则面板根本不渲染 —— DOM 读得到、画面上没有。
//   ② 「点之前先验 elementFromPoint 落在目标上」，别把「点偏了」记成「点不动」。
//
// 这一轮**一枚都不点**（`⚙` 很可能是「高级设置」的真实入口，`文A` 可能是翻译、
// 可能消耗积分），先看清楚有什么、分别在哪。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV1';
const { browser, page } = await launch();

/** 面板 = 节点子树里「宽 > 400 且高 > 100 且含『参考』」那块。 */
const panel = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const cands = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => { const cs = getComputedStyle(o.e);
      return cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height));
  const hit = cands[0];
  if (!hit) return { err: '没找到面板', cands: cands.length };
  const p = hit.e, r = hit.r;

  /** 无文字的按钮靠 SVG path 的 d 当指纹。 */
  const iconFp = (e) => {
    const svg = e.querySelector('svg');
    if (!svg) return null;
    const paths = [...svg.querySelectorAll('path')].map((x) => (x.getAttribute('d') || '')).filter(Boolean);
    if (!paths.length) return 'svg:' + (svg.getAttribute('class') || '').slice(0, 30);
    // 最长的一条 path 当主指纹
    const main = paths.sort((a, b) => b.length - a.length)[0];
    return { d: main.slice(0, 60), nPaths: paths.length,
      stroke: svg.querySelector('path')?.getAttribute('stroke') || null };
  };

  const clickables = [...p.querySelectorAll('button,[role="button"],[aria-label],[onclick]')]
    .map((e) => {
      const q = e.getBoundingClientRect();
      const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
      const on = (cx >= 0 && cy >= 0 && cx < 1440 && cy < 810) ? document.elementFromPoint(cx, cy) : null;
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
        aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        role: e.getAttribute('role'), tag: e.tagName.toLowerCase(),
        cls: (e.className || '').toString().slice(0, 55),
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        icon: iconFp(e),
        onTop: !!(on && (on === e || e.contains(on) || on.contains(e))),
        cursor: getComputedStyle(e).cursor };
    })
    .filter((b) => b.rect[2] > 0 && b.rect[3] > 0);

  return { panelRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    panelText: (p.innerText || '').replace(/\s+/g, ' ').trim(),
    clickables, nClickables: clickables.length,
    noTextNoAria: clickables.filter((b) => !b.text && !b.aria && !b.title).length };
});

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t) || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.25], [0.5, 0.3]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy),
            title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
        }
      }
    }
    return { err: '找不到可点的「' + t + '」' };
  }, t);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(4000);
  return plan;
}

const drawerVisible = () => page.evaluate(() =>
  [...document.querySelectorAll('.copilotKitMessagesContainer')]
    .filter((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return r.width > 20 && r.height > 20 && cs.display !== 'none'
        && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; }).length);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  // **必须先关抽屉，否则面板不渲染**（AU11/AU13 的教训）
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: 'Esc 关抽屉后，dump 参数面板里所有可点元素（含无文字的），SVG path 当图标指纹' });

  const out = {};
  out.drawerVisibleAfterEsc = await drawerVisible();
  console.log('AV1 Esc 后抽屉可见元素数:', out.drawerVisibleAfterEsc);

  for (const [key, title] of [['video', '视频节点'], ['audio', '音频节点'], ['image', '图片节点']]) {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
    out[key] = { sel: await selectByText(title) };
    console.log(`AV1 选中${title}:`, JSON.stringify(out[key].sel).slice(0, 200));
    if (out[key].sel.err) continue;
    out[key].panel = await panel();
    if (out[key].panel.err) { console.log('  面板:', out[key].panel.err); continue; }
    const P = out[key].panel;
    console.log(`\n===== AV1 ${title} 面板 ${JSON.stringify(P.panelRect)}，可点元素 ${P.nClickables} 个（其中无文字无 aria 的 ${P.noTextNoAria} 个）=====`);
    for (const b of P.clickables) {
      console.log(`  [${String(b.rect).padEnd(20)}] text=${(b.text || '-').padEnd(10)} aria=${(b.aria || '-').padEnd(14)} cursor=${(b.cursor || '-').padEnd(7)} onTop=${b.onTop ? 'Y' : 'N'} ${b.icon ? 'icon=' + String(b.icon.d).slice(0, 26) : 'icon=-'}`);
    }
    console.log('  面板全文:', P.panelText.slice(0, 220));
  }

  await logStep(B, {
    id: 'AV1-dump-panel-icon-buttons', title: '参数面板里无文字按钮的全量清点（SVG path 当指纹）',
    target: 'M-139/M-140 里有正文一个字没记的纯图标按钮。**这一枚都不点** —— `⚙` 很可能是'
      + '「高级设置」的真实入口、`文A` 可能是翻译（也许消耗积分），先看清楚再决定',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAV1 完成');
} finally {
  await browser.close();
}
