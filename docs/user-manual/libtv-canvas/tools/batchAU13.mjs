// Batch AU13 —— 只干一件事：**把音频节点参数面板拍下来**。
//
// 正文第 308 行明明白白挂着「⚠️ 音频那三个滑杆本手册只拿到了 DOM 读数，没有画面佐证」，
// 补上这张图就能删掉这句免责声明。
//
// AU12 为什么没拍到（不是产品没画，是我把顺序搞错了）：
//   AU12 开画布先按 Esc 想关抽屉 → 我用 `.copilotKitMessagesContainer` 是否存在来判断，
//   得到 `drawerGone: false` → 于是**紧接着就去选音频节点** → 那个点上还压着抽屉，
//   `selectByText` 的 `elementFromPoint` 全部落空 → 报「找不到可点的音频节点」。
//   等我后来去选视频节点时，点画布顺带把抽屉关掉了，面板才出来（M-169 拍到了）。
//
//   → **先点画布空白把抽屉彻底关掉，再点节点**，别依赖 Esc，也别用「元素还在不在」判断。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU13';
const { browser, page } = await launch();

/** 判「抽屉在不在」要问**可见性**，不是问元素还在不在 DOM 里**（§21.3 的老坑）。 */
const drawerVisible = () => page.evaluate(() =>
  [...document.querySelectorAll('.copilotKitMessagesContainer,[class*="chatViewFadeIn"]')]
    .map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
        visible: r.width > 20 && r.height > 20 && cs.display !== 'none'
          && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05 }; }));

/** 面板 = 那个宽 660 左右的浮层卡片（`.node-floating-ui` 是 263×20 的标题条，不是它）。 */
const panelGeom = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  // 挑节点子树里**最宽且高 > 100** 的浮层卡片
  const cands = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => { const cs = getComputedStyle(o.e);
      return cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height));
  const hit = cands.find((o) => (o.e.innerText || '').includes('参考')) || cands[0];
  if (!hit) return { err: '子树里没有宽面板', cands: cands.length };
  const p = hit.e, r = hit.r;
  const sliders = [...p.querySelectorAll('.mantine-Slider-root')].map((e) => {
    const q = e.getBoundingClientRect();
    const row = e.parentElement ? e.parentElement.textContent : '';
    return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      value: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow')
        || e.closest('[aria-valuenow]')?.getAttribute('aria-valuenow') || null,
      rowText: (row || '').replace(/\s+/g, ' ').trim().slice(0, 14) };
  });
  const btns = [...p.querySelectorAll('button,[role="button"]')].map((e) => {
    const q = e.getBoundingClientRect();
    return { text: (e.innerText || '').trim().slice(0, 8), aria: e.getAttribute('aria-label'),
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
  }).filter((b) => b.rect[3] > 0);
  return { panelRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cls: (p.className || '').toString().slice(0, 80),
    fullyVisible: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810,
    sliders, btns, nSliders: sliders.length, nBtns: btns.length,
    fullText: (p.innerText || '').replace(/\s+/g, ' ').trim() };
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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先点空白关抽屉，再选音频节点拍面板' });

  const out = {};
  out.drawerAtStart = await drawerVisible();
  console.log('AU13 抽屉(前):', JSON.stringify(out.drawerAtStart));

  // **别用 Esc，直接点画布空白** —— 点画布顺带把抽屉收了
  await page.mouse.click(700, 120); await page.waitForTimeout(2400);
  out.drawerAfterBlankClick = await drawerVisible();
  console.log('AU13 点空白后抽屉可见?', out.drawerAfterBlankClick.map((d) => d.visible));

  out.audio = { sel: await selectByText('音频节点') };
  console.log('AU13 选中音频:', JSON.stringify(out.audio.sel).slice(0, 300));
  if (!out.audio.sel.err) {
    out.audio.panel = await panelGeom();
    console.log('AU13 面板 rect:', JSON.stringify(out.audio.panel.panelRect), '完全可见:', out.audio.panel.fullyVisible);
    console.log('AU13 滑杆:', JSON.stringify(out.audio.panel.sliders));
    console.log('AU13 按钮数:', out.audio.panel.nBtns, JSON.stringify(out.audio.panel.btns).slice(0, 500));
    console.log('AU13 面板全文:', out.audio.panel.fullText.slice(0, 300));
    await shot(page, 'M-168-音频节点-参数面板.png');
    out.audio.shot = 'M-168-音频节点-参数面板.png';
  }

  await logStep(B, {
    id: 'AU13-audio-panel-shot', title: '音频节点参数面板实拍（正文那条「没有画面佐证」可以删了）',
    target: '别用 Esc、别用「元素还在不在 DOM 里」判抽屉 —— **点画布空白**才是可靠的一步；'
      + '面板判据也别用 `.node-floating-ui`（那是 263×20 的标题条），用「宽 > 400 且高 > 100 且含『参考』」',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 2500),
    shot: 'M-168-音频节点-参数面板.png',
  });
  console.log('\nAU13 完成');
} finally {
  await browser.close();
}
