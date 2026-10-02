// Batch BD4 —— 推翻 BD3 的判据重来。
//
// ⚠️ BD3 得出的「网格吸附关不掉」**是判据错，不是产品行为**。
//    我用「背景色不是 `rgba(0,0,0,0)`」当「开着」，但：
//      · 鼠标 click 完**仍停在按钮上** → `hover:bg-canvas-controls-hover` 生效
//        → 背景变成 `rgba(255,255,255,0.1)`，看起来像开着，其实是**悬停**。
//      · 对照组 `切换小地图` 露了底：点一下得到 `rgba(255,255,255,0.15)`
//        且 class 多出 **`bg-canvas-controls-active`**；再点一下回到 `0.1`。
//        `0.15` 与 `0.1` 只差一点点，肉眼和正则都分不开 —— **只有 class 分得开**。
//
// 这轮的正确判据（三条同时满足才算「开着」）：
//   ① class 里有 `bg-canvas-controls-active`
//   ② 背景是 `rgba(255, 255, 255, 0.15)`
//   ③ **鼠标已经移开**（否则永远带着 hover 色）
//
// 另外两件顺带钉死：
//   · `隐藏节点连线` 点一下之后，按钮从 DOM 里**按旧 aria 找不到了**
//     （`state3` 返回 `not found`）—— 多半是 aria 变成了「显示节点连线」。坐实。
//   · 蓝点：`pointer-events-none` 已坐实（hover 它读到的都是**底下那个条目**的
//     tooltip）。这轮改从**父级链**反查蓝点挂在哪几个条目上，并确认面板里
//     一共几个蓝点、位置对不对得上。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBD4';
const { browser, page } = await launch();

/** 左下工具条那一整组（顺序固定）的真实状态。
 *  ⚠️ `隐藏节点连线` 点过之后 aria 会变，所以这里**按位置读**而不是按名字读：
 *     取工具条容器内 aria 为 `整理画布…` 那一组里、x 递增的第 3/4/5 枚。 */
const bar = (pg) => pg.evaluate(() => {
  const all = [...document.querySelectorAll('button,[role="button"]')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.y > 760 && r.y < 800 && r.x > 100 && r.x < 300 && r.width >= 20 && r.width <= 40;
  });
  all.sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
  return all.map((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {
      aria: e.getAttribute('aria-label'),
      x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height),
      active: /bg-canvas-controls-active/.test(e.className || ''),
      bg: cs.backgroundColor,
    };
  });
});

/** 「开着」的唯一可信判据：class 里有 active。鼠标必须已移开。 */
const isOn = (it) => !!it && it.active === true;

