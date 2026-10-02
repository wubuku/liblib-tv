// Batch AW2 —— **先把「点开之后到底有没有东西出现」搞清楚**，只点一枚。
//
// AW1 点了 参考/标记/特效 三枚，`diffPanels` 全部返回 `nNew: 0`。
// 但这**不能证明「点了没反应」** —— §15 早就记过：
//   `scenario.mjs` 的 `fingerprint()` 有 `width>120 && height>60` 的尺寸门槛，
//   **窄浮层会被整块挡掉**。上一次就是这么白查了四轮。
// 于是 AW1 的读数**没有判别力**，不能当证据。
//
// 这一轮换判据：**全量 dump，不设任何尺寸门槛**。
//   · 点之前记一次「全页所有可见的顶层浮层候选」，
//   · 点之后记一次，
//   · 做差集 —— 只要页面真的多了一块可见的东西，差集里就会出现。
//   · 另外**直接截图**，截图是最后的裁判（§22 的教训）。
//
// 只点「特效」一枚：五枚里它最像会弹选择器的，而且点错了也只是空弹窗，不会花钱。
// 仍然**不点文A / 提交箭头 / ⤢ / ⚙**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAW2';
const { browser, page } = await launch();

/** 全页可见的「浮层候选」—— **不设尺寸门槛**。 */
const allFloating = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (parseFloat(cs.opacity) === 0) continue;
    if (cs.position !== 'fixed' && cs.position !== 'absolute' && cs.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.right < 0 || r.y > 810 || r.x > 1440) continue;
    const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!txt) continue;   // 空浮层没有观察价值
    out.push({
      cls: (e.className || '').toString().slice(0, 60),
      pos: cs.position, z: cs.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: txt.slice(0, 160),
    });
  }
  // 同一 (cls, rect) 只留一个
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  const p = c.e;
  return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    btns: [...p.querySelectorAll('button,[role="button"]')].map((e) => {
      const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0),
    /** 面板子树里有没有长出「以前没有的东西」 */
    descCount: p.querySelectorAll('*').length,
    descTextLen: (p.innerText || '').length };
});

async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1500);
}

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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '全量 dump（无尺寸门槛）验「点特效之后到底有没有东西出现」' });

  const out = {};
  out.deselected = (await deselect(), await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length));
  out.drag = await dragToY('视频节点', 150);
  const g = out.drag.grabbed;
  await page.mouse.click(g.cx, g.cy + Math.max(0, 150 - g.rect[1]));
  await page.waitForTimeout(4200);
  out.st = await panelState();
  console.log('AW2 面板:', JSON.stringify(out.st.panelRect), 'descCount:', out.st.descCount, 'textLen:', out.st.descTextLen);
  console.log('AW2 面板按钮:', JSON.stringify(out.st.btns.map((b) => b.text)));

  // 点「特效」：点前全量快照 → 点 → 等 → 点后全量快照 → 差集
  const target = out.st.btns.find((b) => b.text === '特效');
  out.target = target;
  if (!target) throw new Error('面板里没有「特效」');
  out.floatBefore = await allFloating();
  out.panelBefore = await panelState();
  console.log('AW2 点前浮层候选:', out.floatBefore.length, '个');

  const cx = target.rect[0] + target.rect[2] / 2, cy = target.rect[1] + target.rect[3] / 2;
  out.hit = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    return e ? { tag: e.tagName, cls: (e.className || '').toString().slice(0, 50),
      btnText: (e.closest('button')?.innerText || '').trim().slice(0, 8),
      cursor: e.closest('button') ? getComputedStyle(e.closest('button')).cursor : null } : null;
  }, [cx, cy]);
  console.log('AW2 点之前确认命中:', JSON.stringify(out.hit));

  await page.mouse.click(cx, cy);
  await page.waitForTimeout(3200);
  await clearToasts(page);

  out.floatAfter = await allFloating();
  out.panelAfter = await panelState();
  console.log('AW2 点后浮层候选:', out.floatAfter.length, '个');

  // 差集
  const keyOf = (o) => o.cls + '|' + o.rect.join(',');
  const before = new Set(out.floatBefore.map(keyOf));
  out.added = out.floatAfter.filter((o) => !before.has(keyOf(o)));
  const afterSet = new Set(out.floatAfter.map(keyOf));
  out.removed = out.floatBefore.filter((o) => !afterSet.has(keyOf(o)));
  console.log('\nAW2 新增浮层', out.added.length, '个 / 消失', out.removed.length, '个');
  for (const a of out.added.slice(0, 12)) {
    console.log(`  + [${String(a.rect).padEnd(22)}] z=${a.z} cls=${a.cls}`);
    console.log(`      文本: ${a.text.slice(0, 200)}`);
  }
  console.log('AW2 面板变化: descCount', out.panelBefore.descCount, '→', out.panelAfter.descCount,
    '| textLen', out.panelBefore.descTextLen, '→', out.panelAfter.descTextLen);

  await shot(page, 'M-152-工具条-特效.png');
  out.shot = 'M-152-工具条-特效.png';

  await logStep(B, {
    id: 'AW2-dump-after-toolbar-click', title: '全量 dump 验「点工具条按钮之后到底有没有东西出现」',
    target: 'AW1 用 `diffPanels` 读到 `nNew: 0`，但 `fingerprint()` 有 `width>120 && height>60` 尺寸门槛，'
      + '**窄浮层会被整块挡掉** —— 这个读数没有判别力。改用无门槛的全量浮层快照做差集',
    evidence: out,
    visible_text: JSON.stringify({ added: out.added.slice(0, 6), panel: [out.panelBefore, out.panelAfter] }).slice(0, 3000),
    shot: 'M-152-工具条-特效.png',
  });
  console.log('\nAW2 完成');
} finally {
  await browser.close();
}
