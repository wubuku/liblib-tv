// Batch AX2 —— **只补两枚**：图片节点的「参考」和「标记」。
//
// AX1 里这两枚读到 `nAdded: 0`，但那个读数**没有判别力**，不能当证据：
//   AX1 把图片节点拖到 y=150 就完事，**没管 x**。而参数面板是**以节点为中心居中、
//   宽 660**（AU7 量出来的），所以节点一旦偏左，整块面板跟着左移 ——
//   AX1 实测面板 rect 是 `[-127,306,660,192]`，工具条「参考」在 **x = -114**，
//   **点击坐标整个落在视口外**。同一次里 `风格` 在 x=2 勉强进屏，就点成了。
//
//   修法：**同时把节点拖到 (720, 150)** —— 节点中心落在视口中心，
//   660 宽的面板就正好是 [390, 990]，整块在屏内。
//
// 这两枚在视频节点上已经验过是「切模式」（AW3：顶部蓝条 + 画布高亮）。
// 本轮验的是**图片节点上是不是同一套**，以及各自蓝条上的文案。
//
// 判据仍用无 class 白名单的全量快照差集（AW3 的教训：特效广场是 Mantine class、
// 运镜广场是原生 fixed overlay，按白名单会漏）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAX2';
const { browser, page } = await launch();

const snap = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    if (cs.position !== 'fixed' && cs.position !== 'absolute' && cs.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.right < 0 || r.y > 810 || r.x > 1440) continue;
    const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!txt) continue;
    out.push({ cls: (e.className || '').toString().slice(0, 55), z: cs.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: txt.slice(0, 300) });
  }
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

/** 取消选中 → 把「图片节点」拖到视口中心 (720,150) → 点它 → **断言选中的是 image**。 */
async function freshSelectImageAtCenter() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1500);
  const g = await page.evaluate(() => {
    const c = [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => (n.innerText || '').includes('图片节点') && !n.classList.contains('selected'))
      .map((n) => { const r = n.getBoundingClientRect();
        const ccx = r.x + r.width / 2, ccy = r.y + r.height / 2;
        const o = (ccx >= 0 && ccy >= 0 && ccx < innerWidth && ccy < innerHeight) ? document.elementFromPoint(ccx, ccy) : null;
        return { n, r, selfHit: !!(o && n.contains(o)) }; })
      .filter((x) => x.r.x >= 5 && x.r.x + x.r.width <= 1435 && x.r.y >= 60 && x.r.y + x.r.height <= 800)
      .sort((a, b) => (b.selfHit - a.selfHit));
    for (const { n, r } of c) {
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const o = document.elementFromPoint(cx, cy);
        if (o && n.contains(o) && !o.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
    }
    return { err: '找不到可拖的图片节点' };
  });
  if (g.err) return g;
  // **同时拖 x 和 y**：节点中心 → (720, 150)
  const dx = Math.round(720 - (g.rect[0] + g.rect[2] / 2));
  const dy = Math.round(150 - g.rect[1]);
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    await page.mouse.move(g.cx, g.cy); await page.mouse.down();
    for (let i = 1; i <= 14; i += 1) { await page.mouse.move(g.cx + (dx * i) / 14, g.cy + (dy * i) / 14); await page.waitForTimeout(70); }
    await page.mouse.up(); await page.waitForTimeout(2200);
  }
  const g2 = await page.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes('图片节点') || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (Math.abs(r.x + r.width / 2 - 720) > 120) continue;
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    }
    return null;
  });
  if (!g2) return { err: '拖完找不到了' };
  await page.mouse.click(g2.cx, g2.cy);
  await page.waitForTimeout(4200);
  const sel = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { none: true };
    const m = /react-flow__node-([a-z-]+)/.exec(n.className || '');
    return { type: m ? m[1] : 'unknown' };
  });
  return { ...g2, selectedType: sel.type, typeOk: sel.type === 'image' };
}

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width >= 500 && o.r.height >= 100)
    .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3)
    .sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
  if (!c) return { err: '没找到面板' };
  const p = c.e;
  return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    inView: c.r.x >= 0 && c.r.right <= 1440,
    btns: [...p.querySelectorAll('button,[role="button"]')].map((e) => {
      const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '把图片节点拖到视口中心（x 也要管），补拍参考/标记' });

  const out = {};
  out.clicks = [];
  for (const [label, shotName] of [['参考', 'M-158-图片-参考.png'], ['标记', 'M-159-图片-标记.png']]) {
    out.clicks.push({ label, start: await freshSelectImageAtCenter() });
    const st = await panelState();
    const r0 = out.clicks[out.clicks.length - 1];
    console.log(`\n--- AX2 ${label} ---`);
    console.log('  节点类型:', r0.start.selectedType, '| 面板:', JSON.stringify(st.panelRect || st.err), '| 面板在视口内:', st.inView);
    if (st.err) { r0.err = st.err; continue; }
    const b = st.btns.find((x) => x.text === label);
    if (!b) { r0.err = '面板里没有「' + label + '」'; r0.available = st.btns.map((x) => x.text); continue; }
    r0.target = b.rect;
    if (b.rect[0] < 0 || b.rect[0] + b.rect[2] > 1440) { r0.err = '按钮仍在视口外，不点（避免把「点偏了」记成「没反应」）'; continue; }
    const before = await snap();
    const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
    r0.hit = await page.evaluate(([x, y]) => {
      const e = document.elementFromPoint(x, y);
      return e ? { tag: e.tagName, btn: (e.closest('button')?.innerText || '').trim().slice(0, 6) } : null;
    }, [cx, cy]);
    await page.mouse.click(cx, cy);
    await page.waitForTimeout(3200);
    await clearToasts(page);
    const after = await snap();
    const bs = new Set(before.map((o) => o.cls + '|' + o.rect.join(',')));
    r0.added = after.filter((o) => !bs.has(o.cls + '|' + o.rect.join(',')))
      .sort((a, b2) => (b2.rect[2] * b2.rect[3]) - (a.rect[2] * a.rect[3]));
    r0.nAdded = r0.added.length;
    r0.top = r0.added[0] || null;
    console.log('  新增', r0.nAdded, '个');
    for (const a of r0.added.slice(0, 3)) console.log(`    + [${String(a.rect).padEnd(22)}] z=${a.z} ${a.cls}\n       ${a.text.slice(0, 180)}`);
    await shot(page, shotName); r0.shot = shotName;
    await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  }

  await logStep(B, {
    id: 'AX2-image-reference-and-mark', title: '补拍图片节点的「参考」与「标记」（节点要同时拖到视口中心）',
    target: 'AX1 把这两枚读成 `nAdded: 0`，**但那是把点击坐标算到了视口外**'
      + '（图片面板 rect `[-127,306,660,192]`、「参考」在 x=-114）—— 点偏了不等于没反应。'
      + '面板以节点为中心居中且宽 660，所以**节点的 x 也要管**：拖到 (720,150)',
    evidence: out,
    visible_text: JSON.stringify(out.clicks.map((c) => ({ l: c.label, n: c.nAdded, top: c.top && { r: c.top.rect, c: c.top.cls, t: c.top.text.slice(0, 200) } }))).slice(0, 2500),
    shot: 'M-158-图片-参考.png',
  });
  console.log('\nAX2 完成');
} finally {
  await browser.close();
}
