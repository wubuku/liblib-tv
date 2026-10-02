// Batch AV2 —— 逐枚实点参数面板里那几枚**无文字按钮**，看它们各自打开什么。
//
// AV1 的清点（零点击）：视频面板 15 个可点元素、其中 5 个无文字无 aria；
// 图片面板 11 个、4 个。其中三枚在两个面板里 **SVG path 完全相同** —— 是同一套公共按钮：
//   文A  icon d = `M15.52 7.2c.16 0 .31.1.37.`
//   ⚙    icon d = `M14 17H5M19 7h-9`
//   ⤢    icon d = `M8.3.3a1 1 0 0 1 1.4 0l8 8`
// 视频另有一枚 `M10.26 1.67c.32 0 .57.25.5`（M-139 里那个 📄）；
// 图片另有一枚 **有 aria** 的 `预设`，以及一枚**连 SVG 都没有**的空按钮。
//
// ⚠️ **不点 `文A`**：它八成是「翻译提示词」，很可能要消耗积分。宁可留白也不冒这个险。
// ⚠️ **不点提交箭头**（⚡135 / ⚡1 旁边那枚圆形），理由同上。
//
// 每一枚都按同一套流程：**点前 fingerprint → 点 → 等 → diffPanels → 截图**，
// 而且每点一次之后先 Esc 收场，保证下一枚的起点是干净的。
// 重点是 **`⚙`** —— Batch AU 找了十三轮都没找到的「高级设置」入口，很可能就是它。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView, fingerprint, diffPanels } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV2';
const { browser, page } = await launch();

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
  return cands.length ? { rect: [Math.round(cands[0].r.x), Math.round(cands[0].r.y), Math.round(cands[0].r.width), Math.round(cands[0].r.height)] } : { err: '没找到面板' };
});

/** 面板里所有可点元素，带图标指纹 —— 用来按下标找回来（坐标每轮都要重读）。 */
const clickables = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return [];
  const p = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0]?.e;
  if (!p) return [];
  const fp = (e) => { const s = e.querySelector('svg');
    if (!s) return 'nosvg';
    const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
    return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 40) : 'svgonly'; };
  return [...p.querySelectorAll('button,[role="button"]')]
    .map((e) => { const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
        aria: e.getAttribute('aria-label'), fp: fp(e),
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        cursor: getComputedStyle(e).cursor }; })
    .filter((b) => b.rect[2] > 0 && b.rect[3] > 0);
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
          return { cx: Math.round(cx), cy: Math.round(cy) };
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

/** 点一枚（按下标 + 图标指纹定位，坐标当场重读），返回点了什么、之后浮层怎么变。 */
async function clickOne(idx, label) {
  const before = await fingerprint(page);
  const list = await clickables();
  const b = list[idx];
  if (!b) return { label, err: '面板里没有第 ' + idx + ' 个可点元素', n: list.length };
  const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
  const hit = await page.evaluate(([cx, cy]) => {
    const e = document.elementFromPoint(cx, cy);
    return e ? e.tagName + '.' + (e.className || '').toString().slice(0, 40) : null;
  }, [cx, cy]);
  if (!b.cursor || b.cursor === 'not-allowed') {
    return { label, target: b, cx, cy, skipped: 'cursor=' + b.cursor };
  }
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(2600);
  const after = await fingerprint(page);
  const d = diffPanels(before, after);
  await clearToasts(page);
  return { label, target: b, cx, cy, hitAtPoint: hit,
    newPanels: d.added || d.new || d,
    panelStillThere: (await panel()).rect || null,
    nodeStillSelected: await page.evaluate(() => !!document.querySelector('.react-flow__node.selected')) };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '逐枚实点无文字按钮（重点 ⚙），不点文A 与提交箭头' });

  const out = {};
  out.sel = await selectByText('视频节点');
  console.log('AV2 选中视频:', JSON.stringify(out.sel));
  out.panelRect = await panel();
  out.list = await clickables();
  console.log('AV2 视频面板可点元素清单:');
  out.list.forEach((b, i) => console.log(`  [${i}] [${String(b.rect).padEnd(20)}] text=${(b.text || '-').padEnd(10)} aria=${(b.aria || '-').padEnd(14)} cursor=${b.cursor} fp=${b.fp.slice(0, 30)}`));

  // 按图标指纹挑：⚙ = `M14 17H5M19 7h-9`、⤢ = `M8.3.3a1 1`、📄 = `M10.26 1.67`
  const byFp = (pfx) => out.list.findIndex((b) => b.fp.startsWith(pfx));
  const targets = [
    ['⚙ 调节滑块', byFp('M14 17H5M19 7h-9')],
    ['⤢ 展开', byFp('M8.3.3a1 1')],
    ['📄 第一个图标', byFp('M10.26 1.67')],
  ];

  out.clicks = [];
  for (const [label, idx] of targets) {
    if (idx < 0) { out.clicks.push({ label, err: '清单里没找到这个图标' }); continue; }
    console.log(`\n--- AV2 点「${label}」（下标 ${idx}）---`);
    const r = await clickOne(idx, label);
    out.clicks.push(r);
    console.log('  结果:', JSON.stringify(r).slice(0, 700));
    if (r.newPanels && Object.keys(r.newPanels).length) {
      await shot(page, `M-15${out.clicks.length}-${label.split(' ')[0]}.png`);
      r.shot = `M-15${out.clicks.length}-${label.split(' ')[0]}.png`;
    }
    // 收场，保证下一枚起点干净
    await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
    const re = await clickables();
    if (re.length !== out.list.length) console.log(`  ⚠ 收场后面板元素数从 ${out.list.length} 变成 ${re.length}`);
    out.list = re;
  }

  await logStep(B, {
    id: 'AV2-click-icon-buttons', title: '参数面板无文字按钮逐枚实点（重点找「高级设置」的真实入口）',
    target: '**不点 `文A`**（八成是翻译提示词，可能扣积分）和提交箭头；'
      + '每枚都走「点前 fingerprint → 点 → diffPanels → 截图」，点完先 Esc 收场',
    evidence: out,
    visible_text: JSON.stringify(out.clicks).slice(0, 2500),
    shot: 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAV2 完成');
} finally {
  await browser.close();
}
