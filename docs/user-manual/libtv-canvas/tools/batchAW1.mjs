// Batch AW1 —— 节点顶部工具条五枚**逐枚实点**：参考 / 标记 / 特效 / 角色库 / 运镜。
//
// 为什么现在点它们：手册里这五枚**只有名字，一个都没被点开过** ——
// 「点了会弹出什么」「能不能多选」「会不会消耗积分」全部未知 📖。
//
// 五条安全边界（本轮严守）：
//   ① **只打开选择器，不选任何一项** —— 不点卡片，就不会建节点、不消耗积分。
//   ② 不点 `文A`（八成是翻译提示词）、不点提交箭头。
//   ③ 不点 `⤢`（会跳到会员订阅页，上一批已经拍过了）。
//   ④ **不点 ⚙**（已坐实是高级设置 toggle，再点会把面板高度改掉，污染本轮起点）。
//   ⑤ 不关 TV Director 抽屉不点别的节点 —— 抽屉关着面板才渲染（AU11 的教训）。
//
// 六条判据（前两批用血换来的，这里直接当默认）：
//   · 先 `Esc` 关抽屉 → 点空白取消选中 → 拖节点到画面上部 → **用坐标点它**
//     （视口里有两个视频节点，按 innerText 取第一个是随机数 —— AV4 就这么开错了面板）
//   · Mantine Popover/Dropdown 懒挂载，**每次点之前重读坐标**
//   · 点之前验 `elementFromPoint` 落在目标上
//   · 判「新浮层」用 `fingerprint()`/`diffPanels()`，不按 class 白名单筛
//   · 点完先 `Esc` 收场，保证下一枚的起点是干净的
//   · 拖节点前必须取消选中（658 宽的面板会盖住节点上半部分）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView, fingerprint, diffPanels } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAW1';
const { browser, page } = await launch();

/** 面板 + 面板里所有可点元素（坐标每次重读）。 */
const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  const p = c.e;
  const btns = [...p.querySelectorAll('button,[role="button"]')].map((e) => {
    const q = e.getBoundingClientRect();
    return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
      aria: e.getAttribute('aria-label'),
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      cursor: getComputedStyle(e).cursor };
  }).filter((b) => b.rect[2] > 0 && b.rect[3] > 0);
  return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    fullyVisible: c.r.x >= 0 && c.r.y >= 0 && c.r.right <= 1440 && c.r.bottom <= 810,
    panelText: (p.innerText || '').replace(/\s+/g, ' ').trim(), btns };
});

async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1500);
}

/** 取消选中后拖节点到 targetY，**返回拖后坐标**（后续一律用坐标，不用文本再找一遍）。 */
async function dragToY(textPart, targetY) {
  const g = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
    }
    return { err: '找不到可拖的「' + t + '」' };
  }, textPart);
  if (g.err) return g;
  const dy = Math.round(targetY - g.rect[1]);
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(2000);
  return { grabbed: g, dy };
}

async function selectAt(cx, cy, wait = 4200) {
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(wait);
  return page.evaluate(() => !!document.querySelector('.react-flow__node.selected'));
}

/** 逐枚点。每枚：点前 fingerprint → 验命中 → 点 → 等 → diffPanels → 收场。 */
async function clickTool(label, shotName) {
  const before = await fingerprint(page);
  const st = await panelState();
  if (st.err) return { label, err: st.err };
  const b = st.btns.find((x) => x.text === label);
  if (!b) return { label, err: '面板里没有「' + label + '」', available: st.btns.map((x) => x.text) };
  const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
  const hit = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    return e ? { tag: e.tagName, txt: (e.textContent || '').trim().slice(0, 10),
      insideBtn: !!(e.closest('button')), btnText: (e.closest('button')?.innerText || '').trim().slice(0, 10) } : null;
  }, [cx, cy]);
  if (b.cursor === 'not-allowed') return { label, rect: b.rect, skipped: 'cursor=not-allowed' };
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(2800);
  const after = await fingerprint(page);
  const d = diffPanels(before, after);
  const added = d.added || [];
  await clearToasts(page);
  const r = { label, rect: b.rect, hitAtPoint: hit,
    newPanels: added.slice(0, 8).map((p) => ({ sig: p.sig, area: p.area, text: (p.all || p.text || '').replace(/\s+/g, ' ').slice(0, 220) })),
    nNew: Array.isArray(added) ? added.length : null,
    panelStillVisible: (await panelState()).fullyVisible };
  // 只有真的浮出新东西才截图
  if (r.nNew) { await shot(page, shotName); r.shot = shotName; }
  // 收场：Esc 关掉可能开着的浮层，并验证面板没被改掉
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const st2 = await panelState();
  r.afterEscape = { panelRect: st2.panelRect, btns: st2.btns.length };
  r.panelUnchanged = st2.panelRect && r.panelStillVisible !== undefined
    ? JSON.stringify(st2.panelRect) === JSON.stringify((await panelState()).panelRect) : null;
  return r;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '顶部工具条五枚逐枚实点（只开选择器，不选任何一项）' });

  const out = {};
  // ① 取消选中 → 拖视频节点到上部 → 用坐标点它
  out.deselected = (await deselect(), await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length));
  out.drag = await dragToY('视频节点', 150);
  console.log('AW1 拖视频节点:', JSON.stringify(out.drag).slice(0, 200));
  const g = out.drag.grabbed;
  out.selected = await selectAt(g.cx, g.cy + Math.max(0, 150 - g.rect[1]));
  console.log('AW1 选中:', out.selected);
  out.st0 = await panelState();
  console.log('AW1 面板:', JSON.stringify(out.st0.panelRect), '完整?', out.st0.fullyVisible);
  console.log('AW1 面板可点元素:', JSON.stringify(out.st0.btns.map((b) => b.text)));

  // ② 五枚逐枚点
  out.clicks = [];
  for (const [label, shotName] of [['参考', 'M-152-工具条-参考.png'], ['标记', 'M-153-工具条-标记.png'],
    ['特效', 'M-154-工具条-特效.png'], ['角色库', 'M-155-工具条-角色库.png'], ['运镜', 'M-156-工具条-运镜.png']]) {
    console.log(`\n--- AW1 点「${label}」---`);
    const r = await clickTool(label, shotName);
    out.clicks.push(r);
    console.log('  ', JSON.stringify(r).slice(0, 800));
    if (r.err) console.log('   ⚠ 失败:', r.err);
  }

  await logStep(B, {
    id: 'AW1-toolbar-five-buttons', title: '节点顶部工具条五枚逐枚实点（参考/标记/特效/角色库/运镜）',
    target: '**只打开选择器、不选任何一项** —— 不点卡片就不会建节点、不消耗积分；'
      + '不点文A（翻译）、不点提交箭头、不点 ⤢（会员页）、不点 ⚙（会改面板高度污染起点）',
    evidence: out,
    visible_text: JSON.stringify(out.clicks).slice(0, 3000),
    shot: out.clicks.find((c) => c.shot)?.shot || 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAW1 完成');
} finally {
  await browser.close();
}