/** 点第 n 枚（0 基，按 x 排序），点完**把鼠标挪到画布中央**再回读。 */
async function tap(pg, n) {
  const items = await bar(pg);
  const it = items[n];
  if (!it) return { err: `第 ${n} 枚不存在（共 ${items.length} 枚）` };
  await pg.mouse.move(it.x + it.w / 2, it.y + it.h / 2);
  await pg.waitForTimeout(250);
  await pg.mouse.click(it.x + it.w / 2, it.y + it.h / 2);
  await pg.waitForTimeout(1800);
  await pg.mouse.move(720, 260);          // ⚠️ 挪开，消除 hover 污染
  await pg.waitForTimeout(700);
  const after = await bar(pg);
  return { before: it, after: after[n] || { err: '点完这枚不见了' }, idx: n };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.mouse.move(720, 260); await page.waitForTimeout(900);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '用 bg-canvas-controls-active 当唯一判据、鼠标移开再回读，重测三枚开关' });

  const out = {};
  const start = await bar(page);
  console.log('工具条（左→右）:');
  start.forEach((b, i) => console.log(`  ${i} [${b.x},${b.y}] ${String(b.w)}×${b.h} aria=${b.aria} active=${b.active} bg=${b.bg}`));
  out.bar = { start };

  // ═══ 逐枚：点开 → 点回，每步都挪开鼠标再回读
  console.log('\n--- 三枚开关逐个往返 ---');
  const rounds = [];
  for (const idx of [0, 1, 2]) {
    const t1 = await tap(page, idx);
    const t2 = await tap(page, idx);
    const label = start[idx] ? start[idx].aria : `第${idx}枚`;
    console.log(`  ${label}：开→${isOn(t1.after) ? '开 ✅' : '没开 ❌'}  再点→${isOn(t2.after) ? '还是开 ❌' : '关掉了 ✅'}`);
    rounds.push({ idx, label,
      turnedOn: isOn(t1.after), turnedOff: !isOn(t2.after),
      beforeAria: t1.before.aria, afterAria1: t1.after.aria, afterAria2: t2.after.aria,
      s1: t1.after, s2: t2.after });
  }
  out.rounds = rounds;

  // 复原检查：此刻应该三枚都不 active
  const nowBar = await bar(page);
  console.log('\n复原检查:', nowBar.map((b) => `${b.aria}=${b.active}`).join('  '));
  out.finalBar = nowBar;
  out.allRestored = nowBar.every((b) => !b.active);

  // ═══ 网格吸附的吸附行为：这次用**正确的判据**确认它真的开着了再拖
  console.log('\n--- 网格吸附：确认开着，再拖节点 ---');
  const gT1 = await tap(page, 2);
  const gOn = isOn(gT1.after);
  console.log('  点一下后 active =', gOn, ' bg =', gT1.after.bg);
  const gOnEvidence = gT1.after;
  if (gOn) {
    // 找一个**独占**的节点，拖一个刻意不是网格倍数的偏移
    const drag = async () => {
      const cands = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
        const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      }));
      for (const c of cands) {
        const pt = await page.evaluate((nid) => {
          const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
          if (!t) return null;
          const r = t.getBoundingClientRect();
          for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
            const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
            const o = document.elementFromPoint(x, y);
            if (o && o.closest('.react-flow__node') === t) return { x, y };
          }
          return null;
        }, c.id);
        if (pt) return { cand: c, pt };
      }
      return null;
    };
    const before = await drag();
    if (before) {
      const g0 = (await page.evaluate((id) => {
        const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
        const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
      }, before.cand.id));
      await page.mouse.move(before.pt.x, before.pt.y); await page.mouse.down();
      for (let i = 1; i <= 12; i += 1) { await page.mouse.move(before.pt.x + 3.1 * i, before.pt.y + 2.3 * i); await page.waitForTimeout(60); }
      await page.mouse.up(); await page.waitForTimeout(1800);
      const g1 = await page.evaluate((id) => {
        const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
        const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
      }, before.cand.id);
      const mv = [g1[0] - g0[0], g1[1] - g0[1]];
      console.log(`  吸附开：请求 (+37.2,+27.6) → 实际位移 ${JSON.stringify(mv)}`,
        mv[0] % 10 === 0 && mv[1] % 10 === 0 ? '（都是 10 的倍数 → 疑似吸附到 10px 网格）' : '');
      out.gridOn = { evidence: gOnEvidence, requested: [37, 28], actual: mv,
        snap10: mv[0] % 10 === 0 && mv[1] % 10 === 0 };
      await shot(page, 'M-180-网格吸附-打开.png');
      out.shot = 'M-180-网格吸附-打开.png';
      // 拖回去
      const p2 = await page.evaluate((id) => {
        const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === id);
        const r = t.getBoundingClientRect();
        for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
          const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
          const o = document.elementFromPoint(x, y);
          if (o && o.closest('.react-flow__node') === t) return { x, y };
        }
        return null;
      }, before.cand.id);
      if (p2) {
        await page.mouse.move(p2.x, p2.y); await page.mouse.down();
        for (let i = 1; i <= 10; i += 1) { await page.mouse.move(p2.x - mv[0] * i / 10, p2.y - mv[1] * i / 10); await page.waitForTimeout(55); }
        await page.mouse.up(); await page.waitForTimeout(1500);
        const g2 = await page.evaluate((id) => {
          const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
          const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
        }, before.cand.id);
        console.log('  拖回后残差:', [g2[0] - g0[0], g2[1] - g0[1]]);
        out.gridOn.residual = [g2[0] - g0[0], g2[1] - g0[1]];
      }
    }
  } else {
    console.log('  ⚠️ 点不开，吸附行为无法测');
    out.gridOn = { err: '点不开' };
  }
  // 关回去
  if (isOn((await bar(page))[2])) { await tap(page, 2); }
  await page.mouse.move(720, 260); await page.waitForTimeout(800);
  await shot(page, 'M-179-网格吸附-关闭.png');
  out.shot2 = 'M-179-网格吸附-关闭.png';
  out.gridOff = (await bar(page))[2];
  console.log('  关回后 active =', out.gridOff.active);

  // ═══ 蓝点：改从父级链反查挂在哪些条目上
  console.log('\n--- 预设蓝点的归属 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(700);
  await fitView(page); await page.waitForTimeout(1400);
  let selId = null;
  for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
    const pt = await page.evaluate((nid) => {
      const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
      if (!t) return null;
      const r = t.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === t) return { x, y };
      }
      return null;
    }, id);
    if (!pt) continue;
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(1900);
    if (await page.evaluate(() => !!document.querySelector('.react-flow__node.selected'))) { selId = id; break; }
  }
  console.log('  选中:', selId);
  if (!selId) { out.blueDot = { err: '没选中图片节点' }; }
  else {
    const pre = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      const b = [...n.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '预设');
      if (!b) return { err: '没有 aria=预设' };
      const r = b.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
    });
    if (pre.err) { out.blueDot = pre; }
    else {
      await page.mouse.click(pre.x, pre.y); await page.waitForTimeout(2800); await clearToasts(page);
      // 从蓝点往上爬父级，找到那个「条目」，读它的名字
      const dots = await page.evaluate(() => {
        const cands = [...document.querySelectorAll('span')].filter((e) => {
          const r = e.getBoundingClientRect();
          if (r.width < 3 || r.width > 16 || r.height < 3 || r.height > 16) return false;
          const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(getComputedStyle(e).backgroundColor);
          if (!m) return false;
          const [, r0, g0, b0] = m.map(Number);
          return b0 > 140 && b0 - r0 > 40;
        });
        return cands.map((e) => {
          const r = e.getBoundingClientRect();
          const cs = getComputedStyle(e);
          // 往上找 6 层，每层都记一次 innerText，找到第一个非空
          const chain = [];
          let p = e;
          for (let i = 0; i < 6 && p; i += 1, p = p.parentElement) {
            chain.push({ up: i, tag: p.tagName,
              cls: (p.className || '').toString().slice(0, 46),
              text: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) });
          }
          const first = chain.find((c) => c.text && c.text.length > 1);
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            bg: cs.backgroundColor, radius: cs.borderRadius,
            pointerEvents: cs.pointerEvents, zIndex: cs.zIndex,
            owner: first ? first.text : null, ownerUp: first ? first.up : null,
            chain };
        });
      });
      console.log(`  蓝点 ${dots.length} 个:`);
      for (const d of dots) {
        console.log(`   [${d.rect}] bg=${d.bg} pe=${d.pointerEvents} → 归属「${d.owner}」(上${d.ownerUp}层)`);
      }
      out.blueDot = { dots, total: dots.length,
        inPanel: dots.filter((d) => d.owner && /^(调度故事板|故事板|人像质感调节|25宫格|剧情推演|画面推演|720全景|多机位|角色|场景设定|产品设定|电影级)/.test(d.owner)).length };
      console.log('  归属为预设条目的:', out.blueDot.inPanel, '个');
      await shot(page, 'M-185-预设工作流-蓝点.png');
      out.shot3 = 'M-185-预设工作流-蓝点.png';
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
  }

  await logStep(B, {
    id: 'BD4-correct-toggle-criterion',
    title: '推翻 BD3 判据：只有 class 里的 bg-canvas-controls-active 才算「开着」',
    target: 'BD3 用「背景色非透明」当开启判据，但鼠标 click 后仍停在按钮上，'
      + 'hover:bg-canvas-controls-hover 会把背景染成 rgba(255,255,255,0.1) —— 看起来像开着。'
      + '对照组切换小地图 露了底：真开启时 class 多出 bg-canvas-controls-active、背景 0.15。'
      + '这轮用 class 当唯一判据，且每次回读前把鼠标移开。',
    evidence: out,
    visible_text: JSON.stringify({ bar: out.bar, rounds: out.rounds, gridOn: out.gridOn, gridOff: out.gridOff }).slice(0, 3500),
    shot: out.shot2,
  });
  console.log('\nBD4 完成');
} finally {
  await browser.close();
}
