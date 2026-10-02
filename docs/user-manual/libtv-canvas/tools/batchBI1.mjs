// Batch BI1 — 连接口在「悬停但未选中」时到底显不显形。
//
// BH2 的遗留 📖：端口完整 innerHTML 已读出三层，且那枚 20×20 的 ⊕ 图标
// **默认 opacity: 0**、M-199 截图是**选中态**。那么「只是悬停、没点选」的时候
// 它显不显形？—— 这是用户最常遇到的场景（鼠标划过节点、还没点下去）。
//
// ⭐ 判据纪律（BE 立的）：**每一步都锚定同一个元素**，不重新查找。
//   BG3 就在这里翻过车：五级状态梯度里每步重新 `querySelector`，
//   React 重渲染后拿到的是另一个节点，读数全串了。
//   所以这里先按 nodeId 定位一次，把 handle 元素的**引用**存进
//   `window.__h`，之后全程只用它。
//
// ⭐ 判「显不显形」不能只看 opacity：元素可能整体 `transform: scale(0)`、
// 或者父级 `overflow:hidden` 裁掉、或者尺寸为 0。所以同时量
//   rect / opacity / visibility / display / transform / 父级 overflow，
// 并用 `elementFromPoint` 反查那个坐标上**实际渲染的是谁**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI1';
const { browser, page } = await launch();

/** 把某个节点的 source 口锚定进 window.__h，之后全程只认它。 */
const anchor = (id) => page.evaluate((nid) => {
  const n = [...document.querySelectorAll('.react-flow__node')]
    .find((x) => x.getAttribute('data-id') === nid);
  if (!n) return { err: 'no node' };
  const h = n.querySelector('[data-handleid="source"]');
  if (!h) return { err: 'no source handle' };
  // 三层结构（BH2 的读数）：0×0 外层 → 80×80 圆 → 20×20 图标
  const circle = h.querySelector('div');
  const icon = circle ? circle.querySelector('svg') : null;
  window.__h = { node: n, handle: h, circle, icon };
  return {
    ok: true,
    handleCls: (h.className || '').toString().slice(0, 60),
    hasCircle: !!circle, hasIcon: !!icon,
    iconTag: icon ? icon.tagName : null,
  };
}, id);

/** 在**已锚定**的那个元素上读显形状态 —— 不重新查找。 */
const readState = () => page.evaluate(() => {
  const { handle: h, circle, icon } = window.__h || {};
  if (!h) return { err: 'no anchor' };
  const pack = (e) => {
    if (!e) return null;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return {
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      opacity: cs.opacity, visibility: cs.visibility, display: cs.display,
      transform: cs.transform, overflow: cs.overflow, pointerEvents: cs.pointerEvents,
    };
  };
  // 父级链上有没有 overflow:hidden 会把它裁掉
  let clipper = null;
  for (let p = h.parentElement; p && p !== document.body; p = p.parentElement) {
    const cs = getComputedStyle(p);
    if (cs.overflow !== 'visible') { clipper = { cls: (p.className || '').toString().slice(0, 40), overflow: cs.overflow }; break; }
  }
  const hs = pack(h), cs2 = circle ? pack(circle) : null, is = pack(icon);
  // ⭐ 真正要问的：那个坐标上**实际渲染的是谁**
  const probe = (() => {
    const cx = is ? is.rect[0] + is.rect[2] / 2 : (cs2 ? cs2.rect[0] + cs2.rect[2] / 2 : null);
    const cy = is ? is.rect[1] + is.rect[3] / 2 : (cs2 ? cs2.rect[1] + cs2.rect[3] / 2 : null);
    if (cx == null) return null;
    const o = document.elementFromPoint(Math.round(cx), Math.round(cy));
    return { at: [Math.round(cx), Math.round(cy)], tag: o ? o.tagName : null,
      inHandle: !!(o && h.contains(o)), cls: o ? (o.className || '').toString().slice(0, 40) : null };
  })();
  return { handle: hs, circle: cs2, icon: is, clipper, probe };
});

const selCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '连接口「悬停未选中」是否显形 —— 锚定同一元素做四态梯度' });

  const out = {};

  // 选 3 个不同类型的节点：图片 / 视频 / 文本
  const targets = [
    { id: 'i-9nlG6HdjK2', name: '图片节点 2' },
    { id: 'v-eMpqKtiLlx', name: '视频节点 3' },
    { id: 't-UtVx3lZmrV', name: '文本节点 1' },
  ];

  const allStates = [];
  for (const t of targets) {
    console.log(`\n══════ ${t.name}（${t.id}）══════`);
    const a = await anchor(t.id);
    if (a.err) { console.log('  锚定失败：', a.err); allStates.push({ ...t, err: a.err }); continue; }
    console.log(`  锚定 OK：handle class="${a.handleCls}" 有80×80圆=${a.hasCircle} 有图标=${a.hasIcon}(${a.iconTag})`);

    // 态 0：基线 —— 鼠标停在画布角落，什么都没选
    await page.mouse.move(120, 120); await page.waitForTimeout(1400);
    const s0 = { label: '基线：鼠标远离，未选中', sel: await selCount(), ...(await readState()) };
    console.log(`  [态0 ${s0.label}] 选中数=${s0.sel}`);
    console.log(`     图标 rect=${JSON.stringify(s0.icon?.rect)} opacity=${s0.icon?.opacity} vis=${s0.icon?.visibility}`);
    console.log(`     该点实际渲染=${JSON.stringify(s0.probe)}`);

    // 态 1：悬停节点本体（卡片中间），**不点**
    const body = await page.evaluate(() => {
      const n = window.__h.node; const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    await page.mouse.move(body[0], body[1]); await page.waitForTimeout(1500);
    const s1 = { label: '悬停节点本体（未点）', sel: await selCount(), ...(await readState()) };
    console.log(`  [态1 ${s1.label}] 选中数=${s1.sel}`);
    console.log(`     图标 rect=${JSON.stringify(s1.icon?.rect)} opacity=${s1.icon?.opacity} vis=${s1.icon?.visibility}`);
    console.log(`     该点实际渲染=${JSON.stringify(s1.probe)}`);

    // 态 2：悬停**口本身**（80×80 圆的中心），仍未点选
    const c = s1.circle?.rect;
    if (c && c[2] > 0) {
      await page.mouse.move(Math.round(c[0] + c[2] / 2), Math.round(c[1] + c[3] / 2));
      await page.waitForTimeout(1500);
      const s2 = { label: '悬停连接口（未点选）', sel: await selCount(), ...(await readState()) };
      console.log(`  [态2 ${s2.label}] 选中数=${s2.sel}`);
      console.log(`     图标 rect=${JSON.stringify(s2.icon?.rect)} opacity=${s2.icon?.opacity} vis=${s2.icon?.visibility}`);
      console.log(`     该点实际渲染=${JSON.stringify(s2.probe)}`);
      allStates.push({ node: t.name, states: [s0, s1, s2] });

      // ⭐ 态 2 拍图：这是「悬停未选中」的真实画面
      if (t.id === 'i-9nlG6HdjK2') {
        await page.mouse.move(120, 400); await page.waitForTimeout(700);
        await page.mouse.move(Math.round(c[0] + c[2] / 2), Math.round(c[1] + c[3] / 2));
        await page.waitForTimeout(1300);
        await shot(page, 'M-200-连接口-悬停未选中.png');
        out.shot = 'M-200-连接口-悬停未选中.png';
        console.log('  📷 已拍 M-200-连接口-悬停未选中.png（悬停态，未点选）');
      }
    } else {
      console.log('  [态2] 连接口的 80×80 圆 rect 为 0，跳过');
      allStates.push({ node: t.name, states: [s0, s1], err: 'circle rect 0' });
    }

    // 态 3：点选（对照：M-199 那张就是这一态）
    const body2 = await page.evaluate(() => {
      const n = window.__h.node; const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    await page.mouse.click(body2[0], body2[1]); await page.waitForTimeout(2200);
    const s3 = { label: '已点选（对照态）', sel: await selCount(), ...(await readState()) };
    console.log(`  [态3 ${s3.label}] 选中数=${s3.sel}`);
    console.log(`     图标 rect=${JSON.stringify(s3.icon?.rect)} opacity=${s3.icon?.opacity} vis=${s3.icon?.visibility}`);

    // ⭐ 汇总判据：四态里**图标 opacity 变了没有**
    const ops = [s0, s1, s2, s3].filter((s) => s.icon).map((s) => ({ label: s.label, sel: s.sel, op: s.icon.opacity, vis: s.icon.visibility, w: s.icon.rect[2] }));
    console.log(`  ⭐ 四态图标读数：${JSON.stringify(ops)}`);
    const opSet = [...new Set(ops.map((o) => o.op))];
    console.log(`  ⭐ 出现的 opacity 取值 = ${JSON.stringify(opSet)} → ${opSet.length === 1 ? '全程不变' : '会变'}`);
    allStates.push({ node: t.name, summary: ops, distinctOpacity: opSet });

    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.states = allStates;

  // 结论：悬停未选中时，图标到底是不是 0
  const hoverRows = allStates.filter((s) => s.summary)
    .map((s) => ({ node: s.node, baseline: s.summary[0]?.op, hoverBody: s.summary[1]?.op, hoverPort: s.summary[2]?.op, selected: s.summary[3]?.op }));
  console.log('\n══════ 汇总 ══════');
  console.log('  节点 | 基线 | 悬停本体 | 悬停口 | 已选中');
  for (const r of hoverRows) console.log(`  ${r.node} | ${r.baseline} | ${r.hoverBody} | ${r.hoverPort} | ${r.selected}`);
  out.table = hoverRows;

  await logStep(B, {
    id: 'BI1-handle-hover-unselected',
    title: '连接口「悬停但未选中」时显不显形',
    target: 'BH2 留下一个 📖：端口图标默认 opacity: 0，M-199 那张截图是选中态。'
      + '但用户最常见的场景是「鼠标划过去、还没点」，那一刻显不显形没有任何记录。'
      + '⭐ 判据：全程锚定同一个元素（BG3 的教训），同时量 rect/opacity/visibility/'
      + 'transform/父级 overflow，并用 elementFromPoint 反查该坐标实际渲染的是谁。',
    evidence: out,
    visible_text: JSON.stringify({ table: out.table, shot: out.shot }).slice(0, 2500),
    shot: out.shot,
  });
  console.log('\nBI1 完成');
} finally {
  await browser.close();
}
